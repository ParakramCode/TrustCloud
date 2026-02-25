"""
TrustCloud AI — API v1 Routes
Versioned API endpoints for trust evaluation.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks

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
        # Storage failure NEVER blocks the API response.
        # Log and move on. The evaluation result was already returned.
        logger.error(f"Storage write failed for record {record_id}: {e}")


@router.post("/evaluate", response_model=TrustResponse)
def evaluate(req: TrustRequest, background_tasks: BackgroundTasks):
    """
    Evaluate AI-generated text for trustworthiness.

    Runs all registered validators (or a subset if `validators` is specified),
    aggregates scores, and returns a structured trust assessment.

    Storage of telemetry records happens asynchronously in the background.
    """
    engine = get_engine()
    config = get_config()

    # Run evaluation
    result = engine.evaluate(
        text=req.text,
        validator_names=req.validators,
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
        "evaluation": {
            "engine_version": config.engine.version,
            "trust_score": result.trust_score,
            "trust_level": result.trust_level,
            "signals": result.signals,
            "validators_run": result.validators_run,
            "validators_failed": result.validators_failed,
            "validator_details": [
                {
                    "name": vr.name,
                    "version": vr.version,
                    "score": vr.score,
                    "error": vr.error,
                    "latency_ms": vr.latency_ms,
                }
                for vr in result.validator_results
            ],
        },
    }

    # Queue async storage write (non-blocking)
    background_tasks.add_task(_write_telemetry, record, record_id)

    return result


@router.get("/validators")
def list_validators():
    """List all registered validators with metadata."""
    engine = get_engine()
    return {
        "validators": engine.registry.info(),
        "count": len(engine.registry),
    }


@router.get("/health")
def health():
    """Health check endpoint."""
    engine = get_engine()
    config = get_config()
    return {
        "status": "ok",
        "service": "TrustCloud AI",
        "engine_version": config.engine.version,
        "validators_loaded": len(engine.registry),
        "validator_names": engine.registry.names(),
        "storage_backend": config.storage.backend,
    }
