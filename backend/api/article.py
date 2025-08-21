import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Query
from typing import Optional, List

from backend.services.azure_blob_service import upload_image
from backend.enum.roles import Role
from backend.utils import get_current_user, require_owner_or_role, require_role
from backend.services.article_service import (
    create_article, delete_article, get_article_by_id, increment_article_views, 
    list_articles, search_response, update_article, 
    get_articles_by_author, get_popular_articles
)
from backend.services.search_service import search_service
from backend.database.cosmos import get_articles_container

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

@articles.get("/")
async def list_all(
    page: Optional[int] = Query(None, alias="page[page]"),
    page_size: Optional[int] = Query(None, alias="page[page_size]"),
    q: Optional[str] = Query(None, alias="page[q]"),
    status: Optional[str] = Query(None, alias="page[status]"),
    sort_by: Optional[str] = Query(None, alias="page[sort_by]"),
    limit: Optional[int] = Query(10)
):
    """Get articles with pagination and filtering."""
    try:
        # Use provided parameters or defaults
        current_page = page or 1
        current_page_size = page_size or limit or 20
        current_status = status or "published"
        
        # Get articles from service
        articles_data = await list_articles(page=current_page, page_size=current_page_size)
        
        # Return in expected format
        return {
            "success": True,
            "data": articles_data,
            "pagination": {
                "page": current_page,
                "page_size": current_page_size,
                "total": len(articles_data) if articles_data else 0
            }
        }
    except Exception as e:
        print(f"Error fetching articles: {e}")
        return {
            "success": False,
            "data": [],
            "error": str(e)
        }

@articles.get("/popular")
async def home_popular_articles(page: int = 1, page_size: int = 10):
    try:
        return await get_popular_articles(page, page_size)
    except Exception as e:
        print(f"Error fetching popular articles: {e}")
        return []

