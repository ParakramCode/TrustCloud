from pydantic import BaseModel
from typing import Optional, Dict

class TrustRequest(BaseModel):
    text: str
    metadata: Optional[Dict] = None
