"""
TrustCloud AI — Trust Aggregator
Pluggable aggregation strategies with knockout logic and signal gating.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from trust_engine.orchestrator import OrchestratorResult
from validators.base import BaseValidator

logger = logging.getLogger("trustcloud.aggregator")


class AggregationStrategy(ABC):
    """Abstract aggregation strategy. Implement to create custom scoring logic."""

    @abstractmethod
    def aggregate(
        self,
        results: List[OrchestratorResult],
        validators: Dict[str, BaseValidator],
    ) -> tuple[float, str]:
        """
        Compute a trust score from validator results.

        Args:
            results: Orchestrator results for each validator.
            validators: Name → BaseValidator map for accessing weights and inversion flags.

        Returns:
            Tuple of (trust_score: float, trust_level: str).
        """
        ...


class WeightedAverageStrategy(AggregationStrategy):
    """
    Standard weighted average.
    Automatically handles inverted signals and missing validators.
    Weights are normalized to sum to 1.0 based on validators that succeeded.
    """

    def aggregate(
        self,
        results: List[OrchestratorResult],
        validators: Dict[str, BaseValidator],
    ) -> tuple[float, str]:
        # Collect successful results with their weights
        weighted_pairs = []

        for r in results:
            if not r.succeeded:
                logger.warning(f"Skipping failed validator '{r.name}' in aggregation.")
                continue

            v = validators.get(r.name)
            if v is None:
                continue

            score = r.output.score
            # Handle inverted signals (higher = worse)
            trust_contribution = (1.0 - score) if v.inverted else score
            weighted_pairs.append((trust_contribution, v.default_weight))

        if not weighted_pairs:
            logger.error("No successful validators — returning 0.0 trust score.")
            return 0.0, "UNKNOWN"

        # Normalize weights to sum to 1.0
        total_weight = sum(w for _, w in weighted_pairs)
        if total_weight == 0:
            return 0.0, "UNKNOWN"

        trust_score = sum(score * weight / total_weight for score, weight in weighted_pairs)
        trust_score = round(trust_score, 3)

        level = _classify_level(trust_score)
        return trust_score, level


class KnockoutGatedStrategy(AggregationStrategy):
    """
    Weighted average with knockout conditions.

    If ANY inverted signal (contradiction, hallucination_risk) exceeds a
    critical threshold, the trust score is capped regardless of other signals.

    This prevents nonsensical results like:
    "contradiction=0.95 but overall trust=MEDIUM" (which the old system produced).
    """

    def __init__(self, knockout_threshold: float = 0.7, knockout_cap: float = 0.3):
        """
        Args:
            knockout_threshold: If any inverted signal exceeds this, knockout triggers.
            knockout_cap: Maximum trust score when knockout is active.
        """
        self.knockout_threshold = knockout_threshold
        self.knockout_cap = knockout_cap

    def aggregate(
        self,
        results: List[OrchestratorResult],
        validators: Dict[str, BaseValidator],
    ) -> tuple[float, str]:
        # First, check knockout conditions
        knockout_triggered = False
        knockout_reason = ""

        for r in results:
            if not r.succeeded:
                continue
            v = validators.get(r.name)
            if v is None:
                continue

            if v.inverted and r.output.score > self.knockout_threshold:
                knockout_triggered = True
                knockout_reason = (
                    f"Knockout: '{r.name}' score {r.output.score:.3f} "
                    f"exceeds threshold {self.knockout_threshold}"
                )
                logger.warning(knockout_reason)
                break

        # Compute base weighted average
        weighted_pairs = []
        for r in results:
            if not r.succeeded:
                continue
            v = validators.get(r.name)
            if v is None:
                continue
            score = r.output.score
            trust_contribution = (1.0 - score) if v.inverted else score
            weighted_pairs.append((trust_contribution, v.default_weight))

        if not weighted_pairs:
            return 0.0, "UNKNOWN"

        total_weight = sum(w for _, w in weighted_pairs)
        if total_weight == 0:
            return 0.0, "UNKNOWN"

        trust_score = sum(s * w / total_weight for s, w in weighted_pairs)

        # Apply knockout cap
        if knockout_triggered:
            trust_score = min(trust_score, self.knockout_cap)

        trust_score = round(trust_score, 3)
        level = _classify_level(trust_score)
        return trust_score, level


def _classify_level(score: float) -> str:
    """Classify a trust score into a human-readable level."""
    if score > 0.75:
        return "HIGH"
    elif score > 0.5:
        return "MEDIUM"
    else:
        return "LOW"
