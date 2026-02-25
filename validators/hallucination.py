"""
TrustCloud AI — Hallucination Risk Validator
Heuristic hallucination risk detector based on uncertainty, vagueness, and absolutism markers.

Epistemic classification: DEFEATER
Method: Keyword heuristic (base uncertainty ≈ 0.20)

Hallucination risk is a defeater because an ungrounded claim, no matter
how coherently expressed, should not be trusted. The absence of factual
grounding undermines the epistemic basis for belief.
"""

import re
from validators.base import BaseValidator, ValidatorOutput, estimate_uncertainty


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
    def method_type(self) -> str:
        return "keyword_heuristic"

    @property
    def signal_type(self) -> str:
        return "defeater"

    def run(self, text: str) -> ValidatorOutput:
        text_lower = text.lower()
        uncertainty = estimate_uncertainty(self.method_type, text)

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

        # Build evidence
        evidence = []
        if found_uncertainty:
            evidence.append({"type": "uncertainty_markers", "found": found_uncertainty})
        if found_vagueness:
            evidence.append({"type": "vagueness_markers", "found": found_vagueness})
        if found_absolutism:
            evidence.append({"type": "absolutism_markers", "found": found_absolutism})
        if grounding_penalty > 0:
            evidence.append({"type": "grounding_penalty", "numeric_refs": numeric_refs})

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

        return ValidatorOutput(
            score=score,
            uncertainty=uncertainty,
            explanation=" ".join(parts),
            evidence=evidence,
        )
