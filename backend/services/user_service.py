from datetime import datetime
import re
import uuid
import math
from fastapi import HTTPException
from typing import Any, Dict, List, Optional
from ai_search import app
from backend.repositories import article_repo, user_repo
from backend.services import article_service
from backend.services.cache_service import (
    get_cache, set_cache, delete_cache, delete_cache_pattern, 
    CACHE_KEYS, CACHE_TTL
)
from backend.utils import hash_password, verify_password

async def _convert_to_user_dto(user: dict) -> dict:
    followers = user.get("followers", [])
    if followers is None:
        followers = []
    
    return {
        "user_id": user.get("id", ""),
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "avatar_url": user.get("avatar_url"),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True),
        "articles_count": user.get("articles_count", 0),
        "total_views": user.get("total_views", 0),
        "total_followers": len(followers),
        "created_at": user.get("created_at")
    }

async def _convert_to_user_detail_dto(user: dict, app_id: Optional[str] = None) -> dict:
    user_id = user.get("id", "")
    
    followers = user.get("followers", [])
    if followers is None:
        followers = []
    total_followers = len(followers)
    
    total_articles = 0
    total_published = 0
    total_views = 0
    total_likes = 0
    
    try:
        stats = await article_repo.get_author_stats(user_id, app_id=app_id)
        total_articles = stats.get('articles_count', 0)
        total_views = stats.get('total_views', 0)
        total_likes = stats.get('total_likes', 0)
        
        user_articles = await article_repo.get_article_by_author(user_id, page=0, page_size=1000, app_id=app_id)
        if user_articles:
            articles_list = user_articles.get("items", []) if isinstance(user_articles, dict) else user_articles
            if articles_list is None:
                articles_list = []
            total_published = len([a for a in articles_list if a.get('status') == 'published'])
    except Exception as e:
        user_articles = user.get("articles", [])
        if user_articles is None:
            user_articles = []
        total_articles = len(user_articles)
    
    return {
        "id": user_id,
        "user_id": user_id,
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "avatar_url": user.get("avatar_url"),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True),
        "total_followers": total_followers,
        "total_articles": total_articles,
        "total_published": total_published,
        "total_views": total_views,
        "total_likes": total_likes,
        "followers": user.get("followers", []) or [],
        "following": user.get("following", []) or [],
        "liked_articles": user.get("liked_articles", []) or [],
        "bookmarked_articles": user.get("bookmarked_articles", []) or [],
        "disliked_articles": user.get("disliked_articles", []) or [],
        "created_at": user.get("created_at"),
        "app_id": user.get("app_id")
    }

async def list_users(app_id: Optional[str] = None) -> List[dict]:
    """
    Base function: Get all users with basic stats enrichment
    - No pagination, no caching
    - Used as foundation for other functions
    """
    users = await user_repo.get_list_user(app_id=app_id)
    if not users:
        return []

    user_dicts = []
    for user in users:
        try:
            stats = await article_repo.get_author_stats(user.get('id'), app_id=app_id)
            user['articles_count'] = stats.get('articles_count', 0)
            user['total_views'] = stats.get('total_views', 0)
            
            user_dict = await _convert_to_user_dto(user)
            user_dicts.append(user_dict)
        except Exception as e:
            user_dict = await _convert_to_user_dto(user)
            user_dicts.append(user_dict)

    return user_dicts

async def list_users_with_pagination(
    page: int = 1, 
    page_size: int = 20, 
    app_id: Optional[str] = None
) -> dict:
    """
    Simple paginated user listing with cache support
    
    Args:
        page: Page number (1-based)
        page_size: Items per page
        app_id: Filter by application ID
        
    Returns:
        Dict with success, data (list of users), and pagination info
    """
    
    cached_result = await get_cache(
        CACHE_KEYS["authors"], 
        app_id=app_id, 
        page=page, 
        page_size=page_size
    )
    
    if cached_result:
        return cached_result

    try:
        users_data = await list_users(app_id=app_id)
        
        if not users_data:
            result = {
                "success": True,
                "data": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_results": 0
                }
            }
            return result
        
        total_items = len(users_data)
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_users = users_data[start_idx:end_idx]
        
        result = {
            "success": True,
            "data": paginated_users,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_pages,
                "total_results": total_items
            }
        }
        
        await set_cache(
            CACHE_KEYS["authors"], 
            result, 
            app_id=app_id, 
            ttl=CACHE_TTL["authors"],
            page=page,
            page_size=page_size
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "data": {"error": str(e)}
        }

async def login(email: str, password: str, app_id: Optional[str] = None) -> Optional[dict]:
    user = await user_repo.get_by_email(email, app_id=app_id)
    if not user or not verify_password(password, user.get("password", "")):
        return None
    if user.get("is_active") is False:
        return None
    
    return user

async def create_user(doc: dict, app_id: Optional[str] = None) -> dict:
    if await user_repo.get_by_email(doc["email"], app_id):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await user_repo.get_by_full_name(doc["full_name"], app_id):
        raise HTTPException(status_code=400, detail="Full name already exists")

    doc["password"] = hash_password(doc.pop("password"))
    doc["role"] = doc.get("role", "user")
    doc["created_at"] = datetime.utcnow().isoformat()
    doc["id"] = uuid.uuid4().hex
    doc["is_active"] = True
    
    doc["followers"] = []
    doc["following"] = []
    doc["liked_articles"] = []
    doc["bookmarked_articles"] = []
    doc["disliked_articles"] = []
    
    if app_id:
        doc["app_id"] = app_id
    
    user = await user_repo.insert(doc)
    
    await delete_cache_pattern(CACHE_KEYS["authors"] + "*", app_id=app_id)
    
    return await _convert_to_user_detail_dto(user, app_id=app_id)

