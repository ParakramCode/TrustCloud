"""
TrustCloud AI — Validators Package
Exports the BaseValidator and all built-in validator classes.
"""

from validators.base import BaseValidator, ValidatorOutput
from validators.coherence import CoherenceValidator
from validators.contradiction import ContradictionValidator
from validators.hallucination import HallucinationValidator
from validators.reasoning import ReasoningDepthValidator
from validators.factuality import FactualDensityValidator
from validators.semantic import SemanticConsistencyValidator

# All built-in validators for auto-discovery by the registry
BUILTIN_VALIDATORS = [
    CoherenceValidator,
    ContradictionValidator,
    HallucinationValidator,
    ReasoningDepthValidator,
    FactualDensityValidator,
    SemanticConsistencyValidator,
]

__all__ = [
    "BaseValidator",
    "ValidatorOutput",
    "CoherenceValidator",
    "ContradictionValidator",
    "HallucinationValidator",
    "ReasoningDepthValidator",
    "FactualDensityValidator",
    "SemanticConsistencyValidator",
    "BUILTIN_VALIDATORS",
]
