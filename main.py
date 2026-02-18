from fastapi import FastAPI
from schemas.request import TrustRequest
from schemas.response import TrustResponse
from trust_engine.engine import TrustEngine

app = FastAPI(title="TrustCloud AI", version="0.1")

engine = TrustEngine()

@app.get("/health")
def health():
    return {"status": "ok", "service": "TrustCloud AI"}

@app.post("/evaluate", response_model=TrustResponse)
def evaluate(req: TrustRequest):
    return engine.evaluate(req.text)
