"""
TrustCloud AI — Base Validator Interface (Epistemic Trust Model)

All validators must implement this abstract base class.
Each validator is a measurement instrument that produces:
- A point estimate (score)
- An uncertainty bound (how much the score could vary)
- An explanation (why the score is what it is)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidatorOutput:
    """
    Standard output from a validator run.

    Epistemic trust requires that every measurement
    reports not just a value, but also its uncertainty.
    A score without uncertainty is epistemically incomplete.
    """

    score: float                          # Signal value in [0, 1]
    uncertainty: float                    # Epistemic uncertainty in [0, 1]
    explanation: str                      # Human-readable reason for the score
    evidence: Optional[list[dict]] = None # Specific evidence items that support the score

    @property
    def lower_bound(self) -> float:
        """Lower bound of 95% credible interval."""
        return max(0.0, self.score - 1.96 * self.uncertainty)

    @property
    def upper_bound(self) -> float:
        """Upper bound of 95% credible interval."""
        return min(1.0, self.score + 1.96 * self.uncertainty)

    @property
    def interval(self) -> tuple[float, float]:
        """95% credible interval as (lower, upper)."""
        return (round(self.lower_bound, 3), round(self.upper_bound, 3))


class BaseValidator(ABC):
    """
    Abstract base class for all trust validators.

    Epistemic Framework:
    - Each validator is a MEASUREMENT INSTRUMENT for one dimension of trust.
    - Measurements have inherent uncertainty depending on the method used.
    - Validators declare their signal_type: "positive_indicator" or "defeater".

    Positive indicators contribute to trust when high.
    Defeaters reduce or cap trust when high (contradiction, hallucination).

    To create a new validator:
    1. Subclass BaseValidator
    2. Implement all abstract properties and run()
    3. Place the file in the validators/ directory
    4. Add the class to BUILTIN_VALIDATORS in validators/__init__.py
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this validator (e.g., 'coherence')."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Version string (e.g., 'v1.0')."""
        ...

    @property
    @abstractmethod
    def default_weight(self) -> float:
        """Default aggregation weight in [0, 1]. Weights are normalized at aggregation time."""
        ...

    @property
    @abstractmethod
    def method_type(self) -> str:
        """
        The measurement methodology used by this validator.
        Used for uncertainty estimation.

        Standard values:
        - 'embedding_similarity'   — model-based, relatively stable (base σ ≈ 0.08)
        - 'keyword_heuristic'      — rule-based, high variance (base σ ≈ 0.20)
        - 'nlp_pipeline'           — spaCy/NER-based, moderate (base σ ≈ 0.12)
        - 'sentiment_analysis'     — TextBlob-based, moderate-high (base σ ≈ 0.15)
        """
        ...

    @property
    def signal_type(self) -> str:
        """
        The epistemic nature of this signal.

        'positive_indicator' — Higher score = MORE trustworthy.
                               Combined additively in aggregation.

        'defeater'           — Higher score = LESS trustworthy.
                               Applied as gates/caps on the composite score.
                               A single strong defeater can override positive indicators.

        Default: 'positive_indicator'.
        """
        return "positive_indicator"

    @property
    def inverted(self) -> bool:
        """Convenience: True if this is a defeater signal."""
        return self.signal_type == "defeater"

    @abstractmethod
    def run(self, text: str) -> ValidatorOutput:
        """
        Execute this validator on the input text.

        Returns:
            ValidatorOutput with score, uncertainty, and explanation.

        Raises:
            Any exception — the orchestrator catches and records failures.
        """
        ...


# ─────────────────────────────────────────────────
# Uncertainty estimation helpers
# ─────────────────────────────────────────────────

# Base uncertainty per method type.
# These are rough estimates. Proper values require calibration data.
BASE_UNCERTAINTY = {
    "embedding_similarity": 0.08,
    "keyword_heuristic": 0.20,
    "nlp_pipeline": 0.12,
    "sentiment_analysis": 0.15,
}


def estimate_uncertainty(method_type: str, text: str) -> float:
    """
    Estimate epistemic uncertainty for a measurement.

    Combines the base uncertainty of the method with a complexity
    factor based on input characteristics.

    This is an approximation. True uncertainty requires calibration
    against labeled data, which is acknowledged as a blind spot.
    """
    base = BASE_UNCERTAINTY.get(method_type, 0.15)

    # Complexity factor: more sentences = more measurement variance
    sentence_count = max(len([s for s in text.split(".") if s.strip()]), 1)

    import math
    complexity_factor = 1.0 + 0.1 * math.log(max(sentence_count / 2, 1))

    # Short texts have higher uncertainty (less signal to measure)
    length_factor = 1.0
    if len(text) < 50:
        length_factor = 1.5  # very short text = much higher uncertainty
    elif len(text) < 100:
        length_factor = 1.2

    uncertainty = base * complexity_factor * length_factor

    return round(min(uncertainty, 0.5), 3)  # Cap at 0.5 (maximum reasonable uncertainty)
