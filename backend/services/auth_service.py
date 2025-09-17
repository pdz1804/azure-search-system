

from backend.config import settings
from backend.repositories.user_repo import get_by_email
from backend.services.user_service import create_user
from backend.utils import create_access_token
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


async def login_with_google(id_token_str: str, app_id: Optional[str] = None):
    try:
        CLIENT_ID = settings.GOOGLE_CLIENT_ID  
        idinfo = id_token.verify_oauth2_token(id_token_str, google_requests.Request(), CLIENT_ID)

        email = idinfo.get("email")
        if not email:
            raise ValueError("Token không chứa email hợp lệ")

        user = await get_by_email(email, app_id=app_id)
        if not user:
            user_data = {
                "full_name": idinfo.get("name", ""),
                "email": email,
                "avatar_url": idinfo.get("picture"),
                "role": "user",
                "password": "",  # Google users don't need password
            }
            user = await create_user(user_data, app_id=app_id)

        # Use user_id from the user object (could be 'id' or 'user_id')
        user_id = user.get("user_id") or user.get("id")
        token = create_access_token({"sub": user_id})

        return {
            "access_token": token, 
            "user_id": user_id, 
            "role": user.get("role", "user")
        }

    except ValueError as e:
        raise ValueError(f"Token không hợp lệ: {str(e)}") from e
    except Exception as e:
        print(f"Google login error: {e}")
        raise RuntimeError(f"Lỗi lấy Google user info: {str(e)}") from e
