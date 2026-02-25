"""
TrustCloud AI — Default Signals (Legacy Compatibility)

NOTE: This module is kept for backward compatibility.
The refactored architecture derives signal names from the validator registry.
New code should use engine.registry.names() instead of this dict.
"""

DEFAULT_SIGNALS = {
    "coherence": 0.0,
    "semantic_consistency": 0.0,
    "contradiction": 0.0,
    "hallucination_risk": 0.0,
    "reasoning_depth": 0.0,
    "factual_density": 0.0,
}
