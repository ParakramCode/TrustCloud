"""
TrustCloud AI — Trust Orchestrator
Runs validators concurrently with timeout and failure isolation.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Dict, List, Optional

from validators.base import BaseValidator, ValidatorOutput

logger = logging.getLogger("trustcloud.orchestrator")


@dataclass
class OrchestratorResult:
    """Result of running a single validator through the orchestrator."""
    name: str
    version: str
    output: Optional[ValidatorOutput]  # None if failed
    error: Optional[str]               # Error message if failed
    latency_ms: float                  # Execution time

    @property
    def succeeded(self) -> bool:
        return self.output is not None and self.error is None


class TrustOrchestrator:
    """
    Executes validators with:
    - Concurrent execution via thread pool (validators use CPU-bound libraries)
    - Per-validator timeout enforcement
    - Failure isolation (one validator crash doesn't kill others)
    - Latency tracking per validator
    """

    def __init__(self, timeout_seconds: float = 10.0, max_workers: int = 6):
        self.timeout_seconds = timeout_seconds
        self.max_workers = max_workers

    def _run_single(self, validator: BaseValidator, text: str) -> OrchestratorResult:
        """Run a single validator with timing and error handling."""
        start = time.perf_counter()
        try:
            output = validator.run(text)
            latency = (time.perf_counter() - start) * 1000
            return OrchestratorResult(
                name=validator.name,
                version=validator.version,
                output=output,
                error=None,
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"Validator '{validator.name}' failed: {type(e).__name__}: {e}")
            return OrchestratorResult(
                name=validator.name,
                version=validator.version,
                output=None,
                error=f"{type(e).__name__}: {e}",
                latency_ms=round(latency, 2),
            )

    def run_all(
        self,
        validators: List[BaseValidator],
        text: str,
        concurrent: bool = True,
    ) -> List[OrchestratorResult]:
        """
        Run all given validators on the input text.

        Args:
            validators: List of validator instances to execute.
            text: Input text to evaluate.
            concurrent: If True, run in thread pool. If False, run sequentially.

        Returns:
            List of OrchestratorResult, one per validator (order preserved).
        """
        if not concurrent:
            return [self._run_single(v, text) for v in validators]

        results: List[OrchestratorResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {
                executor.submit(self._run_single, v, text): v
                for v in validators
            }

            for future in future_map:
                validator = future_map[future]
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    results.append(result)
                except FuturesTimeoutError:
                    logger.error(f"Validator '{validator.name}' timed out after {self.timeout_seconds}s")
                    results.append(OrchestratorResult(
                        name=validator.name,
                        version=validator.version,
                        output=None,
                        error=f"Timeout after {self.timeout_seconds}s",
                        latency_ms=self.timeout_seconds * 1000,
                    ))
                except Exception as e:
                    logger.error(f"Validator '{validator.name}' executor error: {e}")
                    results.append(OrchestratorResult(
                        name=validator.name,
                        version=validator.version,
                        output=None,
                        error=f"ExecutorError: {e}",
                        latency_ms=0.0,
                    ))

        return results
