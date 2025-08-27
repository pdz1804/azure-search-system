from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AuthorDTO(BaseModel):
    id: str
    name: str
    avatar_url: Optional[str] = None


class ArticleDTO(BaseModel):
    """DTO for article list responses"""
    article_id: str
    title: str
    abstract: Optional[str]
    image: Optional[str]
    tags: list[str]
    author: AuthorDTO
    created_date: datetime
    total_like: int
    total_view: int


class ArticleDetailDTO(BaseModel):
    """DTO for article detail responses"""
    id: str
    title: str
    content: str
    abstract: Optional[str]
    status: str
    tags: list[str]
    image: Optional[str]
    author: AuthorDTO
    created_date: datetime
    updated_date: datetime
    total_like: int
    total_view: int
    total_dislike: int
    recommended: Optional[List[ArticleDTO]] = None  # List of recommended ArticleDTO
