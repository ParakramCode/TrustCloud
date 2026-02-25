# TrustCloud AI — Project Synopsis

## Cloud-Based Epistemic Trust Evaluation with ETL Analytics Pipeline

**Project Title:** TrustCloud AI: A Modular Epistemic Trust Evaluation Engine with Cloud-Native ETL and Analytics Infrastructure  
**Domain:** Data Engineering · Cloud Computing · AI Evaluation Systems  
**Author:** Parakram  
**Date:** February 2026  
**Branch:** `refactor1`  
**Repository:** [github.com/ParakramCode/TrustCloud](https://github.com/ParakramCode/TrustCloud)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Research Motivation](#2-research-motivation)
3. [System Architecture](#3-system-architecture)
4. [Cloud Architecture Justification](#4-cloud-architecture-justification)
5. [End-to-End ETL Pipeline Design](#5-end-to-end-etl-pipeline-design)
6. [Data Engineering Perspective](#6-data-engineering-perspective)
7. [Cost-Constrained Design](#7-cost-constrained-design)
8. [Academic Positioning](#8-academic-positioning)
9. [When Not to Use Cloud](#9-when-not-to-use-cloud)
10. [Technology Stack](#10-technology-stack)
11. [Project Timeline](#11-project-timeline)
12. [References](#12-references)

---

## 1. Project Overview

### 1.1 What TrustCloud AI Is

TrustCloud AI is a modular AI trust evaluation engine that analyses AI-generated text and produces structured, multi-dimensional trust assessments. Rather than assigning a single opaque score, the system decomposes trustworthiness into measurable epistemic dimensions — coherence, contradiction, hallucination risk, reasoning depth, factual density, and semantic consistency — each with uncertainty bounds, and aggregates them using formal epistemic logic.

The system operates as a REST API that accepts AI-generated text and returns:

- **Per-dimension trust scores** with uncertainty intervals
- **Epistemic defeater status** (whether disqualifying problems like self-contradiction are present)
- **System confidence** (how certain the system is about its own assessment, distinct from text correctness)
- **Declared blind spots** (what the system explicitly cannot assess)

The project extends into a cloud-based ETL (Extract, Transform, Load) pipeline that captures evaluation telemetry, transforms it into analytical features, and enables research-grade analytics on AI trust patterns over time.

### 1.2 What TrustCloud AI Is Not

TrustCloud AI is not a commercial product, a startup prototype, or a production SaaS platform. It is a **research system** designed to:

1. Explore formal trust modeling for AI-generated text
2. Demonstrate cloud data engineering patterns at educational scale
3. Produce analytically useful data about AI trust characteristics
4. Serve as a technically defensible academic and portfolio project

The system prioritises correctness and structure over speed of delivery. It optimises for learning value over operational throughput.

---

## 2. Research Motivation

### 2.1 The Trust Problem in AI Systems

Large Language Models (LLMs) produce text that is syntactically fluent, stylistically confident, and frequently wrong. The term "hallucination" has entered common usage to describe LLM outputs that are plausible but fabricated. However, hallucination is only one failure mode. AI-generated text can also be:

- **Internally contradictory** — stating two incompatible claims within the same passage
- **Circular in reasoning** — appearing to explain something while offering no actual causal chain
- **Superficially factual** — including specific-sounding numbers that are entirely fabricated
- **Overconfident** — asserting absolute certainty about inherently uncertain topics

These failure modes are not detectable by reading fluency or grammatical analysis. They require structured, multi-dimensional evaluation — which is what TrustCloud AI provides.

### 2.2 Why Existing Approaches Fall Short

Current AI evaluation frameworks (RAGAS, DeepEval, TruLens) produce scalar scores without:

- **Uncertainty quantification** — A score of 0.72 has no error bar. The same validator on similar inputs might produce 0.65 or 0.80. Without uncertainty, the number is uninterpretable.
- **Defeater logic** — A text can score 0.72 overall while having a contradiction score of 0.95. The weighted average masks a disqualifying problem. In formal epistemology, this is called a "defeater" — evidence so strong it overrides all positive indicators.
- **Epistemic honesty** — No existing framework declares what it *cannot* assess. Every system has blind spots; not declaring them is itself a form of dishonesty.

### 2.3 The Epistemic Trust Model

TrustCloud AI addresses these gaps by grounding its evaluation in **epistemology** — the philosophical study of knowledge and justified belief. The core insight is:

> Trust is not a single number. It is a structured assessment with multiple dimensions, inherent uncertainty, potential defeaters, and known limitations.

The system implements this through:

| Concept | Implementation |
|---------|---------------|
| Multi-dimensional trust | 6 independent validators, each measuring a distinct epistemic property |
| Uncertainty bounds | Every score reports σ (uncertainty) and a 95% credible interval |
| Defeater logic | Contradiction and hallucination_risk are classified as "defeaters" — when they exceed a threshold, they cap the composite score regardless of other dimensions |
| Epistemic honesty | Every response includes a `blind_spots` field listing 6 known limitations |
| Confidence ≠ correctness | System confidence (how sure the system is about its assessment) is computed and reported separately from text trustworthiness |

This model is detailed in the companion document: [Epistemic Trust Model Report](./EPISTEMIC_TRUST_MODEL.md).

---

## 3. System Architecture

### 3.1 Application Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        TRUSTCLOUD AI                                 │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    API LAYER (FastAPI, v1)                     │  │
│  │  POST /v1/evaluate    → epistemic trust evaluation            │  │
│  │  GET  /v1/validators  → list registered validators            │  │
│  │  GET  /v1/health      → system status                         │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────▼─────────────────────────────────────┐  │
│  │                    TRUST ENGINE                                │  │
│  │                                                                │  │
│  │  ValidatorRegistry ──► TrustOrchestrator ──► EpistemicAggregator│  │
│  │  (plugin discovery)    (concurrent exec)    (defeater gating)  │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────▼─────────────────────────────────────┐  │
│  │                    VALIDATORS (Plugins)                        │  │
│  │                                                                │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐   │  │
│  │  │  Coherence   │ │Contradiction │ │ Hallucination Risk    │   │  │
│  │  │  (embedding) │ │ (DEFEATER)   │ │ (DEFEATER)            │   │  │
│  │  └─────────────┘ └──────────────┘ └───────────────────────┘   │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐   │  │
│  │  │  Reasoning   │ │  Factual     │ │ Semantic Consistency  │   │  │
│  │  │  Depth       │ │  Density     │ │ (shared model)        │   │  │
│  │  └─────────────┘ └──────────────┘ └───────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    STORAGE (Async, Background)                 │  │
│  │  LocalStorageBackend (dev) │ S3StorageBackend (cloud)          │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI** over Flask/Django | Native async support, automatic OpenAPI documentation, Pydantic integration for request validation |
| **Plugin architecture** for validators | Adding a new trust dimension requires zero changes to engine, orchestrator, or aggregator |
| **ThreadPoolExecutor** for concurrency | Validators use CPU-bound ML libraries (sentence-transformers, spaCy) that hold the GIL. Threads provide adequate parallelism without process overhead |
| **Async storage via BackgroundTasks** | API response latency must not include storage I/O. Telemetry writes happen after the response is sent |
| **Uncertainty in every measurement** | Without uncertainty, scores are epistemically incomplete. This is a core research contribution, not an afterthought |
| **Shared sentence-transformers model** | CoherenceValidator and SemanticConsistencyValidator share one model instance (~400MB memory saved) |

---

## 4. Cloud Architecture Justification

### 4.1 Why Cloud Is Used

The decision to deploy on cloud infrastructure is driven by four factors:

**1. Educational value.** Cloud computing is a core competency in data engineering. Designing, deploying, and operating a system on AWS or GCP develops skills in IAM, networking, container orchestration, managed services, cost management, and infrastructure-as-code. These skills are directly applicable to industry roles.

**2. Research infrastructure.** Research systems that produce data over time require persistent, accessible storage. Cloud object storage (S3/GCS) provides durable, versioned, time-partitioned data that can be queried without running dedicated database servers. This is fundamentally more suitable than local JSON files for longitudinal analysis.

**3. Real-world architectural patterns.** The ETL pipeline pattern (ingest → store → transform → query → visualise) is the backbone of data engineering. Implementing it on cloud services demonstrates understanding of production-grade data systems. This is more compelling in an academic or portfolio context than a purely local implementation.

**4. Scalability narrative.** While the current system processes single evaluations, the architecture is designed to handle batch processing, scheduled ingestion, and analytical workloads. Cloud services allow the system to scale these capabilities without architectural changes.

### 4.2 When Cloud Is Not Necessary

Cloud is not always the right choice. For this project specifically:

- **API serving** does not require cloud. A Docker container running locally or on a single VM is sufficient for the API workload. There is no high-availability requirement.
- **Validator execution** is CPU-bound. Cloud doesn't make validators run faster — it just moves the computation to a remote data centre.
- **Small data volumes.** At student-research scale, the total data volume will be measured in megabytes, not terabytes. A local SQLite database could handle the same analytical workload.

The cloud components are justified **for the ETL pipeline and analytics layer**, not for the API itself. The API can run anywhere; the data pipeline benefits from cloud-managed services.

### 4.3 Provider Selection: AWS

AWS is selected for the following reasons:

| Factor | AWS | GCP | Azure |
|--------|-----|-----|-------|
| Free tier generosity | 12-month free tier + always-free services | $300 credit (90 days) | $200 credit (30 days) |
| S3 (object storage) | 5GB free for 12 months | 5GB free | 5GB free |
| Serverless query | Athena ($5/TB scanned) | BigQuery (1TB/month free) | — |
| ETL service | Glue (free tier available) | Dataflow (no free tier) | Data Factory (no free tier) |
| Academic programs | AWS Educate, credits | GCP for Education | Azure for Students ($100) |
| Industry prevalence | Dominant in data engineering roles | Growing in analytics | Growing in enterprise |

**Decision:** AWS is used because (a) the free tier is longest-lived, (b) S3 + Athena + Glue is the standard academic ETL stack, and (c) AWS experience has the highest transferability to data engineering roles.

**Note on GCP:** BigQuery's 1TB/month free query tier is more generous than Athena for analytical workloads. If query volume exceeds expectations, migrating the analytics layer to BigQuery is straightforward and documented as a contingency.

---

## 5. End-to-End ETL Pipeline Design

### 5.1 Pipeline Overview

```
┌────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  EXTRACT   │───►│   RAW STORE  │───►│  TRANSFORM   │───►│  PROCESSED  │───►│  ANALYTICS   │
│            │    │              │    │              │    │   STORE     │    │              │
│ API ingest │    │ S3 (JSON)    │    │ AWS Glue     │    │ S3 (Parquet)│    │ Athena + QS  │
│ Batch seed │    │ date-partitioned│ │ PySpark      │    │ partitioned │    │ or Streamlit │
└────────────┘    └──────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

### 5.2 Ingestion Layer

#### 5.2.1 Real-Time API Ingestion

Every call to `POST /v1/evaluate` produces a telemetry record that is written to storage asynchronously. The record schema:

```json
{
  "id": "uuid-v4",
  "timestamp": "2026-02-25T10:30:00Z",
  "input": {
    "text": "...",
    "text_length": 142,
    "metadata": { "provider": "openai", "model": "gpt-4.1" }
  },
  "assessment": {
    "engine_version": "trust-engine-v1",
    "composite_trust": 0.346,
    "confidence": 0.862,
    "trust_level": "LOW",
    "defeated": false
  },
  "dimensions": [
    {
      "name": "coherence",
      "signal_type": "positive_indicator",
      "score": 0.421,
      "uncertainty": 0.080,
      "interval": [0.264, 0.578],
      "latency_ms": 45.2,
      "error": null
    }
  ],
  "defeaters": [
    { "name": "contradiction", "severity": 0.0, "active": false }
  ]
}
```

**Storage path (time-partitioned data lake layout):**
```
s3://trustcloud-data/raw/evaluations/2026/02/25/{uuid}.json
```

#### 5.2.2 Batch Seed Ingestion

For initial development and testing, a batch seed script generates evaluation records from curated text samples:

```
seed_data/
├── high_trust_texts.json     # Well-reasoned, factual texts
├── contradictory_texts.json  # Self-contradictory samples
├── hallucinated_texts.json   # Fabricated facts
├── circular_reasoning.json   # Tautological arguments
└── mixed_quality.json        # Realistic mix
```

The seed script runs each sample through the evaluation API and stores results in S3. This provides a baseline dataset for analytics before real usage data accumulates.

#### 5.2.3 Streaming Ingestion (Conceptual)

For production scale (not implemented at student level, but architecturally documented):

```
API → Amazon Kinesis Data Firehose → S3 (auto-batched, compressed)
```

Kinesis Firehose would buffer evaluation records and write them to S3 in micro-batches (every 60 seconds or 1MB, whichever comes first). This eliminates the need for the API to write directly to S3 and provides automatic compression and retry logic.

**Why not implemented:** Kinesis Firehose costs ~$0.035/GB ingested. At student scale (<1MB/month), the cost is negligible but the operational complexity is not justified. The current `BackgroundTasks` approach achieves the same outcome with zero additional infrastructure.

### 5.3 Storage Layer

#### 5.3.1 Raw Data Lake (S3)

```
s3://trustcloud-data/
├── raw/
│   └── evaluations/
│       └── YYYY/MM/DD/
│           └── {uuid}.json               ← raw API telemetry
├── processed/
│   └── trust_scores/
│       └── year=YYYY/month=MM/day=DD/
│           └── part-00000.snappy.parquet  ← transformed features
└── reference/
    └── seed_data/
        └── text_samples.json              ← seed corpus
```

**Design rationale:**

| Property | Decision | Why |
|----------|----------|-----|
| Format (raw) | JSON | Human-readable, schema-flexible, natively produced by FastAPI |
| Format (processed) | Parquet (Snappy compression) | Columnar format, 10-100× smaller than JSON, native to Athena/Spark |
| Partitioning | Time-based (year/month/day) | Athena uses partition pruning to scan only relevant data, reducing query cost |
| Naming | Hive-style (`year=2026/month=02`) | Required by Athena and Glue for automatic partition discovery |

#### 5.3.2 Structured Analytical Storage

**Primary:** Amazon Athena (serverless SQL over S3 Parquet).

Athena charges $5 per terabyte scanned. With Parquet compression and time partitioning, a typical analytical query scans <10MB → cost per query: **$0.00005** (effectively free).

**Why not Redshift:**

| Factor | Athena | Redshift |
|--------|--------|----------|
| Cost model | Per-query ($5/TB) | Per-hour ($0.25/hr min) |
| Monthly cost at student scale | <$0.01 | ~$180 (always-on) |
| Setup time | 5 minutes | 30+ minutes |
| Maintenance | None (serverless) | Cluster management |
| Appropriate for | <100GB, intermittent queries | >100GB, frequent concurrent queries |

Redshift is a production data warehouse. It is technically superior for high-concurrency analytical workloads, but **entirely inappropriate for a student research project**. Using it would demonstrate poor architectural judgment, not sophistication.

### 5.4 Transformation Layer

#### 5.4.1 AWS Glue ETL Job

AWS Glue runs a PySpark script that:

1. Reads raw JSON records from S3
2. Flattens the nested JSON structure into tabular rows
3. Extracts validator scores, uncertainties, and defeater statuses as individual columns
4. Computes derived metrics (score variance across dimensions, confidence-adjusted trust)
5. Writes the output as Parquet to the processed prefix

**Glue job configuration:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Worker type | G.1X (4 vCPU, 16GB) | Minimum viable. Data volume is tiny |
| Number of workers | 2 | Minimum |
| Schedule | Weekly | Data accumulates slowly at research scale |
| Timeout | 10 minutes | Fail fast if something is wrong |
| Job bookmarks | Enabled | Only process new data since last run |

**Estimated cost:** AWS Glue charges $0.44/DPU-hour. A weekly 2-DPU job running 5 minutes costs:

```
2 DPU × (5/60) hours × $0.44/DPU-hour × 4 runs/month = $0.29/month
```

#### 5.4.2 Transformation Schema

The Glue job transforms nested JSON into a flat analytical schema:

**Output table: `trust_scores`**

| Column | Type | Source |
|--------|------|--------|
| `evaluation_id` | STRING | `id` |
| `timestamp` | TIMESTAMP | `timestamp` |
| `text_length` | INT | `input.text_length` |
| `llm_provider` | STRING | `input.metadata.provider` |
| `llm_model` | STRING | `input.metadata.model` |
| `composite_trust` | FLOAT | `assessment.composite_trust` |
| `confidence` | FLOAT | `assessment.confidence` |
| `trust_level` | STRING | `assessment.trust_level` |
| `defeated` | BOOLEAN | `assessment.defeated` |
| `coherence_score` | FLOAT | `dimensions[name=coherence].score` |
| `coherence_uncertainty` | FLOAT | `dimensions[name=coherence].uncertainty` |
| `contradiction_score` | FLOAT | `dimensions[name=contradiction].score` |
| `contradiction_severity` | FLOAT | `defeaters[name=contradiction].severity` |
| `contradiction_active` | BOOLEAN | `defeaters[name=contradiction].active` |
| `hallucination_score` | FLOAT | `dimensions[name=hallucination_risk].score` |
| `hallucination_active` | BOOLEAN | `defeaters[name=hallucination_risk].active` |
| `reasoning_depth_score` | FLOAT | `dimensions[name=reasoning_depth].score` |
| `factual_density_score` | FLOAT | `dimensions[name=factual_density].score` |
| `semantic_consistency_score` | FLOAT | `dimensions[name=semantic_consistency].score` |
| `validators_run` | INT | count of dimensions |
| `validators_failed` | INT | count of dimensions with error |
| `total_latency_ms` | FLOAT | sum of dimension latencies |
| `year` | INT | partition key |
| `month` | INT | partition key |
| `day` | INT | partition key |

#### 5.4.3 Metadata and Lineage

Each Glue job run records:

- **Input path:** S3 prefix scanned
- **Records processed:** count of raw records transformed
- **Records skipped:** count of malformed records
- **Output path:** S3 prefix written
- **Job bookmark:** last processed record timestamp
- **Schema version:** transformation schema version

This is stored as a sidecar JSON file in `s3://trustcloud-data/metadata/glue_runs/`.

### 5.5 Analytics Layer

#### 5.5.1 Athena Query Layer

Athena SQL queries over the processed Parquet data:

**Query 1: Trust distribution by LLM provider**
```sql
SELECT
    llm_provider,
    llm_model,
    COUNT(*) AS evaluations,
    ROUND(AVG(composite_trust), 3) AS avg_trust,
    ROUND(AVG(confidence), 3) AS avg_confidence,
    SUM(CASE WHEN defeated THEN 1 ELSE 0 END) AS defeated_count,
    ROUND(AVG(coherence_score), 3) AS avg_coherence,
    ROUND(AVG(contradiction_score), 3) AS avg_contradiction
FROM trust_scores
GROUP BY llm_provider, llm_model
ORDER BY avg_trust DESC;
```

**Query 2: Defeater activation rate over time**
```sql
SELECT
    year, month, day,
    COUNT(*) AS total,
    SUM(CASE WHEN contradiction_active THEN 1 ELSE 0 END) AS contradiction_defeats,
    SUM(CASE WHEN hallucination_active THEN 1 ELSE 0 END) AS hallucination_defeats,
    ROUND(
        CAST(SUM(CASE WHEN defeated THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*), 3
    ) AS defeat_rate
FROM trust_scores
GROUP BY year, month, day
ORDER BY year, month, day;
```

**Query 3: Uncertainty analysis by method type**
```sql
SELECT
    'embedding_similarity' AS method,
    ROUND(AVG(coherence_uncertainty), 3) AS avg_uncertainty,
    ROUND(STDDEV(coherence_score), 3) AS score_stddev
FROM trust_scores
UNION ALL
SELECT
    'keyword_heuristic',
    ROUND(AVG(reasoning_depth_score), 3),  -- uncertainty not stored separately here
    ROUND(STDDEV(reasoning_depth_score), 3)
FROM trust_scores;
```

#### 5.5.2 Dashboard Design

**Option A: Amazon QuickSight** (14-day free trial, then $9/month for one author)

Suitable for: college submission, demo screenshots, one-time analysis.

**Option B: Streamlit** (free, self-hosted, Python-native)

Suitable for: ongoing research, interactive exploration, portfolio demos.

**Recommended dashboard panels:**

| Panel | Chart Type | Shows |
|-------|-----------|-------|
| Trust Distribution | Histogram | Distribution of composite_trust scores |
| Dimension Radar | Radar chart | Per-dimension scores for a single evaluation |
| Defeater Timeline | Line chart | Contradiction and hallucination severity over time |
| Confidence vs Trust | Scatter plot | System confidence plotted against composite trust |
| Uncertainty Overview | Box plot | Uncertainty ranges per validator type |
| Trust by LLM Model | Bar chart | Average trust broken down by source model |

---

## 6. Data Engineering Perspective

### 6.1 Framing the System

TrustCloud AI can be accurately described as four types of system simultaneously:

#### As an ETL System

```
Extract:   API receives text → generates evaluation → produces JSON telemetry
Transform: Glue flattens JSON → extracts features → converts to Parquet
Load:      Processed data lands in S3 → queryable via Athena
```

This is a textbook ETL pipeline with a domain-specific Extract step (the evaluation is the extraction of trust signals from raw text).

#### As a Feature Engineering Pipeline

Each validator extracts a **feature** from the input text:

| Validator | Feature | Method |
|-----------|---------|--------|
| Coherence | `coherence_score` | Sentence embedding cosine similarity |
| Contradiction | `contradiction_score` | Keyword + sentiment analysis |
| Hallucination Risk | `hallucination_score` | Uncertainty/vagueness/absolutism markers |
| Reasoning Depth | `reasoning_depth_score` | Causal chain detection |
| Factual Density | `factual_density_score` | Named entity + numeric reference density |
| Semantic Consistency | `semantic_consistency_score` | Pairwise embedding similarity |

The trust engine is, in data engineering terms, a **feature extraction pipeline** that converts unstructured text into structured, typed, numerical features suitable for analysis.

#### As AI Evaluation Infrastructure

The system evaluates AI outputs against multiple quality dimensions. This positions it within the growing field of **AI evaluation** (sometimes called "LLM evals"), alongside tools like:

| Tool | Approach | TrustCloud AI Difference |
|------|----------|--------------------------|
| RAGAS | RAG-specific, scalar scores | Domain-general, epistemic model |
| DeepEval | LLM-as-judge | No LLM dependency for evaluation |
| TruLens | Feedback functions | Plugin architecture, uncertainty |
| Anthropic Evals | Benchmark suites | Real-time API, multi-dimensional |

TrustCloud AI is unique in applying formal epistemology to AI evaluation.

#### As a Research Analytics Platform

The ETL pipeline feeds an analytics layer that enables research questions:

- *Does coherence correlate with factual density across LLM providers?*
- *What is the false-positive rate of the contradiction defeater?*
- *How does uncertainty vary with text length?*
- *Do hallucination risk patterns differ between GPT-4 and Claude outputs?*

These are genuine research questions that the system's data infrastructure is designed to answer.

---

## 7. Cost-Constrained Design

### 7.1 Assumptions

- **Budget:** $0 personal money. Only free credits (AWS Educate, promotional credits, free tier).
- **Duration:** 3-6 months of active development.
- **Scale:** ~100-1,000 evaluations total. <1GB of data.
- **Team:** Single developer.

### 7.2 Monthly Cost Estimate

| Service | Usage | Cost |
|---------|-------|------|
| **S3** | <1GB storage + <1,000 PUT requests | $0.02 |
| **Athena** | <100MB scanned per month | $0.0005 |
| **Glue** | 2 DPU × 5 min × 4 runs/month | $0.29 |
| **CloudWatch** | Basic logging | Free tier |
| **ECR** (container registry) | 1 image, <500MB | Free tier (500MB) |
| **EC2** (optional, API hosting) | t2.micro, 750 hrs/month | Free tier (12 months) |
| | **Total** | **~$0.31/month** |

### 7.3 Cost Safety Measures

1. **AWS Budget Alert:** Set at $5/month. Email notification at 80% threshold.
2. **No always-on services:** Glue jobs run on schedule, not continuously.
3. **Athena partition pruning:** Time partitions ensure queries scan minimal data.
4. **Parquet compression:** 10-100× smaller than JSON, directly reduces Athena costs.
5. **No Redshift, EMR, SageMaker, or Kinesis:** These are expensive services with no free tier suitable for student use.

### 7.4 Budget-Aware Alternatives

| If budget runs out | Alternative |
|--------------------|-------------|
| S3 | Local filesystem (`data/evaluations/`) — already implemented |
| Athena | DuckDB (free, local, reads Parquet natively) |
| Glue | Python script with pandas (no cloud dependency) |
| QuickSight | Streamlit (free, Python-native) |
| EC2 | Local Docker (`docker run -p 8000:8000 ...`) |

Every cloud component has a local fallback. The system is designed to degrade gracefully, not fail catastrophically, when cloud resources are unavailable.

---

## 8. Academic Positioning

### 8.1 Research Contributions

TrustCloud AI makes the following contributions:

1. **Epistemic trust model for AI evaluation.** Decomposing trust into formal epistemic dimensions with uncertainty bounds and defeater logic. This is a novel framing not present in existing evaluation frameworks.

2. **Plugin-based validator architecture.** A modular system where adding a new trust dimension requires exactly two changes (new class + registry entry), with zero modifications to engine, orchestrator, or aggregator.

3. **Cloud-native ETL for AI research data.** Demonstrating how evaluation telemetry can be ingested, transformed, and analysed using standard cloud data engineering patterns.

4. **Uncertainty-weighted aggregation.** An aggregation strategy where dimensions with higher measurement uncertainty contribute proportionally less to the composite score.

### 8.2 Portfolio Value

This project demonstrates competency in:

| Skill Area | Evidence |
|------------|----------|
| **Python engineering** | Plugin architecture, ABC patterns, Pydantic models, dependency injection |
| **API design** | Versioned REST API, input validation, structured error handling, async operations |
| **Cloud computing** | AWS S3, Athena, Glue, IAM, cost management |
| **Data engineering** | ETL pipeline, Parquet conversion, schema design, partitioning strategy |
| **Machine learning** | Sentence embeddings, NLP feature extraction, spaCy pipelines |
| **Software architecture** | Modular design, separation of concerns, plugin registry, strategy pattern |
| **Docker/DevOps** | Containerisation, layer caching, volume mounts, CI/CD readiness |
| **Research methodology** | Formal epistemic model, uncertainty quantification, declared limitations |

### 8.3 Research Paper Potential

The epistemic trust model could be submitted to:

- **AAAI** (Association for the Advancement of Artificial Intelligence)
- **FAccT** (ACM Conference on Fairness, Accountability, and Transparency)
- **AIES** (AAAI/ACM Conference on AI, Ethics, and Society)
- **NeurIPS Workshops** (Socially Responsible ML, TrustML)
- **ArXiv preprint** (cs.AI, cs.CL)

The core argument — that scalar trust scores are epistemically flawed and that a multi-dimensional model with uncertainty bounds and defeater logic is more rigorous — is a defensible academic contribution.

---

## 9. When Not to Use Cloud

### 9.1 Honest Assessment

Cloud infrastructure adds value to this project in specific areas and adds unnecessary complexity in others. This section provides an honest evaluation.

#### Where Cloud Adds Value

| Capability | Why Cloud Helps |
|------------|-----------------|
| Persistent data storage | S3 provides durable, versioned object storage accessible from anywhere |
| Analytical queries | Athena provides SQL over Parquet without running a database server |
| ETL orchestration | Glue provides managed Spark execution without cluster management |
| Portfolio signal | "I built on AWS" carries weight in data engineering interviews |

#### Where Cloud Adds Unnecessary Complexity

| Capability | Why Local Is Better |
|------------|---------------------|
| API serving | `docker run` on localhost is simpler than EC2 + security groups + IAM |
| Validator execution | CPU-bound computation doesn't benefit from cloud — same speed locally |
| Development iteration | Local file writes are instant; S3 puts add latency and require credentials |
| Debugging | Local stack traces are immediate; cloud logs require CloudWatch navigation |

#### Where Cloud Is Actively Harmful

| Scenario | Risk |
|----------|------|
| No budget remaining | Cloud services fail silently or charge overages |
| Credential misconfiguration | S3 public bucket = data leak |
| Over-engineering | Using Kinesis + Lambda + Step Functions for 100 evaluations is absurd |
| Résumé-driven architecture | Adding services for portfolio keywords rather than technical need |

### 9.2 The Right Balance

TrustCloud AI uses cloud for what cloud is good at (storage, ETL, analytics) and avoids cloud where it adds no value (API serving during development, validator execution). The local storage backend is the default; S3 is an opt-in configuration via environment variable.

```
# Development (default — no cloud needed)
TRUSTCLOUD_STORAGE_BACKEND=local

# Cloud deployment
TRUSTCLOUD_STORAGE_BACKEND=s3
TRUSTCLOUD_S3_BUCKET=trustcloud-data
```

This is honest architecture. A system that uses cloud for everything, regardless of whether it helps, is not well-engineered — it is over-engineered.

---

## 10. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11 | Core implementation |
| **API Framework** | FastAPI | REST API with async support |
| **ML/NLP** | sentence-transformers, spaCy, TextBlob, scikit-learn | Validator implementations |
| **Data Models** | Pydantic v2 | Request/response validation |
| **Containerisation** | Docker | Reproducible deployment |
| **Cloud Storage** | AWS S3 | Raw + processed data lake |
| **Cloud ETL** | AWS Glue (PySpark) | JSON → Parquet transformation |
| **Cloud Query** | AWS Athena | Serverless SQL analytics |
| **Cloud Visualisation** | QuickSight or Streamlit | Trust analytics dashboards |
| **Version Control** | Git + GitHub | Source control |

---

## 11. Project Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| **Phase 1: Core Engine** | Weeks 1-3 | Validators, engine, API, Docker (✅ Complete) |
| **Phase 2: Epistemic Model** | Week 4 | Uncertainty, defeaters, confidence, blind spots (✅ Complete) |
| **Phase 3: Cloud Storage** | Week 5 | S3 backend, time-partitioned writes |
| **Phase 4: ETL Pipeline** | Weeks 6-7 | Glue crawler + ETL job, Parquet output |
| **Phase 5: Analytics** | Week 8 | Athena tables, SQL queries, dashboard |
| **Phase 6: Seed Data + Evaluation** | Week 9 | Batch evaluation, test corpus, results analysis |
| **Phase 7: Documentation** | Week 10 | Final report, architecture diagrams, research writeup |

---

## 12. References

1. Goldman, A. I. (1986). *Epistemics: The Regulative Theory of Cognition*. Harvard University Press.
2. Pollock, J. L. (1986). *Contemporary Theories of Knowledge*. Rowman & Littlefield.
3. Sosa, E. (2007). *A Virtue Epistemology: Apt Belief and Reflective Knowledge*. Oxford University Press.
4. Ji, Z., et al. (2023). *Survey of Hallucination in Natural Language Generation*. ACM Computing Surveys.
5. Es, S., et al. (2023). *RAGAS: Automated Evaluation of Retrieval Augmented Generation*. arXiv:2309.15217.
6. Kadavath, S., et al. (2022). *Language Models (Mostly) Know What They Know*. arXiv:2207.05221.
7. AWS Well-Architected Framework. (2024). *Cost Optimization Pillar*. Amazon Web Services.
8. Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
9. Reis, J., & Housley, M. (2022). *Fundamentals of Data Engineering*. O'Reilly Media.
10. Lin, S., Hilton, J., & Evans, O. (2022). *Teaching Models to Express Their Uncertainty in Words*. TMLR.

---

*This synopsis is part of the TrustCloud AI project documentation.*  
*System version: trust-engine-v1 | Epistemic Trust Model v1 | ETL Pipeline Design v1*
