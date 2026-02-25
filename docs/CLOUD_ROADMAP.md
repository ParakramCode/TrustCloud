# TrustCloud AI — Cloud Deployment Roadmap

## Strategic Guidance for a Student Research Project

**Written for:** A college student with no AWS experience, limited credits, and a working local system.  
**Tone:** Honest engineering mentorship. No hype.  
**Date:** February 2026

---

## Part 1 — The Honest Answer

### Should This Project Go to Cloud Now?

**No. Not yet.**

Here is why.

Your system works locally. It runs in Docker. You can hit the API, get epistemic trust evaluations, and the results are correct. The research value of TrustCloud AI is in **the epistemic model, the validator architecture, and the formal trust framework** — none of which require cloud infrastructure. Cloud does not make your validators smarter, your aggregation more principled, or your research more rigorous.

Going to cloud right now would mean spending 2-3 weeks learning IAM, S3 policies, Glue crawlers, and Athena table definitions — while your actual research work (the epistemic model, evaluation framework, seed datasets) remains unfinished.

### When Cloud Becomes the Right Move

Cloud becomes justified when you have a specific, concrete reason:

| Trigger | When to Act | Why |
|---------|-------------|-----|
| You have >50 evaluation records and want to query patterns | After seed data exists | Athena is genuinely useful for SQL over structured data |
| You want the project running 24/7 for demos or submissions | Before final submission | A live URL is more impressive than "run this Docker command" |
| You want to learn AWS specifically as a career skill | Any time, but separate from research | Treat it as a learning exercise, not a project requirement |
| Your college submission requires cloud architecture | When you know the rubric | Do the minimum that satisfies the requirement |

### The Decision Framework

Ask yourself three questions:

1. **Do I have data to analyse?** If you haven't generated 50+ evaluation records yet, there is nothing for an ETL pipeline to process. Build the seed dataset first, locally.

2. **Does my submission require a live deployment?** If yes, deploy the API to a single EC2 instance or Railway/Render (free tier). This takes 30 minutes, not 3 weeks.

3. **Am I learning cloud for the project, or learning the project for cloud?** If cloud is the learning goal, build a tiny separate project first (a Lambda + S3 + Athena exercise with dummy data). Don't use your research project as your first cloud experiment.

### What I Recommend Right Now

**Phase A (now, 1-2 weeks):** Stay local. Build the seed dataset. Run 100+ evaluations through the API with diverse text samples. Store results locally. Write the evaluation analysis.

**Phase B (after seed data exists, 1 week):** Upload local evaluation data to S3. Set up Athena to query it. This takes 2-3 hours, not weeks.

**Phase C (before submission, 1 week):** Deploy the API to a free-tier service. Point your report to the live URL. Screenshot the dashboard.

This ordering means you do the **research** first and the **infrastructure** second. The reverse is a common student trap: building a beautiful pipeline with nothing flowing through it.

---

## Part 2 — The Local-First Path (Do This First)

Before any cloud work, build the foundation locally. This is more valuable than any AWS service.

### Step 1: Build a Seed Dataset

Create a curated corpus of AI-generated texts with known properties:

```
seed_data/
├── high_trust/           ← Well-reasoned, factual, coherent texts
│   ├── science_facts.json
│   ├── historical_events.json
│   └── technical_explanations.json
├── contradictory/        ← Texts that contain self-contradictions
│   ├── conflicting_claims.json
│   └── negation_conflicts.json
├── hallucinated/         ← Texts with fabricated facts
│   ├── fake_statistics.json
│   └── invented_entities.json
├── circular/             ← Tautological reasoning
│   ├── self_referential.json
│   └── fake_causality.json
└── mixed/                ← Realistic mix of quality levels
    ├── gpt4_outputs.json
    └── claude_outputs.json
```

Each file contains 10-20 text samples. Total: ~100-200 samples. This is your evaluation corpus.

### Step 2: Run Batch Evaluation Locally

Write a script that feeds every sample through the API and saves results:

