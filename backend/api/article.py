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
    list_articles,
    update_article,
    delete_article,
    get_popular_articles,
    get_articles_by_author,
    increment_article_views
)
from backend.services.tag_service import tag_service
from backend.services.cache_service import get_cache, set_cache, CACHE_TTL
from backend.services.search_service import search_service
from backend.services.recommendation_service import get_recommendation_service
from backend.database.cosmos import get_articles_container

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
    art = await create_article(doc)
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
        
        # Get articles from service (returns List[dict])
        articles_data = await list_articles(page=current_page, page_size=current_page_size, app_id=app_id)
        
        # articles_data is already list of dicts
        articles_dict = articles_data
        
        # Calculate total pages - get total count from database
        from backend.services.article_service import get_total_articles_count
        total_items = await get_total_articles_count(app_id=app_id)
        total_pages = (total_items + current_page_size - 1) // current_page_size  # Ceiling division
        
        # Return in expected format
        result = {
            "success": True,
            "data": articles_dict,
            "pagination": {
                "page": current_page,
                "page_size": current_page_size,
                "total": total_pages,  # total pages
                "total_results": total_items  # total result count
            }
        }
        
        
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
        # Get popular articles (returns List[dict])
        popular = await get_popular_articles(page, page_size, app_id=app_id)
        # popular is already list of dicts
        popular_dict = popular
        
        # Calculate total pages for popular articles
        from backend.services.article_service import get_total_articles_count
        total_items = await get_total_articles_count(app_id=app_id)
        total_pages = (total_items + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": popular_dict,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_pages,  # total pages
                "total_results": total_items  # total result count
            }
        }
    except Exception as e:
        print(f"Error fetching popular articles: {e}")
        return {"success": False, "data": {"error": "Failed to fetch statistics"}}

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
async def get_statistics():
    """Get statistics for articles, authors, views, and bookmarks."""
    # Check Redis cache first
    cache_key = "homepage:statistics"
    cached_stats = await get_cache(cache_key)
    if cached_stats:
        print("📊 Redis Cache HIT for statistics")
        return {"success": True, "data": cached_stats}
    
    print("📊 Redis Cache MISS for statistics - Loading from DB...")
    try:
        # Try to get data from Cosmos DB first
        try:
            articles_container = await get_articles_container()

            # Iterate across all articles and compute aggregates in code to avoid
            # unsupported server-side DISTINCT/count aggregation across partitions.
            total_articles = 0
            total_views = 0
            author_ids = set()

            async for item in articles_container.read_all_items():
                try:
                    if not item or not item.get('is_active'):
                        continue
                    total_articles += 1
                    try:
                        total_views += int(item.get('views', 0) or 0)
                    except Exception:
                        # skip malformed view values
                        pass
                    aid = item.get('author_id')
                    if aid:
                        author_ids.add(aid)
                except Exception:
                    # ignore malformed documents
                    continue

            total_authors = len(author_ids)

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
        
        stats_data = {
            "articles": total_articles,
            "authors": total_authors,
            "total_views": total_views,
            "bookmarks": total_bookmarks
        }
        
        # Cache the results for 3 minutes (180 seconds)
        await set_cache(cache_key, stats_data, ttl=180)
        print("📊 Redis Cache SET for statistics")
        
        return {
            "success": True,
            "data": stats_data
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
    # Check Redis cache first
    cache_key = f"homepage:categories:app_{app_id or 'none'}"
    cached_categories = await get_cache(cache_key)
    if cached_categories:
        print("🏷️ Redis Cache HIT for categories")
        return {"success": True, "data": cached_categories}
    
    print("🏷️ Redis Cache MISS for categories - Loading from DB...")
    try:
        # Try to get data from Cosmos DB first
        try:
            articles_container = await get_articles_container()
            
            # Cosmos DB does not support GROUP BY across partitioned arrays in the SDK easily.
            # We'll read items and aggregate tag counts client-side. Use read_all_items
            # to iterate across partitions without passing unsupported kwargs.
            categories_result = []
            from collections import Counter
            tag_counter = Counter()

            # iterate over all articles and accumulate tags (filter client-side)
            async for item in articles_container.read_all_items():
                try:
                    if not item or not item.get('is_active'):
                        continue
                    # Filter by app_id if provided
                    if app_id and item.get('app_id') != app_id:
                        continue
                    tags = item.get('tags') or []
                    for t in tags:
                        tag_counter[t] += 1
                except Exception:
                    # ignore malformed documents
                    continue

            # prepare top categories (limit to top 10)
            for tag, count in tag_counter.most_common(10):
                categories_result.append({"name": tag, "count": count})
            
        except Exception as db_error:
            print(f"Cosmos DB connection failed, using sample data in the ai_search/data/articles.json for categories: {db_error}")
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
                    # Filter by app_id if provided
                    if app_id and article.get('app_id') != app_id:
                        continue
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
        
        # Cache the results for 3 minutes (180 seconds)
        await set_cache(cache_key, categories_result, ttl=180)
        print("🏷️ Redis Cache SET for categories")
        
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
        articles_container = await get_articles_container()
        
        # Query articles that have the specified category in their tags
        if app_id:
            query = """
            SELECT * FROM c 
            WHERE c.is_active = true 
            AND ARRAY_CONTAINS(c.tags, @category)
            AND c.app_id = @app_id
            ORDER BY c.created_at DESC
            OFFSET @skip LIMIT @limit
            """
        else:
            query = """
            SELECT * FROM c 
            WHERE c.is_active = true 
            AND ARRAY_CONTAINS(c.tags, @category)
            ORDER BY c.created_at DESC
            OFFSET @skip LIMIT @limit
            """
        
        skip = (page - 1) * limit
        parameters = [
            {"name": "@category", "value": category_name},
            {"name": "@skip", "value": skip},
            {"name": "@limit", "value": limit}
        ]
        if app_id:
            parameters.append({"name": "@app_id", "value": app_id})
        
        results = []
        async for doc in articles_container.query_items(query=query, parameters=parameters):
            results.append(doc)
        
        # Calculate total pages for category
        # First get total count for this category
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'published'"
        if category_name != "all":
            count_query += " AND ARRAY_CONTAINS(c.tags, @category)"
        if app_id:
            count_query += " AND c.app_id = @app_id"
        
        count_parameters = []
        if category_name != "all":
            count_parameters.append({"name": "@category", "value": category_name})
        if app_id:
            count_parameters.append({"name": "@app_id", "value": app_id})
        
        total_items = 0
        async for count in articles_container.query_items(query=count_query, parameters=count_parameters):
            total_items = count
            break
        
        total_pages = (total_items + limit - 1) // limit
        
        return {
            "success": True,
            "data": results,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_pages,  # total pages
                "total_results": total_items  # total result count
            }
        }
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
        art = await get_article_by_id(article_id, app_id)
        if not art:
            return JSONResponse(status_code=404, content={"success": False, "data": None})
        
        await increment_article_views(article_id)
        
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
    updated = await update_article(article_id, update_data)
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
    
    await delete_article(article_id)
    return {"success": True, "data": {"message": "deleted"}}

