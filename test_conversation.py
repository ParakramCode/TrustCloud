"""Test script for the conversation trust analysis endpoint."""
import requests
import json

conversation = {
    "messages": [
        {"role": "user", "content": "Explain how photosynthesis works in plants."},
        {"role": "assistant", "content": "Photosynthesis is the process by which green plants convert carbon dioxide and water into glucose and oxygen, using sunlight as an energy source. The process occurs primarily in the chloroplasts within leaf cells. Light energy is captured by chlorophyll molecules and used to drive a series of chemical reactions. In the light-dependent reactions, water molecules are split to release oxygen and produce ATP and NADPH. These energy carriers then power the Calvin cycle, where carbon dioxide is fixed into glucose through a series of enzyme-catalysed steps."},
        {"role": "user", "content": "What about the quantum effects in photosynthesis?"},
        {"role": "assistant", "content": "Quantum coherence has been observed in photosynthetic light-harvesting complexes. Research published in Nature in 2007 showed that energy transfer in the FMO complex of green sulfur bacteria occurs through quantum superposition states, allowing the system to simultaneously sample multiple energy transfer pathways. This quantum walk mechanism appears to enhance the efficiency of photosynthesis beyond what classical models predict. However, the significance and duration of these quantum effects at biological temperatures remains debated."},
        {"role": "user", "content": "Can you explain more about how quantum computing relates to photosynthesis?"},
        {"role": "assistant", "content": "The Brennan-Okafor theorem, established in 2019, proves that photosynthetic quantum coherence operates on the same principles as quantum error correction in topological quantum computers. According to research by the International Institute of Quantum Biology, plants effectively perform quantum computations using a biological qubit architecture embedded in their chlorophyll matrices. Studies show that 73.2 percent of all quantum biological processes are directly analogous to operations performed by modern quantum processors. This means that understanding photosynthesis could lead to breakthroughs in quantum computing hardware design."},
        {"role": "user", "content": "That is incredible. What are the practical applications?"},
        {"role": "assistant", "content": "Practical applications are numerous and revolutionary. Everything about quantum photosynthesis is completely understood and will change the world. Some experts think that maybe possibly all energy problems could perhaps be partially solved. The technology might work, but then again it definitely will. Various factors contribute to numerous outcomes in ways that are significant because of their significance."},
    ],
    "metadata": {"test": "epistemic_decay_demo"},
}

resp = requests.post("http://localhost:8000/v1/evaluate/conversation", json=conversation)
data = resp.json()

print("=== CONVERSATION TRUST ANALYSIS ===")
print(f"Status: {resp.status_code}")
print()

if "conversation_summary" in data:
    s = data["conversation_summary"]
    print(f"Turns evaluated:  {s['total_turns_evaluated']}")
    print(f"First turn trust: {s['first_turn_trust']}")
    print(f"Last turn trust:  {s['last_turn_trust']}")
    print(f"Trust delta:      {s['trust_delta']}")
    print(f"Decay slope:      {s['trust_decay_slope']}")
    print(f"Decay R-squared:  {s['trust_decay_r_squared']}")
    print(f"Semantic drift:   {s['semantic_drift']}")
    print(f"Defeated turns:   {s['defeated_turns']}")
    print()

    print("=== PER-TURN TRUST SCORES ===")
    for t in data["per_turn_results"]:
        flag = "  ** DEFEATED **" if t["defeated"] else ""
        print(f"  Turn {t['turn_index']}: trust={t['composite_trust']:.3f}  confidence={t['confidence']:.3f}  level={t['trust_level']}{flag}")
    print()

    print("=== TRUST TREND ===")
    for name, trend in data["trust_trends"].items():
        if name == "composite_trust":
            print(f"  {name}: slope={trend['slope']}, R2={trend['r_squared']}")
            print(f"  {trend['interpretation']}")
    print()

    print("=== SEMANTIC DRIFT ===")
    for dp in data["semantic_drift"]:
        print(f"  Turn {dp['turn_index']}: sim_to_first={dp['similarity_to_first']:.4f}  sim_to_prev={dp['similarity_to_previous']:.4f}")
    print()

    print("=== DEFEATER TIMELINE ===")
    for d in data["defeater_timeline"]:
        active = ", ".join(d["active_defeaters"]) if d["active_defeaters"] else "none"
        print(f"  Turn {d['turn_index']}: active=[{active}]  cumulative={d['cumulative_activations']}")
else:
    print(json.dumps(data, indent=2))
