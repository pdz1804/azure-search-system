from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

from backend.enum.status import Status
from backend.enum.roles import Role
from backend.services import user_service
from backend.repositories import article_repo
from backend.utils import get_current_user

users = APIRouter(prefix="/api/users", tags=["users"])


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Admin access required"
        )
    return current_user

@users.get("/bookmarks")
async def get_bookmarked_articles(
    app_id: Optional[str] = Query(None, description="Application ID for filtering results"),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["id"]
        article_ids = await user_service.get_user_bookmarks(user_id, app_id)
        
        if not article_ids:
            return {"success": True, "data": []}
        
        articles = await article_repo.get_articles_by_ids(article_ids, app_id)
        return {"success": True, "data": articles}
    except Exception as e:
        return {"success": False, "data": {"error": "Failed to fetch bookmarks"}}

@users.get("/{id}")
async def get_user_by_id(
    id: str, 
    app_id: Optional[str] = Query(None, description="Application ID for filtering results"),
):
    try:
        user = await user_service.get_user_by_id(id, app_id=app_id)
        if not user:
            return JSONResponse(status_code=404, content={"success": False, "data": None, "error": "user_not_found"})
        
        if user.get("error") == "account_deleted":
            return JSONResponse(
                status_code=410,
                content={
                    "success": False, 
                    "data": None, 
                    "error": "account_deleted",
                    "message": user.get("message", "This account has been deleted")
                }
            )
        
        return {"success": True, "data": user}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": str(e)}})

@users.post("/{user_id}/follow")
async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] == user_id:
        return JSONResponse(status_code=400, content={"success": False, "data": {"error": "Cannot follow yourself"}})
    
    result = await user_service.follow_user(current_user["id"], user_id)
    if result:
        return {"success": True, "data": {"message": "User followed successfully"}}
    else:
        return JSONResponse(status_code=400, content={"success": False, "data": {"error": "Unable to follow user"}})


@users.delete("/{user_id}/follow")
async def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    result = await user_service.unfollow_user(current_user["id"], user_id)
    if result:
        return {"success": True, "data": {"message": "User unfollowed successfully"}}
    else:
        return JSONResponse(status_code=400, content={"success": False, "data": {"error": "Unable to unfollow user"}})


@users.get("/{user_id}/follow/status")
async def check_follow_status(user_id: str, current_user: dict = Depends(get_current_user)):
    is_following = await user_service.check_follow_status(current_user["id"], user_id)
    return {"success": True, "data": {"is_following": is_following}}

@users.post("/reactions/{article_id}/{status}")
async def get_article_reactions(
    article_id: str, 
    status: str, 
    current_user: dict = Depends(get_current_user),
    app_id: Optional[str] = Query(None, description="Application ID for cache invalidation"),
):
    user_id = current_user["id"]
    
    match status:
        case Status.LIKE:
            await user_service.like_article(user_id, article_id, app_id=app_id)
            return {"success": True, "data": {"action": "like"}}
        case Status.DISLIKE:
            await user_service.dislike_article(user_id, article_id, app_id=app_id)
            return {"success": True, "data": {"action": "dislike"}}
        case Status.BOOKMARK:
            await user_service.bookmark_article(user_id, article_id)
            return {"success": True, "data": {"action": "bookmark"}}
        case _:
            return JSONResponse(status_code=400, content={"success": False, "data": {"error": "Invalid status"}})


@users.delete("/unreactions/{article_id}/{status}")
async def unreactions(
    article_id: str, 
    status: str, 
    current_user: dict = Depends(get_current_user),
    app_id: Optional[str] = Query(None, description="Application ID for cache invalidation"),
):
    user_id = current_user["id"]
    
    match status:
        case Status.LIKE:
            await user_service.unlike_article(user_id, article_id, app_id=app_id)
            return {"success": True, "data": {"action": "unlike"}}
        case Status.DISLIKE:
            await user_service.undislike_article(user_id, article_id, app_id=app_id)
            return {"success": True, "data": {"action": "undislike"}}
        case Status.BOOKMARK:
            await user_service.unbookmark_article(user_id, article_id)
            return {"success": True, "data": {"action": "unbookmark"}}
        case _:
            return JSONResponse(status_code=400, content={"success": False, "data": {"error": "Invalid status"}})
        
@users.get("/check_article_status/{article_id}")
async def check_article_status(article_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    status = await user_service.check_article_status(user_id, article_id)
    return {"success": True, "data": status}


@users.put("/{user_id}")
async def update_user(
    user_id: str, 
    update_data: UpdateUserRequest,
    admin_user: dict = Depends(require_admin),
    app_id: Optional[str] = Query(None, description="Application ID for cache invalidation"),
):
    try:
        if update_data.role and update_data.role not in [Role.ADMIN, Role.WRITER, Role.USER]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid role. Must be one of: {Role.ADMIN}, {Role.WRITER}, {Role.USER}"
            )
        
        if user_id == admin_user["id"] and update_data.is_active is False:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate your own account"
            )
        
        updated_user = await user_service.update_user(user_id, update_data.dict(exclude_unset=True), app_id=app_id)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "data": updated_user, "message": "User updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update user")


@users.get("/admin/all")
async def get_all_users_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=10000),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results"),
    admin_user: dict = Depends(require_admin)
):
    try:
        result = await user_service.list_users_with_pagination(
            page=page,
            page_size=limit,
            app_id=app_id
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@users.delete("/{user_id}")
async def delete_user(
    user_id: str,
    app_id: Optional[str] = Query(None, description="Application ID for multi-tenant filtering"),
    admin_user: dict = Depends(require_admin)
):
    try:
        if user_id == admin_user["id"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own account"
            )
        
        result = await user_service.delete_user(user_id, app_id)
        if not result:
            raise HTTPException(status_code=404, detail="User not found or access denied")
        
        return {"success": True, "data": {"message": "User deleted successfully"}}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete user")


@users.get("")
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results"),
):
    try:
        result = await user_service.list_users_with_pagination(
            page=page, 
            page_size=limit, 
            app_id=app_id
        )
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "success": False,
            "data": {"error": str(e)}
        })


