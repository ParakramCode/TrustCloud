"""
TrustCloud AI — Contradiction Validator
Detects self-contradiction through marker analysis and sentiment polarity flips.
"""

from validators.base import BaseValidator, ValidatorOutput
from textblob import TextBlob


class ContradictionValidator(BaseValidator):

    @property
    def name(self) -> str:
        return "contradiction"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def default_weight(self) -> float:
        return 0.20

    @property
    def inverted(self) -> bool:
        return True  # Higher score = more contradictory = WORSE trust

    def run(self, text: str) -> ValidatorOutput:
        text_lower = text.lower()

        contradiction_markers = [
            "but", "however", "although", "yet", "on the other hand",
            "contradicts", "in contrast", "nevertheless"
        ]

        negations = ["not", "never", "no", "none", "nothing", "nobody"]

        # Marker-based detection
        found_markers = [w for w in contradiction_markers if w in text_lower]
        marker_score = len(found_markers) * 0.15

        # Negation density
        found_negations = [w for w in negations if w in text_lower]
        negation_score = len(found_negations) * 0.1

        # Sentiment polarity flip detection
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        polarity_conflict = 0.0
        polarity_note = ""
        if polarity > 0.3 and found_negations:
            polarity_conflict = 0.3
            polarity_note = f"Positive sentiment ({polarity:.2f}) conflicts with negation markers."
        elif polarity < -0.3 and found_negations:
            polarity_conflict = 0.3
            polarity_note = f"Negative sentiment ({polarity:.2f}) with negation markers suggests mixed signals."

        score = round(min(marker_score + negation_score + polarity_conflict, 1.0), 3)

        parts = []
        if found_markers:
            parts.append(f"Contradiction markers found: {found_markers}.")
        if found_negations:
            parts.append(f"Negation terms found: {found_negations}.")
        if polarity_note:
            parts.append(polarity_note)
        if not parts:
            parts.append("No contradiction indicators detected.")

        explanation = " ".join(parts)

        return ValidatorOutput(score=score, explanation=explanation)
