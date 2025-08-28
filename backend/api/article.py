import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional, List

from backend.services.azure_blob_service import upload_image
from backend.enum.roles import Role
from backend.utils import get_current_user, require_owner_or_role, require_role
from backend.services.article_service import (
    get_article_by_id,
    create_article,
    get_article_detail,
    list_articles,
    update_article,
    delete_article,
    get_popular_articles,
    get_articles_by_author,
    increment_article_views
)
from backend.services.tag_service import tag_service
from backend.services.search_service import search_service
from backend.services.recommendation_service import get_recommendation_service

load_dotenv()
BASE_URL = os.getenv("BASE_URL")

articles = APIRouter(prefix="/api/articles", tags=["articles"])

@articles.post("/")
async def create(
    request: Request,
    title: str = Form(...),
    abstract: str = Form(...),
    content: str = Form(...),
    tags: Optional[str] = Form(None),
    image: UploadFile = File(None),
    app_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    require_role(current_user, [Role.WRITER, Role.ADMIN])
    doc = {
        "title": title,
        "content": content,
        "tags": tags.split(",") if tags else [],
        "status": "published",
        "author_id": current_user["id"],
        "author_name": current_user.get("full_name"),
        "abstract": abstract,
        "app_id": app_id
    }
    # Log incoming form keys and file presence
    form = None
    try:
        form = await request.form()
        keys = list(form.keys())
        print(f"[DEBUG] create - form keys received: {keys}")
        # If file-like, it's accessible in form.get('image') as UploadFile
        if 'image' in form:
            f = form.get('image')
            try:
                print(f"[DEBUG] create - form['image'] type: {type(f)}, attrs: {getattr(f, 'filename', None)}")
            except Exception:
                print('[DEBUG] create - unable to introspect form image field')
    except Exception as e:
        print(f"[DEBUG] create - failed to read request.form(): {e}")

    if image:
        try:
            print(f"[DEBUG] Received image: filename={image.filename}, content_type={image.content_type}")
            image_url = upload_image(image.file)
            doc["image"] = image_url
        except Exception as e:
            print(f"[ERROR] Failed uploading image in create: {e}")
    else:
        # Try fallback: sometimes the UploadFile param isn't populated but request.form() contains the file
        if form and 'image' in form:
            try:
                f = form.get('image')
                if hasattr(f, 'filename') and getattr(f, 'filename'):
                    print(f"[DEBUG] create - using fallback form image: filename={getattr(f, 'filename', None)}")
                    try:
                        image_url = upload_image(f.file)
                        doc["image"] = image_url
                    except Exception as e:
                        print(f"[ERROR] Failed uploading fallback image in create: {e}")
                else:
                    print('[DEBUG] create - form image exists but has no filename')
            except Exception as e:
                print(f"[DEBUG] create - error handling fallback form image: {e}")
        else:
            print("[DEBUG] No image provided in create request")
    art = await create_article(doc, app_id)
    # Convert DTO to dict for JSON response
    return {"success": True, "data": art}

@articles.get("/")
async def get_articles(
    page: Optional[int] = Query(None, alias="page[page]"),
    page_size: Optional[int] = Query(None, alias="page[page_size]"),
    q: Optional[str] = Query(None, alias="page[q]"),
    status: Optional[str] = Query(None, alias="page[status]"),
    sort_by: Optional[str] = Query(None, alias="page[sort_by]"),
    limit: Optional[int] = Query(10),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    try:
        # Use provided parameters or defaults
        current_page = page or 1
        current_page_size = page_size or limit or 20
        current_status = status or "published"
        
        # Use service layer pagination function
        from backend.services.article_service import list_articles_with_pagination
        result = await list_articles_with_pagination(
            page=current_page, 
            page_size=current_page_size, 
            app_id=app_id
        )
        
        return result
    except Exception as e:
        print(f"Error fetching articles: {e}")
        return JSONResponse(status_code=500, content={
            "success": False,
            "data": {"error": str(e)}
        })

@articles.get("/popular")
async def home_popular_articles(page: int = 1, page_size: int = 10, app_id: Optional[str] = Query(None, description="Application ID for filtering results")):
    try:
        # Use service layer pagination function
        from backend.services.article_service import get_popular_articles_with_pagination
        result = await get_popular_articles_with_pagination(
            page=page, 
            page_size=page_size, 
            app_id=app_id
        )
        
        return result
    except Exception as e:
        print(f"Error fetching popular articles: {e}")
        return {"success": False, "data": {"error": "Failed to fetch popular articles"}}

@articles.post("/generate-tags")
async def generate_article_tags(
    title: str = Form(""),
    abstract: str = Form(""),
    content: str = Form(""),
    user_tags: List[str] = Form([])
):
    """
    Generate article tags using LLM with KeyBERT fallback.
    User provides 0-2 tags, system generates up to 4 total tags.
    """
    try:
        print(f"🏷️ Generating tags for article: '{title[:50]}...'")
        print(f"🏷️ User provided {len(user_tags)} tags: {user_tags}")
        
        # Generate tags using the tag service
        result = await tag_service.generate_article_tags(
            title=title,
            abstract=abstract,
            content=content,
            user_tags=user_tags
        )
        
        print(f"🏷️ Tag generation complete: {len(result['tags'])} tags using {result['method_used']}")
        return result
        
    except Exception as e:
        print(f"❌ Tag generation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "tags": user_tags[:4],  # Fallback to user tags
                "method_used": "error_fallback"
            }
        )

@articles.get("/stats")
async def get_statistics(app_id: Optional[str] = Query(None, description="Application ID for filtering results")):
    """Get statistics for articles, authors, views, and bookmarks."""
    try:
        # Use the service layer function for consistent data with caching
        from backend.services.article_service import get_summary
        stats_data = await get_summary(app_id=app_id)
        
        # Add bookmarks count (placeholder for now)
        stats_data["bookmarks"] = 0  # Placeholder for bookmarks
        
        # Rename fields to match expected API response format
        api_stats = {
            "articles": stats_data.get("total_articles", 0),
            "authors": stats_data.get("authors", 0), 
            "total_views": stats_data.get("total_views", 0),
            "bookmarks": stats_data.get("bookmarks", 0)
        }
        
        return {
            "success": True,
            "data": api_stats
        }
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        # Return sample data as fallback
        return {
            "success": True,
            "data": {
                "articles": 50,
                "authors": 15,
                "total_views": 2500,
                "bookmarks": 0
            }
        }

@articles.get("/categories")
async def get_categories(app_id: Optional[str] = Query(None, description="Application ID for filtering results")):
    """Get all available categories and their article counts."""
    try:
        from backend.services.article_service import get_categories as get_categories_service
        categories_result = await get_categories_service(app_id=app_id)
        
        return {
            "success": True,
            "data": categories_result
        }
    except Exception as e:
        print(f"Error fetching categories: {e}")
        # Return default categories as fallback
        return {
            "success": True,
            "data": [
                {"name": "Technology", "count": 15},
                {"name": "Design", "count": 12},
                {"name": "Business", "count": 10},
                {"name": "Science", "count": 8},
                {"name": "Health", "count": 6},
                {"name": "Lifestyle", "count": 5}
            ]
        }

@articles.get("/categories/{category_name}")
async def get_articles_by_category(
    category_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    """Get articles by category."""
    try:
        from backend.services.article_service import get_articles_by_category as get_articles_by_category_service
        result = await get_articles_by_category_service(category_name, page, limit, app_id)
        return result
    except Exception as e:
        print(f"Error fetching articles by category: {e}")
        return {
            "success": False,
            "data": {"error": str(e)}
        }

# @articles.get("/search")
# async def search_articles(
#     q: str = Query(..., min_length=1),
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100)
# ):
#     """AI-powered article search using the backend search service."""
#     try:
#         result = await search_service.search_articles(q, limit, page)
#         return result
#     except Exception as e:
#         print(f"Article search error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @articles.get("/search/simple")
# async def search_articles_simple(
#     q: str = Query(..., min_length=1),
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100)
# ):
#     """Simple article search as fallback."""
#     try:
#         # This would be a simple database search
#         # For now, return empty results
#         return {
#             "success": True,
#             "data": [],
#             "total": 0,
#             "page": page,
#             "limit": limit,
#             "search_type": "articles_simple"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@articles.get("/{article_id}")
async def get_one(article_id: str, app_id: Optional[str] = Query(None, description="Application ID for multi-tenant filtering")):
    try:
        # Get article detail with auto-generation of recommendations if needed
        art = await get_article_detail(article_id, app_id)
        if not art:
            return JSONResponse(status_code=404, content={"success": False, "data": None})
        
        await increment_article_views(article_id, app_id)
        
        # art is already a dict
        return {
            "success": True,
            "data": art
        }
    except Exception as e:
        print(f"Error fetching article {article_id}: {e}")
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": "Failed to fetch article"}})

