from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def split_sentences(text):
    return [s.strip() for s in text.split('.') if len(s.strip()) > 10]

def check_semantic_consistency(text: str) -> float:
    """
    Returns semantic consistency score [0,1]
    """

    sentences = split_sentences(text)

    if len(sentences) < 2:
        return 1.0  # single statement = consistent by default

    embeddings = model.encode(sentences)

    similarities = []
    for i in range(len(embeddings) - 1):
        sim = cosine_similarity(
            [embeddings[i]],
            [embeddings[i+1]]
        )[0][0]
        similarities.append(sim)

    avg_sim = float(np.mean(similarities))

    # Normalize similarity to 0–1 scale
    normalized = max(0.0, min(avg_sim, 1.0))

    return round(normalized, 3)
