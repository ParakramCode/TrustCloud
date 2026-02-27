# 01 — Coherence Validator

**File:** `validators/coherence.py`
**Lines of code:** 85
**Signal type:** Positive Indicator (higher = more trustworthy)
**Method:** Embedding similarity (base uncertainty ≈ 0.08)
**Weight:** 0.25 (highest of all validators)

---

## What It Measures

The coherence validator answers a simple question: **"Do adjacent sentences in this text talk about the same topic?"**

If sentence 1 is about photosynthesis and sentence 2 is about the stock market, that's incoherent. If both sentences are about plant biology, that's coherent.

It does NOT measure:
- Whether the sentences are *true*
- Whether the logic is *valid*
- Whether the text is *well-written*

It only measures: are adjacent sentences about the same topic?

---

## How It Works — Step by Step

### Step 1: Split the text into sentences

```python
sentences = [s.strip() for s in text.split(".") if s.strip()]
```

This splits the text at every period (`.`), removes whitespace from each piece, and filters out empty strings.

**Limitation:** This is a naive sentence splitter. It will break on:
- Abbreviations: "Dr. Smith" becomes two fragments: "Dr" and "Smith"
- Decimal numbers: "The temperature was 3.5 degrees" splits at 3.5
- Ellipses: "Well... maybe" becomes fragments

A more robust approach would use spaCy's sentence segmenter or NLTK's `sent_tokenize`, but for the current use case (evaluating LLM output, which tends to use clean punctuation), this is acceptable.

### Step 2: Handle trivial inputs

```python
if len(sentences) < 2:
    return ValidatorOutput(
        score=1.0,
        uncertainty=uncertainty * 1.5,
        explanation="Single sentence — coherence is trivially 1.0...",
    )
```

If there's only one sentence, you can't measure coherence *between* sentences. The score defaults to 1.0 (no incoherence detected) but uncertainty is multiplied by 1.5 to signal that this isn't a real measurement.

### Step 3: Convert sentences to embeddings

```python
embeddings = _model.encode(sentences)
```

This is the core step. The sentence transformer model converts each sentence from human-readable text into a **dense numerical vector** — a list of 384 numbers that represent the *meaning* of the sentence.

**What an embedding is:**

Imagine a space where every possible sentence has a position. Sentences with similar meanings are close together; sentences with different meanings are far apart. An embedding is the coordinates of a sentence in that space.

For example:
- "The cat sat on the mat" → `[0.23, -0.41, 0.87, ...]` (384 numbers)
- "A feline rested on the rug" → `[0.21, -0.39, 0.85, ...]` (very similar numbers — same meaning)
- "The stock market crashed" → `[-0.65, 0.12, -0.33, ...]` (very different numbers — different meaning)

### Step 4: Compute pairwise cosine similarity

```python
for i in range(len(embeddings) - 1):
    sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
    sims.append(float(sim))
```

**Cosine similarity** measures the angle between two vectors, ignoring their magnitude. It returns a value between -1 and 1:

- **1.0:** Vectors point in the same direction → sentences have the same meaning
- **0.0:** Vectors are perpendicular → sentences are unrelated
- **-1.0:** Vectors point in opposite directions → sentences have opposite meaning

The formula is:

```
cosine_similarity(A, B) = (A · B) / (|A| × |B|)
```

Where `A · B` is the dot product (multiply corresponding elements and sum) and `|A|` is the vector's length (square root of sum of squares).

**Why cosine and not Euclidean distance?** Cosine similarity is scale-invariant. If one embedding is "louder" (larger numbers) but points in the same direction, cosine similarity still recognises it as similar. This is important because embedding magnitudes can vary.

This loop compares sentence 0 to sentence 1, sentence 1 to sentence 2, and so on — only **adjacent** pairs, not all possible pairs.

### Step 5: Compute statistics

```python
avg_sim = float(np.mean(sims))     # Average similarity across all pairs
min_sim = float(np.min(sims))      # Worst pair (potential topic jump)
std_sim = float(np.std(sims))      # How much similarity varies
```

- `np.mean()` — Sum all values, divide by count. This is the headline score.
- `np.min()` — The lowest similarity found. If there's one bad pair in an otherwise coherent text, min_sim catches it.
- `np.std()` — Standard deviation. If all pairs have similar scores, std is low. If some are high and some are low, std is high.

### Step 6: Adjust uncertainty

```python
if std_sim > 0.2:
    uncertainty = min(uncertainty * 1.3, 0.5)
```

If the pairwise similarities are inconsistent (high standard deviation), the average is less reliable. The uncertainty is increased by 30% to reflect this.

### Step 7: Return the result

The score is `avg_sim` (the average pairwise similarity), clamped to [0, 1].

---

