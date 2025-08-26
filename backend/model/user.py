from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    id: str
    full_name: str = Field(..., max_length=100)
    email: EmailStr
    password: str
    avatar_url: Optional[str] = None
    role: Optional[str] = "user"
    is_active: Optional[bool] = True
