"""
TrustCloud AI — Base Validator Interface
All validators must implement this abstract base class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidatorOutput:
    """Standard output from a validator run."""
    score: float         # Signal value in [0, 1]
    explanation: str     # Human-readable reason for the score


class BaseValidator(ABC):
    """
    Abstract base class for all trust validators.

    Every validator is a self-contained plugin that:
    - Has a unique name and version
    - Declares its own default weight for aggregation
    - Declares whether its signal is inverted (higher = worse)
    - Can run independently on any input text
    - Returns a ValidatorOutput with score + explanation

    To create a new validator:
    1. Subclass BaseValidator
    2. Implement name, version, default_weight, inverted, run()
    3. Place the file in the validators/ directory
    4. The registry will auto-discover it
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this validator (e.g., 'coherence')."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Version string (e.g., 'v1.0')."""
        ...

    @property
    @abstractmethod
    def default_weight(self) -> float:
        """Default aggregation weight in [0, 1]. Weights are normalized at aggregation time."""
        ...

    @property
    def inverted(self) -> bool:
        """
        If True, higher scores indicate WORSE trust (e.g., contradiction, hallucination_risk).
        The aggregator handles inversion: trust_contribution = 1 - score.
        Default: False (higher = better).
        """
        return False

    @abstractmethod
    def run(self, text: str) -> ValidatorOutput:
        """
        Execute this validator on the input text.

        Args:
            text: The AI-generated text to evaluate.

        Returns:
            ValidatorOutput with score in [0, 1] and an explanation string.

        Raises:
            Any exception — the orchestrator catches and records failures.
            Do NOT silently swallow errors inside validators.
        """
        ...