```python
# evaluate_corpus.py
import json, requests, pathlib, time

API = "http://localhost:8000/v1/evaluate"
SEED_DIR = pathlib.Path("seed_data")
OUTPUT_DIR = pathlib.Path("data/evaluations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for category_dir in SEED_DIR.iterdir():
    if not category_dir.is_dir():
        continue
    for file in category_dir.glob("*.json"):
        samples = json.loads(file.read_text())
        for i, sample in enumerate(samples):
            text = sample["text"] if isinstance(sample, dict) else sample
            resp = requests.post(API, json={
                "text": text,
                "metadata": {
                    "category": category_dir.name,
                    "source_file": file.name,
                    "sample_index": i,
                }
            })
            result = resp.json()
            out_file = OUTPUT_DIR / f"{category_dir.name}_{file.stem}_{i}.json"
            out_file.write_text(json.dumps(result, indent=2))
            time.sleep(0.5)  # Don't overwhelm the API
            print(f"  {out_file.name}: trust={result['assessment']['composite_trust']}")
```

Now you have 100+ structured evaluation records in `data/evaluations/`. **This is your raw data lake — locally.**

### Step 3: Local Analytics with DuckDB

DuckDB is a free, embedded analytical database that reads JSON and Parquet natively. No cloud needed.

```python
# analyze.py
import duckdb

con = duckdb.connect()

# Read all evaluation JSONs
con.execute("""
    CREATE TABLE evaluations AS
    SELECT
        assessment.composite_trust,
        assessment.confidence,
        assessment.trust_level,
        assessment.defeated,
        input.metadata.category AS category,
        input.text_length
    FROM read_json_auto('data/evaluations/*.json')
""")

# Query 1: Trust by category
print(con.execute("""
    SELECT category, COUNT(*) as n,
           ROUND(AVG(composite_trust), 3) as avg_trust,
           ROUND(AVG(confidence), 3) as avg_confidence,
           SUM(CASE WHEN defeated THEN 1 ELSE 0 END) as defeated_count
    FROM evaluations
    GROUP BY category
    ORDER BY avg_trust DESC
""").fetchdf().to_string())
```

DuckDB gives you the same analytical power as Athena, for free, with no AWS account. The transition to Athena later is trivial — the SQL is nearly identical.

### Step 4: Local Dashboard with Streamlit

```python
# dashboard.py
import streamlit as st
import duckdb
import plotly.express as px

st.title("TrustCloud AI — Trust Analytics")

con = duckdb.connect()
df = con.execute("""
    SELECT * FROM read_json_auto('data/evaluations/*.json')
""").fetchdf()

# Trust distribution
fig = px.histogram(df, x="assessment.composite_trust", nbins=20, title="Trust Score Distribution")
st.plotly_chart(fig)

# Trust by category
category_df = con.execute("""
    SELECT input.metadata.category as category,
           AVG(assessment.composite_trust) as avg_trust
    FROM read_json_auto('data/evaluations/*.json')
    GROUP BY category
""").fetchdf()
fig2 = px.bar(category_df, x="category", y="avg_trust", title="Average Trust by Category")
st.plotly_chart(fig2)
```

Run with `streamlit run dashboard.py`. You now have a full analytics dashboard with zero cloud cost.

---

## Part 3 — The Cloud Path (When You Are Ready)

### Step 0: AWS Account Setup (30 minutes)

**Actions:**

