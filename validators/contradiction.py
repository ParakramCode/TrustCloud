from textblob import TextBlob

def check_contradiction(text: str) -> float:
    """
    Returns contradiction probability in range [0,1]
    """

    text_lower = text.lower()

    contradiction_markers = [
        "but", "however", "although", "yet", "on the other hand",
        "contradicts", "in contrast", "nevertheless"
    ]

    negations = ["not", "never", "no", "none", "nothing", "nobody"]

    # Marker-based detection
    marker_score = sum(1 for w in contradiction_markers if w in text_lower) * 0.15

    # Negation density
    negation_score = sum(1 for w in negations if w in text_lower) * 0.1

    # Sentiment polarity flip detection
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to +1

    polarity_conflict = 0
    if polarity > 0.3 and any(n in text_lower for n in negations):
        polarity_conflict = 0.3
    elif polarity < -0.3 and any(n in text_lower for n in negations):
        polarity_conflict = 0.3

    score = marker_score + negation_score + polarity_conflict

    return round(min(score, 1.0), 3)
