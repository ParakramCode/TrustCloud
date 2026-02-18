def trust_score(signals: dict) -> float:
    score = (
        0.25 * signals.get("coherence", 0) +
        0.2 * (1 - signals.get("contradiction", 0)) +
        0.2 * (1 - signals.get("hallucination_risk", 0)) +
        0.15 * signals.get("reasoning_depth", 0) +
        0.1 * signals.get("factual_density", 0) +
        0.1 * signals.get("semantic_consistency", 0)
    )
    return round(score, 3)
