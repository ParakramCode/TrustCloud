from fastapi import FastAPI
from schemas.request import TrustRequest
from schemas.response import TrustResponse
from trust_engine.engine import TrustEngine

import boto3
import json
import uuid
from datetime import datetime

# ----------------------------
# App setup
# ----------------------------

app = FastAPI(title="TrustCloud AI", version="0.1")

engine = TrustEngine()

# ----------------------------
# AWS S3 Setup
# ----------------------------
# Uses IAM Role auth (NO hardcoded credentials)
s3 = boto3.client("s3")
S3_BUCKET = "trustcloud-ai-raw"   # must exist in AWS

# ----------------------------
# System Metadata
# ----------------------------

TRUST_ENGINE_METADATA = {
    "name": "TrustEngine",
    "version": "trust-engine-v1",
    "validators": [
        "coherence",
        "contradiction",
        "hallucination",
        "reasoning_depth",
        "factuality",
        "semantic_consistency"
    ]
}

# Change this depending on what model produced the text
LLM_METADATA = {
    "provider": "openai",        # openai | google | anthropic | local | etc
    "model": "gpt-4.1",
    "version": "2025-02-15",
    "type": "chat",
    "temperature": 0.2,
    "top_p": 0.9
}

# ----------------------------
# Routes
# ----------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "TrustCloud AI",
        "engine": TRUST_ENGINE_METADATA["version"]
    }

@app.post("/evaluate", response_model=TrustResponse)
def evaluate(req: TrustRequest):
    # --- Trust evaluation ---
    result = engine.evaluate(req.text)

    # --- Record schema (research-grade telemetry) ---
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),

        "input": {
            "text": req.text
        },

        "llm": LLM_METADATA,

        "trust_engine": {
            "metadata": TRUST_ENGINE_METADATA,
            "output": result.model_dump()
        }
    }

    # --- S3 storage path (time-partitioned data lake layout) ---
    date_path = datetime.utcnow().strftime("%Y/%m/%d")
    key = f"raw/{date_path}/{record['id']}.json"

    # --- Store in S3 ---
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(record),
        ContentType="application/json"
    )

    # --- API response ---
    return result