"""Pydantic models for API response schemas."""

from pydantic import BaseModel
from typing import Optional, Dict, Any

class ArticleHit(BaseModel):
    """Represents a single article search hit in API responses."""
    id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    author_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]
    highlights: Optional[Dict[str, Any]] = None

class AuthorHit(BaseModel):
    """Represents a single author search hit in API responses."""
    id: str
    full_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]
