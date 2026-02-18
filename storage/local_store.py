import json

DB_FILE = "local_db.json"

def save(record):
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(record)

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)
