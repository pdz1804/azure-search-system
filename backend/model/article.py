
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Article(BaseModel):
    id: str
    title: str
    content: str
    abstract: Optional[str]
    status: str
    tags: List[str]
    image: Optional[str]
    author_id: str
    author_name: str
    likes: int
    dislikes: int
    views: int
    created_at: datetime
    updated_at: datetime
    # NOTE: Commented out for preprocessing field removal
    # preprocessed_searchable_text: Optional[str] = None    
