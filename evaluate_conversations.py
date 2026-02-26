"""
TrustCloud AI — Conversation Batch Evaluator

Feeds all seed conversations through the /v1/evaluate/conversation
endpoint and stores structured results for analysis.
"""

import json
import pathlib
import requests
import time
import sys

API = "http://localhost:8000/v1/evaluate/conversation"
SEED_DIR = pathlib.Path("seed_data/conversations")
OUTPUT_DIR = pathlib.Path("data/conversation_evaluations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_conversation(conv: dict) -> dict:
    """Send a conversation to the API and return the report."""
    payload = {
        "messages": conv["messages"],
        "metadata": {
            "conversation_id": conv["id"],
            "pattern": conv["pattern"],
            "description": conv["description"],
            "expected_trend": conv["expected_trend"],
        },
    }

    resp = requests.post(API, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()


def main():
    seed_files = sorted(SEED_DIR.glob("*.json"))

    if not seed_files:
        print("ERROR: No seed conversation files found in seed_data/conversations/")
        sys.exit(1)

    print(f"Found {len(seed_files)} seed files")
    print("=" * 70)

    all_results = []
    total_convs = 0
    failed = 0

    for seed_file in seed_files:
        conversations = json.loads(seed_file.read_text(encoding="utf-8"))
        print(f"\n{seed_file.name}: {len(conversations)} conversations")

        for conv in conversations:
            conv_id = conv["id"]
            pattern = conv["pattern"]
            n_messages = len(conv["messages"])
            total_convs += 1

            print(f"\n  [{total_convs}] {conv_id} ({pattern}, {n_messages} messages)")

            try:
                start = time.time()
                report = evaluate_conversation(conv)
                elapsed = time.time() - start

                # Enrich with metadata
                report["_metadata"] = {
                    "conversation_id": conv_id,
                    "pattern": pattern,
                    "description": conv["description"],
                    "expected_trend": conv["expected_trend"],
                    "source_file": seed_file.name,
                    "total_messages": n_messages,
                }

                # Save individual result
                out_file = OUTPUT_DIR / f"{conv_id}.json"
                out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

                # Print summary
                summary = report.get("conversation_summary", {})
                first_trust = summary.get("first_turn_trust", "?")
                last_trust = summary.get("last_turn_trust", "?")
                delta = summary.get("trust_delta", "?")
                slope = summary.get("trust_decay_slope", "?")
                r2 = summary.get("trust_decay_r_squared", "?")
                drift = summary.get("semantic_drift", "?")

                print(f"    Trust: {first_trust} → {last_trust} (delta={delta})")
                print(f"    Slope: {slope}, R²: {r2}")
                print(f"    Drift: {drift}")
                print(f"    Time:  {elapsed:.1f}s")

                all_results.append(report)

            except Exception as e:
                print(f"    FAILED: {e}")
                failed += 1
                continue

            # Brief pause between conversations
            time.sleep(0.5)

    # Save combined results
    combined_file = OUTPUT_DIR / "_all_conversations.json"
    combined_file.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

    # Print final summary table
    print("\n" + "=" * 70)
    print("BATCH EVALUATION COMPLETE")
    print(f"Total: {total_convs} | Succeeded: {total_convs - failed} | Failed: {failed}")
    print("=" * 70)
    print(f"\n{'ID':<35} {'Pattern':<25} {'1st':>5} {'Last':>5} {'Delta':>7} {'Slope':>9} {'R²':>6}")
    print("-" * 95)

    for r in all_results:
        meta = r.get("_metadata", {})
        s = r.get("conversation_summary", {})
        print(
            f"{meta.get('conversation_id', '?'):<35} "
            f"{meta.get('pattern', '?'):<25} "
            f"{s.get('first_turn_trust', 0):>5.3f} "
            f"{s.get('last_turn_trust', 0):>5.3f} "
            f"{s.get('trust_delta', 0):>+7.3f} "
            f"{s.get('trust_decay_slope', 0):>+9.4f} "
            f"{s.get('trust_decay_r_squared', 0):>6.3f}"
        )

    print(f"\nResults saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
