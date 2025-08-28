from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
	email: EmailStr
	password: str
	app_id: Optional[str] = None
