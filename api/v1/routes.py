"""
TrustCloud AI — API v1 Routes
Versioned API endpoints for epistemic trust evaluation.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from schemas.request import TrustRequest
from schemas.response import TrustResponse
from schemas.conversation import ConversationRequest
from api.dependencies import get_engine, get_storage, get_config

logger = logging.getLogger("trustcloud.api.v1")

router = APIRouter(prefix="/v1", tags=["v1"])


def _write_telemetry(record: dict, record_id: str) -> None:
    """Background task: write evaluation telemetry to storage."""
    try:
        storage = get_storage()
        storage.write(record, record_id)
    except Exception as e:
        logger.error(f"Storage write failed for record {record_id}: {e}")


@router.post("/evaluate", response_model=TrustResponse)
def evaluate(req: TrustRequest, background_tasks: BackgroundTasks):
    """
    Evaluate AI-generated text for epistemic trustworthiness.

    Returns a structured epistemic trust assessment including:
    - Per-dimension scores with uncertainty bounds
    - Defeater statuses
    - System confidence (distinct from text trust)
    - Known blind spots

    Storage of telemetry records happens asynchronously.
    """
    engine = get_engine()
    config = get_config()

    # Run epistemic evaluation
    try:
        result = engine.evaluate(
            text=req.text,
            validator_names=req.validators,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "available_validators": engine.registry.names(),
            },
        )

    # Build telemetry record
    record_id = str(uuid.uuid4())
    record = {
        "id": record_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": {
            "text": req.text,
            "text_length": len(req.text),
            "metadata": req.metadata,
        },
        "assessment": {
            "engine_version": config.engine.version,
            "composite_trust": result.assessment.composite_trust,
            "confidence": result.assessment.confidence,
            "trust_level": result.assessment.trust_level,
            "defeated": result.assessment.defeated,
        },
        "dimensions": [
            {
                "name": d.name,
                "signal_type": d.signal_type,
                "score": d.score,
                "uncertainty": d.uncertainty,
                "interval": d.interval,
                "latency_ms": d.latency_ms,
                "error": d.error,
            }
            for d in result.dimensions
        ],
        "defeaters": [
            {
                "name": df.name,
                "severity": df.severity,
                "active": df.active,
            }
            for df in result.defeaters
        ],
    }

    # Queue async storage write
    background_tasks.add_task(_write_telemetry, record, record_id)

    return result


@router.post("/evaluate/conversation")
def evaluate_conversation(req: ConversationRequest, background_tasks: BackgroundTasks):
    """
    Evaluate epistemic trust across a multi-turn conversation.

    Runs the full TrustEngine on each assistant turn independently,
    then computes:
    - Per-turn trust scores and dimension breakdowns
    - Trust decay trends (linear regression over turn index)
    - Semantic drift (embedding similarity to conversation anchor)
    - Defeater accumulation timeline

    This endpoint is designed for studying epistemic quality
    degradation in long LLM conversations.
    """
    from trust_engine.conversation import ConversationAnalyzer

    engine = get_engine()
    config = get_config()

    analyzer = ConversationAnalyzer(engine=engine)

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        report = analyzer.analyze(
            messages=messages,
            evaluate_user_turns=req.evaluate_user_turns,
        )
    except Exception as e:
        logger.error(f"Conversation analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Conversation analysis failed: {str(e)}"},
        )

    # Build telemetry record
    record_id = str(uuid.uuid4())
    record = {
        "id": record_id,
        "type": "conversation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": req.metadata,
        "turn_count": len(req.messages),
        "evaluated_turns": report.get("evaluated_turns", 0),
        "summary": report.get("conversation_summary", {}),
    }

    background_tasks.add_task(_write_telemetry, record, record_id)

    return report


@router.get("/validators")
def list_validators():
    """List all registered validators with epistemic metadata."""
    engine = get_engine()
    return {
        "validators": engine.registry.info(),
        "count": len(engine.registry),
        "model": "epistemic_trust_v1",
    }


@router.get("/health")
def health():
    """Health check with epistemic model information."""
    engine = get_engine()
    config = get_config()

    # Count by signal type
    validators_info = engine.registry.info()
    positive_count = sum(1 for v in validators_info if v.get("signal_type") == "positive_indicator")
    defeater_count = sum(1 for v in validators_info if v.get("signal_type") == "defeater")

    return {
        "status": "ok",
        "service": "TrustCloud AI",
        "model": "epistemic_trust_v1",
        "engine_version": config.engine.version,
        "validators_loaded": len(engine.registry),
        "positive_indicators": positive_count,
        "defeaters": defeater_count,
        "storage_backend": config.storage.backend,
        "endpoints": {
            "evaluate": "/v1/evaluate",
            "evaluate_conversation": "/v1/evaluate/conversation",
            "validators": "/v1/validators",
        },
    }