1. Go to [aws.amazon.com](https://aws.amazon.com) → "Create an AWS Account"
2. Use your personal email. You will need a credit/debit card (they charge $1 and refund it)
3. Choose the **Free Tier** plan
4. After account creation, **immediately** do these safety steps:

**Budget Protection (do this before ANYTHING else):**

```
AWS Console → Billing → Budgets → Create Budget
  Type: Cost budget
  Amount: $5.00 per month
  Alerts: Email at 50% ($2.50) and 80% ($4.00)
```

```
AWS Console → Billing → Billing Preferences
  ☑ Receive Free Tier Usage Alerts
  ☑ Receive Billing Alerts
  Email: your email
```

**IAM Safety:**

```
AWS Console → IAM → Users → Create User
  Name: trustcloud-dev
  Access: Programmatic access
  Policy: AmazonS3FullAccess, AmazonAthenaFullAccess
  (Do NOT use root account for anything after this)
```

Save the Access Key ID and Secret Access Key somewhere safe. You will need them.

**Install AWS CLI:**

```powershell
# On Windows
winget install Amazon.AWSCLI
# Then configure
aws configure
# Enter: Access Key ID, Secret Key, Region: us-east-1, Output: json
```

### Step 1: S3 Bucket (10 minutes)

```powershell
# Create bucket
aws s3 mb s3://trustcloud-data-YOUR-UNIQUE-SUFFIX --region us-east-1

# Upload your local evaluation data
aws s3 sync data/evaluations/ s3://trustcloud-data-YOUR-UNIQUE-SUFFIX/raw/evaluations/

# Verify
aws s3 ls s3://trustcloud-data-YOUR-UNIQUE-SUFFIX/raw/evaluations/ --recursive | head -10
```

**Cost:** 5GB free for 12 months. Your data is <10MB. Free.

### Step 2: Athena Query Setup (20 minutes)

```
AWS Console → Athena → Settings
  Query result location: s3://trustcloud-data-YOUR-UNIQUE-SUFFIX/athena-results/
```

Create a database and table:

```sql
CREATE DATABASE trustcloud;

CREATE EXTERNAL TABLE trustcloud.raw_evaluations (
    assessment struct<
        composite_trust: double,
        confidence: double,
        trust_level: string,
        defeated: boolean
    >,
    dimensions array<struct<
        name: string,
        score: double,
        uncertainty: double,
        signal_type: string
    >>,
    defeaters array<struct<
        name: string,
        severity: double,
        active: boolean
    >>,
    engine_version string,
    validators_run int,
    validators_failed int
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://trustcloud-data-YOUR-UNIQUE-SUFFIX/raw/evaluations/';
```

Now query it:

```sql
SELECT
    assessment.composite_trust,
    assessment.trust_level,
    assessment.defeated
FROM trustcloud.raw_evaluations
LIMIT 10;
```

**Cost:** First 5TB scanned per month is $5/TB. Your data is <10MB → cost per query: $0.00005. Effectively free.

### Step 3: Glue ETL (Optional — Only If You Need Parquet)

This is only necessary if your data grows large enough that JSON queries become slow. At student scale, you can skip this and query JSON directly with Athena.

If you do need it:

```
AWS Console → Glue → Crawlers → Create Crawler
  Name: trustcloud-raw-crawler
  Data source: s3://trustcloud-data-YOUR-UNIQUE-SUFFIX/raw/evaluations/
  Database: trustcloud
  Schedule: On-demand
  Run it once → it creates a table automatically
```

For the ETL job (JSON → Parquet):

```
AWS Console → Glue → ETL Jobs → Script editor
  Engine: PySpark
  Workers: 2 (minimum)
```

**Cost:** $0.44/DPU-hour. A 5-minute job with 2 DPUs = $0.07. Run sparingly.

### Step 4: API Deployment (When Needed)

**Cheapest option:** AWS EC2 `t2.micro` (free tier for 12 months).

```powershell
# Build and push Docker image to ECR
aws ecr create-repository --repository-name trustcloud-ai

# Get login
aws ecr get-login-password | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag trustcloud-ai:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/trustcloud-ai:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/trustcloud-ai:latest
```

Then launch an EC2 instance, pull the image, run it. But honestly:

**Even cheaper option:** Use [Railway](https://railway.app) or [Render](https://render.com) — both have free tiers that just take a Dockerfile. Zero AWS networking knowledge needed. Five-minute deploy.

**My recommendation:** Deploy the API to Render (free, simple). Use AWS only for S3 + Athena (the data engineering parts). This gives you cloud data engineering experience without fighting EC2 security groups.

---

## Part 4 — What NOT to Use

This is the most important section for protecting your credits.

### Dangerous Services (Avoid These)

| Service | Why It's Dangerous | Monthly Cost |
|---------|-------------------|------|
| **RDS** (managed database) | Charges per hour even when idle | $15-30+ |
| **Redshift** | Data warehouse, charges per hour | $180+ |
| **SageMaker** | ML notebooks charge per hour | $5-50+ |
| **ECS/Fargate** | Container hosting charges per second | $10-30+ |
| **NAT Gateway** | Charges per GB + per hour, easy to forget | $30+ |
| **Elastic IP** (unattached) | Charges per hour if not attached to running instance | $3.60 |
| **CloudWatch Logs** (excessive) | Charges per GB ingested | Varies |
| **Kinesis** | Charges per shard-hour | $10+ |

### Safe Services (Free or Negligible Cost)

| Service | Free Tier | Your Usage |
|---------|-----------|------------|
| **S3** | 5GB, 12 months | ✅ <10MB |
| **Athena** | $5/TB scanned | ✅ <10MB = $0.00005/query |
| **Glue** | 10 DPU-hours/month free (first month) | ✅ Use sparingly |
| **IAM** | Always free | ✅ |
| **CloudWatch** (basic) | 10 metrics, 3 dashboards free | ✅ |
| **Lambda** | 1M requests/month free | ✅ If needed |
| **EC2 t2.micro** | 750 hours/month, 12 months | ✅ One instance |

### The Golden Rule

> **If a service charges per hour, do not leave it running overnight.**

Set a phone reminder. Shut down EC2 instances, stop Glue jobs, delete forgotten resources. A single forgotten RDS instance costs $15/month for 12 months = $180 you did not plan to spend.

---

## Part 5 — Skills You Will Learn

### From the Local-First Path

| Skill | How You Learn It |
|-------|-----------------|
| Data pipeline design | Building the seed → evaluate → store → query → visualise pipeline |
| SQL analytics | Writing DuckDB/Athena queries over structured trust data |
| Data modeling | Designing the flat analytical schema from nested evaluation JSON |
| Python data engineering | Batch processing scripts, JSON transformation, Parquet conversion |
| Dashboard development | Streamlit + Plotly for interactive research visualisation |

### From the Cloud Path

| Skill | How You Learn It |
|-------|-----------------|
| AWS IAM | Creating users, policies, least-privilege access |
| S3 data lake design | Time-partitioned storage, Hive-style naming, lifecycle policies |
| Serverless SQL (Athena) | Querying S3 data without managing a database |
| ETL orchestration (Glue) | PySpark jobs for JSON → Parquet transformation |
| Cost management | Budgets, alerts, understanding pricing models |
| Docker + deployment | Container registry, cloud deployment, environment configuration |

### Career Relevance

| Role | Skills This Project Demonstrates |
|------|----------------------------------|
| Data Engineer | ETL pipeline, S3, Athena, Glue, schema design, Parquet |
| ML Engineer | Feature extraction, model-based validators, uncertainty quantification |
| Backend Engineer | FastAPI, plugin architecture, async patterns, Docker |
| Cloud Engineer | AWS services, IAM, cost management, infrastructure design |

---

## Part 6 — Realistic Roadmap

### The Order That Makes Sense

```
Week 1-2:  LOCAL    Build seed dataset (100+ samples across 5 categories)
           LOCAL    Run batch evaluation, store results locally
           LOCAL    Set up DuckDB analytics + Streamlit dashboard
           LOCAL    Write analysis of results for your report
              ↓
Week 3:    CLOUD    Create AWS account with budget protection
           CLOUD    Upload evaluation data to S3
           CLOUD    Set up Athena table, run same queries as DuckDB
           CLOUD    Screenshot everything for your report
              ↓
Week 4:    CLOUD    (Optional) Deploy API to Render or EC2
           CLOUD    (Optional) Set up Glue ETL job
           DOCS     Write final report with architecture diagrams
           DOCS     Reference both local and cloud implementations
```

### What Your Final Report Can Honestly Say

> "TrustCloud AI was developed and evaluated locally, then deployed to AWS to demonstrate cloud data engineering patterns. The local development environment uses DuckDB for analytics; the cloud deployment uses S3 + Athena for the same purpose, demonstrating architectural portability. The system processes [N] evaluation records through a [local/cloud] ETL pipeline and provides analytical dashboards for trust pattern analysis."

This is honest, technically accurate, and demonstrates real understanding. It does not claim to "scale to millions" or "handle enterprise workloads" — because it doesn't, and claiming so would be dishonest.

---

## Summary: The Decision Tree

```
START
  │
  ├─ Do you have 50+ evaluation records?
  │   NO ──► Build seed dataset first (local). Stop here until you do.
  │   YES ──┐
  │         │
  │         ├─ Do you need cloud for your submission?
  │         │   NO ──► Use DuckDB + Streamlit. Done. Cloud adds nothing.
  │         │   YES ──┐
  │         │         │
  │         │         ├─ Do you have an AWS account with budget protection?
  │         │         │   NO ──► Set up account + $5 budget alert FIRST.
  │         │         │   YES ──┐
  │         │         │         │
  │         │         │         └─► Upload to S3 → Athena → Screenshot → Done.
  │         │         │             Total AWS cost: <$0.50
  │         │         │             Time: 2-3 hours
  │         │
  │         ├─ Do you want to learn AWS as a career skill?
  │             YES ──► Treat it as a separate learning exercise.
  │                     Build a tiny Lambda + S3 + Athena demo first.
  │                     Then apply to TrustCloud.
  │             NO ──► Don't use AWS. Your project doesn't need it.
  │
  └─ END
```

The best cloud architecture is the one you build **after** you have data worth putting in it.
