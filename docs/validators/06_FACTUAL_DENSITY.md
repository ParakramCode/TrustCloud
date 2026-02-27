# 06 — Factual Density Validator

**File:** `validators/factuality.py`
**Lines of code:** 87
**Signal type:** Positive Indicator (higher = more trustworthy)
**Method:** NLP pipeline / spaCy (base uncertainty ≈ 0.12)
**Weight:** 0.10 (lowest of all validators)

---

## What It Measures

The factual density validator answers: **"How many specific, potentially verifiable references does this text contain?"**

It counts four types of factual elements:
1. Named entities (people, organisations, locations)
2. Numbers
3. Dates and times
4. Proper nouns

**The critical caveat (stated in the code itself):**

> "Factual density measures density of factual REFERENCES, not factual ACCURACY."

A text that says "Dr. Smith at Harvard published a study in 2019 showing 94% improvement" has high factual density — many entities, numbers, and proper nouns. But **every single one of these could be fabricated.** The validator cannot verify truth; it can only count references.

This is why it has the **lowest weight** (0.10) of all validators.

---

## How spaCy Works

```python
import spacy
_nlp = spacy.load("en_core_web_sm")
```

### What spaCy is

spaCy is an industrial-strength NLP (Natural Language Processing) library. It processes text through a **pipeline** of steps:

```
Raw text → Tokenisation → POS tagging → NER → Parsed document
```

### What `en_core_web_sm` means

| Part | Meaning |
|------|---------|
| `en` | English language |
| `core` | Core functionality (includes all standard pipeline components) |
| `web` | Trained on web text (blogs, news, comments) |
| `sm` | Small model (~12 MB). Other sizes: `md` (medium, ~40 MB), `lg` (large, ~560 MB) |

### How the pipeline processes text

```python
doc = _nlp("Apple was founded by Steve Jobs in 1976 in Cupertino, California.")
```

This produces a `Doc` object containing:

| Token | POS | Entity Type |
|-------|-----|------------|
| Apple | PROPN | ORG |
| was | AUX | - |
| founded | VERB | - |
| by | ADP | - |
| Steve | PROPN | PERSON |
| Jobs | PROPN | PERSON |
| in | ADP | - |
| 1976 | NUM | DATE |
| in | ADP | - |
| Cupertino | PROPN | GPE |
| , | PUNCT | - |
| California | PROPN | GPE |
| . | PUNCT | - |

**POS** = Part of Speech (PROPN = proper noun, VERB = verb, etc.)
**Entity Type** = NER label (ORG = organisation, PERSON = person, GPE = geo-political entity, DATE = date)

---

## The Four Measurements

### 1. Named Entities

```python
entity_count = len(doc.ents)
```

`doc.ents` returns all named entities found by the NER (Named Entity Recognition) model.

**Entity types spaCy recognises:**

| Label | Meaning | Example |
|-------|---------|---------|
| PERSON | Named person | "Steve Jobs" |
| ORG | Organisation | "Apple", "WHO" |
| GPE | Country, city, state | "California", "France" |
| DATE | Dates and periods | "1976", "next week" |
| TIME | Times | "3 PM", "noon" |
| MONEY | Monetary values | "$50 million" |
| CARDINAL | Numbers not in other categories | "three", "42" |
| ORDINAL | Ordinal numbers | "first", "3rd" |
| PERCENT | Percentages | "94%", "ninety percent" |
| LOC | Non-GPE locations | "the Pacific Ocean" |

**Contribution to score:** Each entity adds 0.3 to the raw factual score.

### 2. Numeric References

```python
number_count = len(re.findall(r"\d+", text))
```

Counts all number sequences in the text using regex (same approach as the hallucination validator).

**Contribution to score:** Each number adds 0.2.

### 3. Date/Time Entities

```python
date_entities = [ent for ent in doc.ents if ent.label_ in ("DATE", "TIME")]
```

Filters entities to only DATE and TIME types.

**Contribution to score:** Each date/time adds 0.2.

**Note:** Dates are also counted in `entity_count`, so they contribute to both measurements. This means dates are double-weighted — which makes sense because a text that mentions specific dates is more likely to be factually grounded.

### 4. Proper Nouns

```python
proper_nouns = [t for t in doc if t.pos_ == "PROPN"]
```

Counts tokens (individual words) tagged as proper nouns by spaCy's part-of-speech tagger.

**Contribution to score:** Each proper noun adds 0.3.

**Overlap with entities:** Many proper nouns are also parts of named entities. "Steve Jobs" is 2 proper nouns and 1 entity (PERSON). This means proper nouns and entities partially overlap in counting.