async def get_user_by_id(user_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    user = await user_repo.get_user_by_id(user_id, app_id=app_id)
    if user:
        if not user.get("is_active", True):
            return {
                "error": "account_deleted",
                "message": "This account has been deleted",
                "user_id": user_id
            }
        
        user_detail = await _convert_to_user_detail_dto(user, app_id=app_id)
        
        await set_cache(
            CACHE_KEYS["user_detail"], 
            user_detail, 
            user_id=user_id, 
            app_id=app_id,
            ttl=CACHE_TTL["user_detail"]
        )
        
        return user_detail
    return None

async def update_user(user_id: str, update_data: dict, app_id: Optional[str] = None) -> Optional[dict]:
    try:
        existing_user = await user_repo.get_user_by_id(user_id, app_id)
        if not existing_user:
            return None
        
        updated_user = await user_repo.update_user(user_id, update_data)
        
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["authors"] + "*", app_id=app_id)
        
        if "is_active" in update_data:
            await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
        
        return await _convert_to_user_detail_dto(updated_user, app_id=app_id)
    except Exception as e:
        raise

async def follow_user(follower_id: str, followee_id: str, app_id: Optional[str] = None):
    return await user_repo.follow_user(follower_id, followee_id, app_id)

async def unfollow_user(follower_id: str, followee_id: str, app_id: Optional[str] = None):
    return await user_repo.unfollow_user(follower_id, followee_id, app_id)

async def check_follow_status(follower_id: str, followee_id: str, app_id: Optional[str] = None) -> bool:
    return await user_repo.check_follow_status(follower_id, followee_id, app_id)

async def like_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_liked = await check_article_status(user_id, article_id, app_id)
    if is_liked and is_liked.get("reaction_type") == "none":
        await user_repo.like_article(user_id, article_id)
        await article_repo.increment_article_likes(article_id)
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="like", app_id=app_id, article_id=article_id)
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def unlike_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_unliked = await check_article_status(user_id, article_id, app_id)
    if is_unliked["reaction_type"] == "like":
        await user_repo.unlike_article(user_id, article_id)
        await article_repo.decrement_article_likes(article_id)
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="unlike", app_id=app_id, article_id=article_id)
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def dislike_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_disliked = await check_article_status(user_id, article_id, app_id)
    if is_disliked and is_disliked.get("reaction_type") == "none":
        await user_repo.dislike_article(user_id, article_id)
        await article_service.increment_article_dislikes(article_id)
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="dislike", app_id=app_id, article_id=article_id)
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def undislike_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_disliked = await check_article_status(user_id, article_id, app_id)
    if is_disliked["reaction_type"] == "dislike":
        await user_repo.undislike_article(user_id, article_id)
        await article_service.decrement_article_dislikes(article_id)
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="undislike", app_id=app_id, article_id=article_id)
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def bookmark_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    await user_repo.bookmark_article(user_id, article_id)
    from backend.services.article_service import clear_affected_caches
    await clear_affected_caches(operation="bookmark", app_id=app_id, article_id=article_id)
    await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def unbookmark_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    await user_repo.unbookmark_article(user_id, article_id)
    from backend.services.article_service import clear_affected_caches
    await clear_affected_caches(operation="unbookmark", app_id=app_id, article_id=article_id)
    await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def check_article_status(user_id: str, article_id: str, app_id: Optional[str] = None) -> Dict[str, Any]:
    user = await user_repo.get_user_by_id(user_id, app_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reaction_type = 'none'
    if article_id in user.get("liked_articles", []):
        reaction_type = 'like'
    elif article_id in user.get("disliked_articles", []):
        reaction_type = 'dislike'

    is_bookmarked = article_id in user.get('bookmarked_articles', [])
    return {"reaction_type": reaction_type, "is_bookmarked": is_bookmarked}

async def get_user_bookmarks(user_id: str, app_id: Optional[str] = None) -> list:
    user = await user_repo.get_user_by_id(user_id, app_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.get("bookmarked_articles", [])

async def get_user_followers(user_id: str, app_id: Optional[str] = None) -> list:
    user = await user_repo.get_user_by_id(user_id, app_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.get("followers", [])

async def delete_reaction(article_id: str, app_id: Optional[str] = None) -> bool:
    users = await user_repo.get_list_user(app_id=app_id)
    for user in users:
        user_id = user.get("id")
        if article_id in user.get("liked_articles", []):
            await unlike_article(user_id, article_id, app_id=app_id)
        if article_id in user.get("disliked_articles", []):
            await undislike_article(user_id, article_id)

        if article_id in user.get('bookmarked_articles', []):
            try:
                await unbookmark_article(user_id, article_id, app_id)
            except Exception:
                pass

    return True
    
async def search_response_users(data: Dict) -> List[dict]:
    users_ids = [user["id"] for user in data.get("results", [])]

    users = await user_repo.get_users_by_ids(users_ids)
    return [await _convert_to_user_dto(user) for user in users]

async def delete_user(user_id: str, app_id: Optional[str] = None) -> bool:
    try:
        user = await user_repo.get_user_by_id(user_id, app_id)
        if not user:
            return False
        
        user_articles = await article_repo.get_article_by_author(user_id, page=0, page_size=1000, app_id=app_id)
        if user_articles:
            articles_list = user_articles.get("items", []) if isinstance(user_articles, dict) else user_articles
            if articles_list and len(articles_list) > 0:
                
                for article in articles_list:
                    try:
                        await article_repo.delete_article(article.get("id"))
                    except Exception as e:
                        pass

        success = await user_repo.delete_user(user_id)
        if not success:
            return False
        
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id) 
        await delete_cache_pattern(CACHE_KEYS["authors"] + "*"+app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["authors"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
        
        return True
        
    except Exception as e:
        return False
