"""
TrustCloud AI — Analytics Dashboard

Interactive trust analytics dashboard powered by DuckDB + Streamlit + Plotly.

Usage:
    streamlit run dashboard.py
"""

import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pathlib
import json

# ── Page Config ──
st.set_page_config(
    page_title="TrustCloud AI — Analytics",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──
st.markdown("""
<style>
    .main > div { padding-top: 1rem; }
    .stMetric { background: #1a1a2e; border-radius: 10px; padding: 15px; }
    h1 { color: #e0e0ff; }
    h2 { color: #a0a0d0; }
    h3 { color: #8080b0; }
</style>
""", unsafe_allow_html=True)


# ── Load Data ──
@st.cache_resource
def load_data():
    con = duckdb.connect()

    # Main evaluations table
    con.execute("""
        CREATE TABLE evaluations AS
        SELECT
            input.metadata.category AS category,
            input.metadata.topic AS topic,
            input.metadata.source AS source,
            length(input.text) AS text_length,
            assessment.composite_trust AS composite_trust,
            assessment.confidence AS confidence,
            assessment.trust_level AS trust_level,
            assessment.defeated AS defeated,
            validators_run,
            validators_failed
        FROM read_json_auto('data/evaluations/*.json',
            ignore_errors=true, filename=true)
        WHERE filename NOT LIKE '%_index%'
    """)

    # Dimension-level data
    con.execute("""
        CREATE TABLE dim_flat AS
        SELECT
            input.metadata.category AS category,
            input.metadata.topic AS topic,
            assessment.composite_trust AS composite_trust,
            d.name AS validator_name,
            d.score AS score,
            d.uncertainty AS uncertainty,
            d.signal_type AS signal_type,
            d.latency_ms AS latency_ms
        FROM read_json_auto('data/evaluations/*.json',
            ignore_errors=true, filename=true),
            unnest(dimensions) AS t(d)
        WHERE filename NOT LIKE '%_index%'
    """)

    # Defeater data
    con.execute("""
        CREATE TABLE defeaters_flat AS
        SELECT
            input.metadata.category AS category,
            d.name AS defeater_name,
            d.severity AS severity,
            d.active AS active
        FROM read_json_auto('data/evaluations/*.json',
            ignore_errors=true, filename=true),
            unnest(defeaters) AS t(d)
        WHERE filename NOT LIKE '%_index%'
    """)

    return con


con = load_data()

# ── Sidebar ──
st.sidebar.title("🔬 TrustCloud AI")
st.sidebar.markdown("**Epistemic Trust Analytics**")
st.sidebar.markdown("---")

categories = con.execute("SELECT DISTINCT category FROM evaluations ORDER BY category").fetchdf()["category"].tolist()
selected_categories = st.sidebar.multiselect(
    "Filter by Category",
    categories,
    default=categories,
)

if not selected_categories:
    st.warning("Select at least one category.")
    st.stop()

cat_filter = ", ".join(f"'{c}'" for c in selected_categories)

# ── Header Metrics ──
st.title("🔬 TrustCloud AI — Trust Analytics Dashboard")
st.markdown("*Epistemic trust evaluation results across the seed corpus*")

metrics = con.execute(f"""
    SELECT
        COUNT(*) AS total,
        ROUND(AVG(composite_trust), 3) AS avg_trust,
        ROUND(AVG(confidence), 3) AS avg_conf,
        SUM(CASE WHEN defeated THEN 1 ELSE 0 END) AS defeated
    FROM evaluations
    WHERE category IN ({cat_filter})
""").fetchdf().iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Evaluations", int(metrics["total"]))
col2.metric("Average Trust", f"{metrics['avg_trust']:.3f}")
col3.metric("Average Confidence", f"{metrics['avg_conf']:.3f}")
col4.metric("Defeated", int(metrics["defeated"]))

st.markdown("---")

# ── Row 1: Trust Distribution + Category Comparison ──
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.subheader("Trust Score Distribution")
    dist_df = con.execute(f"""
        SELECT composite_trust, category
        FROM evaluations
        WHERE category IN ({cat_filter})
    """).fetchdf()

    fig = px.histogram(
        dist_df, x="composite_trust", color="category",
        nbins=25, barmode="overlay", opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"composite_trust": "Composite Trust", "category": "Category"},
    )
    fig.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

with r1c2:
    st.subheader("Average Trust by Category")
    cat_df = con.execute(f"""
        SELECT
            category,
            ROUND(AVG(composite_trust), 3) AS avg_trust,
            ROUND(AVG(confidence), 3) AS avg_confidence,
            COUNT(*) AS n
        FROM evaluations
        WHERE category IN ({cat_filter})
        GROUP BY category
        ORDER BY avg_trust DESC
    """).fetchdf()

    fig2 = px.bar(
        cat_df, x="category", y="avg_trust",
        color="avg_trust",
        color_continuous_scale="RdYlGn",
        range_color=[0, 0.7],
        text="avg_trust",
        labels={"avg_trust": "Average Trust", "category": "Category"},
    )
    fig2.update_traces(textposition="outside", texttemplate="%{text:.3f}")
    fig2.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Row 2: Validator Heatmap + Defeater Analysis ──
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.subheader("Validator Scores by Category")
    heatmap_df = con.execute(f"""
        SELECT
            category,
            validator_name,
            ROUND(AVG(score), 3) AS avg_score
        FROM dim_flat
        WHERE category IN ({cat_filter})
        GROUP BY category, validator_name
        ORDER BY category, validator_name
    """).fetchdf()

    pivot = heatmap_df.pivot(index="category", columns="validator_name", values="avg_score")

    fig3 = px.imshow(
        pivot,
        text_auto=".3f",
        color_continuous_scale="RdYlGn",
        aspect="auto",
        labels={"color": "Score", "x": "Validator", "y": "Category"},
    )
    fig3.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig3, use_container_width=True)