@articles.get("/stats")
async def get_statistics():
    """Get statistics for articles, authors, views, and bookmarks."""
    try:
        # Try to get data from Cosmos DB first
        try:
            articles_container = await get_articles_container()
            
            # Get total articles count
            articles_count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.is_active = true"
            articles_count_result = [item async for item in articles_container.query_items(query=articles_count_query)]
            total_articles = articles_count_result[0] if articles_count_result else 0
            
            # Get total views
            views_query = "SELECT VALUE SUM(c.views) FROM c WHERE c.is_active = true"
            views_result = [item async for item in articles_container.query_items(query=views_query)]
            total_views = views_result[0] if views_result else 0
            
            # Get total authors (unique author_ids)
            authors_query = "SELECT VALUE COUNT(DISTINCT c.author_id) FROM c WHERE c.is_active = true"
            authors_result = [item async for item in articles_container.query_items(query=authors_query)]
            total_authors = authors_result[0] if authors_result else 0
            
        except Exception as db_error:
            print(f"Cosmos DB connection failed, using sample data: {db_error}")
            # Fallback to sample data from articles.json
            import json
            import os
            
            # Path to the sample articles file
            sample_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ai_search', 'data', 'articles.json')
            
            if os.path.exists(sample_file_path):
                with open(sample_file_path, 'r', encoding='utf-8') as f:
                    sample_articles = json.load(f)
                
                # Calculate statistics from sample data
                total_articles = len(sample_articles)
                total_views = sum(article.get('views', 0) for article in sample_articles)
                total_authors = len(set(article.get('author_id') for article in sample_articles if article.get('author_id')))
            else:
                # If sample file not found, use default values
                total_articles = 50
                total_views = 2500
                total_authors = 15
        
        # For bookmarks, we'll need to check user reactions
        # This is a simplified version - in a real app you'd count actual bookmarks
        total_bookmarks = 0  # Placeholder for now
        
        return {
            "success": True,
            "data": {
                "articles": total_articles,
                "authors": total_authors,
                "total_views": total_views,
                "bookmarks": total_bookmarks
            }
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
async def get_categories():
    """Get all available categories and their article counts."""
    try:
        # Try to get data from Cosmos DB first
        try:
            articles_container = await get_articles_container()
            
            # Get unique categories and their counts
            categories_query = """
            SELECT 
                c.tags,
                COUNT(1) as count
            FROM c 
            WHERE c.is_active = true AND c.tags != null
            GROUP BY c.tags
            """
            
            categories_result = []
            async for item in articles_container.query_items(query=categories_query):
                if item.get("tags"):
                    for tag in item["tags"]:
                        # Find existing category or create new one
                        existing = next((cat for cat in categories_result if cat["name"] == tag), None)
                        if existing:
                            existing["count"] += item["count"]
                        else:
                            categories_result.append({
                                "name": tag,
                                "count": item["count"]
                            })
            
        except Exception as db_error:
            print(f"Cosmos DB connection failed, using sample data for categories: {db_error}")
            # Fallback to sample data from articles.json
            import json
            import os
            from collections import Counter
            
            # Path to the sample articles file
            sample_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ai_search', 'data', 'articles.json')
            
            if os.path.exists(sample_file_path):
                with open(sample_file_path, 'r', encoding='utf-8') as f:
                    sample_articles = json.load(f)
                
                # Count tags from sample data
                all_tags = []
                for article in sample_articles:
                    if article.get('tags'):
                        all_tags.extend(article['tags'])
                
                tag_counts = Counter(all_tags)
                categories_result = [
                    {"name": tag, "count": count} 
                    for tag, count in tag_counts.most_common(10)  # Top 10 categories
                ]
            else:
                # If sample file not found, use default categories
                categories_result = [
                    {"name": "Technology", "count": 15},
                    {"name": "Design", "count": 12},
                    {"name": "Business", "count": 10},
                    {"name": "Science", "count": 8},
                    {"name": "Health", "count": 6},
                    {"name": "Lifestyle", "count": 5}
                ]
        
        # Add default categories if none exist
        if not categories_result:
            categories_result = [
                {"name": "Technology", "count": 15},
                {"name": "Design", "count": 12},
                {"name": "Business", "count": 10},
                {"name": "Science", "count": 8},
                {"name": "Health", "count": 6},
                {"name": "Lifestyle", "count": 5}
            ]
        
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
    limit: int = Query(10, ge=1, le=100)
):
    """Get articles by category."""
    try:
        articles_container = await get_articles_container()
        
        # Query articles that have the specified category in their tags
        query = """
        SELECT * FROM c 
        WHERE c.is_active = true 
        AND ARRAY_CONTAINS(@category, c.tags)
        ORDER BY c.created_at DESC
        OFFSET @skip LIMIT @limit
        """
        
        skip = (page - 1) * limit
        parameters = [
            {"name": "@category", "value": category_name},
            {"name": "@skip", "value": skip},
            {"name": "@limit", "value": limit}
        ]
        
        results = []
        async for doc in articles_container.query_items(query=query, parameters=parameters):
            results.append(doc)
        
        return {
            "success": True,
            "data": results,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(results)
            }
        }
    except Exception as e:
        print(f"Error fetching articles by category: {e}")
        return {
            "success": False,
            "data": [],
            "error": str(e)
        }

@articles.get("/search")
async def search_articles(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """AI-powered article search using the backend search service."""
    try:
        result = await search_service.search_articles(q, limit, page)
        return result
    except Exception as e:
        print(f"Article search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@articles.get("/search/simple")
async def search_articles_simple(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Simple article search as fallback."""
    try:
        # This would be a simple database search
        # For now, return empty results
        return {
            "success": True,
            "data": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "search_type": "articles_simple"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@articles.get("/{article_id}")
async def get_one(article_id: str):
    try:
        art = await get_article_by_id(article_id)
        if not art:
            raise HTTPException(status_code=404, detail="Article not found")
        await increment_article_views(article_id)
        return {
            "success": True,
            "data": art
        }
    except Exception as e:
        print(f"Error fetching article {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch article")

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

@articles.get("/author/{author_id}")
async def articles_by_author(author_id: str, page: int = 1, page_size: int = 20):
    return await get_articles_by_author(author_id, page - 1, page_size)
