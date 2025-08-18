import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from typing import Optional

from numpy import imag
from backend.services.azure_blob_service import upload_image
from backend.model.request.response_ai import ResponseFromAI
from backend.enum.roles import Role
from backend.utils import get_current_user, require_owner_or_role, require_role
from backend.services.article_service import (
    create_article, delete_article, get_article_by_id, increment_article_views, 
    list_articles, search_response, update_article, 
    get_articles_by_author, get_popular_articles, get_recent_articles
)


load_dotenv()
BASE_URL = os.getenv("BASE_URL")

articles = APIRouter(prefix="/api/articles", tags=["articles"])


@articles.post("/")
async def create(
    title: str = Form(...),
    abstract: str = Form(...),
    content: str = Form(...),
    tags: Optional[str] = Form(None),
    image: UploadFile = File(None),
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
        "abstract": abstract
    }
    if image:
        image_url = upload_image(image.file)
        doc["image"] = image_url
    art = await create_article(doc)
    return art
    # return Article(
    #     id=art["id"],
    #     title=art["title"],
    #     content=art["content"],
    #     abstract=art.get("abstract"),
    #     status=art.get("status"),
    #     tags=art.get("tags", []),
    #     image=art.get("image"),
    #     author_id=art.get("author_id"),
    #     author_name=art.get("author_name"),
    #     likes=art.get("likes", 0),
    #     dislike=art.get("dislike", 0),
    #     views=art.get("views", 0),
    #     created_at=art.get("created_at"),
    #     updated_at=art.get("updated_at")
    # )

@articles.get("/")
async def list_all(page: int = 1, page_size: int = 20):
    return await list_articles(page=page, page_size=page_size)

@articles.get("/{article_id}")
async def get_one(article_id: str):
    art = await get_article_by_id(article_id)
    if not art:
        raise HTTPException(status_code=404, detail="Article not found")
    return art

@articles.put("/{article_id}")
async def update(
    article_id: str,
    title: Optional[str] = Form(None),
    abstract: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    image: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    art = await get_article_by_id(article_id)
    if not art:
        raise HTTPException(status_code=404, detail="Article not found")
    if art.get("author_id") != current_user["id"] and current_user.get("role") not in [ Role.ADMIN]:
        raise HTTPException(status_code=403, detail="Not allowed to update")
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
        image_url = upload_image(image.file)
        update_data["image"] = image_url
    updated = await update_article(article_id, update_data)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")
    return updated

@articles.delete("/{article_id}")
async def remove(article_id: str, current_user: dict = Depends(get_current_user)):
    art = await get_article_by_id(article_id)
    if not art:
        raise HTTPException(status_code=404, detail="Article not found")
    if art.get("author_id") != current_user["id"] and current_user.get("role") not in [ Role.ADMIN]:
        raise HTTPException(status_code=403, detail="Not allowed to delete")
    await delete_article(article_id)
    return {"detail": "deleted"}

# @articles.get("/view/{article_id}")
# async def view_article(article_id: str):
#     await increment_article_views(article_id)
#     return {"detail": "Article views incremented"}

# @articles.post("/{article_id}/like")
# async def like_article(article_id: str, current_user: dict = Depends(get_current_user)):
#     art = await get_article_by_id(article_id)
#     if not art:
#         raise HTTPException(status_code=404, detail="Article not found")
    
#     from backend.services.article_service import like_article as like_article_service
#     result = await like_article_service(article_id, str(current_user["_id"]))
    
#     if result:
#         return {"detail": "Article liked successfully"}
#     else:
#         raise HTTPException(status_code=400, detail="Unable to like article")

# @articles.post("/{article_id}/dislike")
# async def dislike_article(article_id: str, current_user: dict = Depends(get_current_user)):
#     art = await get_article_by_id(article_id)
#     if not art:
#         raise HTTPException(status_code=404, detail="Article not found")
    
#     # Update dislikes in database (implement in article_service)
#     from backend.services.article_service import dislike_article as dislike_article_service
#     result = await dislike_article_service(article_id, str(current_user["_id"]))
    
#     if result:
#         return {"detail": "Article disliked successfully"}
#     else:
#         raise HTTPException(status_code=400, detail="Unable to dislike article")

@articles.get("/author/{author_id}")
async def articles_by_author(author_id: str, page: int = 1, page_size: int = 20):
    return await get_articles_by_author(author_id, page, page_size)

@articles.get("/popular")
async def home_popular_articles(page: int = 1, page_size: int = 10):
    return await get_popular_articles(page, page_size)

@articles.get("/recent")
async def home_recent_articles(page: int = 1, page_size: int = 10):
    return await get_recent_articles(page, page_size)

@articles.get("/search/search_response")
async def search_article_response(data: ResponseFromAI):
    return await search_response(data)

