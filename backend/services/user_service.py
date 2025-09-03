"""User-facing business logic.

Contains user related operations such as registration, login and
user-article reactions. It coordinates repository calls and delegates
article related counters to the article service where appropriate.
"""

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
    """Convert user data to dict following UserDTO structure"""
    return {
        "user_id": user.get("id", ""),
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "avatar_url": user.get("avatar_url"),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True),
        "articles_count": user.get("articles_count", 0),
        "total_views": user.get("total_views", 0),
        "total_followers": len(user.get("followers", [])),
        "created_at": user.get("created_at")
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
        "id": user_id,  # Keep original id for frontend compatibility
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
        # Include the arrays that frontend needs for statistics
        "followers": user.get("followers", []),
        "following": user.get("following", []),
        "liked_articles": user.get("liked_articles", []),
        "bookmarked_articles": user.get("bookmarked_articles", []),
        "disliked_articles": user.get("disliked_articles", []),
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
        except Exception as e:
            print(f"⚠️ Failed to get stats for user {user.get('id', 'unknown')}: {e}")
            # If stats fail, still include user with basic info
            user_dict = await _convert_to_user_dto(user)
            user_dicts.append(user_dict)
    
    print(f"👥 [LIST USERS] Processed {len(user_dicts)} users. Sample stats: {[(u.get('full_name', 'Unknown'), u.get('articles_count', 0), u.get('total_views', 0)) for u in user_dicts[:3]]}")
    
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
    
    # Check cache first
    cached_result = await get_cache(
        CACHE_KEYS["authors"], 
        app_id=app_id, 
        page=page, 
        page_size=page_size
    )
    
    if cached_result:
        print("👥 Redis Cache HIT for users pagination")
        return cached_result
    
    print("👥 Redis Cache MISS for users pagination - Loading from DB...")
    
    try:
        # Get base users data
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
        
        # Apply pagination
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
        
        # Cache the result
        await set_cache(
            CACHE_KEYS["authors"], 
            result, 
            app_id=app_id, 
            ttl=CACHE_TTL["authors"],
            page=page,
            page_size=page_size
        )
        print("👥 Redis Cache SET for users pagination")
        
        return result
        
    except Exception as e:
        print(f"Error fetching users with pagination: {e}")
        return {
            "success": False,
            "data": {"error": str(e)}
        }

async def login(email: str, password: str) -> Optional[dict]:
    user = await user_repo.get_by_email(email)
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
    
    # Initialize empty arrays for social features
    doc["followers"] = []
    doc["following"] = []
    doc["liked_articles"] = []
    doc["bookmarked_articles"] = []
    doc["disliked_articles"] = []
    
    # Add app_id to user document if provided
    if app_id:
        doc["app_id"] = app_id
    
    user = await user_repo.insert(doc)
    
    # Clear users list cache after creating new user
    await delete_cache_pattern(CACHE_KEYS["authors"] + "*", app_id=app_id)
    print("👥 Cleared users cache after creating new user")
    
    # Convert to UserDetailDTO format before returning
    return await _convert_to_user_detail_dto(user, app_id=app_id)


async def get_user_by_id(user_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    user = await user_repo.get_user_by_id(user_id, app_id=app_id)  # ✅ Truyền app_id
    if user:
        # Check if user is active
        if not user.get("is_active", True):
            # Return special error for deleted accounts
            return {
                "error": "account_deleted",
                "message": "This account has been deleted",
                "user_id": user_id
            }
        
        user_detail = await _convert_to_user_detail_dto(user, app_id=app_id)
        
        # Cache the result
        await set_cache(
            CACHE_KEYS["user_detail"], 
            user_detail, 
            user_id=user_id, 
            app_id=app_id,
            ttl=CACHE_TTL["user_detail"]
        )
        print(f"👤 Redis Cache SET for user {user_id}")
        
        return user_detail
    return None


async def update_user(user_id: str, update_data: dict, app_id: Optional[str] = None) -> Optional[dict]:
    """Update user information (role, status, etc.)"""
    try:
        # Get existing user
        existing_user = await user_repo.get_user_by_id(user_id, app_id)
        if not existing_user:
            return None
        
        # Update user data
        updated_user = await user_repo.update_user(user_id, update_data)
        
        # Clear related caches using new cache API with app_id
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)  # Clear specific user cache
        await delete_cache_pattern(CACHE_KEYS["authors"] + "*", app_id=app_id)  # Clear authors list cache
        
        # If user status changed, also clear related article caches
        if "is_active" in update_data:
            print(f"🔄 User status changed to {update_data['is_active']}, clearing related caches")
            # Clear homepage statistics since user count might change
            await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
        
        # Convert to UserDetailDTO format before returning
        return await _convert_to_user_detail_dto(updated_user, app_id=app_id)
    except Exception as e:
        print(f"Error in update_user service: {e}")
        raise

async def follow_user(follower_id: str, followee_id: str, app_id: Optional[str] = None):
    return await user_repo.follow_user(follower_id, followee_id, app_id)

async def unfollow_user(follower_id: str, followee_id: str, app_id: Optional[str] = None):
    return await user_repo.unfollow_user(follower_id, followee_id, app_id)

