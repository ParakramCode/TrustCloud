"""
TrustCloud AI — Conversation Request/Response Schemas

Pydantic models for the conversation-level trust evaluation endpoint.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List


class ConversationMessage(BaseModel):
    """A single message in a multi-turn conversation."""

    role: str = Field(
        ...,
        description="Message role: 'system', 'user', or 'assistant'.",
    )
    content: str = Field(
        ...,
        description="Message content text.",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"system", "user", "assistant"}
        if v.lower() not in allowed:
            raise ValueError(f"Role must be one of {allowed}, got '{v}'.")
        return v.lower()


class ConversationRequest(BaseModel):
    """Request schema for conversation-level trust evaluation."""

    messages: List[ConversationMessage] = Field(
        ...,
        min_length=2,
        description="Ordered list of conversation messages. Must contain at least 2 messages.",
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Optional metadata (LLM provider, model, temperature, etc.).",
    )
    evaluate_user_turns: bool = Field(
        default=False,
        description="If True, also evaluate user messages (default: only assistant turns).",
    )

    @field_validator("messages")
    @classmethod
    def must_have_assistant_turn(cls, v: List[ConversationMessage]) -> List[ConversationMessage]:
        has_assistant = any(m.role == "assistant" for m in v)
        if not has_assistant:
            raise ValueError("Conversation must contain at least one assistant message to evaluate.")
        return v
