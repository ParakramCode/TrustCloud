# TrustCloud AI — Project Summary

**Project:** TrustCloud AI: Epistemic Trust Evaluation Engine with Cloud ETL Pipeline  
**Author:** Parakram  
**Repository:** [github.com/ParakramCode/TrustCloud](https://github.com/ParakramCode/TrustCloud)  
**Date:** February 2026

---

## What This Project Does

TrustCloud AI evaluates AI-generated text for trustworthiness. It takes a passage of text produced by a Large Language Model and returns a structured, multi-dimensional trust assessment — not a single score, but a profile of how trustworthy the text is across six dimensions, each with uncertainty bounds and a clear explanation of what was measured and what was not.

The system is built as a modular Python API, containerised with Docker, and designed to feed into a cloud-based ETL pipeline for research analytics.

---

## Why It Exists

Large Language Models produce text that reads well but may contain fabricated facts, circular reasoning, internal contradictions, or false confidence. Existing evaluation tools assign a single number (e.g., "trust = 0.72") with no indication of what that number means, how uncertain it is, or what was not measured. TrustCloud AI addresses this by grounding trust evaluation in **epistemology** — the study of knowledge and justified belief — producing assessments that are transparent, decomposable, and honest about their own limitations.

---

## Project Structure

```
TrustCloud AI/
├── main.py                      ← FastAPI application entry point
├── api/
│   ├── dependencies.py          ← Dependency injection (engine, storage, config singletons)
│   └── v1/routes.py             ← Versioned API routes (/v1/evaluate, /v1/validators, /v1/health)
├── trust_engine/
│   ├── engine.py                ← Top-level facade: wires registry + orchestrator + aggregator
│   ├── registry.py              ← Plugin registry with auto-discovery and name aliases
│   ├── orchestrator.py          ← Concurrent validator execution with per-validator timeouts
│   └── aggregator.py            ← Epistemic aggregation: uncertainty-weighted averaging + defeater gating
├── validators/
│   ├── base.py                  ← Abstract base class: defines signal_type, method_type, uncertainty
│   ├── coherence.py             ← Sentence embedding similarity (positive indicator)
│   ├── contradiction.py         ← Marker + sentiment analysis (DEFEATER)
│   ├── hallucination.py         ← Vagueness/absolutism heuristics (DEFEATER)
│   ├── reasoning.py             ← Causal chain detection (positive indicator)
│   ├── factuality.py            ← Named entity + numeric reference density (positive indicator)
│   └── semantic.py              ← Pairwise semantic similarity (positive indicator)
├── schemas/
│   ├── request.py               ← Input validation (Pydantic)
│   ├── response.py              ← Epistemic trust response: dimensions, defeaters, confidence, blind spots
│   └── config.py                ← Typed configuration from environment variables
├── storage/
│   └── backend.py               ← Pluggable storage: local filesystem or S3
├── docs/
│   ├── PROJECT_SYNOPSIS.md      ← Full project synopsis with cloud architecture and ETL design
│   └── EPISTEMIC_TRUST_MODEL.md ← Formal report on the epistemic trust model
├── Dockerfile                   ← Production container image
└── requirements.txt             ← Python dependencies
```

---

## How It Works

```
Text In ──► 6 Validators (concurrent) ──► Epistemic Aggregator ──► Trust Response Out
```

1. **Input**: AI-generated text is sent to `POST /v1/evaluate`.
2. **Validation**: Six validators run concurrently, each measuring a different property of the text. Each returns a score, an uncertainty bound, and an explanation.
3. **Aggregation**: Scores are classified as *positive indicators* (coherence, reasoning, factuality, semantic consistency) or *defeaters* (contradiction, hallucination risk). Positive indicators are combined using uncertainty-weighted averaging. If any defeater exceeds its threshold, the composite trust is capped.
4. **Response**: The API returns the composite trust score, system confidence, per-dimension details with credible intervals, defeater statuses, and a list of declared blind spots.
5. **Storage**: Evaluation telemetry is written asynchronously to local storage or S3 for later analysis.

---

## Key Concepts

| Concept | Meaning |
|---------|---------|
| **Epistemic trust** | A rational agent's justified degree of belief that information is reliable enough to warrant updating their own beliefs |
| **Positive indicator** | A dimension where a higher score means more trust (coherence, reasoning, factuality, semantic consistency) |
| **Defeater** | A dimension where a high score *disqualifies* trust regardless of other dimensions (contradiction, hallucination risk) |
| **Uncertainty** | Every score has a ±σ bound reflecting how much the measurement could vary |
| **Confidence** | How certain the *system* is about its *assessment* — independent from whether the text is actually correct |
| **Blind spots** | What the system *cannot* assess, declared explicitly in every response |

---

## Cloud ETL Pipeline (Planned)

The evaluation data feeds into an AWS-based analytics pipeline:

```
API Telemetry ──► S3 (raw JSON) ──► AWS Glue (transform) ──► S3 (Parquet) ──► Athena (SQL) ──► Dashboard
```

- **Storage**: S3 with time-partitioned data lake layout
- **Transformation**: AWS Glue flattens nested JSON into columnar Parquet
- **Analytics**: Athena provides serverless SQL queries over processed data
- **Cost**: Estimated $0.31/month at student scale, with local fallbacks for every cloud service

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| API | FastAPI + Uvicorn |
| ML/NLP | sentence-transformers, spaCy, TextBlob, scikit-learn |
| Validation | Pydantic v2 |
| Container | Docker |
| Cloud Storage | AWS S3 |
| Cloud ETL | AWS Glue (PySpark) |
| Cloud Query | AWS Athena |
| Version Control | Git + GitHub |

---

## What Makes This Different

1. **Not a product** — a research system with formal epistemological grounding.
2. **Not a single score** — a structured profile with uncertainty, defeaters, and blind spots.
3. **Not a black box** — every score comes with an explanation and evidence items.
4. **Not over-engineered** — cloud is used where it adds value, local fallbacks exist for everything.
5. **Not heuristics-only** — the trust model has formal semantics grounded in epistemic philosophy.
