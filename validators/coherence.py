# validators/coherence.py
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def check_coherence(text):
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    if len(sentences) < 2:
        return 1.0
    
    embeddings = model.encode(sentences)
    sims = []

    for i in range(len(embeddings)-1):
        sim = cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
        sims.append(sim)

    return float(np.mean(sims))
