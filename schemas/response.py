"""
TrustCloud AI — Epistemic Trust Response Schema

The response schema encodes the full epistemic trust assessment.
Instead of a single score, the system reports:
- Per-dimension scores with uncertainty bounds
- Defeater status (whether epistemic defeaters are active)
- System confidence (distinct from text trust)
- Known blind spots (what the system cannot assess)
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, List


class DimensionResult(BaseModel):
    """Result from a single trust dimension (validator)."""

    name: str = Field(..., description="Dimension identifier.")
    version: str = Field(..., description="Validator version string.")
    signal_type: str = Field(..., description="'positive_indicator' or 'defeater'.")
    method_type: str = Field(..., description="Measurement methodology used.")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Point estimate in [0, 1]. None if failed.")
    uncertainty: Optional[float] = Field(None, ge=0.0, le=0.5, description="Epistemic uncertainty bound.")
    interval: Optional[list[float]] = Field(None, description="95% credible interval [lower, upper].")
    explanation: Optional[str] = Field(None, description="Human-readable explanation for the score.")
    evidence: Optional[list[dict]] = Field(None, description="Specific evidence items supporting the score.")
    error: Optional[str] = Field(None, description="Error message if the validator failed.")
    latency_ms: float = Field(..., description="Execution time in milliseconds.")

    @property
    def succeeded(self) -> bool:
        return self.score is not None and self.error is None


class DefeaterStatus(BaseModel):
    """Status of an epistemic defeater."""

    name: str = Field(..., description="Defeater identifier.")
    severity: Optional[float] = Field(None, description="Defeater score (higher = more severe).")
    threshold: float = Field(..., description="Activation threshold.")
    active: bool = Field(..., description="Whether this defeater is currently triggered.")
    explanation: Optional[str] = Field(None, description="Why this defeater fired or didn't.")


class ConfidenceFactors(BaseModel):
    """Breakdown of what contributes to system confidence."""

    validator_success_rate: float = Field(..., description="Fraction of validators that succeeded.")
    mean_uncertainty: float = Field(..., description="Average uncertainty across dimensions.")
    input_quality: float = Field(..., description="Input text quality factor (length-based).")
    dimension_coverage: float = Field(..., description="Fraction of trust dimensions measured.")


class EpistemicAssessment(BaseModel):
    """The core epistemic trust assessment."""

    composite_trust: float = Field(..., ge=0.0, le=1.0, description="Aggregated trust estimate.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="System confidence in its own assessment (NOT text correctness).")
    trust_level: str = Field(..., description="Categorical: HIGH, MEDIUM, LOW, or DEFEATED.")
    defeated: bool = Field(False, description="Whether any epistemic defeater is active.")
    interpretation: str = Field(..., description="Natural language interpretation of the assessment.")


class TrustResponse(BaseModel):
    """
    Full epistemic trust evaluation response.

    This response embodies the epistemic trust model:
    - composite_trust is a point estimate with known uncertainty
    - confidence measures how much the system trusts its OWN assessment
    - defeaters are separated from positive indicators
    - blind_spots explicitly declare what the system CANNOT assess
    """

    # Core assessment
    assessment: EpistemicAssessment = Field(..., description="Aggregated epistemic trust assessment.")

    # Per-dimension details
    dimensions: List[DimensionResult] = Field(
        ..., description="Detailed results for each trust dimension."
    )

    # Defeater status
    defeaters: List[DefeaterStatus] = Field(
        ..., description="Status of each epistemic defeater."
    )

    # Confidence breakdown
    confidence_factors: ConfidenceFactors = Field(
        ..., description="Factors contributing to system confidence."
    )

    # Meta
    engine_version: str = Field(..., description="Trust engine version.")
    validators_run: int = Field(..., description="Total validators executed.")
    validators_failed: int = Field(0, description="Validators that failed.")

    # Epistemic honesty
    blind_spots: List[str] = Field(
        ...,
        description="Known limitations: what the system CANNOT assess. Epistemic honesty requires declaring these."
    )
