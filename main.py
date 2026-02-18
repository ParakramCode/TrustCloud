from trust_engine.engine import TrustEngine

def process():
    print("\n=== TrustCloud AI :: Trust Evaluation Engine ===\n")
    text = input("Enter AI-generated text:\n\n")

    engine = TrustEngine()
    result = engine.evaluate(text)

    print("\n=== SIGNAL REPORT ===")
    for k, v in result["signals"].items():
        print(f"{k:22s} : {v}")

    print("\n=== TRUST SCORE ===")
    print("Trust Score:", result["trust_score"])
    print("Trust Level:", result["trust_level"])

if __name__ == "__main__":
    process()
