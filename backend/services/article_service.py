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
from uuid import uuid4
import uuid
from backend.model.request.response_ai import ResponseFromAI
from backend.repositories import article_repo
from backend.services import user_service
from backend.services.cache_service import (
    get_cache, set_cache, delete_cache_pattern, 
    CACHE_KEYS, CACHE_TTL, generate_cache_key
)

async def create_article(doc: dict) -> dict:
    # prepare fields expected by repository/db
    now = datetime.utcnow().isoformat()
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["id"] = uuid.uuid4().hex
    doc["is_active"] = True
    doc.setdefault("likes", 0)
    doc.setdefault("dislikes", 0)
    doc.setdefault("views", 0)

    # persist via repository layer
    inserted_id = await article_repo.insert_article(doc)
    art = await article_repo.get_article_by_id(inserted_id)
    
    # Invalidate caches that list articles so the home/recent pages
    # reflect the newly created item.
    await delete_cache_pattern("articles:home*")
    await delete_cache_pattern("articles:recent*")
    
    return art

async def get_article_by_id(article_id: str) -> Optional[dict]:
    # Try to get from cache first
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    cached_article = await get_cache(cache_key)
    
    if cached_article:
        return cached_article
    
    article = await article_repo.get_article_by_id(article_id)
    if article:
        await set_cache(cache_key, article, CACHE_TTL["detail"])
    
    return article

async def update_article(article_id: str, update_doc: dict) -> Optional[dict]:
    update_doc["updated_at"] = datetime.utcnow().isoformat()
    await article_repo.update_article(article_id, update_doc)
    
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)
    await delete_cache_pattern("articles:home*")
    await delete_cache_pattern("articles:recent*")
    
    return await get_article_by_id(article_id)

async def delete_article(article_id: str):
    await article_repo.delete_article(article_id)
    await user_service.delete_reaction(article_id)
    cache_key = CACHE_KEYS["article_detail"].format(article_id=article_id)
    await delete_cache_pattern(cache_key)
    await delete_cache_pattern("articles:home*")
    await delete_cache_pattern("articles:recent*")

async def list_articles(page: int, page_size: int) -> List[dict]:
    cache_key = generate_cache_key(CACHE_KEYS["articles_home"], page=page, page_size=page_size)
    
    cached_articles = await get_cache(cache_key)
    if cached_articles:
        print(f"📋 Cache HIT for home articles page {page}")
        return cached_articles
    
    print(f"💾 Cache MISS for home articles page {page}")
    result = await article_repo.list_articles(page, page_size)
    
    # Extract the actual articles from the repository response
    articles = result.get("items", []) if isinstance(result, dict) else result
    
    if articles:
        # Cache the result
        await set_cache(cache_key, articles, CACHE_TTL["home"])
    
    return articles
    
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

async def get_articles_by_author(author_id: str, page: int = 1, page_size: int = 20) -> List[dict]:
    cache_key = generate_cache_key(CACHE_KEYS["user_articles"], user_id=author_id, page=page, page_size=page_size)
    
    cached_articles = await get_cache(cache_key)
    if cached_articles:
        return cached_articles
    
    articles = await article_repo.get_article_by_author(author_id, page, page_size)
    
    if articles:
        await set_cache(cache_key, articles, CACHE_TTL["user_articles"])
    
    return articles

async def get_popular_articles(page: int = 1, page_size: int = 10) -> List[dict]:
    cache_key = generate_cache_key(CACHE_KEYS["articles_popular"], page=page, page_size=page_size)
    
    cached_articles = await get_cache(cache_key)
    if cached_articles:
        return cached_articles
    
    try:
        # Get articles from repository
        articles_data = await article_repo.list_articles(page=1, page_size=page_size * 3)  # Get more for sorting
        
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
        
        # Cache the result
        await set_cache(cache_key, result, CACHE_TTL["popular"])
        
        return result
        
    except Exception as e:
        print(f"❌ Error in get_popular_articles: {e}")
        return []

async def search_response(data: Dict) -> List[dict]:
    article_ids = [article["id"] for article in data.get("results", [])]
    return await article_repo.get_articles_by_ids(article_ids)


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