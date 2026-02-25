"""
TrustCloud AI — Response Schemas
Structured output from the trust evaluation pipeline.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, List


class ValidatorResult(BaseModel):
    """Result from a single validator execution."""

    name: str = Field(..., description="Validator identifier.")
    version: str = Field(..., description="Validator version string.")
    score: Optional[float] = Field(None, description="Score in [0, 1]. None if validator failed.")
    error: Optional[str] = Field(None, description="Error message if the validator failed.")
    latency_ms: float = Field(..., description="Execution time in milliseconds.")

    @property
    def succeeded(self) -> bool:
        return self.score is not None and self.error is None


class TrustResponse(BaseModel):
    """Full trust evaluation response."""

    trust_score: float = Field(..., ge=0.0, le=1.0, description="Aggregated trust score.")
    trust_level: str = Field(..., description="Trust level classification: HIGH, MEDIUM, or LOW.")
    signals: Dict[str, Optional[float]] = Field(
        ..., description="Per-validator signal scores. None for failed validators."
    )
    validator_results: List[ValidatorResult] = Field(
        ..., description="Detailed per-validator execution results."
    )
    validators_run: int = Field(..., description="Number of validators executed.")
    validators_failed: int = Field(0, description="Number of validators that failed.")
    engine_version: str = Field(..., description="Trust engine version string.")