---

## Score Normalisation

```python
token_count = max(len(doc), 1)

factual_score = (
    (entity_count * 0.3) +
    (number_count * 0.2) +
    (len(date_entities) * 0.2) +
    (len(proper_nouns) * 0.3)
)

normalized = factual_score / token_count
score = round(min(normalized * 10, 1.0), 3)
```

### Step by step:

1. **Raw factual score:** Weighted sum of all factual elements.
2. **Normalise by token count:** Divide by the number of words. This makes the score density-based — a 10-word sentence with 3 entities scores higher than a 100-word paragraph with 3 entities.
3. **Scale by 10:** The raw normalised score is usually small (0.01–0.1), so it's multiplied by 10 to use the full [0, 1] range.
4. **Cap at 1.0:** Prevents scores above 1.

### Why normalisation matters

Without normalisation, longer texts would always score higher (more words = more entities). Normalisation ensures we measure **density** — how packed with factual references the text is per unit of length.

---

## Libraries Used

### `spacy` (`import spacy`)

**What it is:** Industrial NLP library for Python. Used for tokenisation, part-of-speech tagging, named entity recognition, dependency parsing, and more.

**How it differs from TextBlob:** TextBlob is a simple, dictionary-based tool. spaCy uses trained machine learning models that understand context. TextBlob would tag "Apple" the same way in "I ate an apple" and "Apple released a new phone." spaCy recognises the second as an ORG entity.

**Installation:**
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

The `spacy download` step downloads the trained model weights (~12 MB for `sm`).

**Key methods used:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `_nlp(text)` | `Doc` object | Process text through the full NLP pipeline |
| `doc.ents` | List of `Span` objects | All named entities found |
| `ent.label_` | String | The entity type (PERSON, ORG, etc.) |
| `ent.text` | String | The entity text ("Steve Jobs") |
| `doc` (iterable) | `Token` objects | Iterate over all tokens (words) |
| `token.pos_` | String | Part-of-speech tag (PROPN, VERB, etc.) |
| `token.text` | String | The word itself |

### `re` (Python standard library)

Same usage as hallucination validator — `re.findall(r"\d+", text)` to count numbers.

---

## Worked Example

**Input text:**
> "Dr. Maria Chen at Stanford University published a study in Nature in 2023 showing that 67% of patients responded to the treatment within 14 days."

**spaCy processing:**

| Entity | Type |
|--------|------|
| Maria Chen | PERSON |
| Stanford University | ORG |
| Nature | ORG |
| 2023 | DATE |
| 67% | PERCENT |
| 14 days | DATE |

**Counts:**
- Entities: 6
- Numbers: `re.findall(r"\d+", text)` → ["2023", "67", "14"] = 3
- Date entities: 2 (2023, 14 days)
- Proper nouns: "Dr", "Maria", "Chen", "Stanford", "University", "Nature" = ~6

**Raw score:** (6 × 0.3) + (3 × 0.2) + (2 × 0.2) + (6 × 0.3) = 1.8 + 0.6 + 0.4 + 1.8 = 4.6

**Token count:** ~24 tokens

**Normalised:** 4.6 / 24 = 0.192

**Final score:** min(0.192 × 10, 1.0) = **1.0** (capped)

This is correct — the sentence is extremely dense with factual references.

**Counter-example:**
> "Things happen in various ways because of numerous factors that affect several outcomes."

**Counts:**
- Entities: 0
- Numbers: 0
- Date entities: 0
- Proper nouns: 0

**Score: 0.0** — Zero factual density. Correctly identified as completely ungrounded.

---

## Limitations

1. **Density ≠ accuracy:** "Dr. Fakename at Imaginary University in 2099" scores high but is entirely fabricated.
2. **NER errors:** spaCy's small model makes mistakes. Common errors:
   - "The Washington Post" sometimes tagged as a person
   - "EU" may not be recognised as an entity
   - Unusual names may be missed entirely
3. **Double-counting:** Dates are counted in both `entity_count` and `date_entities`. Proper nouns within entities are counted in both `entity_count` and `proper_nouns`. This inflates scores for texts with many named entities.
4. **Low weight (0.10):** The system deliberately gives this validator low influence because factual density is the weakest proxy for actual trustworthiness. A well-crafted lie with specific (but false) references would score perfectly.
5. **Genre bias:** Scientific and news texts naturally have high factual density. Literary, philosophical, and conversational texts naturally have low density. The validator penalises certain genres regardless of their actual quality.
