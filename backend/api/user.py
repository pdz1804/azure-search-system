from fastapi import APIRouter, Depends, HTTPException

from backend.enum.status import Status
from backend.services import user_service
from backend.utils import get_current_user


users = APIRouter(prefix="/api/users", tags=["users"])

@users.get("/")
async def list_users():
    return await user_service.list_users()

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
        raise HTTPException(status_code=400, detail="Unable to unfollow user")

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
