"""
TrustCloud AI — API Dependencies
Dependency injection for the FastAPI application.
Provides shared instances of engine and storage to route handlers.
"""

import logging
from functools import lru_cache

from schemas.config import AppConfig
from trust_engine.engine import TrustEngine
from storage.backend import StorageBackend, create_storage_backend

logger = logging.getLogger("trustcloud.api")


@lru_cache()
def get_config() -> AppConfig:
    """Load application configuration (cached singleton)."""
    config = AppConfig.from_env()
    logger.info(f"Loaded config: engine={config.engine.version}, storage={config.storage.backend}")
    return config


@lru_cache()
def get_engine() -> TrustEngine:
    """Create and cache the TrustEngine singleton."""
    config = get_config()
    engine = TrustEngine(config=config.engine)
    return engine


@lru_cache()
def get_storage() -> StorageBackend:
    """Create and cache the StorageBackend singleton."""
    config = get_config()
    return create_storage_backend(config.storage)
