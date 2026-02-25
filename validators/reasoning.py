"""
TrustCloud AI — Reasoning Depth Validator
Measures reasoning quality: structure, multi-step chains, and penalizes
circular reasoning, tautologies, and fake causality.
"""

import re
from validators.base import BaseValidator, ValidatorOutput


class ReasoningDepthValidator(BaseValidator):

    @property
    def name(self) -> str:
        return "reasoning_depth"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def default_weight(self) -> float:
        return 0.15

    def run(self, text: str) -> ValidatorOutput:
        text_lower = text.lower()

        # --- Reasoning connectors (positive) ---
        reasoning_markers = [
            "because", "therefore", "thus", "hence", "so that",
            "as a result", "due to", "leads to", "causes", "results in"
        ]
        found_reasoning = [w for w in reasoning_markers if w in text_lower]
        structure_score = len(found_reasoning) * 0.15

        # --- Circular reasoning detection (penalty) ---
        circular_patterns = [
            r"(.+) because \1",
            r"(.+) is caused by \1",
            r"(.+) leads to \1",
            r"(.+) results in \1",
            r"(.+) explains itself",
            r"(.+) because it is \1"
        ]
        circular_hits = sum(1 for p in circular_patterns if re.search(p, text_lower))
        circular_penalty = circular_hits * 0.6

        self_cause_markers = [
            "caused by itself", "explains itself", "self caused",
            "causes itself", "results from itself"
        ]
        if any(p in text_lower for p in self_cause_markers):
            circular_penalty += 0.6

        # --- Tautology detection (penalty) ---
        tautology_patterns = [
            r"(.+) is (.+) because it is (.+)",
            r"(.+) happens because (.+) happens",
            r"(.+) exists because (.+) exists"
        ]
        tautology_hits = sum(1 for p in tautology_patterns if re.search(p, text_lower))
        tautology_penalty = tautology_hits * 0.5

        # --- Fake causality detection (penalty) ---
        fake_causal_phrases = [
            "proves that", "this proves", "which proves",
            "therefore it is true", "hence it must be"
        ]
        found_fake = [p for p in fake_causal_phrases if p in text_lower]
        fake_penalty = len(found_fake) * 0.2

        # --- Multi-step reasoning bonus ---
        chain_markers = ["first", "then", "next", "finally", "step", "process", "mechanism"]
        found_chain = [w for w in chain_markers if w in text_lower]
        chain_bonus = len(found_chain) * 0.1

        # --- Final score ---
        total_penalty = circular_penalty + tautology_penalty + fake_penalty
        raw_score = structure_score + chain_bonus - total_penalty
        score = round(max(0.0, min(raw_score, 1.0)), 3)

        # --- Explanation ---
        parts = []
        if found_reasoning:
            parts.append(f"Reasoning markers: {found_reasoning}.")
        if found_chain:
            parts.append(f"Multi-step chain markers: {found_chain} (+{chain_bonus:.2f}).")
        if circular_penalty > 0:
            parts.append(f"Circular reasoning detected (-{circular_penalty:.2f}).")
        if tautology_penalty > 0:
            parts.append(f"Tautology detected (-{tautology_penalty:.2f}).")
        if found_fake:
            parts.append(f"Fake causality: {found_fake} (-{fake_penalty:.2f}).")
        if not parts:
            parts.append("No reasoning structure detected.")

        return ValidatorOutput(score=score, explanation=" ".join(parts))
