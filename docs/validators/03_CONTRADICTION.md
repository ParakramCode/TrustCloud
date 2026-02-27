# 03 — Contradiction Validator

**File:** `validators/contradiction.py`
**Lines of code:** 99
**Signal type:** DEFEATER (higher = LESS trustworthy)
**Method:** Keyword heuristic + sentiment analysis (base uncertainty ≈ 0.18)
**Weight:** 0.20

---

## What It Measures

The contradiction validator answers: **"Does this text contradict itself?"**

A text that says "The economy is growing" and then says "The economy is shrinking" contains a contradiction. A self-contradicting text cannot be trusted regardless of how well it scores on other dimensions.

This is why contradiction is classified as a **defeater**, not a positive indicator. The epistemic principle is:

> *A single strong contradiction invalidates the entire text's trustworthiness.*

If the contradiction score exceeds the defeater threshold (0.7 by default), the aggregator **caps** the final trust score at 0.3, regardless of what coherence, reasoning, or factual density scored.

---

## How It Works — Three Detection Methods

The validator combines three separate approaches and sums their scores:

### Method 1: Contradiction Marker Detection

```python
contradiction_markers = [
    "but", "however", "although", "yet", "on the other hand",
    "contradicts", "in contrast", "nevertheless"
]
found_markers = [w for w in contradiction_markers if w in text_lower]
marker_score = len(found_markers) * 0.15
```

**What it does:** Searches for words that typically introduce contrasting or opposing statements.

**How scoring works:** Each marker found adds 0.15 to the score.
- 0 markers found → 0.0
- 1 marker ("however") → 0.15
- 3 markers ("but", "however", "yet") → 0.45
- 7+ markers → hits the 1.0 cap

**Limitation:** These markers don't always indicate contradiction. "The weather was cold, but I enjoyed the hike" is not a contradiction — it's a valid contrast. This detector cannot tell the difference. The high base uncertainty (0.18) partially accounts for this imprecision.

### Method 2: Negation Density

```python
negations = ["not", "never", "no", "none", "nothing", "nobody"]
found_negations = [w for w in negations if w in text_lower]
negation_score = len(found_negations) * 0.1
```

**What it does:** Counts negation words. Dense negation often accompanies contradictory statements.

**How scoring works:** Each negation adds 0.10.

**Limitation:** Negation is a normal part of language. "Not all birds can fly" is a perfectly valid statement with no contradiction. High negation density is a *weak* signal for contradiction, not a definitive one.

**Important detail about keyword matching:** The code uses `if w in text_lower`, not word-boundary matching. This means "nothing" will also match when searching for "not" (because "not" appears inside "nothing"). Similarly, "nobody" contains "no". This is a known imprecision — it will occasionally double-count.

### Method 3: Sentiment Polarity Conflict

```python
blob = TextBlob(text)
polarity = blob.sentiment.polarity

polarity_conflict = 0.0
if polarity > 0.3 and found_negations:
    polarity_conflict = 0.3
elif polarity < -0.3 and found_negations:
    polarity_conflict = 0.3
```

**What it does:** Checks whether the overall sentiment of the text conflicts with the presence of negation words.

