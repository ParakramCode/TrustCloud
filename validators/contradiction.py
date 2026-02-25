"""
TrustCloud AI — Contradiction Validator
Detects self-contradiction through marker analysis and sentiment polarity flips.

Epistemic classification: DEFEATER
Method: Keyword heuristic + sentiment analysis (base uncertainty ≈ 0.18)

A defeater is a signal that, when strong, should CAP the overall trust
regardless of how well other dimensions score. Contradiction is the
canonical epistemic defeater: a text that contradicts itself cannot
be trusted, no matter how coherent or well-grounded it appears.
"""

from validators.base import BaseValidator, ValidatorOutput, estimate_uncertainty
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
    def method_type(self) -> str:
        return "sentiment_analysis"

    @property
    def signal_type(self) -> str:
        return "defeater"

    def run(self, text: str) -> ValidatorOutput:
        text_lower = text.lower()
        uncertainty = estimate_uncertainty(self.method_type, text)

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

        # Build evidence
        evidence = []
        if found_markers:
            evidence.append({"type": "contradiction_markers", "found": found_markers})
        if found_negations:
            evidence.append({"type": "negation_terms", "found": found_negations})
        if polarity_conflict > 0:
            evidence.append({"type": "polarity_conflict", "polarity": round(polarity, 3), "note": polarity_note})

        parts = []
        if found_markers:
            parts.append(f"Contradiction markers found: {found_markers}.")
        if found_negations:
            parts.append(f"Negation terms found: {found_negations}.")
        if polarity_note:
            parts.append(polarity_note)
        if not parts:
            parts.append("No contradiction indicators detected.")

        return ValidatorOutput(
            score=score,
            uncertainty=uncertainty,
            explanation=" ".join(parts),
            evidence=evidence,
        )
