"""User-facing business logic.

Contains user related operations such as registration, login and
user-article reactions. It coordinates repository calls and delegates
article related counters to the article service where appropriate.
"""

from datetime import datetime
import uuid
from fastapi import HTTPException
from typing import Any, Dict, Dict, List, Optional
from backend.model.dto.user_dto import user_dto
from backend.repositories import article_repo, user_repo
from backend.services import article_service
from backend.services.cache_service import CACHE_KEYS, delete_cache_pattern
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
    doc["created_at"] = datetime.utcnow().isoformat()
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
    is_liked = await check_article_status(user_id, article_id)
    if is_liked and is_liked.get("type") == "none":
        await user_repo.like_article(user_id, article_id)
        await article_repo.increment_article_likes(article_id)
        cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
        await delete_cache_pattern(cache_key)
        await delete_cache_pattern("articles:home*")
        await delete_cache_pattern("articles:recent*")


async def unlike_article(user_id: str, article_id: str):
    is_unliked = await check_article_status(user_id, article_id)
    if is_unliked["type"] == "like":
        await user_repo.unlike_article(user_id, article_id)
        await article_repo.decrement_article_likes(article_id)
        cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
        await delete_cache_pattern(cache_key)
        await delete_cache_pattern("articles:home*")
        await delete_cache_pattern("articles:recent*")

async def dislike_article(user_id: str, article_id: str):
    is_disliked = await check_article_status(user_id, article_id)
    if is_disliked and is_disliked.get("type") == "none":
        await user_repo.dislike_article(user_id, article_id)
        await article_service.increment_article_dislikes(article_id)
        cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
        await delete_cache_pattern(cache_key)
        await delete_cache_pattern("articles:home*")
        await delete_cache_pattern("articles:recent*")

async def undislike_article(user_id: str, article_id: str):
    is_disliked = await check_article_status(user_id, article_id)
    if is_disliked["type"] == "dislike":
        await user_repo.undislike_article(user_id, article_id)
        await article_service.decrement_article_dislikes(article_id)
        cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
        await delete_cache_pattern(cache_key)
        await delete_cache_pattern("articles:home*")
        await delete_cache_pattern("articles:recent*")

async def bookmark_article(user_id: str, article_id: str):
    await user_repo.bookmark_article(user_id, article_id)

async def unbookmark_article(user_id: str, article_id: str):
    await user_repo.unbookmark_article(user_id, article_id)   

async def check_article_status(user_id: str, article_id: str) -> Dict[str, Any]:
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Build a unified response expected by frontend: { reaction_type: 'like'|'dislike'|'none', is_bookmarked: bool }
    reaction_type = 'none'
    if article_id in user.get("liked_articles", []):
        reaction_type = 'like'
    elif article_id in user.get("disliked_articles", []):
        reaction_type = 'dislike'

    is_bookmarked = article_id in user.get('bookmarked_articles', [])
    return {"reaction_type": reaction_type, "is_bookmarked": is_bookmarked}

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

async def delete_reaction(article_id: str) -> bool:
    users = await user_repo.get_list_user()
    for user in users:
        user_id = user.get("id")
        if article_id in user.get("liked_articles", []):
            await unlike_article(user_id, article_id)
        if article_id in user.get("disliked_articles", []):
            await undislike_article(user_id, article_id)

        # also remove from bookmarks to avoid stale references
        if article_id in user.get('bookmarked_articles', []):
            try:
                await unbookmark_article(user_id, article_id)
            except Exception:
                # continue cleanup even if one fails
                pass

    return True
    
async def search_response_users(data: Dict) -> List[dict]:
    users_ids = [user["id"] for user in data.get("results", [])]
    return await user_repo.get_users_by_ids(users_ids)

def map_to_user_dto(user: dict) -> user_dto:
    return user_dto(
        id=user["id"],
        full_name=user.get("full_name"),
        email=user.get("email"),
        num_followers=len(user.get("followers", [])),
        num_following=len(user.get("following", [])),
        num_articles=len(user.get("articles", [])),
        role=user.get("role"),
        avatar_url=user.get("avatar_url")
    ) 
