from datetime import datetime
import uuid
from fastapi import HTTPException
from typing import Any, Dict, Dict, Optional
from backend.model.dto.user_dto import user_dto
from backend.repositories import article_repo, user_repo
from backend.services import article_service
from backend.utils import get_current_user, hash_password, verify_password

async def list_users() -> list:
    users = await user_repo.get_list_user()
    return users

async def login(email: str, password: str) -> Optional[dict]:
    user = await user_repo.get_by_email(email)
    if not user or not verify_password(password, user.get("password", "")):
        return None
    return user

async def create_user(doc: dict) -> dict:
    if await user_repo.get_by_email(doc["email"]):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await user_repo.get_by_full_name(doc["full_name"]):
        raise HTTPException(status_code=400, detail="Full name already exists")

    doc["password"] = hash_password(doc.pop("password"))
    doc["role"] = doc.get("role", "user")
    doc["created_at"] = datetime.utcnow()
    doc["id"] = uuid.uuid4().hex
    user = await user_repo.insert(doc)
    return user

async def get_user_by_id(user_id: str) -> Optional[dict]:
    user = await user_repo.get_user_by_id(user_id)
    return map_to_user_dto(user) if user else None

async def follow_user(follower_id: str, followee_id: str):
    return await user_repo.follow_user(follower_id, followee_id)

async def unfollow_user(follower_id: str, followee_id: str):
    return await user_repo.unfollow_user(follower_id, followee_id)

async def check_follow_status(follower_id: str, followee_id: str) -> bool:
    """Check if follower_id is following followee_id"""
    return await user_repo.check_follow_status(follower_id, followee_id)

async def like_article(user_id: str, article_id: str):
    is_liked = await user_repo.like_article(user_id, article_id)
    if is_liked:
        await article_repo.increment_article_likes(article_id)

async def unlike_article(user_id: str, article_id: str):
    is_unliked = await user_repo.unlike_article(user_id, article_id)
    if is_unliked:
        await article_repo.decrement_article_likes(article_id)

async def dislike_article(user_id: str, article_id: str):
    is_disliked = await user_repo.dislike_article(user_id, article_id)
    if is_disliked:
        await article_service.increment_article_dislikes(article_id)

async def undislike_article(user_id: str, article_id: str):
    is_disliked = await user_repo.undislike_article(user_id, article_id)
    if is_disliked:
        await article_service.decrement_article_dislikes(article_id)

async def bookmark_article(user_id: str, article_id: str):
    await user_repo.bookmark_article(user_id, article_id)

async def unbookmark_article(user_id: str, article_id: str):
    await user_repo.unbookmark_article(user_id, article_id)   

async def check_article_status(user_id: str, article_id: str) -> Dict[str, Any]:
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if article_id in user.get("liked_articles", []):
        return {"type": "like"}
    elif article_id in user.get("disliked_articles", []):
        return {"type": "dislike"}
    else:
        return {"type": "none"}

async def get_user_bookmarks(user_id: str) -> list:
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.get("bookmarked_articles", [])

async def get_user_followers(user_id: str) -> list:
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.get("followers", [])

async def delete_reaction( article_id: str) -> bool:
    users = await user_repo.get_users()
    for user in users:
        for r in user.get("liked_articles", []):
            if r.get("article_id") == article_id:
                await unlike_article(user.get("id"), article_id)
                break
        for r in user.get("disliked_articles", []):
            if r.get("article_id") == article_id:
                await undislike_article(user.get("id"), article_id)
                break
    


def map_to_user_dto(user: dict) -> user_dto:
    return user_dto(
        id=str(user["_id"]),
        full_name=user.get("full_name"),
        email=user.get("email"),
        role=user.get("role"),
        avatar_url=user.get("avatar_url")
    )
