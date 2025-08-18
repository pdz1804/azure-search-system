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
    avatar: Optional[UploadFile] = File(None)
):
    user_data = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "role": role,
    }

    if avatar:
        image_url = upload_image(avatar.file)
        user_data["avatar_url"] = image_url

    user = await create_user(user_data)
    if not user:
        raise HTTPException(status_code=400, detail="User could not be created")
        
    token = create_access_token({"sub": user["id"]})
    return TokenResponse(access_token=token, user_id=user["id"], role=user.get("role", "user"))
