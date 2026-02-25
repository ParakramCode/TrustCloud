"""
TrustCloud AI — Batch Evaluation Script (Phase A)

Feeds all seed data samples through the running API and stores
structured evaluation results locally for analysis.

Usage:
    Ensure the API is running: docker run -p 8000:8000 ...
    Then: python evaluate_corpus.py
"""

import json
import pathlib
import time
import sys
import requests

API_URL = "http://localhost:8000/v1/evaluate"
SEED_DIR = pathlib.Path("seed_data")
OUTPUT_DIR = pathlib.Path("data/evaluations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Verify API is reachable ──
print("Checking API connectivity...")
try:
    health = requests.get("http://localhost:8000/v1/health", timeout=5)
    health.raise_for_status()
    info = health.json()
    print(f"  API is up: {info.get('service')} | engine={info.get('engine_version')} | validators={info.get('validators_loaded')}")
except Exception as e:
    print(f"  ERROR: Cannot reach API at {API_URL}")
    print(f"  {e}")
    print(f"  Make sure the Docker container is running: docker run -p 8000:8000 ...")
    sys.exit(1)

# ── Process seed data ──
total = 0
succeeded = 0
failed = 0
results_index = []  # summary for quick analysis

print()
print("=" * 70)
print("  BATCH EVALUATION — TrustCloud AI Seed Corpus")
print("=" * 70)

for category_dir in sorted(SEED_DIR.iterdir()):
    if not category_dir.is_dir():
        continue

    category = category_dir.name
    print(f"\n── Category: {category} ──")

    for file in sorted(category_dir.glob("*.json")):
        try:
            samples = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  SKIP {file.name}: invalid JSON ({e})")
            continue

        for i, sample in enumerate(samples):
            total += 1
            text = sample["text"] if isinstance(sample, dict) else sample
            topic = sample.get("topic", "unknown") if isinstance(sample, dict) else "unknown"
            source = sample.get("source", "unknown") if isinstance(sample, dict) else "unknown"

            # Build request
            payload = {
                "text": text,
                "metadata": {
                    "category": category,
                    "source_file": file.name,
                    "sample_index": i,
                    "topic": topic,
                    "source": source,
                }
            }

            try:
                start = time.time()
                resp = requests.post(API_URL, json=payload, timeout=60)
                elapsed = round((time.time() - start) * 1000)
                resp.raise_for_status()
                result = resp.json()

                # Save full result
                out_name = f"{category}_{file.stem}_{i:03d}.json"
                out_path = OUTPUT_DIR / out_name

                # Embed input metadata into the saved record
                record = {
                    "input": payload,
                    **result,
                }
                out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

                # Extract summary
                assessment = result.get("assessment", {})
                trust = assessment.get("composite_trust", "?")
                conf = assessment.get("confidence", "?")
                level = assessment.get("trust_level", "?")
                defeated = assessment.get("defeated", False)

                status = "DEFEATED" if defeated else level
                print(f"  [{total:3d}] {out_name:55s} trust={trust:<6} conf={conf:<6} {status:8s} ({elapsed}ms)")

                results_index.append({
                    "file": out_name,
                    "category": category,
                    "topic": topic,
                    "composite_trust": trust,
                    "confidence": conf,
                    "trust_level": level,
                    "defeated": defeated,
                    "latency_ms": elapsed,
                })
                succeeded += 1

            except requests.exceptions.RequestException as e:
                failed += 1
                print(f"  [{total:3d}] FAILED: {file.name}[{i}] — {e}")

            # Small delay to avoid overwhelming the API
            time.sleep(0.3)

# ── Save index ──
index_path = OUTPUT_DIR / "_evaluation_index.json"
index_path.write_text(json.dumps(results_index, indent=2), encoding="utf-8")

# ── Summary ──
print()
print("=" * 70)
print(f"  COMPLETE: {succeeded}/{total} evaluations succeeded, {failed} failed")
print(f"  Results saved to: {OUTPUT_DIR}/")
print(f"  Index saved to:   {index_path}")
print("=" * 70)

# Category summary
print()
print("  Category Summary:")
print(f"  {'Category':<20s} {'Count':>5s} {'Avg Trust':>10s} {'Avg Conf':>10s} {'Defeated':>8s}")
print("  " + "-" * 55)

from collections import defaultdict
cat_stats = defaultdict(lambda: {"count": 0, "trust_sum": 0, "conf_sum": 0, "defeated": 0})

for r in results_index:
    cat = r["category"]
    cat_stats[cat]["count"] += 1
    if isinstance(r["composite_trust"], (int, float)):
        cat_stats[cat]["trust_sum"] += r["composite_trust"]
        cat_stats[cat]["conf_sum"] += r["confidence"]
    if r["defeated"]:
        cat_stats[cat]["defeated"] += 1

for cat, s in sorted(cat_stats.items()):
    avg_trust = round(s["trust_sum"] / max(s["count"], 1), 3)
    avg_conf = round(s["conf_sum"] / max(s["count"], 1), 3)
    print(f"  {cat:<20s} {s['count']:>5d} {avg_trust:>10.3f} {avg_conf:>10.3f} {s['defeated']:>8d}")
