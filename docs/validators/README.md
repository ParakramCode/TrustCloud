# TrustCloud AI — Validator System Documentation

## What This Folder Contains

Each file in this directory is a deep-dive explanation of one component of the TrustCloud AI validator system. These are written to give you a **complete understanding** of what every line of code does, what libraries are used, why they were chosen, and what the limitations are.

## Reading Order

Start here, then read the validators in this order:

| # | Document | What You'll Learn |
|---|----------|-------------------|
| 1 | [00_BASE_VALIDATOR.md](00_BASE_VALIDATOR.md) | The foundation — what every validator must implement, how uncertainty works, what `score` and `uncertainty` actually mean |
| 2 | [01_COHERENCE.md](01_COHERENCE.md) | How sentence embeddings measure topical coherence |
| 3 | [02_SEMANTIC_CONSISTENCY.md](02_SEMANTIC_CONSISTENCY.md) | How semantic similarity differs from coherence (they share a model) |
| 4 | [03_CONTRADICTION.md](03_CONTRADICTION.md) | How contradiction is detected and why it's a *defeater*, not a regular signal |
| 5 | [04_HALLUCINATION.md](04_HALLUCINATION.md) | How hallucination *risk* is estimated (not actual hallucination detection) |
| 6 | [05_REASONING_DEPTH.md](05_REASONING_DEPTH.md) | How the system detects real reasoning vs. circular logic and tautologies |
| 7 | [06_FACTUAL_DENSITY.md](06_FACTUAL_DENSITY.md) | How spaCy NER counts factual references (and why count ≠ accuracy) |

## The Two Types of Validators

Every validator in the system is classified as one of:

- **Positive Indicator** — A higher score means *more trustworthy*. These are combined additively during aggregation.
- **Defeater** — A higher score means *less trustworthy*. These act as **gates** — a single strong defeater can cap the entire trust score regardless of how well positive indicators scored.

| Validator | Type | Why |
|-----------|------|-----|
| Coherence | Positive Indicator | Two coherent sentences are more trustworthy than incoherent ones |
| Semantic Consistency | Positive Indicator | Consistent meaning across sentences suggests reliable content |
| Reasoning Depth | Positive Indicator | Well-structured arguments with real causal chains are more trustworthy |
| Factual Density | Positive Indicator | References to specific entities/numbers suggest verifiable claims |
| Contradiction | **Defeater** | A self-contradicting text cannot be trusted, period |
| Hallucination Risk | **Defeater** | Vague, absolutist, or ungrounded claims suggest fabrication |

## Libraries Used Across All Validators

| Library | Used By | Purpose | Documentation |
|---------|---------|---------|---------------|
| `sentence-transformers` | Coherence, Semantic | Converts text into numerical vectors (embeddings) | [sbert.net](https://www.sbert.net/) |
| `scikit-learn` | Coherence, Semantic | Computes cosine similarity between embeddings | [scikit-learn.org](https://scikit-learn.org/) |
| `numpy` | Coherence, Semantic | Array operations — mean, std, min calculations | [numpy.org](https://numpy.org/) |
| `spaCy` | Factual Density | Named Entity Recognition (NER) and part-of-speech tagging | [spacy.io](https://spacy.io/) |
| `TextBlob` | Contradiction | Sentiment analysis (polarity detection) | [textblob.readthedocs.io](https://textblob.readthedocs.io/) |
| `re` (stdlib) | Hallucination, Reasoning, Factuality | Regular expressions for pattern matching | Part of Python |
