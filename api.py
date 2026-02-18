from flask import Flask, request, jsonify
from trust_engine.engine import TrustEngine

app = Flask(__name__)
engine = TrustEngine()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "TrustCloud AI"})

@app.route("/validate", methods=["POST"])
def validate_text():
    data = request.json

    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text = data["text"]
    result = engine.evaluate(text)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
