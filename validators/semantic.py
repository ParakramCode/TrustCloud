"""
TrustCloud AI — Semantic Consistency Validator
Measures semantic consistency between adjacent sentences using sentence embeddings.

NOTE: This validator shares the same embedding model as the CoherenceValidator.
      In future, a shared model provider should be used to avoid double-loading.
      For now, it reuses the module-level instance from coherence.py.
"""

from validators.base import BaseValidator, ValidatorOutput
from validators.coherence import _model  # Share the sentence-transformers model
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class SemanticConsistencyValidator(BaseValidator):

    @property
    def name(self) -> str:
        return "semantic_consistency"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def default_weight(self) -> float:
        return 0.10

    def run(self, text: str) -> ValidatorOutput:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]

        if len(sentences) < 2:
            return ValidatorOutput(
                score=1.0,
                explanation="Single meaningful sentence — semantic consistency is trivially 1.0."
            )

        embeddings = _model.encode(sentences)

        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            similarities.append(float(sim))

        avg_sim = float(np.mean(similarities))
        score = round(max(0.0, min(avg_sim, 1.0)), 3)

        explanation = (
            f"Computed pairwise semantic similarity across {len(sentences)} sentences "
            f"(min length >10 chars). Average cosine similarity: {avg_sim:.3f}."
        )

        return ValidatorOutput(score=score, explanation=explanation)