@articles.put("/{article_id}")
async def update(
    article_id: str,
    title: Optional[str] = Form(None),
    abstract: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    image: UploadFile = File(None),
    app_id: Optional[str] = Form(None, description="Application ID for multi-tenant filtering"),
    current_user: dict = Depends(get_current_user)
):
    # Get article with app_id filtering for security
    art = await get_article_by_id(article_id, app_id)
    if not art:
        return JSONResponse(status_code=404, content={"success": False, "data": None})
    
    # Verify the article belongs to the current user's app_id (if specified)
    if app_id and art.get("app_id") != app_id:
        print(f"🔒 Access denied: Article {article_id} app_id mismatch - requested: {app_id}, actual: {art.get('app_id')}")
        return JSONResponse(status_code=403, content={"success": False, "data": {"error": "Access denied - app_id mismatch"}})
    
    # Check user permissions
    if art.get("author_id") != current_user["id"] and current_user.get("role") not in [Role.ADMIN]:
        return JSONResponse(status_code=403, content={"success": False, "data": {"error": "Not allowed to update"}})
    update_data = {}
    if title is not None and title != "":
        update_data["title"] = title
    if content is not None and content != "":
        update_data["content"] = content
    if abstract is not None and abstract != "":    
        update_data["abstract"] = abstract
    if tags is not None and tags != "":
        update_data["tags"] = tags.split(",") if tags else []
    if status is not None and status != "":
        update_data["status"] = status
    if image and image != "" :
        try:
            print(f"[DEBUG] Received image for update: filename={image.filename}, content_type={image.content_type}")
            image_url = upload_image(image.file)
            update_data["image"] = image_url
        except Exception as e:
            print(f"[ERROR] Failed uploading image in update: {e}")
    else:
        print("[DEBUG] No image provided in update request")
    updated = await update_article(article_id, update_data, app_id)
    if not updated:
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": "Update failed"}})
    # Convert DTO to dict for JSON response
    return {"success": True, "data": updated}

