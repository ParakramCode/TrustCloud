"""Flatten evaluation JSONs into a single TSV for Athena (tab-delimited, no quoting issues)."""
import json, csv, pathlib

EVAL_DIR = pathlib.Path("data/evaluations")
OUT_FILE = pathlib.Path("data/athena_evaluations.tsv")

rows = []
for f in sorted(EVAL_DIR.glob("*.json")):
    if f.name.startswith("_"):
        continue
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  SKIP {f.name}: {e}")
        continue

    assessment = data.get("assessment", {})
    inp = data.get("input", {})
    metadata = inp.get("metadata", {})
    conf_factors = data.get("confidence_factors", {})

    # Extract dimension scores into flat columns
    dim_scores = {}
    for dim in data.get("dimensions", []):
        name = dim.get("name", "unknown")
        dim_scores[f"dim_{name}_score"] = dim.get("score")
        dim_scores[f"dim_{name}_uncertainty"] = dim.get("uncertainty")

    # Extract defeater info
    defeater_names = []
    for d in data.get("defeaters", []):
        if d.get("active"):
            defeater_names.append(d.get("name", ""))

    row = {
        "filename": f.name,
        "category": metadata.get("category", ""),
        "topic": metadata.get("topic", ""),
        "source": metadata.get("source", ""),
        "composite_trust": assessment.get("composite_trust"),
        "confidence": assessment.get("confidence"),
        "trust_level": assessment.get("trust_level", ""),
        "defeated": str(assessment.get("defeated", False)).lower(),
        "engine_version": data.get("engine_version", ""),
        "validators_run": data.get("validators_run", 0),
        "validators_failed": data.get("validators_failed", 0),
        "validator_success_rate": conf_factors.get("validator_success_rate"),
        "mean_uncertainty": conf_factors.get("mean_uncertainty"),
        "active_defeaters": ";".join(defeater_names) if defeater_names else "",
        **dim_scores,
    }
    rows.append(row)

# Collect all possible columns
all_keys = list(dict.fromkeys(k for row in rows for k in row.keys()))

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_FILE, "w", newline="", encoding="utf-8") as tsvfile:
    writer = csv.DictWriter(tsvfile, fieldnames=all_keys, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows with {len(all_keys)} columns to {OUT_FILE}")
print(f"Columns: {all_keys}")
