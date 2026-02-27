# 05 — Reasoning Depth Validator

**File:** `validators/reasoning.py`
**Lines of code:** 135
**Signal type:** Positive Indicator (higher = more trustworthy)
**Method:** Keyword heuristic (base uncertainty ≈ 0.20)
**Weight:** 0.15

---

## What It Measures

The reasoning depth validator answers: **"Does this text contain real, structured argumentation — or is it circular, tautological, or faking causality?"**

This is the most complex keyword-based validator because it computes both **positive signals** (good reasoning) and **negative penalties** (bad reasoning), then combines them.

---

## The Scoring System

Unlike simpler validators that only detect one kind of signal, reasoning depth computes:

```
final_score = (positive_signals + bonuses) - (penalties)
```

Clamped to [0, 1].

---

## Positive Signals

### Reasoning Connectors

```python
reasoning_markers = [
    "because", "therefore", "thus", "hence", "so that",
    "as a result", "due to", "leads to", "causes", "results in"
]
found_reasoning = [w for w in reasoning_markers if w in text_lower]
structure_score = len(found_reasoning) * 0.15
```

**What these detect:** Words that signal causal or logical connections between ideas.

**Why they matter:** Trustworthy text typically *explains* why something is true, not just *asserts* it.

- Assertion: "The economy is growing."
- Reasoning: "The economy is growing **because** consumer spending increased, which **leads to** higher GDP."

**Score contribution:** Each marker adds 0.15.

### Multi-Step Chain Markers

```python
chain_markers = ["first", "then", "next", "finally", "step", "process", "mechanism"]
found_chain = [w for w in chain_markers if w in text_lower]
chain_bonus = len(found_chain) * 0.1
```

**What these detect:** Language that structures an explanation into sequential steps.

**Why they matter:** Multi-step explanations suggest the author has a detailed understanding. "First X happens, then Y, which causes Z" is more epistemically grounded than "X causes Z."

**Score contribution:** Each marker adds 0.10 as a bonus.

---

## Negative Penalties

### Circular Reasoning Detection

```python
circular_patterns = [
    r"(.+) because \1",        # "X because X"
    r"(.+) is caused by \1",   # "X is caused by X"
    r"(.+) leads to \1",       # "X leads to X"
    r"(.+) results in \1",     # "X results in X"
    r"(.+) explains itself",
    r"(.+) because it is \1"
]
circular_hits = sum(1 for p in circular_patterns if re.search(p, text_lower))
circular_penalty = circular_hits * 0.6
```

**What circular reasoning is:**

Circular reasoning (also called "begging the question") occurs when the conclusion is assumed in the premise:

- "The Bible is true because it's the word of God, and we know it's the word of God because the Bible says so."
- "This policy is good because it produces positive outcomes, and we know the outcomes are positive because the policy is good."

**How the regex works:**

The pattern `r"(.+) because \1"` uses a **capture group** and a **backreference**:

- `(.+)` — Captures any sequence of characters (the "X" part)
- ` because ` — Matches the literal word "because" with spaces
- `\1` — Matches whatever was captured in the first group (the same "X")

So `re.search(r"(.+) because \1", "trust is important because trust is important")` would match, because "trust is important" appears before and after "because".

**Penalty:** 0.6 per circular pattern detected. This is severe — a single circular argument drops the score by more than half a standard reasoning marker can add.

### Self-Causation Markers

```python
self_cause_markers = [
    "caused by itself", "explains itself", "self caused",
    "causes itself", "results from itself"
]
if any(p in text_lower for p in self_cause_markers):
    circular_penalty += 0.6
```

**What this catches:** Explicit statements of self-causation, which is a particularly egregious form of circular reasoning.

**Penalty:** An additional 0.6 if any self-cause phrase is found.

### Tautology Detection

```python
tautology_patterns = [
    r"(.+) is (.+) because it is (.+)",    # "X is Y because it is Y"
    r"(.+) happens because (.+) happens",   # "X happens because X happens"
    r"(.+) exists because (.+) exists"      # "X exists because X exists"
]
tautology_hits = sum(1 for p in tautology_patterns if re.search(p, text_lower))
tautology_penalty = tautology_hits * 0.5
```

**What a tautology is:**

A tautology says the same thing twice in different words, presenting it as if it's explanatory:

- "Water is wet because it has the property of wetness."
- "The law is the law because the law states that it is the law."

