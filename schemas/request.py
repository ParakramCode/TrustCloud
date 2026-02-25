"""
TrustCloud AI — Request Schemas
Input validation and boundary enforcement.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict


class TrustRequest(BaseModel):
    """Validated input for trust evaluation."""

    text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="AI-generated text to evaluate for trustworthiness."
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Optional metadata about the source LLM (provider, model, temperature, etc.)."
    )
    validators: Optional[list[str]] = Field(
        default=None,
        description="Optional list of specific validator names to run. If None, all validators run."
    )

    @field_validator("text")
    @classmethod
    def text_must_have_content(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("Text too short for meaningful evaluation (minimum 10 characters after stripping).")
        return stripped