with r2c2:
    st.subheader("Defeater Severity by Category")
    def_df = con.execute(f"""
        SELECT
            category,
            defeater_name,
            ROUND(AVG(severity), 3) AS avg_severity,
            ROUND(MAX(severity), 3) AS max_severity,
            SUM(CASE WHEN active THEN 1 ELSE 0 END) AS activated,
            COUNT(*) AS total
        FROM defeaters_flat
        WHERE category IN ({cat_filter})
        GROUP BY category, defeater_name
        ORDER BY category, defeater_name
    """).fetchdf()

    fig4 = px.bar(
        def_df, x="category", y="avg_severity",
        color="defeater_name", barmode="group",
        text="avg_severity",
        color_discrete_sequence=["#ff6b6b", "#ffd93d"],
        labels={"avg_severity": "Avg Severity", "category": "Category", "defeater_name": "Defeater"},
    )
    fig4.add_hline(y=0.7, line_dash="dash", line_color="red",
                   annotation_text="Activation Threshold (0.7)")
    fig4.update_traces(textposition="outside", texttemplate="%{text:.3f}")
    fig4.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── Row 3: Confidence vs Trust Scatter + Uncertainty Box Plot ──
r3c1, r3c2 = st.columns(2)

with r3c1:
    st.subheader("Confidence vs Trust")
    scatter_df = con.execute(f"""
        SELECT composite_trust, confidence, category, defeated, topic
        FROM evaluations
        WHERE category IN ({cat_filter})
    """).fetchdf()

    fig5 = px.scatter(
        scatter_df, x="composite_trust", y="confidence",
        color="category", symbol="defeated",
        hover_data=["topic"],
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"composite_trust": "Composite Trust", "confidence": "System Confidence"},
    )
    fig5.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig5, use_container_width=True)

with r3c2:
    st.subheader("Uncertainty by Validator")
    unc_df = con.execute(f"""
        SELECT validator_name, uncertainty, signal_type, category
        FROM dim_flat
        WHERE category IN ({cat_filter})
    """).fetchdf()

    fig6 = px.box(
        unc_df, x="validator_name", y="uncertainty",
        color="signal_type",
        color_discrete_map={"positive_indicator": "#4ecdc4", "defeater": "#ff6b6b"},
        labels={"uncertainty": "Uncertainty (σ)", "validator_name": "Validator"},
    )
    fig6.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ── Row 4: Radar Chart for Selected Category ──
st.subheader("Dimension Profile by Category (Radar)")

radar_cat = st.selectbox("Select category for radar chart", sorted(selected_categories))

radar_df = con.execute(f"""
    SELECT
        validator_name,
        ROUND(AVG(score), 3) AS avg_score
    FROM dim_flat
    WHERE category = '{radar_cat}'
    GROUP BY validator_name
    ORDER BY validator_name
""").fetchdf()

if len(radar_df) > 0:
    fig7 = go.Figure()
    fig7.add_trace(go.Scatterpolar(
        r=radar_df["avg_score"].tolist() + [radar_df["avg_score"].iloc[0]],
        theta=radar_df["validator_name"].tolist() + [radar_df["validator_name"].iloc[0]],
        fill="toself",
        fillcolor="rgba(78, 205, 196, 0.3)",
        line=dict(color="#4ecdc4", width=2),
        name=radar_cat,
    ))
    fig7.update_layout(
        template="plotly_dark",
        height=450,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1]),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=60, r=60, t=30, b=30),
    )
    st.plotly_chart(fig7, use_container_width=True)
else:
    st.info("No dimension data available for this category.")

st.markdown("---")

# ── Footer: Raw Data Table ──
st.subheader("Raw Evaluation Data")
raw_df = con.execute(f"""
    SELECT
        category, topic, composite_trust, confidence,
        trust_level, defeated, text_length
    FROM evaluations
    WHERE category IN ({cat_filter})
    ORDER BY composite_trust DESC
""").fetchdf()
st.dataframe(raw_df, use_container_width=True, height=400)

# ── Sidebar stats ──
st.sidebar.markdown("---")
st.sidebar.markdown("**Data Summary**")
total_files = len(list(pathlib.Path("data/evaluations").glob("*.json"))) - 1  # minus index
st.sidebar.metric("Evaluation Files", total_files)

parquet_exists = pathlib.Path("data/processed/evaluations.parquet").exists()
st.sidebar.metric("Parquet Export", "✅ Ready" if parquet_exists else "❌ Run analytics.py")

st.sidebar.markdown("---")
st.sidebar.markdown("*TrustCloud AI v1 — Epistemic Trust Model*")