**Difference from circular reasoning:** Circular reasoning uses the conclusion as a premise. Tautology restates the same claim as its own explanation. Both are logically empty.

**Penalty:** 0.5 per tautology detected — slightly less severe than circular reasoning.

### Fake Causality Detection

```python
fake_causal_phrases = [
    "proves that", "this proves", "which proves",
    "therefore it is true", "hence it must be"
]
found_fake = [p for p in fake_causal_phrases if p in text_lower]
fake_penalty = len(found_fake) * 0.2
```

**What fake causality is:**

Fake causality uses causal language to assert a conclusion without actually providing a causal chain:

- "The vaccine caused autism, which proves that vaccines are dangerous." (No causal chain shown)
- "Correlation X exists, therefore it is true that Y causes Z." (Correlation ≠ causation)

**Penalty:** 0.2 per phrase — less severe than circular reasoning because some uses of "proves that" are legitimate.

---

## Final Score Calculation

```python
total_penalty = circular_penalty + tautology_penalty + fake_penalty
raw_score = structure_score + chain_bonus - total_penalty
score = round(max(0.0, min(raw_score, 1.0)), 3)
```

**Key insight:** Penalties can drive the score negative, but `max(0.0, ...)` floors it at 0. A text with circular reasoning AND no positive reasoning markers gets a score of 0.0 — complete absence of valid reasoning.

### Uncertainty adjustment

```python
if total_penalty > 0:
    uncertainty = min(uncertainty * 1.3, 0.5)
```

If penalties were applied, uncertainty increases by 30%. This acknowledges that the penalty detection (regex-based) is imprecise and may have false positives.

---

## Libraries Used

### `re` (Python standard library)

The reasoning validator makes heavy use of regular expressions:

| Pattern | Purpose | Python Regex Feature Used |
|---------|---------|--------------------------|
| `r"(.+) because \1"` | Circular reasoning | **Capture groups** and **backreferences** |
| `r"(.+) is (.+) because it is (.+)"` | Tautology | **Multiple capture groups** |

**Capture groups** `(.+)` capture matched text and `\1` refers back to the first group's content. This is how the regex detects "X because X" — the same phrase appearing on both sides.

**`re.search(pattern, string)`** returns a match object if the pattern is found anywhere in the string, or `None` if not found. We only care about whether a match exists (truthiness), not what was matched.

No external libraries are used.

---

## Worked Example

**Input text:**
> "Climate change occurs because rising CO2 leads to increased greenhouse effect. This process happens in several steps: first, CO2 absorbs infrared radiation, then the energy is re-emitted, which results in warming."

**Reasoning markers:** "because", "leads to", "results in" → 3 × 0.15 = 0.45

**Chain markers:** "process", "first", "then" → 3 × 0.10 = 0.30

**Circular patterns:** None detected → 0.0

**Tautology patterns:** None detected → 0.0

**Fake causality:** None detected → 0.0

**Score:** 0.45 + 0.30 - 0.0 = **0.75**

This is a high score — the text demonstrates structured, multi-step reasoning with explicit causal connections.

**Counter-example:**
> "Climate is climate because the climate is the climate. This proves that climate exists because it exists."

**Reasoning markers:** "because" → 1 × 0.15 = 0.15

**Chain markers:** None → 0.0

**Circular patterns:** "climate is climate because the climate is the climate" → likely matches `(.+) because \1` → penalty 0.6

**Tautology patterns:** "exists because it exists" → likely matches → penalty 0.5

**Fake causality:** "this proves" → 1 × 0.2 = 0.2

**Score:** 0.15 + 0.0 - (0.6 + 0.5 + 0.2) = 0.15 - 1.3 = **-1.15 → clamped to 0.0**

Zero reasoning depth — correctly identified as empty argumentation.

---

## Limitations

1. **Regex backreferences require exact matches:** `r"(.+) because \1"` only detects "X because X" when X is the *exact same string*. "Trust is important because trustworthiness matters" is semantically circular but won't match because the words are different.
2. **Positive markers ≠ good reasoning:** "Because therefore thus hence" — four markers, zero actual reasoning. The validator counts markers, not logical validity.
3. **Penalties are fixed, not contextual:** A single use of "this proves" in a math proof (where it's legitimate) gets the same penalty as in a pseudoscience screed.
4. **No semantic understanding:** The validator cannot tell whether a "because" statement actually provides a valid cause. "The sun rises because roosters crow" has a reasoning marker but the reasoning is wrong.
