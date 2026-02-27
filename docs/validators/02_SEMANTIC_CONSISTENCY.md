# 02 — Semantic Consistency Validator

**File:** `validators/semantic.py`
**Lines of code:** 80
**Signal type:** Positive Indicator (higher = more trustworthy)
**Method:** Embedding similarity (base uncertainty ≈ 0.08)
**Weight:** 0.10

---

## What It Measures

Semantic consistency asks: **"Do adjacent sentences maintain consistent meaning?"**

This sounds almost identical to coherence, but there's a subtle difference:

| Aspect | Coherence | Semantic Consistency |
|--------|-----------|---------------------|
| Filters short sentences | No — all fragments count | Yes — only sentences > 10 characters |
| Focus | "Are these sentences about the same topic?" | "Do these sentences mean consistent things?" |
| Noise sensitivity | Higher (fragments from naive splitting can skew results) | Lower (short fragments are filtered out) |

In practice, these two validators produce similar but not identical scores. The semantic validator tends to score slightly higher because filtering out short fragments removes noisy, low-similarity pairs.

---

## How It Differs from Coherence

### The key line

```python
sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
```

Compare to coherence:
```python
sentences = [s.strip() for s in text.split(".") if s.strip()]
```

Coherence keeps **any non-empty fragment**. Semantic consistency requires **at least 10 characters**. This means fragments like "Dr", "e.g", or "3" (from decimal splitting) are excluded.

### Everything else is the same

- Same model (`all-MiniLM-L6-v2` — imported directly from the coherence module)
- Same cosine similarity computation
- Same score range [0, 1]

### Why have both?

Having two similar-but-not-identical validators provides:
1. **Measurement redundancy** — If both agree, you have more confidence. If they disagree, it signals something interesting (possibly a text with short disruptive fragments).
2. **Different sensitivity** — Coherence is more sensitive to structural noise; semantic consistency is more robust.

---

## The Shared Model

```python
from validators.coherence import _model  # Share the sentence-transformers model
```

This is a **critical design decision**. The `all-MiniLM-L6-v2` model uses ~250 MB of RAM. If each validator loaded its own copy, that would be 500 MB for two validators doing the same thing.

By importing `_model` from `coherence.py`, both validators share a single model instance. Python modules are singletons — no matter how many times you import `coherence`, the `_model` object is only created once.

---

## Algorithm Walkthrough

```python
def run(self, text: str) -> ValidatorOutput:
    # 1. Split into meaningful sentences (>10 chars)
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
    
    # 2. Handle trivial case
    if len(sentences) < 2:
        return ValidatorOutput(score=1.0, uncertainty=uncertainty * 1.5, ...)
    
    # 3. Encode all sentences into embeddings
    embeddings = _model.encode(sentences)
    
    # 4. Compare each adjacent pair
    similarities = []
    for i in range(len(embeddings) - 1):
        sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
        similarities.append(float(sim))
    
    # 5. Compute statistics
    avg_sim = float(np.mean(similarities))
    min_sim = float(np.min(similarities))
    score = round(max(0.0, min(avg_sim, 1.0)), 3)
    
    # 6. Return with evidence
    return ValidatorOutput(score=score, uncertainty=uncertainty, ...)
```

**Note:** Unlike coherence, semantic consistency does NOT adjust uncertainty based on standard deviation. This is a simpler validator that relies on the filtered input to reduce noise.

---

## Libraries Used

All libraries are shared with the coherence validator (see [01_COHERENCE.md](01_COHERENCE.md)):

| Library | What's Used | Why |
|---------|------------|-----|
| `sentence-transformers` | Imported indirectly via `coherence._model` | Sentence embeddings |
| `scikit-learn` | `cosine_similarity()` | Similarity computation |
| `numpy` | `np.mean()`, `np.min()` | Statistics |

No new libraries are introduced.

---

## Limitations

1. **High overlap with coherence** — These two validators are measuring very similar things. In a more mature system, you might replace them with a single validator that handles both filtering strategies, or differentiate them more clearly (e.g., semantic consistency could compare the first sentence to the last, not just adjacent pairs).
2. **Same sentence splitting problem** — Still uses period-based splitting.
3. **The 10-character threshold is arbitrary** — "She ran" is 7 characters but a valid sentence. "Dr. Smith" is 9 characters and not a sentence. The threshold is a rough heuristic.
