"""Data Transfer Objects for User API responses.

This module defines the structure of user data returned by API endpoints.
These DTOs ensure consistent response formats and provide type safety.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class UserDTO(BaseModel):
    """Data Transfer Object for user list responses.
    
    Contains basic user information for listing and search results.
    """
    user_id: str
    full_name: str
    email: EmailStr
    avatar_url: Optional[str] = None
    role: Optional[str] = "user"
    is_active: Optional[bool] = True


class UserDetailDTO(BaseModel):
    """Data Transfer Object for detailed user responses.
    
    Contains comprehensive user information including statistics.
    Used for user profile pages and detailed user views.
    """
    user_id: str
    full_name: str
    email: EmailStr
    avatar_url: Optional[str] = None
    role: Optional[str] = "user"
    is_active: Optional[bool] = True
    
    # Statistics
    total_followers: int = 0
    total_articles: int = 0
    total_published: int = 0
    total_views: int = 0
    total_likes: int = 0
