"""
TrustCloud AI — Epistemic Trust Aggregator

Aggregation strategies for the epistemic trust model.

Key principles:
1. Positive indicators are combined via uncertainty-weighted average.
2. Defeaters are applied as gates — a strong defeater CAPS the composite.
3. Dimensions with higher uncertainty contribute LESS to the aggregate.
4. System confidence is computed separately from text trust.
5. Known blind spots are declared explicitly.
"""

import logging
import math
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from trust_engine.orchestrator import OrchestratorResult
from validators.base import BaseValidator

logger = logging.getLogger("trustcloud.aggregator")


# ─────────────────────────────────────────────────
# Known blind spots — what TrustCloud cannot assess
# ─────────────────────────────────────────────────

SYSTEM_BLIND_SPOTS = [
    "Factual accuracy of specific claims is not verified against external knowledge bases or databases.",
    "Source attribution and citation validity are not assessed.",
    "Domain-specific correctness is not evaluated (no domain expert model).",
    "Temporal validity is not checked — claims may be outdated.",
    "Cultural and contextual appropriateness is not measured.",
    "Intentional deception by the text author cannot be detected if the text is internally consistent.",
]


class AggregationStrategy(ABC):
    """Abstract aggregation strategy."""

    @abstractmethod
    def aggregate(
        self,
        results: List[OrchestratorResult],
        validators: Dict[str, BaseValidator],
    ) -> dict:
        """
        Compute an epistemic trust assessment from validator results.

        Returns a dict with:
        - composite_trust: float
        - confidence: float
        - trust_level: str
        - defeated: bool
        - interpretation: str
        - defeater_statuses: list
        - confidence_factors: dict
        - blind_spots: list
        """
        ...


