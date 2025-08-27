"""Business logic for articles.

This module implements higher-level operations used by the API
handlers. It coordinates cache lookups, repository calls and related
side effects (e.g. clearing cache, notifying user services). The
expected flow for an incoming request is:

- API route (backend/api/*) -> calls a function here
- functions here call repository functions in backend/repositories/*
- this module handles caching, pagination, scoring etc.

No direct DB access happens here; use the repository layer.
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid
from backend.model.dto.article_dto import AuthorDTO
from backend.repositories import article_repo
from backend.services import user_service
from backend.services.cache_service import (
    get_cache, set_cache, delete_cache_pattern, 
    CACHE_KEYS, CACHE_TTL, generate_cache_key
)

async def _convert_to_author_dto(article: dict) -> AuthorDTO:
    """Convert article author data to AuthorDTO"""
    author_id = article.get("author_id", "")
    author_name = article.get("author_name", "")
    
    # For now, just return basic info without avatar to avoid performance issues
    # In production, you might want to batch fetch avatars or cache them
    return AuthorDTO(
        id=author_id,
        name=author_name,
        avatar_url=None  # Will be optimized later
    )

async def _convert_to_author_dto_with_avatar(article: dict) -> AuthorDTO:
    """Convert article author data to AuthorDTO with avatar lookup"""
    author_id = article.get("author_id", "")
    author_name = article.get("author_name", "")
    
    # Try to get avatar from user service for detail view
    author_avatar = None
    try:
        from backend.services.user_service import get_user_by_id
        user_info = await get_user_by_id(author_id)
        if user_info and hasattr(user_info, 'avatar_url'):
            author_avatar = user_info.avatar_url
    except Exception:
        # If we can't get user info, just use None
        pass
    
    return AuthorDTO(
        id=author_id,
        name=author_name,
        avatar_url=author_avatar
    )

async def _convert_to_article_dto(article: dict) -> dict:
    """Convert article data to dict following ArticleDTO structure"""
    author_dto = await _convert_to_author_dto(article)
    
    return {
        "article_id": article.get("id", ""),
        "title": article.get("title", ""),
        "abstract": article.get("abstract"),
        "image": article.get("image"),
        "tags": article.get("tags", []),
        "author": author_dto.model_dump(),  # Convert to dict
        "created_date": article.get("created_at"),
        "total_like": article.get("likes", 0),
        "total_view": article.get("views", 0)
    }

async def _convert_to_article_detail_dto(article: dict) -> dict:
    """Convert article data to dict following ArticleDetailDTO structure"""
    author_dto = await _convert_to_author_dto_with_avatar(article)
    
    # Get recommended article IDs from database
    recommended_ids = []
    recommended_dtos = []
    
    # If no recommendations exist, generate them
    try:
        from backend.services.recommendation_service import get_recommendation_service
                    
        article_id = article.get("id", "")
        recommendation_service = get_recommendation_service()
                    
        print(f"🔄 No recommendations found for article {article_id}, generating new ones...")
                    
        # Get recommendations using recommendation service
        recommendations, was_refreshed = await recommendation_service.get_article_recommendations(article_id)
                    
        if recommendations and was_refreshed:
            # Extract just the article IDs from recommendations
            recommended_ids = [rec.get("article_id") for rec in recommendations if rec.get("article_id")]
            print(f"✅ Generated {len(recommended_ids)} recommendations for article {article_id}")
        else:
            recommended_ids = []
                    
    except Exception as e:
        print(f"⚠️ Failed to generate recommendations for article {article.get('id', '')}: {e}")
        # Continue without recommendations rather than failing
        recommended_ids = []
    
    # Convert recommended article IDs to ArticleDTO objects
    if recommended_ids:
        try:
            for rec_id in recommended_ids:
                rec_article = await article_repo.get_article_by_id(rec_id)
                if rec_article:
                    rec_dto = await _convert_to_article_dto(rec_article)
                    recommended_dtos.append(rec_dto)  # rec_dto is already a dict now
        except Exception as e:
            print(f"⚠️ Failed to fetch recommended articles: {e}")
            recommended_dtos = []
    
    return {
        "id": article.get("id", ""),
        "title": article.get("title", ""),
        "content": article.get("content", ""),
        "abstract": article.get("abstract"),
        "status": article.get("status", ""),
        "tags": article.get("tags", []),
        "image": article.get("image"),
        "author": author_dto.model_dump(),  # Convert to dict
        "created_date": article.get("created_at"),
        "updated_date": article.get("updated_at"),
        "total_like": article.get("likes", 0),
        "total_view": article.get("views", 0),
        "total_dislike": article.get("dislikes", 0),
        "recommended": recommended_dtos if recommended_dtos else None
    }

async def create_article(doc: dict) -> dict:
    # prepare fields expected by repository/db
    now = datetime.utcnow().isoformat()
    doc["created_at"] = now
    doc["updated_at"] = now  # For new articles, updated_at = created_at
    doc["id"] = uuid.uuid4().hex
    doc["is_active"] = True
    doc.setdefault("likes", 0)
    doc.setdefault("dislikes", 0)
    doc.setdefault("views", 0)
    
    print(f"📝 Creating new article with created_at = updated_at = {now}")

    # persist via repository layer
    inserted_id = await article_repo.insert_article(doc)
    art = await article_repo.get_article_by_id(inserted_id)
    
    # Invalidate caches that list articles so the home/recent pages
    # reflect the newly created item.
    await delete_cache_pattern("articles:home*")
    await delete_cache_pattern("articles:recent*")
    
    # Convert to dict before returning
    return await _convert_to_article_detail_dto(art)

async def get_article_by_id(article_id: str) -> Optional[dict]:
    """
    Get article by ID with optional automatic recommendations generation.
    
    Args:
        article_id: The article ID to fetch
    
    Returns:
        Dict following ArticleDetailDTO structure with recommended field (list of article data)
    """
    # Try to get from cache first (without recommendations for now)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    cached_article = await get_cache(cache_key)
    
    article = None
    if cached_article:
        return cached_article
    else:
        # Get fresh article data
        article = await article_repo.get_article_by_id(article_id)
    
    if article:
        article_dict = await _convert_to_article_detail_dto(article)
        
        # Cache the dict data
        await set_cache(cache_key, article_dict, CACHE_TTL["detail"])
        
        return article_dict
    
    return None

async def update_article(article_id: str, update_doc: dict) -> Optional[dict]:
    # Only add updated_at if it's not a recommendations-only update
    if not (set(update_doc.keys()) <= {'recommended', 'recommended_time'}):
        update_doc["updated_at"] = datetime.utcnow().isoformat()
    
    print(f"📝 Article service updating article {article_id}")
    print(f"🔑 Update fields: {list(update_doc.keys())}")
    
    updated_article = await article_repo.update_article(article_id, update_doc)
    
    # Clear caches to ensure fresh data
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)
    await delete_cache_pattern("articles:home*")
    await delete_cache_pattern("articles:recent*")
    
    print(f"🗑️ Cleared caches for article {article_id}")
    
    # Convert to dict before returning
    if updated_article:
        return await _convert_to_article_detail_dto(updated_article)
    return None

async def delete_article(article_id: str):
    await article_repo.delete_article(article_id)
    await user_service.delete_reaction(article_id)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)
    await delete_cache_pattern("articles:home*")
    await delete_cache_pattern("articles:recent*")

async def list_articles(page: int, page_size: int, app_id: Optional[str] = None) -> List[dict]:
    cache_key = generate_cache_key(CACHE_KEYS["articles_home"], page=page, page_size=page_size, app_id=app_id or 'none')
    
    cached_articles = await get_cache(cache_key)
    if cached_articles:
        print(f"📋 Cache HIT for home articles page {page}")
        # Return cached dict data directly
        return cached_articles
    
    print(f"💾 Cache MISS for home articles page {page}")
    result = await article_repo.list_articles(page, page_size, app_id=app_id)
    
    # Extract the actual articles from the repository response
    articles = result.get("items", []) if isinstance(result, dict) else result
    
    if articles:
        # Convert to dicts
        article_dicts = [await _convert_to_article_dto(article) for article in articles]
        # Cache the dicts
        await set_cache(cache_key, article_dicts, CACHE_TTL["home"])
        return article_dicts
    
    return []
    
async def increment_article_views(article_id: str):
    await article_repo.increment_article_views(article_id)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)

async def increment_article_dislikes(article_id: str):
    await article_repo.increment_article_dislikes(article_id)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)

async def increment_article_likes(article_id: str):
    await article_repo.increment_article_likes(article_id)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)

async def decrement_article_likes(article_id: str):
    await article_repo.decrement_article_likes(article_id)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)

async def decrement_article_dislikes(article_id: str):
    await article_repo.decrement_article_dislikes(article_id)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)

# async def like_article(article_id: str, user_id: str) -> bool:
#     """Like an article. Returns True if successful, False if already liked."""
#     try:
#         # Check if user already liked this article
#         # existing_like = await article_repo.get_user_article_reaction(article_id, user_id, "like")
#         # if existing_like:
#         #     return False  # Already liked
        
#         # # Remove any existing dislike first
#         # await article_repo.remove_user_article_reaction(article_id, user_id, "dislike")
        
#         # # Add like
#         # await article_repo.add_user_article_reaction(article_id, user_id, "like")
#         await article_repo.increment_article_likes(article_id)
        
#         # Clear cache for article detail and popular articles
#         cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
#         await delete_cache_pattern(cache_key)
#         await delete_cache_pattern("articles:popular*")
        
#         return True
#     except Exception:
#         return False

# async def dislike_article(article_id: str, user_id: str) -> bool:
#     """Dislike an article. Returns True if successful, False if already disliked."""
#     try:
#         # Check if user already disliked this article
#         # existing_dislike = await article_repo.get_user_article_reaction(article_id, user_id, "dislike")
#         # if existing_dislike:
#         #     return False  # Already disliked
        
#         # # Remove any existing like first
#         # await article_repo.remove_user_article_reaction(article_id, user_id, "like")
        
#         # # Add dislike
#         # await article_repo.add_user_article_reaction(article_id, user_id, "dislike")
#         await article_repo.increment_article_dislikes(article_id)
        
#         # Clear cache for article detail
#         cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
#         await delete_cache_pattern(cache_key)
        
#         return True
#     except Exception:
#         return False

async def get_articles_by_author(author_id: str, page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> List[dict]:
    cache_key = generate_cache_key(CACHE_KEYS["user_articles"], user_id=author_id, page=page, page_size=page_size, app_id=app_id or 'none')
    
    cached_articles = await get_cache(cache_key)
    if cached_articles:
        # Return cached dict data directly
        return cached_articles
    
    articles = await article_repo.get_article_by_author(author_id, page, page_size, app_id=app_id)
    
    if articles:
        # Convert to dicts
        article_dicts = [await _convert_to_article_dto(article) for article in articles]
        # Cache the dicts
        await set_cache(cache_key, article_dicts, CACHE_TTL["user_articles"])
        return article_dicts
    
    return []

async def get_popular_articles(page: int = 1, page_size: int = 10, app_id: Optional[str] = None) -> List[dict]:
    cache_key = generate_cache_key(CACHE_KEYS["articles_popular"], page=page, page_size=page_size, app_id=app_id or 'none')
    
    cached_articles = await get_cache(cache_key)
    if cached_articles:
        # Return cached dict data directly
        return cached_articles
    
    try:
        # Get articles from repository
        articles_data = await article_repo.list_articles(page=1, page_size=page_size * 3, app_id=app_id)  # Get more for sorting
        
        # Handle different return formats from repository
        if isinstance(articles_data, dict):
            articles = articles_data.get("items", [])
        elif isinstance(articles_data, list):
            articles = articles_data
        else:
            return []
        
        if not articles:
            return []
        
        print(f"📄 Found {len(articles)} articles for popularity calculation")
        
        # Calculate popularity score with time decay
        now = datetime.utcnow()
        
        for article in articles:
            # Ensure article has required fields
            article.setdefault("likes", 0)
            article.setdefault("views", 0)
            
            # Get article creation date
            created_at = article.get("created_at")
            if isinstance(created_at, str):
                try:
                    # Handle different datetime formats
                    if created_at.endswith('Z'):
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        created_date = datetime.fromisoformat(created_at)
                except Exception as e:
                    print(f"⚠️ Error parsing date {created_at}: {e}")
                    created_date = now  # Fallback to now if parsing fails
            else:
                created_date = now
            
            # Calculate days since creation
            days_old = (now - created_date).days
            
            # Time decay factor: newer articles get higher scores
            # Articles lose 5% popularity per day, minimum 10% after 30 days
            time_factor = max(0.1, 0.95 ** days_old)
            
            # Base popularity score
            likes = int(article.get("likes", 0))
            views = int(article.get("views", 0))
            base_score = likes * 3 + views  # Likes worth 3x views
            
            # Apply time decay
            popularity_score = base_score * time_factor
            article["popularity_score"] = popularity_score
            
        
        # Sort by popularity score (with time decay)
        articles.sort(key=lambda x: x.get("popularity_score", 0), reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        result = articles[start_idx:end_idx]
        
        # Remove popularity_score from final result (internal use only)
        for article in result:
            article.pop("popularity_score", None)
        
        # Convert to dicts
        article_dicts = [await _convert_to_article_dto(article) for article in result]
        
        # Cache the dicts
        await set_cache(cache_key, article_dicts, CACHE_TTL["popular"])
        
        return article_dicts
        
    except Exception as e:
        print(f"❌ Error in get_popular_articles: {e}")
        return []

async def search_response_articles(data: Dict) -> List[dict]:
    article_ids = [article["id"] for article in data.get("results", [])]
    articles = await article_repo.get_articles_by_ids(article_ids)
    # Convert to dicts
    return [await _convert_to_article_dto(article) for article in articles]


async def get_summary() -> Dict:
    """Aggregate basic articles summary for dashboards.

    Note: For simplicity we fetch up to 1000 most recent articles.
    """
    try:
        data = await article_repo.list_articles(page=1, page_size=1000)
        items = data.get("items", []) if isinstance(data, dict) else data
        total = len(items)
        published = len([a for a in items if a.get("status") == "published"])
        drafts = len([a for a in items if a.get("status") == "draft"])
        total_views = sum(int(a.get("views", 0)) for a in items)
        total_likes = sum(int(a.get("likes", 0)) for a in items)
        authors = len({a.get("author_id") for a in items if a.get("author_id")})
        return {
            "total_articles": total,
            "published_articles": published,
            "draft_articles": drafts,
            "total_views": total_views,
            "total_likes": total_likes,
            "authors": authors,
        }
    except Exception:
        return {
            "total_articles": 0,
            "published_articles": 0,
            "draft_articles": 0,
            "total_views": 0,
            "total_likes": 0,
            "authors": 0,
        }

async def get_total_articles_count(app_id: Optional[str] = None):
    """Get total count of published articles."""
    try:
        from backend.database.cosmos import get_articles_container
        articles_container = await get_articles_container()
        
        if app_id:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'published' AND c.app_id = @app_id"
            parameters = [{"name": "@app_id", "value": app_id}]
        else:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'published'"
            parameters = []
            
        async for count in articles_container.query_items(query=query, parameters=parameters):
            return count
        return 0
    except Exception:
        return 0

async def get_total_articles_count_by_author(author_id: str, app_id: Optional[str] = None):
    """Get total count of published articles by specific author."""
    try:
        from backend.database.cosmos import get_articles_container
        articles_container = await get_articles_container()
        
        if app_id:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'published' AND c.author_id = @author_id AND c.app_id = @app_id"
            parameters = [{"name": "@author_id", "value": author_id}, {"name": "@app_id", "value": app_id}]
        else:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'published' AND c.author_id = @author_id"
            parameters = [{"name": "@author_id", "value": author_id}]
        
        async for count in articles_container.query_items(query=query, parameters=parameters):
            return count
        return 0
    except Exception:
        return 0