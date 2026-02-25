"""
TrustCloud AI — Configuration Schemas
Typed configuration for engine, storage, and system settings.
"""

from pydantic import BaseModel, Field
from typing import Optional
import os


class StorageConfig(BaseModel):
    """Storage backend configuration."""

    backend: str = Field(
        default="local",
        description="Storage backend type: 'local' or 's3'."
    )
    # Local storage
    local_path: str = Field(
        default="data/evaluations",
        description="Local directory for evaluation records."
    )
    # S3 storage
    s3_bucket: str = Field(
        default="trustcloud-ai-raw",
        description="S3 bucket name."
    )
    s3_prefix: str = Field(
        default="raw/evaluations",
        description="S3 key prefix for evaluation records."
    )


class EngineConfig(BaseModel):
    """Trust engine configuration."""

    version: str = Field(default="trust-engine-v1", description="Engine version identifier.")
    validator_timeout_seconds: float = Field(
        default=10.0,
        description="Per-validator execution timeout in seconds."
    )
    enable_concurrent: bool = Field(
        default=True,
        description="Run validators concurrently (True) or sequentially (False)."
    )


class AppConfig(BaseModel):
    """Application-level configuration. Reads from environment variables."""

    engine: EngineConfig = Field(default_factory=EngineConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build configuration from environment variables with sensible defaults."""
        return cls(
            engine=EngineConfig(
                version=os.environ.get("TRUSTCLOUD_ENGINE_VERSION", "trust-engine-v1"),
                validator_timeout_seconds=float(os.environ.get("TRUSTCLOUD_VALIDATOR_TIMEOUT", "10.0")),
                enable_concurrent=os.environ.get("TRUSTCLOUD_CONCURRENT", "true").lower() == "true",
            ),
            storage=StorageConfig(
                backend=os.environ.get("TRUSTCLOUD_STORAGE_BACKEND", "local"),
                local_path=os.environ.get("TRUSTCLOUD_LOCAL_PATH", "data/evaluations"),
                s3_bucket=os.environ.get("TRUSTCLOUD_S3_BUCKET", "trustcloud-ai-raw"),
                s3_prefix=os.environ.get("TRUSTCLOUD_S3_PREFIX", "raw/evaluations"),
            ),
        )
