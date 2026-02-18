from pydantic import BaseModel
from typing import Dict

class TrustResponse(BaseModel):
    trust_score: float
    trust_level: str
    signals: Dict[str, float]
