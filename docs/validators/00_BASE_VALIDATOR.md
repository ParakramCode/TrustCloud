# 00 — Base Validator & Uncertainty Model

**File:** `validators/base.py`
**Lines of code:** 176

This is the foundation of the entire validator system. Every validator inherits from `BaseValidator` and returns a `ValidatorOutput`. If you understand this file, you understand the architecture.

---

## Part 1: ValidatorOutput — What Validators Return

Every validator in the system produces exactly one `ValidatorOutput`. Here's what each field means:

```python
@dataclass
class ValidatorOutput:
    score: float            # The measurement — a number between 0 and 1
    uncertainty: float      # How much that number could be wrong
    explanation: str        # A human-readable sentence explaining WHY
    evidence: list[dict]    # Specific proof items (markers found, scores computed, etc.)
```

### `score` (float, 0 to 1)

This is the validator's measurement. What it *means* depends on the validator's `signal_type`:

- **Positive indicator:** Higher score = more trustworthy. A coherence score of 0.9 means "the sentences are very similar in topic."
- **Defeater:** Higher score = *less* trustworthy. A hallucination score of 0.8 means "strong hallucination risk detected."

The score is always between 0.0 and 1.0. The system enforces this with `max(0.0, min(score, 1.0))`.

### `uncertainty` (float, 0 to 0.5)

This is the crucial field that separates TrustCloud from a naive scoring tool. Every measurement has error. A thermometer might read 37°C but the true value could be anywhere between 36.5°C and 37.5°C. The uncertainty tells you how wide that range is.

**Why it matters for the aggregator:** When combining scores, validators with *lower uncertainty* are given more weight. If the coherence validator says "score = 0.8, uncertainty = 0.08" and the reasoning validator says "score = 0.3, uncertainty = 0.20", the aggregator trusts the coherence score more because it's more certain.

The uncertainty is capped at 0.5. If uncertainty reaches 0.5, the measurement is essentially meaningless — the score could be anywhere from 0 to 1.

### `explanation` (str)

A human-readable sentence explaining the score. This is not for machines — it's for anyone reading the API response to understand *why* the system scored this text the way it did.

### `evidence` (list of dicts)

Structured proof items. Each dict typically has a `type` field and supporting data. For example, the coherence validator returns pairwise similarity scores between each sentence pair. This allows downstream tools (dashboards, reports) to dig deeper than the headline score.

---

## Part 2: The 95% Credible Interval

`ValidatorOutput` has three computed properties that use the uncertainty:

```python
@property
def lower_bound(self) -> float:
    return max(0.0, self.score - 1.96 * self.uncertainty)

@property
def upper_bound(self) -> float:
    return min(1.0, self.score + 1.96 * self.uncertainty)

@property
def interval(self) -> tuple[float, float]:
    return (round(self.lower_bound, 3), round(self.upper_bound, 3))
```

### What 1.96 means

The number 1.96 comes from statistics. If you assume the true score follows a normal distribution centred on the measured score, then:

- The true value falls within **±1.96 standard deviations** of the measured value **95% of the time**.
- This is called a **95% credible interval** (or confidence interval in frequentist statistics).

### Example

If `score = 0.7` and `uncertainty = 0.08`:
- Lower bound: `0.7 - 1.96 × 0.08 = 0.543`
- Upper bound: `0.7 + 1.96 × 0.08 = 0.857`
- Interval: `(0.543, 0.857)`

This means: "We estimate the true coherence is 0.7, but it could reasonably be anywhere between 0.54 and 0.86."

### Why this matters

Without the interval, a score of 0.7 could be:
- A precise measurement that is definitely around 0.7 (low uncertainty)
- A rough guess that could be anywhere between 0.3 and 1.0 (high uncertainty)

The interval tells you which case you're dealing with.

---

## Part 3: BaseValidator — The Abstract Class

Every validator must implement this interface:

```python
class BaseValidator(ABC):
```