class EpistemicAggregationStrategy(AggregationStrategy):
    """
    Epistemic trust aggregation.

    Architecture:
    1. Separate results into positive indicators and defeaters.
    2. Compute uncertainty-weighted average of positive indicators.
    3. Check defeaters against thresholds.
    4. If any defeater fires, cap the composite.
    5. Compute system confidence independently.
    6. Generate natural language interpretation.
    """

    def __init__(self, defeater_threshold: float = 0.7, defeater_cap: float = 0.3):
        self.defeater_threshold = defeater_threshold
        self.defeater_cap = defeater_cap

    def aggregate(
        self,
        results: List[OrchestratorResult],
        validators: Dict[str, BaseValidator],
    ) -> dict:

        # ── Step 1: Classify results ──
        positive_results = []
        defeater_results = []

        for r in results:
            v = validators.get(r.name)
            if v is None:
                continue
            if v.signal_type == "defeater":
                defeater_results.append((r, v))
            else:
                positive_results.append((r, v))

        # ── Step 2: Compute uncertainty-weighted positive aggregate ──
        composite = self._compute_positive_aggregate(positive_results)

        # ── Step 3: Evaluate defeaters ──
        defeater_statuses, defeated, active_defeater_name = self._evaluate_defeaters(defeater_results)

        # ── Step 4: Apply defeater cap ──
        if defeated:
            composite = min(composite, self.defeater_cap)

        composite = round(composite, 3)

        # ── Step 5: Compute system confidence ──
        all_succeeded = [(r, v) for r, v in positive_results + defeater_results if r.succeeded]
        total = len(positive_results) + len(defeater_results)
        confidence_factors = self._compute_confidence(
            results=results,
            succeeded_count=len(all_succeeded),
            total_count=total,
        )
        confidence = confidence_factors["overall"]

        # ── Step 6: Classify level ──
        if defeated:
            trust_level = "DEFEATED"
        elif composite > 0.75:
            trust_level = "HIGH"
        elif composite > 0.5:
            trust_level = "MEDIUM"
        else:
            trust_level = "LOW"

        # ── Step 7: Generate interpretation ──
        interpretation = self._generate_interpretation(
            composite=composite,
            confidence=confidence,
            trust_level=trust_level,
            defeated=defeated,
            active_defeater_name=active_defeater_name,
            total=total,
            succeeded=len(all_succeeded),
        )

        return {
            "composite_trust": composite,
            "confidence": round(confidence, 3),
            "trust_level": trust_level,
            "defeated": defeated,
            "interpretation": interpretation,
            "defeater_statuses": defeater_statuses,
            "confidence_factors": confidence_factors,
            "blind_spots": SYSTEM_BLIND_SPOTS,
        }

    def _compute_positive_aggregate(self, positive_results: list) -> float:
        """
        Uncertainty-weighted average of positive indicators.
        Dimensions with higher uncertainty contribute less.
        """
        weighted_pairs = []

        for r, v in positive_results:
            if not r.succeeded:
                continue

            score = r.output.score
            uncertainty = r.output.uncertainty
            weight = v.default_weight

            # Certainty-adjusted weight: more uncertain → less influence
            certainty = max(1.0 - uncertainty, 0.1)
            adjusted_weight = weight * certainty
            weighted_pairs.append((score, adjusted_weight))

        if not weighted_pairs:
            return 0.0

        total_weight = sum(w for _, w in weighted_pairs)
        if total_weight == 0:
            return 0.0

        return sum(s * w / total_weight for s, w in weighted_pairs)

    def _evaluate_defeaters(self, defeater_results: list) -> tuple:
        """
        Check each defeater against its threshold.
        Returns (statuses_list, defeated_bool, active_defeater_name).
        """
        statuses = []
        defeated = False
        active_name = None

        for r, v in defeater_results:
            if not r.succeeded:
                statuses.append({
                    "name": v.name,
                    "severity": None,
                    "threshold": self.defeater_threshold,
                    "active": False,
                    "explanation": f"Defeater '{v.name}' could not be evaluated (validator error).",
                })
                continue

            severity = r.output.score
            active = severity > self.defeater_threshold

            if active and not defeated:
                defeated = True
                active_name = v.name

            statuses.append({
                "name": v.name,
                "severity": round(severity, 3),
                "threshold": self.defeater_threshold,
                "active": active,
                "explanation": (
                    f"ACTIVE: {v.name} severity {severity:.3f} exceeds threshold {self.defeater_threshold}. "
                    f"Trust is capped at {self.defeater_cap}."
                ) if active else (
                    f"CLEAR: {v.name} severity {severity:.3f} is below threshold {self.defeater_threshold}."
                ),
            })

        return statuses, defeated, active_name

    def _compute_confidence(self, results: list, succeeded_count: int, total_count: int) -> dict:
        """
        Compute system confidence — how much the system trusts its OWN assessment.
        This is NOT a measure of text correctness.
        """
        # Factor 1: Validator success rate
        success_rate = succeeded_count / max(total_count, 1)

        # Factor 2: Mean uncertainty across succeeded validators
        uncertainties = [
            r.output.uncertainty for r in results
            if r.succeeded and r.output is not None
        ]
        mean_uncertainty = sum(uncertainties) / max(len(uncertainties), 1) if uncertainties else 0.5

        # Factor 3: Input quality (based on text length from first result)
        # Short texts offer less signal → lower confidence
        input_quality = 1.0  # default, adjusted below if we have data

        # Factor 4: Coverage (what fraction of dimensions do we have data for)
        coverage = succeeded_count / max(total_count, 1)

        # Overall confidence
        overall = success_rate * (1 - mean_uncertainty) * coverage
        overall = round(max(0.0, min(overall, 1.0)), 3)

        return {
            "overall": overall,
            "validator_success_rate": round(success_rate, 3),
            "mean_uncertainty": round(mean_uncertainty, 3),
            "input_quality": round(input_quality, 3),
            "dimension_coverage": round(coverage, 3),
        }

    def _generate_interpretation(
        self,
        composite: float,
        confidence: float,
        trust_level: str,
        defeated: bool,
        active_defeater_name: Optional[str],
        total: int,
        succeeded: int,
    ) -> str:
        """Generate a natural language interpretation of the assessment."""

        parts = []

        if defeated:
            parts.append(
                f"TRUST DEFEATED: Epistemic defeater '{active_defeater_name}' is active. "
                f"Composite trust is capped at {composite:.3f} regardless of other dimensions."
            )
        else:
            level_desc = {
                "HIGH": "high epistemic trust",
                "MEDIUM": "moderate epistemic trust",
                "LOW": "low epistemic trust",
            }
            parts.append(
                f"Assessment indicates {level_desc.get(trust_level, trust_level)} "
                f"(composite: {composite:.3f})."
            )

        conf_desc = "high" if confidence > 0.7 else ("moderate" if confidence > 0.4 else "low")
        parts.append(
            f"System confidence is {conf_desc} ({confidence:.3f}): "
            f"{succeeded}/{total} validators succeeded."
        )

        parts.append(
            "Note: This assessment evaluates textual properties only. "
            "Factual correctness of specific claims has not been independently verified."
        )

        return " ".join(parts)


class WeightedAverageStrategy(AggregationStrategy):
    """Legacy: Simple weighted average without epistemic features. Kept for comparison."""

    def aggregate(self, results, validators) -> dict:
        weighted_pairs = []
        for r in results:
            if not r.succeeded:
                continue
            v = validators.get(r.name)
            if v is None:
                continue
            score = r.output.score
            contrib = (1.0 - score) if v.inverted else score
            weighted_pairs.append((contrib, v.default_weight))

        if not weighted_pairs:
            return {"composite_trust": 0.0, "confidence": 0.0, "trust_level": "UNKNOWN",
                    "defeated": False, "interpretation": "No validators succeeded.",
                    "defeater_statuses": [], "confidence_factors": {}, "blind_spots": SYSTEM_BLIND_SPOTS}

        total = sum(w for _, w in weighted_pairs)
        score = round(sum(s * w / total for s, w in weighted_pairs), 3) if total > 0 else 0.0

        level = "HIGH" if score > 0.75 else ("MEDIUM" if score > 0.5 else "LOW")

        return {
            "composite_trust": score, "confidence": 0.5, "trust_level": level,
            "defeated": False, "interpretation": f"Simple weighted average: {score:.3f}.",
            "defeater_statuses": [], "confidence_factors": {},
            "blind_spots": SYSTEM_BLIND_SPOTS,
        }
