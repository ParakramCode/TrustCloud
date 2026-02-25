"""
TrustCloud AI — DuckDB Analytics

Run SQL queries over the evaluation data locally.
Usage: python analytics.py
"""

import duckdb
import pathlib
import json

DATA_DIR = pathlib.Path("data/evaluations")

con = duckdb.connect()

# ── Load evaluation JSON files into a table ──
# DuckDB reads nested JSON natively
con.execute("""
    CREATE TABLE evaluations AS
    SELECT
        -- Input metadata
        input.metadata.category AS category,
        input.metadata.topic AS topic,
        input.metadata.source AS source,
        input.metadata.source_file AS source_file,
        length(input.text) AS text_length,

        -- Assessment
        assessment.composite_trust AS composite_trust,
        assessment.confidence AS confidence,
        assessment.trust_level AS trust_level,
        assessment.defeated AS defeated,

        -- Validators
        validators_run,
        validators_failed,

        -- Engine
        engine_version
    FROM read_json_auto('data/evaluations/*.json',
        ignore_errors=true,
        filename=true
    )
    WHERE filename NOT LIKE '%_index%'
""")

# ── Also extract dimension-level data ──
con.execute("""
    CREATE TABLE dimensions AS
    SELECT
        input.metadata.category AS category,
        input.metadata.topic AS topic,
        assessment.composite_trust AS composite_trust,
        unnest(dimensions) AS dim
    FROM read_json_auto('data/evaluations/*.json',
        ignore_errors=true,
        filename=true
    )
    WHERE filename NOT LIKE '%_index%'
""")

con.execute("""
    CREATE TABLE dim_flat AS
    SELECT
        category,
        topic,
        composite_trust,
        dim.name AS validator_name,
        dim.score AS score,
        dim.uncertainty AS uncertainty,
        dim.signal_type AS signal_type,
        dim.latency_ms AS latency_ms
    FROM dimensions
""")

# ── Also extract defeater data ──
con.execute("""
    CREATE TABLE defeater_data AS
    SELECT
        input.metadata.category AS category,
        unnest(defeaters) AS def
    FROM read_json_auto('data/evaluations/*.json',
        ignore_errors=true,
        filename=true
    )
    WHERE filename NOT LIKE '%_index%'
""")

con.execute("""
    CREATE TABLE defeaters_flat AS
    SELECT
        category,
        def.name AS defeater_name,
        def.severity AS severity,
        def.active AS active
    FROM defeater_data
""")


print("=" * 70)
print("  TRUSTCLOUD AI — EVALUATION ANALYTICS")
print("=" * 70)


# ── Query 1: Category Summary ──
print("\n1. TRUST BY CATEGORY")
print("-" * 60)
result = con.execute("""
    SELECT
        category,
        COUNT(*) AS n,
        ROUND(AVG(composite_trust), 3) AS avg_trust,
        ROUND(MIN(composite_trust), 3) AS min_trust,
        ROUND(MAX(composite_trust), 3) AS max_trust,
        ROUND(AVG(confidence), 3) AS avg_conf,
        SUM(CASE WHEN defeated THEN 1 ELSE 0 END) AS defeated
    FROM evaluations
    GROUP BY category
    ORDER BY avg_trust DESC
""").fetchdf()
print(result.to_string(index=False))


# ── Query 2: Validator Scores by Category ──
print("\n\n2. AVERAGE VALIDATOR SCORES BY CATEGORY")
print("-" * 60)
result2 = con.execute("""
    SELECT
        category,
        validator_name,
        ROUND(AVG(score), 3) AS avg_score,
        ROUND(AVG(uncertainty), 3) AS avg_unc,
        signal_type
    FROM dim_flat
    GROUP BY category, validator_name, signal_type
    ORDER BY category, signal_type DESC, validator_name
""").fetchdf()
print(result2.to_string(index=False))