## The Sentence Transformer Model

```python
_model = SentenceTransformer("all-MiniLM-L6-v2")
```

### What is `all-MiniLM-L6-v2`?

It's a pre-trained model from the [Sentence Transformers](https://www.sbert.net/) library. Let's unpack the name:

| Part | Meaning |
|------|---------|
| `all` | Trained on a large collection of diverse text datasets (over 1 billion training pairs) |
| `MiniLM` | Based on the MiniLM architecture — a distilled (compressed) version of larger language models |
| `L6` | Has 6 transformer layers (larger models have 12 or 24) |
| `v2` | Second version of this model |

### Key specs

- **Output dimension:** 384 (each sentence becomes a 384-number vector)
- **Model size:** ~80 MB on disk, ~250 MB in memory
- **Speed:** ~14,000 sentences per second on GPU, ~100–500 on CPU
- **Quality:** Excellent for sentence similarity tasks. Ranked in the top tier on the [STS Benchmark](https://paperswithcode.com/sota/semantic-textual-similarity-on-sts-benchmark)

### Why this model was chosen

1. **Small enough to run on CPU** — No GPU required, which is important for a student project
2. **Good enough for sentence similarity** — This is the #1 use case it was designed for
3. **Well-documented** — Extensive documentation and community support
4. **Loaded once, used everywhere** — The `_model` variable is created at module level, so it loads once when the server starts, not every time a request comes in

### How it loads

```python
_model = SentenceTransformer("all-MiniLM-L6-v2")
```

On first run, this downloads the model from Hugging Face Hub (~80 MB) and caches it locally. On subsequent runs, it loads from cache. The cache is typically at `~/.cache/huggingface/`.

---

## Libraries Used

### `sentence-transformers` (`from sentence_transformers import SentenceTransformer`)

**What it is:** A Python library that provides pre-trained models for converting sentences into fixed-length vector embeddings.

**Why we need it:** Without embeddings, we'd have to compare sentences using string matching or keyword overlap, which can't capture meaning. "A cat sat" and "A feline rested" share no words but have the same meaning — embeddings capture this.

**Key method:** `model.encode(sentences)` — Takes a list of strings, returns a numpy array of shape `(num_sentences, 384)`.

**Installation:** `pip install sentence-transformers` — This also installs PyTorch and Hugging Face Transformers as dependencies.

### `scikit-learn` (`from sklearn.metrics.pairwise import cosine_similarity`)

**What it is:** Python's most widely used machine learning library. We only use one function from it.

**Why we need it:** `cosine_similarity()` computes the cosine similarity between two sets of vectors. We could compute this manually with numpy, but scikit-learn handles edge cases (zero vectors, numerical stability) and is heavily optimised.

**Input/Output:** Takes two 2D arrays and returns a similarity matrix. We pass `[embeddings[i]]` (1×384) and `[embeddings[i+1]]` (1×384) and get a 1×1 matrix, from which we extract `[0][0]`.

### `numpy` (`import numpy as np`)

**What it is:** Python's fundamental library for numerical computing. Provides fast array operations.

**Why we need it:** `np.mean()`, `np.min()`, and `np.std()` compute statistics on the list of similarity scores. These operations are trivially simple but numpy does them efficiently and handles edge cases (empty arrays, NaN values).

---

## Worked Example

**Input text:**
> "The Earth orbits the Sun. This orbital period takes 365.25 days. Bananas are yellow."

**Step 1:** Split into sentences:
- S1: "The Earth orbits the Sun"
- S2: "This orbital period takes 365.25 days"  (Note: "365.25 days" will split incorrectly due to the period after "25")
- Actually splits as: "The Earth orbits the Sun", "This orbital period takes 365", "25 days", "Bananas are yellow"

**Step 3:** Each sentence → 384-dim embedding

**Step 4:** Compare adjacent pairs:
- S1 vs S2: ~0.65 (both about Earth's orbit — similar)
- S2 vs S3: variable (fragment about "25 days")
- S3 vs S4: ~0.1 (days vs bananas — very different topic)

**Step 5:** Average similarity: ~0.4, Min: ~0.1, Std: high

**Result:** `score = 0.4`, indicating moderate coherence with a significant topic jump.

---

## Limitations

1. **Naive sentence splitting:** Periods in abbreviations and numbers cause incorrect splits.
2. **Topical coherence ≠ logical coherence:** Two sentences can be on the same topic but logically contradict each other. This validator would give them a high score.
3. **Short texts:** Single-sentence texts get a default score of 1.0 with high uncertainty.
4. **Language:** The model is English-centric. It handles some multilingual text but performance degrades.
5. **Semantic similarity ≠ factual accuracy:** "The sun is cold" and "The sun is not warm" are semantically similar but both wrong.
