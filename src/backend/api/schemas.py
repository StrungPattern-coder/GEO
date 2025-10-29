from pydantic import BaseModel
from typing import List, Optional

class Fact(BaseModel):
    id: str
    subject: str
    predicate: str
    object: str
    source_url: str
    source_name: Optional[str] = None
    truth_weight: float = 0.5
    score: Optional[float] = None
    ts: Optional[str] = None
    idx: Optional[int] = None
    corroboration_count: Optional[int] = None
    recency_weight: Optional[float] = None
    trust_score: Optional[float] = None
    trust_explain: Optional[str] = None
    entity_type: Optional[str] = None  # Person, Paper, Organization, Concept, etc.
    domain_score: Optional[float] = None  # Domain reputation score (0.0-1.0)

class AskRequest(BaseModel):
    query: str
    max_facts: int = 8

class AskResponse(BaseModel):
    answer: str
    facts: List[Fact]
