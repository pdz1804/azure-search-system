"""User-facing business logic.

Contains user related operations such as registration, login and
user-article reactions. It coordinates repository calls and delegates
article related counters to the article service where appropriate.
"""

from datetime import datetime
import uuid
from fastapi import HTTPException
from typing import Any, Dict, List, Optional
from backend.repositories import article_repo, user_repo
from backend.services import article_service
from backend.services.cache_service import CACHE_KEYS, delete_cache_pattern, get_cache, set_cache
from backend.utils import hash_password, verify_password


async def _convert_to_user_dto(user: dict) -> dict:
    """Convert user data to dict following UserDTO structure"""
    return {
        "user_id": user.get("id", ""),
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "avatar_url": user.get("avatar_url"),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True)
    }


async def _convert_to_user_detail_dto(user: dict, app_id: Optional[str] = None) -> dict:
    """Convert user data to dict following UserDetailDTO structure with statistics"""
    # Get user statistics
    user_id = user.get("id", "")
    
    # Calculate statistics
    total_followers = len(user.get("followers", []))
    total_articles = 0
    total_published = 0
    total_views = 0
    total_likes = 0
    
    try:
        # Get article statistics for this user (filtered by app_id)
        stats = await article_repo.get_author_stats(user_id, app_id=app_id)
        total_articles = stats.get('articles_count', 0)
        total_views = stats.get('total_views', 0)
        total_likes = stats.get('total_likes', 0)
        
        # Get published articles count (filtered by app_id)
        user_articles = await article_repo.get_article_by_author(user_id, page=0, page_size=1000, app_id=app_id)
        if user_articles:
            articles_list = user_articles.get("items", []) if isinstance(user_articles, dict) else user_articles
            total_published = len([a for a in articles_list if a.get('status') == 'published'])
    except Exception as e:
        print(f"⚠️ Failed to get user statistics for {user_id}: {e}")
        # Use fallback values
        total_articles = len(user.get("articles", []))
    
    return {
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
        "total_likes": total_likes
    }


async def list_users_with_pagination_admin(page: int = 1, limit: int = 20, app_id: Optional[str] = None) -> dict:
    """Get all users for admin dashboard with pagination."""
    try:
        users_data = await list_users(app_id=app_id)
        
        if not users_data:
            return {
                "success": True,
                "data": [],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 0,
                    "total_results": 0
                }
            }
        
        # Apply pagination
        total_items = len(users_data)
        total_pages = (total_items + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_users = users_data[start_idx:end_idx]
        
        return {
            "success": True,
            "data": paginated_users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_pages,
                "total_results": total_items
            }
        }
    except Exception as e:
        print(f"Error fetching users for admin with pagination: {e}")
        return {
            "success": False,
            "data": {"error": str(e)}
        }


async def list_users_with_cache(page: int = 1, page_size: int = 20, featured: bool = False, app_id: Optional[str] = None) -> dict:
    """Get all users with pagination and caching support."""
    # Check Redis cache first
    cache_key = f"authors:page_{page}_limit_{page_size}_featured_{featured}_app_{app_id or 'none'}"
    cached_authors = await get_cache(cache_key)
    if cached_authors:
        print("👥 Redis Cache HIT for authors")
        return cached_authors
    
    print("👥 Redis Cache MISS for authors - Loading from DB...")
    try:
        users_data = await list_users(app_id=app_id)
        
        if not users_data:
            result = {
                "success": True,
                "data": [],
                "pagination": {
                    "page": page,
                    "limit": page_size,
                    "total": 0,  # total pages
                    "total_results": 0  # total result count
                }
            }
            return result
        
        # Filter featured users if requested
        if featured:
            # For now, consider users with more articles as "featured"
            # In a real app, you'd have a featured flag in the user model
            users_data = [u for u in users_data if u.get("article_count", 0) > 0]
        
        # Apply pagination
        total_items = len(users_data)
        total_pages = (total_items + page_size - 1) // page_size  # Ceiling division
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_users = users_data[start_idx:end_idx]
        
        result = {
            "success": True,
            "data": paginated_users,
            "pagination": {
                "page": page,
                "limit": page_size,
                "total": total_pages,  # total pages
                "total_results": total_items  # total result count
            }
        }
        
        print(f"👥 [USERS SERVICE DEBUG] Returning pagination: {result['pagination']}")
        print(f"👥 [USERS SERVICE DEBUG] total_items={total_items}, total_pages={total_pages}, limit={page_size}")
        
        # Cache the results for 3 minutes (180 seconds)
        await set_cache(cache_key, result, ttl=180)
        print("👥 Redis Cache SET for authors")
        
        return result
    except Exception as e:
        print(f"Error fetching users with cache: {e}")
        return {
            "success": False,
            "data": {"error": str(e)}
        }