async def check_follow_status(follower_id: str, followee_id: str, app_id: Optional[str] = None) -> bool:
    """Check if follower_id is following followee_id"""
    return await user_repo.check_follow_status(follower_id, followee_id, app_id)

async def like_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_liked = await check_article_status(user_id, article_id, app_id)
    if is_liked and is_liked.get("reaction_type") == "none":
        await user_repo.like_article(user_id, article_id)
        await article_repo.increment_article_likes(article_id)
        # Use centralized cache clearing from article service
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="like", app_id=app_id, article_id=article_id)
        # Also clear user cache for updated reaction status
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def unlike_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_unliked = await check_article_status(user_id, article_id, app_id)
    if is_unliked["reaction_type"] == "like":
        await user_repo.unlike_article(user_id, article_id)
        await article_repo.decrement_article_likes(article_id)
        # Use centralized cache clearing from article service
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="unlike", app_id=app_id, article_id=article_id)
        # Also clear user cache for updated reaction status
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def dislike_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_disliked = await check_article_status(user_id, article_id, app_id)
    if is_disliked and is_disliked.get("reaction_type") == "none":
        await user_repo.dislike_article(user_id, article_id)
        await article_service.increment_article_dislikes(article_id)
        # Use centralized cache clearing from article service
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="dislike", app_id=app_id, article_id=article_id)
        # Also clear user cache for updated reaction status
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def undislike_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    is_disliked = await check_article_status(user_id, article_id, app_id)
    if is_disliked["reaction_type"] == "dislike":
        await user_repo.undislike_article(user_id, article_id)
        await article_service.decrement_article_dislikes(article_id)
        # Use centralized cache clearing from article service
        from backend.services.article_service import clear_affected_caches
        await clear_affected_caches(operation="undislike", app_id=app_id, article_id=article_id)
        # Also clear user cache for updated reaction status
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def bookmark_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    await user_repo.bookmark_article(user_id, article_id)
    # Use centralized cache clearing from article service
    from backend.services.article_service import clear_affected_caches
    await clear_affected_caches(operation="bookmark", app_id=app_id, article_id=article_id)
    # Also clear user cache for updated bookmark status
    await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def unbookmark_article(user_id: str, article_id: str, app_id: Optional[str] = None):
    await user_repo.unbookmark_article(user_id, article_id)
    # Use centralized cache clearing from article service
    from backend.services.article_service import clear_affected_caches
    await clear_affected_caches(operation="unbookmark", app_id=app_id, article_id=article_id)
    # Also clear user cache for updated bookmark status
    await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id)

async def check_article_status(user_id: str, article_id: str, app_id: Optional[str] = None) -> Dict[str, Any]:
    user = await user_repo.get_user_by_id(user_id, app_id)
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

        # also remove from bookmarks to avoid stale references
        if article_id in user.get('bookmarked_articles', []):
            try:
                await unbookmark_article(user_id, article_id, app_id)
            except Exception:
                # continue cleanup even if one fails
                pass

    return True
    
async def search_response_users(data: Dict) -> List[dict]:
    users_ids = [user["id"] for user in data.get("results", [])]

    print(f"👥 [SEARCH RESPONSE USERS] Users IDs: {users_ids}")

    users = await user_repo.get_users_by_ids(users_ids)
    # Convert to UserDTO format
    return [await _convert_to_user_dto(user) for user in users]


async def delete_user(user_id: str, app_id: Optional[str] = None) -> bool:
    """Soft delete a user by setting is_active=false (admin only)"""
    try:
        # Get user with app_id filtering for security
        user = await user_repo.get_user_by_id(user_id, app_id)
        if not user:
            print(f"❌ User {user_id} not found or app_id mismatch for deletion")
            return False
        
        # Check if user has articles (for logging purposes)
        user_articles = await article_repo.get_article_by_author(user_id, page=0, page_size=1000, app_id=app_id)
        if user_articles:
            articles_list = user_articles.get("items", []) if isinstance(user_articles, dict) else user_articles
            if articles_list and len(articles_list) > 0:
                print(f"⚠️ User {user_id} has {len(articles_list)} articles. Deleting user will also delete their articles.")
                
                # Delete all user's articles
                for article in articles_list:
                    try:
                        await article_repo.delete_article(article.get("id"))
                    except Exception as e:
                        print(f"⚠️ Failed to delete article {article.get('id')}: {e}")

                print(f"ℹ️ User {user_id} has {len(articles_list)} articles. Articles will remain but user will be deactivated.")
        
        # Soft delete user from repository (sets is_active=false)
        success = await user_repo.delete_user(user_id)
        if not success:
            return False
        
        # Clear affected caches
        await delete_cache(CACHE_KEYS["user_detail"], user_id=user_id, app_id=app_id) 
        await delete_cache_pattern(CACHE_KEYS["authors"] + "*"+app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["authors"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)  # Clear stats since user count changed
        
        print(f"✅ User {user_id} soft deleted successfully (set is_active=false)")
        print(f"🗑️ Cleared Redis cache for user {user_id} and authors list")
        return True
        
    except Exception as e:
        print(f"❌ Error soft deleting user {user_id}: {e}")
        return False


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
