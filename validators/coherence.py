"""
TrustCloud AI — Coherence Validator
Measures topical coherence between adjacent sentences using sentence embeddings.

Epistemic classification: POSITIVE INDICATOR
Method: Embedding similarity (model-based, base uncertainty ≈ 0.08)
"""

from validators.base import BaseValidator, ValidatorOutput, estimate_uncertainty
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

# Shared model instance — loaded once at module level.
_model = SentenceTransformer("all-MiniLM-L6-v2")


class CoherenceValidator(BaseValidator):

    @property
    def name(self) -> str:
        return "coherence"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def default_weight(self) -> float:
        return 0.25

    @property
    def method_type(self) -> str:
        return "embedding_similarity"

    @property
    def signal_type(self) -> str:
        return "positive_indicator"

    def run(self, text: str) -> ValidatorOutput:
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        uncertainty = estimate_uncertainty(self.method_type, text)

        if len(sentences) < 2:
            return ValidatorOutput(
                score=1.0,
                uncertainty=uncertainty * 1.5,  # Higher uncertainty for trivial case
                explanation="Single sentence — coherence is trivially 1.0. High uncertainty due to insufficient data.",
                evidence=[{"type": "trivial_input", "sentence_count": len(sentences)}],
            )

        embeddings = _model.encode(sentences)
        sims = []

        for i in range(len(embeddings) - 1):
            sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            sims.append(float(sim))

        avg_sim = float(np.mean(sims))
        min_sim = float(np.min(sims))
        std_sim = float(np.std(sims)) if len(sims) > 1 else 0.0

        score = round(max(0.0, min(avg_sim, 1.0)), 3)

        # Adjust uncertainty based on measurement variance
        if std_sim > 0.2:
            uncertainty = min(uncertainty * 1.3, 0.5)

        explanation = (
            f"Measured cosine similarity between {len(sentences)} adjacent sentence pairs. "
            f"Average similarity: {avg_sim:.3f}, minimum: {min_sim:.3f}, std: {std_sim:.3f}."
        )

        evidence = [
            {"type": "pairwise_similarity", "pair_index": i, "similarity": round(s, 3)}
            for i, s in enumerate(sims)
        ]

        return ValidatorOutput(
            score=score,
            uncertainty=uncertainty,
            explanation=explanation,
            evidence=evidence,
        )
