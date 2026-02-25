"""
TrustCloud AI — Hallucination Risk Validator
Heuristic hallucination risk detector based on uncertainty, vagueness, and absolutism markers.
"""

import re
from validators.base import BaseValidator, ValidatorOutput


class HallucinationValidator(BaseValidator):

    @property
    def name(self) -> str:
        return "hallucination_risk"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def default_weight(self) -> float:
        return 0.20

    @property
    def inverted(self) -> bool:
        return True  # Higher score = higher hallucination risk = WORSE trust

    def run(self, text: str) -> ValidatorOutput:
        text_lower = text.lower()

        uncertainty_markers = [
            "maybe", "might", "could be", "possibly", "it seems",
            "i think", "i believe", "likely", "apparently", "suggests that"
        ]

        vagueness_markers = [
            "many", "some", "various", "numerous", "several",
            "a lot", "a number of", "things", "stuff"
        ]

        absolutism_markers = [
            "always", "never", "everyone", "everything", "completely", "guaranteed"
        ]

        found_uncertainty = [w for w in uncertainty_markers if w in text_lower]
        found_vagueness = [w for w in vagueness_markers if w in text_lower]
        found_absolutism = [w for w in absolutism_markers if w in text_lower]

        uncertainty_score = len(found_uncertainty) * 0.15
        vagueness_score = len(found_vagueness) * 0.1
        absolutism_score = len(found_absolutism) * 0.1

        # Numeric grounding check
        numeric_refs = len(re.findall(r"\d+", text))
        grounding_penalty = 0.2 if numeric_refs == 0 else 0.0

        score = round(min(uncertainty_score + vagueness_score + absolutism_score + grounding_penalty, 1.0), 3)

        parts = []
        if found_uncertainty:
            parts.append(f"Uncertainty markers: {found_uncertainty}.")
        if found_vagueness:
            parts.append(f"Vagueness markers: {found_vagueness}.")
        if found_absolutism:
            parts.append(f"Absolutism markers: {found_absolutism}.")
        if grounding_penalty > 0:
            parts.append("No numeric references found — grounding penalty applied.")
        if not parts:
            parts.append("No hallucination risk indicators detected.")

        return ValidatorOutput(score=score, explanation=" ".join(parts))
