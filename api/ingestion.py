from flask import Flask, request, jsonify
from queue import Queue

queue = Queue()
app = Flask(__name__)

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    queue.put(data)
    return jsonify({"status": "queued for validation"})

@app.route("/queue", methods=["GET"])
def get_job():
    if queue.empty():
        return jsonify({"status": "empty"})
    return jsonify(queue.get())

def run_api():
    app.run(port=5000)