# ── Query 3: Defeater Activation ──
print("\n\n3. DEFEATER ACTIVATION BY CATEGORY")
print("-" * 60)
result3 = con.execute("""
    SELECT
        category,
        defeater_name,
        COUNT(*) AS total,
        SUM(CASE WHEN active THEN 1 ELSE 0 END) AS activated,
        ROUND(AVG(severity), 3) AS avg_severity,
        ROUND(MAX(severity), 3) AS max_severity
    FROM defeaters_flat
    GROUP BY category, defeater_name
    ORDER BY category, defeater_name
""").fetchdf()
print(result3.to_string(index=False))


# ── Query 4: Trust vs Text Length ──
print("\n\n4. TRUST BY TEXT LENGTH BUCKET")
print("-" * 60)
result4 = con.execute("""
    SELECT
        CASE
            WHEN text_length < 100 THEN 'short (<100)'
            WHEN text_length < 250 THEN 'medium (100-250)'
            WHEN text_length < 400 THEN 'long (250-400)'
            ELSE 'very long (400+)'
        END AS length_bucket,
        COUNT(*) AS n,
        ROUND(AVG(composite_trust), 3) AS avg_trust,
        ROUND(AVG(confidence), 3) AS avg_conf
    FROM evaluations
    GROUP BY length_bucket
    ORDER BY avg_trust DESC
""").fetchdf()
print(result4.to_string(index=False))


# ── Query 5: Top & Bottom 5 ──
print("\n\n5. HIGHEST TRUST EVALUATIONS")
print("-" * 60)
result5 = con.execute("""
    SELECT
        category,
        topic,
        ROUND(composite_trust, 3) AS trust,
        ROUND(confidence, 3) AS conf,
        trust_level,
        defeated
    FROM evaluations
    ORDER BY composite_trust DESC
    LIMIT 5
""").fetchdf()
print(result5.to_string(index=False))

print("\n\n6. LOWEST TRUST EVALUATIONS")
print("-" * 60)
result6 = con.execute("""
    SELECT
        category,
        topic,
        ROUND(composite_trust, 3) AS trust,
        ROUND(confidence, 3) AS conf,
        trust_level,
        defeated
    FROM evaluations
    ORDER BY composite_trust ASC
    LIMIT 5
""").fetchdf()
print(result6.to_string(index=False))


# ── Query 6: Correlation between dimensions ──
print("\n\n7. DIMENSION CORRELATION (Coherence vs Reasoning Depth)")
print("-" * 60)
result7 = con.execute("""
    SELECT
        a.category,
        ROUND(CORR(a.score, b.score), 3) AS correlation,
        COUNT(*) AS n
    FROM dim_flat a
    JOIN dim_flat b ON a.category = b.category
        AND a.topic = b.topic
    WHERE a.validator_name = 'coherence'
      AND b.validator_name = 'reasoning_depth'
    GROUP BY a.category
    ORDER BY correlation DESC
""").fetchdf()
print(result7.to_string(index=False))


# ── Save all tables as Parquet ──
print("\n\n" + "=" * 70)
print("  EXPORTING TO PARQUET")
print("=" * 70)
parquet_dir = pathlib.Path("data/processed")
parquet_dir.mkdir(parents=True, exist_ok=True)

con.execute(f"COPY evaluations TO '{parquet_dir}/evaluations.parquet' (FORMAT PARQUET)")
con.execute(f"COPY dim_flat TO '{parquet_dir}/dimensions.parquet' (FORMAT PARQUET)")
con.execute(f"COPY defeaters_flat TO '{parquet_dir}/defeaters.parquet' (FORMAT PARQUET)")
print(f"  Saved: {parquet_dir}/evaluations.parquet")
print(f"  Saved: {parquet_dir}/dimensions.parquet")
print(f"  Saved: {parquet_dir}/defeaters.parquet")
print("  (These are ready for S3 upload when you move to cloud)")

con.close()