async def list_users(app_id: Optional[str] = None) -> List[dict]:
    users = await user_repo.get_list_user(app_id=app_id)
    if not users:
        return []

    # Convert each user to UserDTO format
    user_dicts = []
    for user in users:
        try:
            # Enrich with quick stats (also filter by app_id)
            stats = await article_repo.get_author_stats(user.get('id'), app_id=app_id)
            user['articles_count'] = stats.get('articles_count', 0)
            user['total_views'] = stats.get('total_views', 0)
            
            user_dict = await _convert_to_user_dto(user)
            user_dicts.append(user_dict)
        except Exception:
            # If stats fail, still include user with basic info
            user_dict = await _convert_to_user_dto(user)
            user_dicts.append(user_dict)
    
    return user_dicts

async def login(email: str, password: str) -> Optional[dict]:
    user = await user_repo.get_by_email(email)
    if not user or not verify_password(password, user.get("password", "")):
        return None
    return user

async def create_user(doc: dict, app_id: Optional[str] = None) -> dict:
    if await user_repo.get_by_email(doc["email"]):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await user_repo.get_by_full_name(doc["full_name"]):
        raise HTTPException(status_code=400, detail="Full name already exists")

    doc["password"] = hash_password(doc.pop("password"))
    doc["role"] = doc.get("role", "user")
    doc["created_at"] = datetime.utcnow().isoformat()
    doc["id"] = uuid.uuid4().hex
    
    # Add app_id to user document if provided
    if app_id:
        doc["app_id"] = app_id
    
    user = await user_repo.insert(doc)
    
    # Convert to UserDetailDTO format before returning
    return await _convert_to_user_detail_dto(user, app_id=app_id)

async def get_user_by_id(user_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    user = await user_repo.get_user_by_id(user_id)
    if user:
        return await _convert_to_user_detail_dto(user, app_id=app_id)
    return None


async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """Update user information (role, status, etc.)"""
    try:
        # Get existing user
        existing_user = await user_repo.get_user_by_id(user_id)
        if not existing_user:
            return None
        
        # Update user data
        updated_user = await user_repo.update_user(user_id, update_data)
        
        # Clear any related caches
        await delete_cache_pattern("authors:*")
        
        # Convert to UserDetailDTO format before returning
        return await _convert_to_user_detail_dto(updated_user)
    except Exception as e:
        print(f"Error in update_user service: {e}")
        raise

async def follow_user(follower_id: str, followee_id: str):
    return await user_repo.follow_user(follower_id, followee_id)

async def unfollow_user(follower_id: str, followee_id: str):
    return await user_repo.unfollow_user(follower_id, followee_id)

async def check_follow_status(follower_id: str, followee_id: str) -> bool:
    """Check if follower_id is following followee_id"""
    return await user_repo.check_follow_status(follower_id, followee_id)

async def like_article(user_id: str, article_id: str):
    is_liked = await check_article_status(user_id, article_id)
    if is_liked and is_liked.get("reaction_type") == "none":
        await user_repo.like_article(user_id, article_id)
        await article_repo.increment_article_likes(article_id)
        cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
        await delete_cache_pattern(cache_key)
        await delete_cache_pattern("articles:home*")
        await delete_cache_pattern("articles:recent*")


async def unlike_article(user_id: str, article_id: str):
    is_unliked = await check_article_status(user_id, article_id)
    if is_unliked["reaction_type"] == "like":
        await user_repo.unlike_article(user_id, article_id)
        await article_repo.decrement_article_likes(article_id)
        cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
        await delete_cache_pattern(cache_key)
        await delete_cache_pattern("articles:home*")
        await delete_cache_pattern("articles:recent*")

async def dislike_article(user_id: str, article_id: str):
    is_disliked = await check_article_status(user_id, article_id)
    if is_disliked and is_disliked.get("reaction_type") == "none":
        await user_repo.dislike_article(user_id, article_id)
        await article_service.increment_article_dislikes(article_id)
        cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
        await delete_cache_pattern(cache_key)
        await delete_cache_pattern("articles:home*")
        await delete_cache_pattern("articles:recent*")

async def undislike_article(user_id: str, article_id: str):
    is_disliked = await check_article_status(user_id, article_id)
    if is_disliked["reaction_type"] == "dislike":
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
    users = await user_repo.get_users_by_ids(users_ids)
    # Convert to UserDTO format
    return [await _convert_to_user_dto(user) for user in users]


# Remove old function that used the old user_dto class
# def map_to_user_dto(user: dict) -> user_dto:
#     return user_dto(
#         id=user["id"],
#         full_name=user.get("full_name"),
#         email=user.get("email"),
#         num_followers=len(user.get("followers", [])),
#         num_following=len(user.get("following", [])),
#         num_articles=len(user.get("articles", [])) if user.get("articles") else 0,
#         role=user.get("role"),
#         avatar_url=user.get("avatar_url")
#     ) 