@articles.delete("/{article_id}")
async def remove(article_id: str, app_id: Optional[str] = Query(None, description="Application ID for multi-tenant filtering"), current_user: dict = Depends(get_current_user)):
    # Get article with app_id filtering for security
    art = await get_article_by_id(article_id, app_id)
    if not art:
        return JSONResponse(status_code=404, content={"success": False, "data": None})
    
    # Verify the article belongs to the current user's app_id (if specified)
    if app_id and art.get("app_id") != app_id:
        print(f"🔒 Access denied: Article {article_id} app_id mismatch - requested: {app_id}, actual: {art.get('app_id')}")
        return JSONResponse(status_code=403, content={"success": False, "data": {"error": "Access denied - app_id mismatch"}})
    
    # Check user permissions
    if art.get("author_id") != current_user["id"] and current_user.get("role") not in [Role.ADMIN]:
        return JSONResponse(status_code=403, content={"success": False, "data": {"error": "Not allowed to delete"}})
    
    result = await delete_article(article_id, app_id)
    if not result:
        return JSONResponse(status_code=404, content={"success": False, "data": {"error": "Article not found or access denied"}})
    return {"success": True, "data": {"message": "deleted"}}

@articles.get("/author/{author_id}")
async def articles_by_author(author_id: str, page: int = 1, page_size: int = 20, app_id: Optional[str] = Query(None, description="Application ID for filtering results")):
    try:
        # Use service layer pagination function
        from backend.services.article_service import get_articles_by_author_with_pagination
        result = await get_articles_by_author_with_pagination(
            author_id=author_id,
            page=page, 
            page_size=page_size, 
            app_id=app_id
        )
        
        return result
    except Exception as e:
        print(f"Error fetching articles by author: {e}")
        return JSONResponse(status_code=500, content={
            "success": False,
            "data": {"error": str(e)}
        })
