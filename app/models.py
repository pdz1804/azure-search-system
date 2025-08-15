from pydantic import BaseModel
from typing import Optional, Dict, Any

class ArticleHit(BaseModel):
    id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    author_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]
    highlights: Optional[Dict[str, Any]] = None

class AuthorHit(BaseModel):
    id: str
    full_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]