**The logic:**
- If the text is **positive** (polarity > 0.3) but contains negation words → conflict detected (you're saying positive things while negating things)
- If the text is **negative** (polarity < -0.3) and contains negation words → conflict detected (negation within already negative text creates ambiguity)

**How scoring works:** If a conflict is detected, 0.3 is added to the score.

### Final Score Combination

```python
score = round(min(marker_score + negation_score + polarity_conflict, 1.0), 3)
```

All three signals are summed. The result is capped at 1.0.

**Score interpretation:**
- **0.0–0.2:** No significant contradiction indicators
- **0.3–0.5:** Some contrasting language detected — may or may not be actual contradiction
- **0.6–0.7:** Multiple contradiction signals — approaching the defeater threshold
- **0.7+:** Defeater activates — trust score will be capped at 0.3

---

## TextBlob: The Sentiment Library

```python
from textblob import TextBlob
```

### What TextBlob is

TextBlob is a simplified text processing library built on top of NLTK (Natural Language Toolkit). It provides a simple API for common NLP tasks.

### How sentiment analysis works

```python
blob = TextBlob("This movie was absolutely wonderful and I loved every moment of it.")
print(blob.sentiment)
# Sentiment(polarity=0.625, subjectivity=0.6)
```

**Polarity** ranges from -1.0 (very negative) to +1.0 (very positive). 0.0 is neutral.

**Subjectivity** ranges from 0.0 (very objective) to 1.0 (very subjective). We don't use subjectivity in this validator.

### How TextBlob computes polarity

TextBlob uses a **lexicon-based approach**:

1. It has a dictionary of ~2,900 words, each with a pre-assigned polarity score. For example:
   - "wonderful" → +1.0
   - "terrible" → -1.0
   - "okay" → +0.1
   - "the" → 0.0 (neutral)

2. It processes each word in the text, looks up its polarity, and computes a weighted average accounting for modifiers like "very" (intensifier) or "not" (negation).

3. The final polarity is the average across all scored words.

### Why TextBlob and not a more sophisticated model

- **Simple and fast** — No GPU needed, runs in milliseconds
- **Deterministic** — Same text always gives the same polarity (unlike LLM-based sentiment)
- **Good enough for polarity detection** — We only need to know positive/negative/neutral, not fine-grained emotion

### Limitations of TextBlob

1. **Cannot detect sarcasm:** "Oh great, another bug" → positive polarity (because of "great")
2. **Domain-insensitive:** "The patient tested positive" → positive polarity (but this is a medical statement, not a positive sentiment)
3. **Ignores context:** Each word is scored independently, regardless of surrounding words
4. **English only**

---

## As a Defeater: How It Interacts with the Aggregator

When this validator's score exceeds the defeater threshold (0.7), the aggregator behavior changes:

```
Normal flow:
  coherence=0.8, reasoning=0.7, factuality=0.6
  → composite_trust = weighted_average ≈ 0.7

With active defeater:
  coherence=0.8, reasoning=0.7, factuality=0.6, contradiction=0.75
  → composite_trust = min(weighted_average, 0.3) ≈ 0.3
```

The trust score is **capped** at the `defeater_cap` value (default 0.3). This means a text can score perfectly on coherence, reasoning, and factuality, but if it contradicts itself, the final score will never exceed 0.3.

This reflects the epistemic principle: **contradiction is a structural failure that undermines all other trust signals.**

---

## Worked Example

**Input text:**
> "Climate change is definitely not happening. However, the rising temperatures clearly show that climate change is accelerating. Nobody can deny that nothing has changed."

**Step 1 — Markers:**
- Found: "however" → 0.15

**Step 2 — Negations:**
- Found: "not", "nobody", "nothing" → but note, "nothing" contains "not", so searching for "not" in the text also matches within "nothing". Let's check: `"not" in text_lower` → True (appears as "not happening"). `"nobody" in text_lower` → True. `"nothing" in text_lower` → True.
- 3 negations × 0.1 = 0.30

**Step 3 — Sentiment:**
- TextBlob polarity: The text mixes "definitely", "clearly", "rising" (positive words) with "not happening" and "nobody" — let's estimate polarity ≈ 0.1 (slightly positive, but TextBlob may go either way)
- If polarity > 0.3: polarity_conflict = 0.3. If not: 0.0
- Likely: 0.0 (polarity probably not above 0.3 threshold)

**Final score:** 0.15 + 0.30 + 0.0 = **0.45**

This is below the defeater threshold (0.7), so it would not cap the trust score. The contradiction is detected at moderate level but not strong enough to trigger the defeater.

**This reveals a limitation:** The text contains a blatant contradiction ("not happening" vs "accelerating"), but because our detector uses word-level heuristics rather than semantic understanding, it only partially catches it.

---

## Limitations

1. **Word-level, not semantic-level:** Cannot detect contradictions that use different words to say opposite things (e.g., "The economy is booming" followed by "GDP has declined sharply").
2. **High false-positive rate:** Legitimate contrasts ("X is good, but Y is better") trigger the same markers as contradictions.
3. **Substring matching:** `"not" in text` matches inside "nothing", "notwithstanding", "noted", etc.
4. **Binary polarity conflict:** The sentiment check only fires when polarity > 0.3 OR < -0.3. Texts with mild mixed sentiment slip through.
5. **No cross-sentence comparison:** The validator looks at the whole text as one blob. It doesn't compare sentence 1's claim to sentence 2's claim. A true contradiction detector would use Natural Language Inference (NLI) models to check whether one sentence entails, contradicts, or is neutral with respect to another.
