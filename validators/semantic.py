"""
TrustCloud AI — Semantic Consistency Validator
Measures semantic consistency between adjacent sentences using sentence embeddings.

Epistemic classification: POSITIVE INDICATOR
Method: Embedding similarity (base uncertainty ≈ 0.08)

Shares the sentence-transformers model with CoherenceValidator to avoid
double-loading (~400MB memory savings).
"""

from validators.base import BaseValidator, ValidatorOutput, estimate_uncertainty
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

    @property
    def method_type(self) -> str:
        return "embedding_similarity"

    @property
    def signal_type(self) -> str:
        return "positive_indicator"

    def run(self, text: str) -> ValidatorOutput:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
        uncertainty = estimate_uncertainty(self.method_type, text)

        if len(sentences) < 2:
            return ValidatorOutput(
                score=1.0,
                uncertainty=uncertainty * 1.5,
                explanation="Single meaningful sentence — semantic consistency is trivially 1.0. Higher uncertainty due to insufficient data.",
                evidence=[{"type": "trivial_input", "sentence_count": len(sentences)}],
            )

        embeddings = _model.encode(sentences)

        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            similarities.append(float(sim))

        avg_sim = float(np.mean(similarities))
        min_sim = float(np.min(similarities))
        score = round(max(0.0, min(avg_sim, 1.0)), 3)

        evidence = [
            {"type": "pairwise_similarity", "pair_index": i, "similarity": round(s, 3)}
            for i, s in enumerate(similarities)
        ]

        explanation = (
            f"Computed pairwise semantic similarity across {len(sentences)} sentences "
            f"(min length >10 chars). Average cosine similarity: {avg_sim:.3f}, "
            f"minimum: {min_sim:.3f}."
        )

        return ValidatorOutput(
            score=score,
            uncertainty=uncertainty,
            explanation=explanation,
            evidence=evidence,
        )
