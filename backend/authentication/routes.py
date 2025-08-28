"""Authentication routes.

Handles login and registration. On successful login/register the
endpoints return a JWT `access_token` that should be supplied as a
Bearer token in the `Authorization` header for protected routes.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException,UploadFile
from pydantic import BaseModel, EmailStr
from backend.services.azure_blob_service import upload_image
from backend.model.request.login_request import LoginRequest
from backend.utils import create_access_token, save_file
from backend.services.user_service import create_user, login

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
auth = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    user_id: str
    role: str


@auth.post("/login", response_model=TokenResponse)
async def login_user(data: LoginRequest):
    # Authenticate using user_service which validates password.
    user = await login(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["id"]})
    return TokenResponse(access_token=token, user_id=user["id"], role=user.get("role", "user"))


@auth.post("/register", response_model=TokenResponse)
async def register(
    full_name: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    app_id: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None)
):
    # Collect registration fields and optionally upload avatar to blob
    user_data = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "role": role,
    }

    if avatar and hasattr(avatar, 'filename') and avatar.filename:
        try:
            # upload_image returns a URL to the blob storage  
            image_url = upload_image(avatar.file)
            user_data["avatar_url"] = image_url
            print(f"Avatar uploaded successfully for user: {user_data['email']}")
        except Exception as e:
            print(f"Failed uploading avatar: {e}")
            # Continue without avatar rather than failing registration

    user = await create_user(user_data, app_id=app_id)
    if not user:
        raise HTTPException(status_code=400, detail="User could not be created")
        
    token = create_access_token({"sub": user["user_id"]})
    return TokenResponse(access_token=token, user_id=user["user_id"], role=user.get("role", "user"))
