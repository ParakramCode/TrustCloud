"""
TrustCloud AI — Trust Engine (Facade)
Wires together registry, orchestrator, and aggregator into a single evaluate() call.
"""

import logging
from typing import List, Optional

from schemas.config import EngineConfig
from schemas.response import TrustResponse, ValidatorResult
from trust_engine.registry import ValidatorRegistry
from trust_engine.orchestrator import TrustOrchestrator
from trust_engine.aggregator import (
    AggregationStrategy,
    KnockoutGatedStrategy,
)

logger = logging.getLogger("trustcloud.engine")


class TrustEngine:
    """
    Top-level facade for the trust evaluation pipeline.

    Responsibilities:
    - Owns the validator registry
    - Owns the orchestrator and aggregator
    - Provides evaluate() as the single entry point
    - Handles selective evaluation (run only specific validators)
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

        # Build aggregator (default: knockout-gated)
        self.aggregator = aggregation_strategy or KnockoutGatedStrategy()

    def evaluate(
        self,
        text: str,
        validator_names: Optional[List[str]] = None,
    ) -> TrustResponse:
        """
        Run trust evaluation on the input text.

        Args:
            text: AI-generated text to evaluate.
            validator_names: Optional list of validator names to run.
                             If None, all registered validators run.

        Returns:
            TrustResponse with scores, signals, and per-validator details.
        """
        # Resolve which validators to run
        if validator_names:
            validators = self.registry.get_many(validator_names)
        else:
            validators = self.registry.all()

        # Run orchestrator
        orchestrator_results = self.orchestrator.run_all(
            validators=validators,
            text=text,
            concurrent=self.config.enable_concurrent,
        )

        # Build validator lookup for aggregator
        validator_map = {v.name: v for v in validators}

        # Aggregate
        trust_score, trust_level = self.aggregator.aggregate(
            results=orchestrator_results,
            validators=validator_map,
        )

        # Build response
        signals = {}
        validator_results = []
        failed_count = 0

        for r in orchestrator_results:
            signals[r.name] = r.output.score if r.succeeded else None
            validator_results.append(ValidatorResult(
                name=r.name,
                version=r.version,
                score=r.output.score if r.succeeded else None,
                error=r.error,
                latency_ms=r.latency_ms,
            ))
            if not r.succeeded:
                failed_count += 1

        return TrustResponse(
            trust_score=trust_score,
            trust_level=trust_level,
            signals=signals,
            validator_results=validator_results,
            validators_run=len(orchestrator_results),
            validators_failed=failed_count,
            engine_version=self.config.version,
        )
