"""Print summary table of all conversation evaluation results."""
import json, pathlib

results = json.loads(
    pathlib.Path("data/conversation_evaluations/_all_conversations.json")
    .read_text(encoding="utf-8")
)

for r in results:
    m = r.get("_metadata", {})
    s = r.get("conversation_summary", {})
    cid = m.get("conversation_id", "?")
    pat = m.get("pattern", "?")
    ft = s.get("first_turn_trust", 0)
    lt = s.get("last_turn_trust", 0)
    delta = s.get("trust_delta", 0)
    slope = s.get("trust_decay_slope") or 0
    r2 = s.get("trust_decay_r_squared") or 0
    drift = s.get("semantic_drift", "?")
    defeated = s.get("defeated_turns", 0)
    print(f"{cid}")
    print(f"  pattern={pat}  trust: {ft:.3f} -> {lt:.3f}  delta={delta:+.3f}  slope={slope:+.4f}  R2={r2:.3f}  drift={drift}  defeated={defeated}")
