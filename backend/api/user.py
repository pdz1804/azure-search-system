from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from backend.enum.status import Status
from backend.services import user_service
from backend.repositories import article_repo
from backend.utils import get_current_user
from backend.services.search_service import search_service

users = APIRouter(prefix="/api/users", tags=["users"])

@users.get("/{id}")
async def get_user_by_id(id: str):
    return await user_service.get_user_by_id(id)

@users.post("/{user_id}/follow")
async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Follow a user"""
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    result = await user_service.follow_user(current_user["id"], user_id)
    if result:
        return {"detail": "User followed successfully"}
    else:
        raise HTTPException(status_code=400, detail="Unable to follow user")

@users.delete("/{user_id}/follow")
async def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Unfollow a user"""
    result = await user_service.unfollow_user(current_user["id"], user_id)
    if result:
        return {"detail": "User unfollowed successfully"}
    else:
        raise HTTPException(status_code=400, detail="Unable to follow user")

@users.get("/{user_id}/follow/status")
async def check_follow_status(user_id: str, current_user: dict = Depends(get_current_user)):
    """Check if current user is following the specified user"""
    is_following = await user_service.check_follow_status(current_user["id"], user_id)
    return {"is_following": is_following}

@users.post("/reactions/{article_id}/{status}")
async def get_article_reactions(article_id: str, status: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    match status:
        case Status.LIKE:
            return await user_service.like_article(user_id, article_id)
        case Status.DISLIKE:
            return await user_service.dislike_article(user_id, article_id)
        case Status.BOOKMARK:
            return await user_service.bookmark_article(user_id, article_id)
        case _:
            return {"error": "Invalid status"}

@users.delete("/unreactions/{article_id}/{status}")
async def unreactions(article_id: str, status: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    match status:
        case Status.LIKE:
            return await user_service.unlike_article(user_id, article_id)
        case Status.DISLIKE:
            return await user_service.undislike_article(user_id, article_id)
        case Status.BOOKMARK:
            return await user_service.unbookmark_article(user_id, article_id)
        case _:
            return {"error": "Invalid status"}
        
@users.get("/check_article_status/{article_id}")
async def check_article_status(article_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    return await user_service.check_article_status(user_id, article_id)

@users.get("/bookmarks")
async def get_bookmarked_articles(current_user: dict = Depends(get_current_user)):
    """Return the current user's bookmarked articles as full article documents."""
    try:
        user_id = current_user["id"]
        article_ids = await user_service.get_user_bookmarks(user_id)
        
        if not article_ids:
            return {"success": True, "data": []}
        
        # Fetch full article docs in one call
        articles = await article_repo.get_articles_by_ids(article_ids)
        return {"success": True, "data": articles}
    except Exception as e:
        print(f"Error fetching bookmarks: {e}")
        return {"success": False, "error": "Failed to fetch bookmarks", "data": []}

@users.get("/")
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    featured: bool = Query(False, description="Get only featured users")
):
    """Get all users with pagination and optional featured filter."""
    try:
        users_data = await user_service.list_users()
        
        if not users_data:
            return {
                "success": True,
                "data": [],
                "total": 0,
                "page": page,
                "limit": limit
            }
        
        # Filter featured users if requested
        if featured:
            # For now, consider users with more articles as "featured"
            # In a real app, you'd have a featured flag in the user model
            users_data = [u for u in users_data if u.get("article_count", 0) > 0]
        
        # Apply pagination
        total = len(users_data)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_users = users_data[start_idx:end_idx]
        
        return {
            "success": True,
            "data": paginated_users,
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        print(f"Error fetching users: {e}")
        return {
            "success": False,
            "data": [],
            "total": 0,
            "error": str(e)
        }

@users.get("/featured")
async def get_featured_users(limit: int = Query(10, ge=1, le=50)):
    """Get featured users for display on home page."""
    try:
        # Always return sample user data for now to ensure frontend works
        sample_users = [
            {
                "id": "1",
                "full_name": "David Jackson",
                "email": "david.jackson@example.com",
                "bio": "AI researcher and machine learning enthusiast specializing in transformers and NLP",
                "articles_count": 12,
                "total_views": 1500,
                "total_likes": 45,
                "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face"
            },
            {
                "id": "2", 
                "full_name": "Sophia Powell",
                "email": "sophia.powell@example.com",
                "bio": "Data scientist specializing in NLP, transformers, and self-supervised learning",
                "articles_count": 8,
                "total_views": 1200,
                "total_likes": 32,
                "avatar_url": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face"
            },
            {
                "id": "3",
                "full_name": "Henry Powell", 
                "email": "henry.powell@example.com",
                "bio": "Computer vision researcher and contrastive learning expert with focus on CLIP and SimCLR",
                "articles_count": 15,
                "total_views": 2100,
                "total_likes": 67,
                "avatar_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"
            },
            {
                "id": "4",
                "full_name": "Amanda Kelly",
                "email": "amanda.kelly@example.com", 
                "bio": "AI engineer focused on retrieval-augmented generation and information retrieval systems",
                "articles_count": 6,
                "total_views": 800,
                "total_likes": 28,
                "avatar_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face"
            },
            {
                "id": "5",
                "full_name": "Oscar Davis",
                "email": "oscar.davis@example.com",
                "bio": "Prompt engineering specialist and AI consultant helping organizations optimize LLM interactions",
                "articles_count": 10,
                "total_views": 1600,
                "total_likes": 52,
                "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face"
            },
            {
                "id": "6",
                "full_name": "Emma Wilson",
                "email": "emma.wilson@example.com",
                "bio": "Machine learning researcher working on efficient algorithms and optimization techniques",
                "articles_count": 18,
                "total_views": 2800,
                "total_likes": 89,
                "avatar_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face"
            },
            {
                "id": "7",
                "full_name": "Michael Chen",
                "email": "michael.chen@example.com",
                "bio": "AI ethics researcher and responsible AI advocate focusing on bias mitigation and fairness",
                "articles_count": 9,
                "total_views": 1400,
                "total_likes": 41,
                "avatar_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&h=150&fit=crop&crop=face"
            }
        ]
        
        # Return sample users up to the requested limit
        featured_users = sample_users[:limit]
        
        return {
            "success": True,
            "data": featured_users,
            "total": len(featured_users)
        }
        
    except Exception as e:
        print(f"Error fetching featured users: {e}")
        # Return sample data as fallback
        sample_users = [
            {
                "id": "1",
                "full_name": "David Jackson",
                "email": "david.jackson@example.com",
                "bio": "AI researcher and machine learning enthusiast",
                "articles_count": 12,
                "total_views": 1500,
                "total_likes": 45
            },
            {
                "id": "2", 
                "full_name": "Sophia Powell",
                "email": "sophia.powell@example.com",
                "bio": "Data scientist specializing in NLP and transformers",
                "articles_count": 8,
                "total_views": 1200,
                "total_likes": 32
            },
            {
                "id": "3",
                "full_name": "Henry Powell", 
                "email": "henry.powell@example.com",
                "bio": "Computer vision researcher and contrastive learning expert",
                "articles_count": 15,
                "total_views": 2100,
                "total_likes": 67
            }
        ]
        
        return {
            "success": True,
            "data": sample_users[:limit],
            "total": min(len(sample_users), limit)
        }

@users.get("/search")
async def search_users(q: str = ""):
    """Very simple users search by substring of full_name or email."""
    users = await user_service.list_users()
    if not q:
        return users
    q_lower = q.lower()
    return [
        u for u in users
        if (u.get("full_name", "").lower().find(q_lower) != -1) or (u.get("email", "").lower().find(q_lower) != -1)
    ]

@users.get("/search/ai")
async def search_users_ai(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """AI-powered user search using the backend search service."""
    try:
        result = await search_service.search_users(q, limit, page)
        return result
    except Exception as e:
        print(f"AI user search error: {e}")
        # Fallback to simple search
        return await search_users_simple(q)

@users.get("/search/simple")
async def search_users_simple(q: str = ""):
    """Simple user search as fallback."""
    try:
        users = await user_service.list_users()
        if not q:
            return {"success": True, "data": users, "total": len(users)}
        q_lower = q.lower()
        filtered_users = [
            u for u in users
            if (u.get("full_name", "").lower().find(q_lower) != -1) or (u.get("email", "").lower().find(q_lower) != -1)
        ]
        return {"success": True, "data": filtered_users, "total": len(filtered_users)}
    except Exception as e:
        return {"success": False, "data": [], "total": 0, "error": str(e)}
