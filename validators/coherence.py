"""
TrustCloud AI — Coherence Validator
Measures topical coherence between adjacent sentences using sentence embeddings.
"""

from validators.base import BaseValidator, ValidatorOutput
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

# Shared model instance — loaded once at module level.
# The registry ensures this module is only imported once.
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

    def run(self, text: str) -> ValidatorOutput:
        sentences = [s.strip() for s in text.split(".") if s.strip()]

        if len(sentences) < 2:
            return ValidatorOutput(
                score=1.0,
                explanation="Single sentence — coherence is trivially 1.0."
            )

        embeddings = _model.encode(sentences)
        sims = []

        for i in range(len(embeddings) - 1):
            sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            sims.append(float(sim))

        avg_sim = float(np.mean(sims))
        min_sim = float(np.min(sims))

        score = round(max(0.0, min(avg_sim, 1.0)), 3)

        explanation = (
            f"Measured cosine similarity between {len(sentences)} adjacent sentence pairs. "
            f"Average similarity: {avg_sim:.3f}, minimum: {min_sim:.3f}."
        )

        return ValidatorOutput(score=score, explanation=explanation)
