"""
TrustCloud AI — Trust Engine (Epistemic Trust Model)

Facade that wires registry, orchestrator, and epistemic aggregator.
Produces a full epistemic trust assessment.
"""

import logging
from typing import List, Optional

from schemas.config import EngineConfig
from schemas.response import (
    TrustResponse,
    EpistemicAssessment,
    DimensionResult,
    DefeaterStatus,
    ConfidenceFactors,
)
from trust_engine.registry import ValidatorRegistry
from trust_engine.orchestrator import TrustOrchestrator
from trust_engine.aggregator import (
    AggregationStrategy,
    EpistemicAggregationStrategy,
)

logger = logging.getLogger("trustcloud.engine")


class TrustEngine:
    """
    Top-level facade for the epistemic trust evaluation pipeline.

    The engine orchestrates:
    1. Validator registry (which validators exist)
    2. Orchestrator (how validators are executed — concurrently, with timeouts)
    3. Aggregator (how results are combined — epistemic model)

    The output is a TrustResponse that encodes the full epistemic assessment.
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        aggregation_strategy: Optional[AggregationStrategy] = None,
    ):
        self.config = config or EngineConfig()

        # Build registry and auto-discover validators
        self.registry = ValidatorRegistry()
        self.registry.auto_discover()
        logger.info(f"TrustEngine initialized with {len(self.registry)} validators: {self.registry.names()}")

        # Build orchestrator
        self.orchestrator = TrustOrchestrator(
            timeout_seconds=self.config.validator_timeout_seconds,
        )

        # Build aggregator (default: epistemic)
        self.aggregator = aggregation_strategy or EpistemicAggregationStrategy()

    def evaluate(
        self,
        text: str,
        validator_names: Optional[List[str]] = None,
    ) -> TrustResponse:
        """
        Run epistemic trust evaluation on the input text.

        Args:
            text: AI-generated text to evaluate.
            validator_names: Optional list of validator names to run.

        Returns:
            TrustResponse with full epistemic assessment.
        """
        # Resolve which validators to run
        if validator_names:
            validators = self.registry.get_many(validator_names)
        else:
            validators = self.registry.all()

        # Run orchestrator (concurrent, with timeouts)
        orchestrator_results = self.orchestrator.run_all(
            validators=validators,
            text=text,
            concurrent=self.config.enable_concurrent,
        )

        # Build validator lookup for aggregator
        validator_map = {v.name: v for v in validators}

        # Aggregate using epistemic strategy
        agg = self.aggregator.aggregate(
            results=orchestrator_results,
            validators=validator_map,
        )

        # ── Build structured response ──

        # Dimension results
        dimensions = []
        failed_count = 0

        for r in orchestrator_results:
            v = validator_map.get(r.name)
            if r.succeeded and v:
                dimensions.append(DimensionResult(
                    name=r.name,
                    version=r.version,
                    signal_type=v.signal_type,
                    method_type=v.method_type,
                    score=round(r.output.score, 3),
                    uncertainty=round(r.output.uncertainty, 3),
                    interval=list(r.output.interval),
                    explanation=r.output.explanation,
                    evidence=r.output.evidence,
                    error=None,
                    latency_ms=r.latency_ms,
                ))
            else:
                dimensions.append(DimensionResult(
                    name=r.name,
                    version=r.version,
                    signal_type=v.signal_type if v else "unknown",
                    method_type=v.method_type if v else "unknown",
                    score=None,
                    uncertainty=None,
                    interval=None,
                    explanation=None,
                    evidence=None,
                    error=r.error,
                    latency_ms=r.latency_ms,
                ))
                failed_count += 1

        # Defeater statuses
        defeaters = [
            DefeaterStatus(
                name=ds["name"],
                severity=ds["severity"],
                threshold=ds["threshold"],
                active=ds["active"],
                explanation=ds["explanation"],
            )
            for ds in agg["defeater_statuses"]
        ]

        # Confidence factors
        cf = agg.get("confidence_factors", {})
        confidence_factors = ConfidenceFactors(
            validator_success_rate=cf.get("validator_success_rate", 0.0),
            mean_uncertainty=cf.get("mean_uncertainty", 0.5),
            input_quality=cf.get("input_quality", 1.0),
            dimension_coverage=cf.get("dimension_coverage", 0.0),
        )

        # Core assessment
        assessment = EpistemicAssessment(
            composite_trust=agg["composite_trust"],
            confidence=agg["confidence"],
            trust_level=agg["trust_level"],
            defeated=agg["defeated"],
            interpretation=agg["interpretation"],
        )

        return TrustResponse(
            assessment=assessment,
            dimensions=dimensions,
            defeaters=defeaters,
            confidence_factors=confidence_factors,
            engine_version=self.config.version,
            validators_run=len(orchestrator_results),
            validators_failed=failed_count,
            blind_spots=agg["blind_spots"],
        )
