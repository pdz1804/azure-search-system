"""Utility helpers for authentication, password hashing, token
creation/validation and file saving.

This module provides small building blocks used by the auth routes
and dependency injection in FastAPI handlers:
- password hashing + verification
- JWT creation and decoding
- FastAPI dependency to resolve the current user from Authorization header
- simple file save helper (used by endpoints that accept UploadFile)
"""

import os
from datetime import datetime, timedelta
from typing import Optional
import uuid
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, UploadFile
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Password hashing context (bcrypt)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Expect an Authorization header with a Bearer token
api_key_scheme = APIKeyHeader(name="Authorization")

credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials"
)


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage."""
    return pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against the stored hash."""
    return pwd.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token embedding `data` and expiry.

    The token stores the payload with an `exp` claim. The caller should
    place the subject (user id) under the `sub` key.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> str:
    """Decode a JWT and return the `sub` (user id) or raise 401."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(api_key_scheme)):
    """FastAPI dependency that extracts the current user dict from the
    Authorization header (expects 'Bearer <token>').
    """
    token = token.replace("Bearer ", "")
    user_id = decode_token(token)
    
    # Import here to avoid circular dependency
    from backend.repositories.user_repo import get_user_by_id
    return await get_user_by_id(user_id)


def require_role(user: dict, roles: list):
    """Raise 403 unless user role is in allowed roles."""
    if user.get("role") not in roles:
        raise HTTPException(status_code=403, detail="Forbidden")


def require_owner_or_role(user: dict, roles: list, owner_id: str):
    """Allow action if user is the owner (matching id) or has one of the
    provided roles. Otherwise raise 403.
    """
    if user.get("role") in roles:
        return
    if str(user["_id"]) == str(owner_id):
        return
    raise HTTPException(status_code=403, detail="Forbidden")


async def save_file(file: UploadFile) -> str:
    """Persist UploadFile to a local static/files directory and return
    the generated filename. Used by some endpoints for quick local
    storage (the project also supports uploading to Azure Blob via
    `backend.services.azure_blob_service`)."""
    upload_dir = os.path.join(os.getcwd(), "static", "files")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}-{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    await file.seek(0)
    data = await file.read()
    with open(file_path, "wb") as f:
        f.write(data)
    return filename