`ABC` stands for **Abstract Base Class** (from Python's `abc` module). This means you cannot create a `BaseValidator` object directly — you must create a subclass that implements all the abstract methods.

### Required Properties (must be implemented)

| Property | Type | Purpose |
|----------|------|---------|
| `name` | str | Unique identifier — e.g., `"coherence"`, `"contradiction"` |
| `version` | str | Version string — e.g., `"v1.0"`. Allows tracking when validators change. |
| `default_weight` | float | How much influence this validator has in aggregation. Higher = more influence. Weights are normalised at aggregation time, so they don't need to sum to 1. |
| `method_type` | str | The measurement methodology — determines base uncertainty level. See table below. |

### Optional Properties (have defaults)

| Property | Default | Purpose |
|----------|---------|---------|
| `signal_type` | `"positive_indicator"` | Whether this is a positive signal or a defeater |
| `inverted` | Computed from `signal_type` | `True` if this is a defeater (convenience property) |

### Required Method

```python
@abstractmethod
def run(self, text: str) -> ValidatorOutput:
```

This is the core. Every validator takes a string and returns a `ValidatorOutput`. The orchestrator calls this method, catches any exceptions, and records timing.

---

## Part 4: Method Types and Base Uncertainty

Each validator declares a `method_type` that determines its **base uncertainty**:

```python
BASE_UNCERTAINTY = {
    "embedding_similarity": 0.08,   # Model-based — relatively stable
    "keyword_heuristic":    0.20,   # Rule-based — high variance
    "nlp_pipeline":         0.12,   # spaCy NER — moderate
    "sentiment_analysis":   0.15,   # TextBlob — moderate-high
}
```

### Why different methods have different uncertainties

- **Embedding similarity (σ = 0.08):** Uses a trained machine learning model (`all-MiniLM-L6-v2`). The model was trained on millions of sentence pairs and produces consistent results. Running it twice on the same text gives the same output. Low uncertainty.

- **Keyword heuristic (σ = 0.20):** Searches for specific words like "maybe", "however", "therefore". The presence of a word like "but" doesn't definitively mean contradiction — it could be a valid contrast. Word lists are inherently imprecise. High uncertainty.

- **NLP pipeline (σ = 0.12):** Uses spaCy's trained pipeline for named entity recognition. It's a model, so it's more reliable than keyword matching, but NER makes mistakes (e.g., treating "The Washington Post" as a person instead of an organisation). Moderate uncertainty.

- **Sentiment analysis (σ = 0.15):** Uses TextBlob, which is a simple polarity detector. It captures broad sentiment but misses sarcasm, domain-specific language, and nuance. Moderate-high uncertainty.

---

## Part 5: The `estimate_uncertainty()` Function

This function computes the final uncertainty for a specific measurement, adjusting the base uncertainty based on the input text:

```python
def estimate_uncertainty(method_type: str, text: str) -> float:
    base = BASE_UNCERTAINTY.get(method_type, 0.15)

    sentence_count = max(len([s for s in text.split(".") if s.strip()]), 1)
    complexity_factor = 1.0 + 0.1 * math.log(max(sentence_count / 2, 1))

    length_factor = 1.0
    if len(text) < 50:
        length_factor = 1.5
    elif len(text) < 100:
        length_factor = 1.2

    uncertainty = base * complexity_factor * length_factor
    return round(min(uncertainty, 0.5), 3)
```

### Step by step:

1. **Start with base uncertainty** for the method type (e.g., 0.08 for embedding similarity).

2. **Complexity factor:** More sentences = more things to measure = more chances for the measurement to be wrong. This uses a logarithmic scaling (`math.log`) so the increase is gradual — going from 2 sentences to 10 increases uncertainty gently.

3. **Length factor:** Very short texts (under 50 characters) get 1.5x uncertainty because there's not enough content to measure reliably. Texts under 100 characters get 1.2x.

4. **Cap at 0.5:** Uncertainty above 0.5 would mean the 95% credible interval spans nearly the entire [0, 1] range, making the measurement meaningless.

### Example calculation

For embedding similarity on a 3-sentence, 200-character text:
- Base: 0.08
- Complexity: `1.0 + 0.1 × log(3/2)` = `1.0 + 0.1 × 0.405` = 1.041
- Length: 1.0 (text > 100 chars)
- Final: `0.08 × 1.041 × 1.0` = **0.083**

For keyword heuristic on a 1-sentence, 30-character text:
- Base: 0.20
- Complexity: `1.0 + 0.1 × log(max(0.5, 1))` = 1.0
- Length: 1.5 (text < 50 chars)
- Final: `0.20 × 1.0 × 1.5` = **0.300**

### Honest limitation

These base uncertainty values are **rough estimates**, not calibrated values. True calibration would require a labelled dataset where human experts score the same texts, and then you measure how much the validator's scores deviate from human judgement. This is acknowledged as a blind spot of the system.

---

## Part 6: Libraries Used in This File

| Library | Import | Purpose |
|---------|--------|---------|
| `abc` | `from abc import ABC, abstractmethod` | Python's built-in module for Abstract Base Classes. `ABC` is the parent class, `@abstractmethod` marks methods that subclasses *must* implement. If a subclass doesn't implement an abstract method, Python raises `TypeError` at instantiation. |
| `dataclasses` | `from dataclasses import dataclass, field` | Python's built-in module for creating classes that mainly hold data. `@dataclass` auto-generates `__init__`, `__repr__`, and `__eq__` methods. `ValidatorOutput` uses this to avoid writing boilerplate constructor code. |
| `typing` | `from typing import Optional` | Python's built-in type hints. `Optional[list[dict]]` means "this can be a list of dicts, or it can be `None`." |
| `math` | `import math` (inside function) | Python's built-in math module. Used for `math.log()` (natural logarithm) in the complexity factor calculation. |

None of the imports in `base.py` require external packages — they're all part of Python's standard library.
