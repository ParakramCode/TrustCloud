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
    }
