from unittest.util import _MAX_LENGTH
from git import Optional
from proto import Field
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    id: str
    full_name: str = Field(..., max_length=100)
    email: EmailStr
    password: str
    avatar_url: Optional[str] = None
    role: Optional[str] = "user"
