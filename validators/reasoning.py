import re

def check_reasoning_depth(text: str) -> float:
    """
    Measures reasoning quality, not just structure.
    Penalizes circular reasoning, tautologies, and fake causality.
    """

    text_lower = text.lower()

    # Reasoning connectors (structure)
    reasoning_markers = [
        "because", "therefore", "thus", "hence", "so that",
        "as a result", "due to", "leads to", "causes", "results in"
    ]

    structure_score = sum(1 for w in reasoning_markers if w in text_lower) * 0.15

    # ---------------------------
    # Circular reasoning detection
    # ---------------------------
    circular_patterns = [
        r"(.+) because \1",
        r"(.+) is caused by \1",
        r"(.+) leads to \1",
        r"(.+) results in \1",
        r"(.+) explains itself",
        r"(.+) because it is \1"
    ]

    circular_penalty = 0
    for pattern in circular_patterns:
        if re.search(pattern, text_lower):
            circular_penalty += 0.6

    # Self-causation phrases
    self_cause_markers = [
        "caused by itself",
        "explains itself",
        "self caused",
        "causes itself",
        "results from itself"
    ]

    if any(p in text_lower for p in self_cause_markers):
        circular_penalty += 0.6

    # ---------------------------
    # Tautology detection
    # ---------------------------
    tautology_patterns = [
        r"(.+) is (.+) because it is (.+)",
        r"(.+) happens because (.+) happens",
        r"(.+) exists because (.+) exists"
    ]

    tautology_penalty = 0
    for pattern in tautology_patterns:
        if re.search(pattern, text_lower):
            tautology_penalty += 0.5

    # ---------------------------
    # Fake causality detection
    # ---------------------------
    fake_causal_phrases = [
        "proves that",
        "this proves",
        "which proves",
        "therefore it is true",
        "hence it must be"
    ]

    fake_causal_penalty = sum(1 for p in fake_causal_phrases if p in text_lower) * 0.2

    # ---------------------------
    # Depth bonus for multi-step reasoning
    # ---------------------------
    chain_markers = ["first", "then", "next", "finally", "step", "process", "mechanism"]
    chain_bonus = sum(1 for w in chain_markers if w in text_lower) * 0.1

    # ---------------------------
    # Final score
    # ---------------------------
    score = structure_score + chain_bonus
    score -= (circular_penalty + tautology_penalty + fake_causal_penalty)

    # Clamp to 0–1
    score = max(0.0, min(score, 1.0))

    return round(score, 3)
