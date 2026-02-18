import re

def check_hallucination(text: str) -> float:
    """
    Heuristic hallucination risk detector
    Returns risk score in range [0,1]
    """

    text_lower = text.lower()

    uncertainty_markers = [
        "maybe", "might", "could be", "possibly", "it seems",
        "i think", "i believe", "likely", "apparently", "suggests that"
    ]

    vagueness_markers = [
        "many", "some", "various", "numerous", "several",
        "a lot", "a number of", "things", "stuff"
    ]

    absolutism_markers = [
        "always", "never", "everyone", "everything", "completely", "guaranteed"
    ]

    uncertainty_score = sum(1 for w in uncertainty_markers if w in text_lower) * 0.15
    vagueness_score = sum(1 for w in vagueness_markers if w in text_lower) * 0.1
    absolutism_score = sum(1 for w in absolutism_markers if w in text_lower) * 0.1

    # numeric grounding check
    numeric_refs = len(re.findall(r"\d+", text))
    grounding_penalty = 0.2 if numeric_refs == 0 else 0

    score = uncertainty_score + vagueness_score + absolutism_score + grounding_penalty

    return round(min(score, 1.0), 3)