@articles.get("/author/{author_id}")
async def articles_by_author(author_id: str, page: int = 1, page_size: int = 20, app_id: Optional[str] = Query(None, description="Application ID for filtering results")):
    # Check Redis cache first
    cache_key = f"articles:author:{author_id}:page_{page}_size_{page_size}:app_{app_id or 'none'}"
    cached_articles = await get_cache(cache_key)
    if cached_articles:
        print(f"✍️ Redis Cache HIT for author {author_id} articles")
        return cached_articles
    
    print(f"✍️ Redis Cache MISS for author {author_id} articles - Loading from DB...")
    # Get articles by author (returns List[dict])
    articles_list = await get_articles_by_author(author_id, page - 1, page_size, app_id=app_id)
    # articles_list is already list of dicts
    articles_dict = articles_list
    
    # Calculate total pages for this author
    from backend.services.article_service import get_total_articles_count_by_author
    total_items = await get_total_articles_count_by_author(author_id, app_id=app_id)
    total_pages = (total_items + page_size - 1) // page_size
    
    result = {
        "success": True,
        "data": articles_dict,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_pages,  # total pages
            "total_results": total_items  # total result count
        }
    }
    
    # Cache the results for 3 minutes (180 seconds)
    await set_cache(cache_key, result, ttl=180)
    print(f"✍️ Redis Cache SET for author {author_id} articles")
    
    return result
