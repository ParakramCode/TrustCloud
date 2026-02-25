"""
TrustCloud AI — Storage Backend Interface
Abstract storage with pluggable backends (local, S3).
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict

from schemas.config import StorageConfig

logger = logging.getLogger("trustcloud.storage")


class StorageBackend(ABC):
    """Abstract storage backend. Implement to add new storage targets."""

    @abstractmethod
    def write(self, record: Dict[str, Any], record_id: str) -> None:
        """
        Write an evaluation record to storage.

        Args:
            record: The full telemetry record as a dictionary.
            record_id: Unique identifier for this record.

        Raises:
            Any exception — callers handle storage failures gracefully.
        """
        ...


class LocalStorageBackend(StorageBackend):
    """Writes evaluation records as JSON files to local disk."""

    def __init__(self, base_path: str = "data/evaluations"):
        self.base_path = base_path

    def write(self, record: Dict[str, Any], record_id: str) -> None:
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        dir_path = os.path.join(self.base_path, date_path)
        os.makedirs(dir_path, exist_ok=True)

        file_path = os.path.join(dir_path, f"{record_id}.json")
        with open(file_path, "w") as f:
            json.dump(record, f, indent=2, default=str)

        logger.info(f"Wrote evaluation record to {file_path}")


class S3StorageBackend(StorageBackend):
    """Writes evaluation records to AWS S3."""

    def __init__(self, bucket: str, prefix: str = "raw/evaluations"):
        import boto3
        self.s3 = boto3.client("s3")
        self.bucket = bucket
        self.prefix = prefix

    def write(self, record: Dict[str, Any], record_id: str) -> None:
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        key = f"{self.prefix}/{date_path}/{record_id}.json"

        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(record, default=str),
            ContentType="application/json",
        )

        logger.info(f"Wrote evaluation record to s3://{self.bucket}/{key}")


def create_storage_backend(config: StorageConfig) -> StorageBackend:
    """Factory function to create the appropriate storage backend from config."""
    if config.backend == "s3":
        return S3StorageBackend(bucket=config.s3_bucket, prefix=config.s3_prefix)
    elif config.backend == "local":
        return LocalStorageBackend(base_path=config.local_path)
    else:
        raise ValueError(f"Unknown storage backend: {config.backend}")
