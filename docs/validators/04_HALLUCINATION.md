# 04 — Hallucination Risk Validator

**File:** `validators/hallucination.py`
**Lines of code:** 100
**Signal type:** DEFEATER (higher = LESS trustworthy)
**Method:** Keyword heuristic (base uncertainty ≈ 0.20)
**Weight:** 0.20

---

## What It Measures

The hallucination validator answers: **"Does this text show signs of being fabricated or ungrounded?"**

**Critical distinction:** This validator does NOT detect actual hallucinations. It detects **linguistic patterns that correlate with hallucination**. It cannot verify whether "The Brennan-Okafor theorem" actually exists — it can only notice that the text uses vague hedging language or excessive absolutism, which hallucinated texts tend to do.

This is why the validator is named `hallucination_risk`, not `hallucination_detector`.

---

## The Three Signal Categories

### Category 1: Uncertainty Markers

```python
uncertainty_markers = [
    "maybe", "might", "could be", "possibly", "it seems",
    "i think", "i believe", "likely", "apparently", "suggests that"
]
found_uncertainty = [w for w in uncertainty_markers if w in text_lower]
uncertainty_score = len(found_uncertainty) * 0.15
```

**What these detect:** Language that hedges or avoids commitment.

**The paradox:** In scientific writing, hedging is *good* — it shows appropriate epistemic humility. Saying "the data suggests that" is more honest than "the data proves that." But in LLM output, excessive hedging often indicates the model is "uncertain" about something it's generating — it knows it doesn't have strong evidence for the claim.

**Score contribution:** Each marker adds 0.15. Three markers → 0.45.

### Category 2: Vagueness Markers

```python
vagueness_markers = [
    "many", "some", "various", "numerous", "several",
    "a lot", "a number of", "things", "stuff"
]
found_vagueness = [w for w in vagueness_markers if w in text_lower]
vagueness_score = len(found_vagueness) * 0.1
```

**What these detect:** Words that sound informative but carry no specific information.

**Why vagueness signals hallucination:** When an LLM doesn't have specific facts, it falls back to vague quantifiers. Compare:

- Grounded: "A 2019 study of 6,500 participants found..."
- Vague: "Various studies have found that numerous factors..."

The first is verifiable. The second could be entirely fabricated and you'd never know.

**Score contribution:** Each marker adds 0.10. Lower weight than uncertainty markers because vagueness is weaker evidence of hallucination (some legitimate texts are naturally vague).

### Category 3: Absolutism Markers

```python
absolutism_markers = [
    "always", "never", "everyone", "everything", "completely", "guaranteed"
]
found_absolutism = [w for w in absolutism_markers if w in text_lower]
absolutism_score = len(found_absolutism) * 0.1
```

**What these detect:** Overly strong claims that are rarely true in reality.

**Why absolutism signals hallucination:** LLMs in hallucination mode often overclaim. Real experts say "in most cases" or "typically." Hallucinating LLMs say "always" and "everyone agrees."

Compare:
- Careful: "Most climate scientists agree that..."
- Absolutist: "Everyone knows that climate change will completely..."

**Score contribution:** Each marker adds 0.10.

---

## Category 4: Grounding Penalty

```python
numeric_refs = len(re.findall(r"\d+", text))
grounding_penalty = 0.2 if numeric_refs == 0 else 0.0
```

**What this does:** Checks whether the text contains any numbers at all.

**The `re.findall()` function:** This uses Python's regular expression module. The pattern `r"\d+"` means:
- `\d` — Any digit character (0-9)
- `+` — One or more of the previous character

So `re.findall(r"\d+", "The study of 6500 people in 2019")` returns `["6500", "2019"]`.

**Why no numbers is a risk signal:** Factual, grounded text almost always contains numbers — dates, quantities, percentages, measurements. If a text claims to be informative but contains zero numbers, it's more likely to be fabricated generalities.

**Score contribution:** A flat 0.2 penalty if no numbers at all. This is a one-time penalty, not cumulative.

**Limitation:** Some texts are legitimately number-free. Poetry, philosophical arguments, and emotional narratives don't need numbers. This validator would penalise them unfairly. The high base uncertainty (0.20) partially compensates.

---

## Final Score Combination

```python
score = round(min(
    uncertainty_score + vagueness_score + absolutism_score + grounding_penalty,
    1.0
), 3)
```

All four signals are summed and capped at 1.0.

**Score interpretation:**
- **0.0:** No hallucination risk indicators at all (rare — most text has some hedging)
- **0.1–0.3:** Minor risk — normal hedging and vagueness
- **0.3–0.5:** Moderate risk — multiple markers present
- **0.5–0.7:** High risk — heavy vagueness/absolutism/hedging
- **0.7+:** Defeater activates — trust score capped at 0.3

---

## Libraries Used

### `re` (Python standard library)

```python
import re
```

**What it is:** Python's regular expression module. Built into Python, no installation needed.

**What we use:** `re.findall(pattern, string)` — Returns all non-overlapping matches of the pattern in the string as a list.

**The pattern `r"\d+"`:**
- `r"..."` — Raw string (backslashes are treated literally, not as escape characters)
- `\d` — Matches any digit (0-9)
- `+` — Matches one or more of the preceding element

**Example:**
```python
re.findall(r"\d+", "In 2019, 6500 participants scored 94.7 percent")
# Returns: ['2019', '6500', '94', '7']
# Note: '94.7' is split into '94' and '7' because '.' is not a digit
```

### No external libraries

Unlike the coherence validator (which uses sentence-transformers) or the contradiction validator (which uses TextBlob), the hallucination validator uses **only keyword lists and regex**. This makes it:
- Very fast (sub-millisecond)
- Zero external dependencies beyond Python
- But also the least sophisticated detector in the system

---

## Worked Example

**Input text:**
> "Various experts suggest that quantum biology might possibly revolutionise everything. Many studies confirm that numerous breakthroughs are happening in several fields."

**Uncertainty markers:** "suggest", "might", "possibly" → 3 × 0.15 = 0.45

**Vagueness markers:** "various", "many", "numerous", "several" → 4 × 0.10 = 0.40

**Absolutism markers:** "everything" → 1 × 0.10 = 0.10

**Grounding penalty:** No numbers in the text → 0.20

**Total:** 0.45 + 0.40 + 0.10 + 0.20 = **1.15 → capped to 1.0**

**Result:** Maximum hallucination risk. Defeater activates. Trust score would be capped at 0.3.

This is correct — the text is a masterclass in saying nothing specific while sounding informative.

---

## Comparison: What This Validator Can and Cannot Catch

| Scenario | Can Detect? | Why |
|----------|------------|-----|
| "Various studies show numerous results" | ✅ Yes | Vagueness markers |
| "Everything is completely guaranteed" | ✅ Yes | Absolutism markers |
| "Maybe it might possibly work" | ✅ Yes | Uncertainty markers |
| A text with no numbers at all | ✅ Yes | Grounding penalty |
| "The Brennan-Okafor theorem (2019) proves..." | ❌ No | Contains numbers and no hedging — looks grounded even though the theorem is fabricated |
| "73.2% of quantum processes..." | ❌ No | Contains a specific number — looks factual even if the number is made up |
| A well-written, confident lie | ❌ No | No vagueness, no hedging, no absolutism — stylistically identical to truth |

**The fundamental limitation:** This validator detects the *style* of hallucination, not the *substance*. A sophisticated hallucinator that uses specific (but fabricated) numbers and confident (but false) claims will pass undetected. Detecting that would require fact-checking against external knowledge bases, which is beyond this system's scope and is listed as a blind spot.
