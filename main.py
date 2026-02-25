"""
TrustCloud AI — Application Entry Point

This file is a thin shell. All logic lives in:
- api/v1/routes.py      → versioned API endpoints
- api/dependencies.py   → dependency injection
- trust_engine/          → evaluation pipeline
- validators/            → validator plugins
- storage/               → storage backends
- schemas/               → request/response models + config
"""

import logging
from fastapi import FastAPI
from api.v1.routes import router as v1_router

# ──────────────────────────────────────
# Logging
# ──────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

# ──────────────────────────────────────
# Application
# ──────────────────────────────────────
app = FastAPI(
    title="TrustCloud AI",
    description="Modular AI trust evaluation engine with pluggable validators.",
    version="0.2.0",
)

# Mount versioned routes
app.include_router(v1_router)


# ──────────────────────────────────────
# Root health check (unversioned)
# ──────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "TrustCloud AI",
        "docs": "/docs",
        "health": "/v1/health",
        "evaluate": "/v1/evaluate",
    }