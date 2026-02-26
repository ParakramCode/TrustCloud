"""
TrustCloud AI — Conversation Trust Analysis

Orchestrates per-turn epistemic trust evaluation across a multi-turn
LLM conversation. Computes trust decay metrics, semantic drift,
and cross-turn consistency indicators.

Architecture:
- Reuses existing TrustEngine (validators + aggregator) per turn.
- Adds a temporal analysis layer on top.
- No validator changes required — conversation analysis is purely
  an orchestration concern.

Limitations (documented for epistemic honesty):
- Cross-turn hallucination tracking is not supported (would require
  cross-document NLI, which is beyond current validators).
- Trust inertia is intentionally absent — each turn is evaluated
  independently to avoid bias propagation.
- Semantic drift uses embedding cosine similarity, which measures
  topic shift but not logical consistency.
"""

import logging
import numpy as np
from typing import List, Optional
from dataclasses import dataclass, field

from trust_engine.engine import TrustEngine
from schemas.response import TrustResponse


logger = logging.getLogger("trustcloud.conversation")


@dataclass
class TurnResult:
    """Trust evaluation for a single conversation turn."""
    turn_index: int
    role: str
    content_preview: str  # First 100 chars
    content_length: int
    trust_response: TrustResponse


@dataclass
class DriftPoint:
    """Semantic similarity between a turn and the conversation anchor (turn 0)."""
    turn_index: int
    similarity_to_first: float  # Cosine similarity to the first assistant turn
    similarity_to_previous: float  # Cosine similarity to the previous assistant turn


@dataclass
class TrustTrend:
    """Statistical summary of trust evolution across turns."""
    metric: str
    values: List[float]
    mean: float
    slope: float          # Linear regression slope (negative = decay)
    r_squared: float      # How well a linear trend fits
    interpretation: str


class ConversationAnalyzer:
    """
    Analyzes epistemic trust across a multi-turn conversation.

    For each assistant turn:
    1. Runs the full TrustEngine evaluation
    2. Extracts per-dimension scores
    3. Computes semantic drift from conversation anchor

    Then computes:
    - Trust decay trends (slope of trust over turn index)
    - Dimension-level trends (which dimensions degrade fastest)
    - Semantic drift curve
    - Defeater accumulation
    """

    def __init__(self, engine: TrustEngine):
        self.engine = engine
        # Lazy-load the sentence transformer (reuses the one from coherence validator)
        self._model = None

    def _get_embedding_model(self):
        """Lazy-load sentence transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def analyze(
        self,
        messages: List[dict],
        evaluate_user_turns: bool = False,
    ) -> dict:
        """
        Run conversation-level trust analysis.

        Args:
            messages: List of {role: str, content: str} message dicts.
            evaluate_user_turns: If True, also evaluate user messages.
                                 Default False (only assistant turns).

        Returns:
            Full conversation trust report as a dict.
        """
        # 1. Filter and evaluate turns
        turn_results = self._evaluate_turns(messages, evaluate_user_turns)

        if not turn_results:
            return {
                "error": "No evaluable turns found in conversation.",
                "turn_count": len(messages),
            }

        # 2. Compute semantic drift
        assistant_contents = [
            msg["content"] for msg in messages
            if msg.get("role") == "assistant"
        ]
        drift_points = self._compute_semantic_drift(assistant_contents)

        # 3. Compute trust trends
        trends = self._compute_trends(turn_results)

        # 4. Compute defeater accumulation
        defeater_timeline = self._compute_defeater_timeline(turn_results)

        # 5. Build summary
        summary = self._build_summary(turn_results, trends, drift_points)

        return {
            "conversation_summary": summary,
            "turn_count": len(messages),
            "evaluated_turns": len(turn_results),
            "per_turn_results": [
                {
                    "turn_index": tr.turn_index,
                    "role": tr.role,
                    "content_preview": tr.content_preview,
                    "content_length": tr.content_length,
                    "composite_trust": tr.trust_response.assessment.composite_trust,
                    "confidence": tr.trust_response.assessment.confidence,
                    "trust_level": tr.trust_response.assessment.trust_level,
                    "defeated": tr.trust_response.assessment.defeated,
                    "dimensions": {
                        d.name: {
                            "score": d.score,
                            "uncertainty": d.uncertainty,
                        }
                        for d in tr.trust_response.dimensions
                        if d.score is not None
                    },
                }
                for tr in turn_results
            ],
            "semantic_drift": [
                {
                    "turn_index": dp.turn_index,
                    "similarity_to_first": round(dp.similarity_to_first, 4),
                    "similarity_to_previous": round(dp.similarity_to_previous, 4),
                }
                for dp in drift_points
            ],
            "trust_trends": {
                t.metric: {
                    "values": [round(v, 4) for v in t.values],
                    "mean": round(t.mean, 4),
                    "slope": round(t.slope, 6),
                    "r_squared": round(t.r_squared, 4),
                    "interpretation": t.interpretation,
                }
                for t in trends
            },
            "defeater_timeline": defeater_timeline,
            "blind_spots": [
                "Each turn is evaluated independently — cross-turn hallucination propagation is not tracked.",
                "Semantic drift measures topic shift, not logical consistency.",
                "Trend slopes may be unreliable with fewer than 5 evaluated turns.",
                "User messages may influence LLM quality but are not evaluated by default.",
                "Trust decay may reflect topic complexity changes, not actual quality degradation.",
            ],
        }

    def _evaluate_turns(
        self,
        messages: List[dict],
        evaluate_user_turns: bool,
    ) -> List[TurnResult]:
        """Evaluate each qualifying turn through the TrustEngine."""
        results = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Skip non-evaluable turns
            if role == "system":
                continue
            if role == "user" and not evaluate_user_turns:
                continue
            if len(content.strip()) < 10:
                continue

            try:
                trust_result = self.engine.evaluate(text=content)
                results.append(TurnResult(
                    turn_index=i,
                    role=role,
                    content_preview=content[:100],
                    content_length=len(content),
                    trust_response=trust_result,
                ))
            except Exception as e:
                logger.warning(f"Turn {i} evaluation failed: {e}")
                continue

        return results

    def _compute_semantic_drift(self, texts: List[str]) -> List[DriftPoint]:
        """Compute embedding-based semantic drift across turns."""
        if len(texts) < 2:
            return []

        model = self._get_embedding_model()
        embeddings = model.encode(texts)

        from sklearn.metrics.pairwise import cosine_similarity

        drift_points = []
        for i in range(len(embeddings)):
            sim_to_first = float(cosine_similarity(
                [embeddings[i]], [embeddings[0]]
            )[0][0])

            sim_to_prev = 1.0 if i == 0 else float(cosine_similarity(
                [embeddings[i]], [embeddings[i - 1]]
            )[0][0])

            drift_points.append(DriftPoint(
                turn_index=i,
                similarity_to_first=sim_to_first,
                similarity_to_previous=sim_to_prev,
            ))

        return drift_points

    def _compute_trends(self, turn_results: List[TurnResult]) -> List[TrustTrend]:
        """Compute linear trends for key metrics across turns."""
        if len(turn_results) < 2:
            return []

        trends = []

        # Composite trust trend
        trust_values = [tr.trust_response.assessment.composite_trust for tr in turn_results]
        trends.append(self._fit_trend("composite_trust", trust_values))

        # Confidence trend
        conf_values = [tr.trust_response.assessment.confidence for tr in turn_results]
        trends.append(self._fit_trend("confidence", conf_values))

        # Per-dimension trends
        dim_names = set()
        for tr in turn_results:
            for d in tr.trust_response.dimensions:
                if d.score is not None:
                    dim_names.add(d.name)

        for dim_name in sorted(dim_names):
            dim_values = []
            for tr in turn_results:
                score = None
                for d in tr.trust_response.dimensions:
                    if d.name == dim_name and d.score is not None:
                        score = d.score
                        break
                if score is not None:
                    dim_values.append(score)

            if len(dim_values) >= 2:
                trends.append(self._fit_trend(f"dim_{dim_name}", dim_values))

        return trends

    def _fit_trend(self, metric: str, values: List[float]) -> TrustTrend:
        """Fit a linear trend to a series of values."""
        x = np.arange(len(values), dtype=float)
        y = np.array(values, dtype=float)

        # Linear regression: y = slope * x + intercept
        if len(values) >= 2:
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        else:
            slope = 0.0
            r_squared = 0.0

        # Generate interpretation
        if abs(slope) < 0.005:
            direction = "stable"
        elif slope < 0:
            direction = "declining"
        else:
            direction = "improving"

        strength = "weak" if r_squared < 0.3 else "moderate" if r_squared < 0.7 else "strong"

        interpretation = (
            f"{metric} shows a {strength} {direction} trend "
            f"(slope={slope:.4f}, R²={r_squared:.3f}). "
        )

        if direction == "declining" and r_squared > 0.3:
            interpretation += "This suggests measurable epistemic degradation over the conversation."
        elif direction == "stable":
            interpretation += "No significant trend detected."
        elif direction == "improving":
            interpretation += "Quality indicators improve over the conversation."

        if len(values) < 5:
            interpretation += " Note: trend computed from fewer than 5 data points — interpret with caution."

        return TrustTrend(
            metric=metric,
            values=values,
            mean=float(np.mean(y)),
            slope=float(slope),
            r_squared=float(r_squared),
            interpretation=interpretation,
        )

    def _compute_defeater_timeline(self, turn_results: List[TurnResult]) -> List[dict]:
        """Track which defeaters activate at each turn."""
        timeline = []
        cumulative_activations = 0

        for tr in turn_results:
            active_defeaters = [
                d.name for d in tr.trust_response.defeaters if d.active
            ]
            if active_defeaters:
                cumulative_activations += len(active_defeaters)

            timeline.append({
                "turn_index": tr.turn_index,
                "active_defeaters": active_defeaters,
                "cumulative_activations": cumulative_activations,
            })

        return timeline

    def _build_summary(
        self,
        turn_results: List[TurnResult],
        trends: List[TrustTrend],
        drift_points: List[DriftPoint],
    ) -> dict:
        """Build a high-level summary of the conversation analysis."""
        trust_values = [tr.trust_response.assessment.composite_trust for tr in turn_results]
        defeated_count = sum(1 for tr in turn_results if tr.trust_response.assessment.defeated)

        # Find the composite trust trend
        trust_trend = next((t for t in trends if t.metric == "composite_trust"), None)

        # Semantic drift summary
        if drift_points:
            final_drift = drift_points[-1].similarity_to_first
            drift_label = (
                "minimal" if final_drift > 0.8
                else "moderate" if final_drift > 0.5
                else "significant"
            )
        else:
            final_drift = None
            drift_label = "unmeasured"

        return {
            "total_turns_evaluated": len(turn_results),
            "mean_trust": round(float(np.mean(trust_values)), 4),
            "first_turn_trust": round(trust_values[0], 4),
            "last_turn_trust": round(trust_values[-1], 4),
            "trust_delta": round(trust_values[-1] - trust_values[0], 4),
            "defeated_turns": defeated_count,
            "trust_decay_slope": round(trust_trend.slope, 6) if trust_trend else None,
            "trust_decay_r_squared": round(trust_trend.r_squared, 4) if trust_trend else None,
            "semantic_drift": drift_label,
            "semantic_drift_final_similarity": round(final_drift, 4) if final_drift else None,
        }
