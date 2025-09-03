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
import math
from backend.model.dto.article_dto import AuthorDTO
from backend.repositories import article_repo
from backend.services import user_service
from backend.services.cache_service import (
    get_cache, set_cache, delete_cache, delete_cache_pattern, 
    CACHE_KEYS, CACHE_TTL
)
from backend.services.text_preprocessing_service import (
    preprocess_article_text, should_regenerate_preprocessed_text
)

async def clear_affected_caches(
    operation: str,
    app_id: Optional[str] = None,
    article_id: Optional[str] = None,
    author_id: Optional[str] = None,
    updated_fields: Optional[List[str]] = None
):
    """
    Universal cache clearing function that intelligently clears only affected caches
    
    Operations:
    - "create": New article created → clear all listings, stats, categories, author
    - "delete": Article deleted → clear all listings, stats, categories, author
    - "update": Article updated → selective clearing based on updated_fields
    - "like": Article liked → clear detail, popular, stats, home listings
    - "unlike": Article unliked → clear detail, popular, stats, home listings
    - "dislike": Article disliked → clear detail, stats, home listings
    - "undislike": Article undisliked → clear detail, stats, home listings
    - "view": Article viewed → clear detail, popular, stats, home listings
    - "bookmark": Article bookmarked → clear user cache only (handled in user_service)
    - "unbookmark": Article unbookmarked → clear user cache only (handled in user_service)
    """
    
    print(f"🗑️ Cache clearing: {operation} (app_id: {app_id}, article_id: {article_id}, author_id: {author_id})")
    
    # Always clear article detail if article_id provided
    if article_id:
        await delete_cache(CACHE_KEYS["article_detail"], app_id=app_id, article_id=article_id)
    
    # Operation-specific cache clearing
    if operation == "create":
        # New article affects everything
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
        if author_id:
            author_pattern = CACHE_KEYS["articles_author"].format(author_id=author_id) + "*"
            await delete_cache_pattern(author_pattern, app_id=app_id)
    
    elif operation == "delete":
        # Article removal affects everything
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
        if author_id:
            author_pattern = CACHE_KEYS["articles_author"].format(author_id=author_id) + "*"
            await delete_cache_pattern(author_pattern, app_id=app_id)
    
    elif operation == "update" and updated_fields:
        fields_set = set(updated_fields)
        
        # Recommendations only - minimal impact
        if fields_set <= {'recommended', 'recommended_time'}:
            # Only article detail already cleared above
            pass
        
        # Status change affects visibility
        elif 'status' in fields_set:
            await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
            await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
            await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
            if author_id:
                author_pattern = CACHE_KEYS["articles_author"].format(author_id=author_id) + "*"
                await delete_cache_pattern(author_pattern, app_id=app_id)
        
        # Tags change affects categories
        elif 'tags' in fields_set:
            await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
            
        elif 'abstract' in fields_set:
            await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
            await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)

        # Content changes affect popularity
        elif any(field in fields_set for field in ['title', 'content', 'abstract', 'image']):
            await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        
        # Other minor changes - only detail cache cleared above
    
    elif operation in ["like", "unlike", "view"]:
        # Interactions that affect popularity AND main article listings (like counts shown in cards)
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
    
    elif operation in ["dislike", "undislike"]:
        # Interactions that affect stats AND main article listings (dislike counts shown in detail)
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
    
    elif operation in ["bookmark", "unbookmark"]:
        # Bookmark operations don't affect article stats but need to clear article lists where bookmark status might be shown
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        # Note: user cache clearing is handled in user_service for bookmark operations
    
    print(f"✅ Cache clearing completed for {operation}")

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
        "app_id": article.get("app_id", ""),
        "article_id": article.get("id", ""),
        "title": article.get("title", ""),
        "abstract": article.get("abstract"),
        "image": article.get("image"),
        "tags": article.get("tags", []),
        "status": article.get("status", "published"),  # Include status field
        "author": author_dto.model_dump(),  # Convert to dict
        "created_date": article.get("created_at"),
        "total_like": article.get("likes", 0),
        "total_view": article.get("views", 0)
    }

async def _convert_to_article_detail_dto(article: dict, recommended_dtos: Optional[List[dict]] = None, app_id: Optional[str] = None) -> dict:
    """Convert article data to dict following ArticleDetailDTO structure"""
    author_dto = await _convert_to_author_dto_with_avatar(article)
    
    return {
        "app_id": article.get("app_id", ""),
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
        "recommended": recommended_dtos if recommended_dtos else None,
        "recommended_time": article.get("recommended_time")
    }

async def create_article(doc: dict, app_id: Optional[str] = None) -> dict:
    # prepare fields expected by repository/db
    now = datetime.utcnow().isoformat()
    doc["created_at"] = now
    doc["updated_at"] = now  # For new articles, updated_at = created_at
    doc["id"] = uuid.uuid4().hex
    doc["is_active"] = True
    doc.setdefault("likes", 0)
    doc.setdefault("dislikes", 0)
    doc.setdefault("views", 0)
    
    # Set app_id if provided
    if app_id:
        doc["app_id"] = app_id
    
    # Generate preprocessed searchable text
    # NOTE: Commented out for preprocessing field removal
    # try:
    #     doc["preprocessed_searchable_text"] = preprocess_article_text(doc)
    #     print(f"✨ Generated preprocessed text for new article: {len(doc['preprocessed_searchable_text'])} characters")
    # except Exception as e:
    #     print(f"⚠️ Failed to generate preprocessed text for new article: {e}")
    #     doc["preprocessed_searchable_text"] = None
    
    print(f"📝 Creating new article with created_at = updated_at = {now}")

    # persist via repository layer
    inserted_id = await article_repo.insert_article(doc)
    art = await article_repo.get_article_by_id(inserted_id, app_id=app_id)
    
    # Clear affected caches
    await clear_affected_caches(
        operation="create",
        app_id=app_id,
        author_id=doc.get("author_id")
    )
    
    # Convert to dict before returning
    return await _convert_to_article_detail_dto(art, None, app_id=app_id)

async def get_article_by_id(article_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    return await article_repo.get_article_by_id(article_id, app_id=app_id)


async def get_article_detail(article_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    """
    Get article by ID with optional app_id filtering.
    
    Args:
        article_id: The article ID to fetch
        app_id: Optional application ID for filtering
    
    Returns:
        Dict following ArticleDetailDTO structure with recommended field (list of article data)
        Returns None if article not found or doesn't belong to specified app_id
    """
    # Try to get from cache first using new cache API
    cached_article = await get_cache(CACHE_KEYS["article_detail"], app_id=app_id, article_id=article_id)
    
    if cached_article:
        print(f"🔍 Cache HIT for article {article_id}:")
        print(f"   - Has recommended_time: {'recommended_time' in cached_article}")
        print(f"   - recommended_time value: {cached_article.get('recommended_time')}")
        print(f"   - Has recommended: {'recommended' in cached_article}")
        print(f"   - recommended count: {len(cached_article.get('recommended', []))}")
        return cached_article
    else:
        # Get fresh article data
        article = await article_repo.get_article_by_id(article_id, app_id=app_id)
        print(f"🔍 Database returned for article {article_id}:")
        if article:
            print(f"   - Has recommended_time: {'recommended_time' in article}")
            print(f"   - recommended_time value: {article.get('recommended_time')}")
            print(f"   - Has recommended: {'recommended' in article}")
            print(f"   - recommended count: {len(article.get('recommended', []))}")
        else:
            print(f"   - Article not found in database")
    
    if article:
        # Check app_id filtering if specified
        if app_id and article.get('app_id') != app_id:
            print(f"🔒 Article {article_id} belongs to app '{article.get('app_id')}', requested app '{app_id}' - access denied")
            return None
        
        # Get recommended article IDs from database
        recommended_ids = []
        recommended_dtos = []
        
        # Check if article already has recommendations in the database
        existing_recommendations = article.get("recommended", [])
        recommended_time = article.get("recommended_time")
        
        # Check if recommendations need to be refreshed (older than 60 minutes)
        should_refresh_recommendations = False
        if existing_recommendations and recommended_time:
            try:
                last_recommended = datetime.fromisoformat(recommended_time)
                current_time = datetime.utcnow()
                time_diff = current_time - last_recommended
                minutes_since_recommendation = time_diff.total_seconds() / 60
                
                print(f"⏰ Recommendations last updated: {recommended_time}")
                print(f"⏰ Minutes since last recommendation: {minutes_since_recommendation:.1f}")
                
                # Refresh if more than 60 minutes old
                if minutes_since_recommendation >= 60:
                    should_refresh_recommendations = True
                    print(f"🔄 Recommendations are {minutes_since_recommendation:.1f} minutes old, will refresh")
                else:
                    print(f"💾 Recommendations are {minutes_since_recommendation:.1f} minutes old, using cached")
            except Exception as e:
                print(f"⚠️ Error parsing recommended_time '{recommended_time}': {e}")
                # If we can't parse the time, assume we need fresh recommendations
                should_refresh_recommendations = True
        
        # Handle recommendations based on cache status
        if existing_recommendations and not should_refresh_recommendations:
            # Use existing recommendations WITHOUT updating recommended_time
            recommended_ids = [rec.get("article_id") for rec in existing_recommendations if rec.get("article_id")]
            print(f"📋 Found {len(recommended_ids)} existing recommendations for article {article.get('id', '')}")
            print(f"📋 Recommendation IDs: {recommended_ids[:3]}..." if len(recommended_ids) > 3 else f"📋 Recommendation IDs: {recommended_ids}")
            print(f"💾 Using cached recommendations, NOT updating recommended_time")
        else:
            # Generate fresh recommendations (either none exist or they're expired)
            try:
                from backend.services.recommendation_service import get_recommendation_service
                            
                recommendation_service = get_recommendation_service()
                            
                if not existing_recommendations:
                    print(f"🔄 No recommendations found for article {article_id}, generating new ones...")
                else:
                    print(f"🔄 Recommendations expired for article {article_id}, generating fresh ones...")
                            
                # Get recommendations using recommendation service
                recommendations, was_refreshed = await recommendation_service.get_article_recommendations(article_id, app_id)
                            
                if recommendations and was_refreshed:
                    # Extract just the article IDs from recommendations
                    recommended_ids = [rec.get("article_id") for rec in recommendations if rec.get("article_id")]
                    print(f"✅ Generated {len(recommended_ids)} recommendations for article {article_id}")
                    print(f"🔄 Updated recommended_time in database for article {article_id}")
                else:
                    recommended_ids = []
                    print(f"⚠️ Failed to generate fresh recommendations, using existing ones if available")
                    # If generation failed but we have existing recommendations, use them
                    if existing_recommendations:
                        recommended_ids = [rec.get("article_id") for rec in existing_recommendations if rec.get("article_id")]
                        print(f"💾 Falling back to {len(recommended_ids)} existing recommendations")
                            
            except Exception as e:
                print(f"⚠️ Failed to generate recommendations for article {article.get('id', '')}: {e}")
                # Continue without recommendations rather than failing
                recommended_ids = []
        
        # Convert recommended article IDs to ArticleDTO objects
        if recommended_ids:
            try:
                print(f"🔄 Converting {len(recommended_ids)} recommendation IDs to full article objects...")
                
                # Use the recommendation service to fetch full article details efficiently
                from backend.services.recommendation_service import get_recommendation_service
                recommendation_service = get_recommendation_service()
                
                # Convert lightweight recommendations back to the format expected by fetch_article_details_for_recommendations
                lightweight_recommendations = []
                for rec_id in recommended_ids:
                    # Find the original recommendation object to get the score
                    original_rec = next((rec for rec in existing_recommendations if rec.get('article_id') == rec_id), None)
                    score = original_rec.get('score', 0.0) if original_rec else 0.0
                    lightweight_recommendations.append({
                        'article_id': rec_id,
                        'score': score
                    })
                
                # Fetch full article details using the recommendation service
                detailed_recommendations = await recommendation_service.fetch_article_details_for_recommendations(lightweight_recommendations, app_id)
                
                # Filter by app_id if specified and convert to DTOs
                for rec_article in detailed_recommendations:
                    if rec_article:
                        # Filter recommendations by app_id if specified
                        if app_id and rec_article.get('app_id') != app_id:
                            print(f"🔒 Filtering recommendation {rec_article.get('id', 'unknown')} - different app_id")
                            continue
                        
                        rec_dto = await _convert_to_article_dto(rec_article)
                        recommended_dtos.append(rec_dto)
                        print(f"✅ Converted recommendation {rec_article.get('id', 'unknown')} to article DTO: {rec_dto.get('title', 'No title')}")
                
                print(f"📋 Final recommended_dtos count: {len(recommended_dtos)}")
            except Exception as e:
                print(f"⚠️ Failed to fetch recommended articles: {e}")
                recommended_dtos = []
        
        # Convert to detail DTO with recommendations
        article_dict = await _convert_to_article_detail_dto(article, recommended_dtos, app_id=app_id)
        
        # Debug: Log what we're returning to the API
        print(f"🔍 Article service returning:")
        print(f"   - Has recommended_time: {'recommended_time' in article_dict}")
        print(f"   - recommended_time value: {article_dict.get('recommended_time')}")
        print(f"   - Has recommended: {'recommended' in article_dict}")
        print(f"   - recommended count: {len(article_dict.get('recommended', []))}")
        
        # Cache the dict data using new cache API
        await set_cache(
            CACHE_KEYS["article_detail"], 
            article_dict, 
            app_id=app_id, 
            ttl=CACHE_TTL["detail"],
            article_id=article_id
        )
        
        return article_dict
    
    return None

async def update_article(article_id: str, update_doc: dict, app_id: Optional[str] = None) -> Optional[dict]:
    # Only add updated_at if it's not a recommendations-only update
    if not (set(update_doc.keys()) <= {'recommended', 'recommended_time'}):
        update_doc["updated_at"] = datetime.utcnow().isoformat()
    
    print(f"📝 Article service updating article {article_id}")
    print(f"🔑 Update fields: {list(update_doc.keys())}")
    
    # Get article info before update to get author_id and check if preprocessing needed
    original_article = await article_repo.get_article_by_id(article_id)
    
    # Check if text preprocessing is needed
    # NOTE: Commented out for preprocessing field removal
    # content_fields = {'title', 'abstract', 'content'}
    # if content_fields.intersection(set(update_doc.keys())):
    #     try:
    #         # Get current values, preferring updated values
    #         current_title = update_doc.get('title', original_article.get('title', ''))
    #         current_abstract = update_doc.get('abstract', original_article.get('abstract', ''))
    #         current_content = update_doc.get('content', original_article.get('content', ''))
    #         
    #         # Generate new preprocessed text
    #         article_data = {
    #             'title': current_title,
    #             'abstract': current_abstract,
    #             'content': current_content
    #         }
    #         update_doc["preprocessed_searchable_text"] = preprocess_article_text(article_data)
    #         print(f"✨ Updated preprocessed text: {len(update_doc['preprocessed_searchable_text'])} characters")
    #         
    #     except Exception as e:
    #         print(f"⚠️ Failed to update preprocessed text: {e}")
    #         # Don't fail the update if preprocessing fails
    
    updated_article = await article_repo.update_article(article_id, update_doc)
    
    # Clear affected caches based on updated fields
    await clear_affected_caches(
        operation="update",
        app_id=app_id,
        article_id=article_id,
        author_id=original_article.get("author_id") if original_article else None,
        updated_fields=list(update_doc.keys())
    )
    
    # Convert to dict before returning
    if updated_article:
        return await _convert_to_article_detail_dto(updated_article, None, app_id=app_id)
    return None

async def delete_article(article_id: str, app_id: Optional[str] = None):
    # Get article info before deletion to get author_id and app_id
    # Pass app_id to ensure we only delete articles from the correct app
    article_to_delete = await article_repo.get_article_by_id(article_id, app_id)
    
    if not article_to_delete:
        print(f"❌ Article {article_id} not found or app_id mismatch for deletion")
        return False
    
    await article_repo.delete_article(article_id)
    await user_service.delete_reaction(article_id)
    
    # Use the article's actual app_id if not provided
    if not app_id and article_to_delete:
        app_id = article_to_delete.get("app_id")
    
    # Clear affected caches
    await clear_affected_caches(
        operation="delete",
        app_id=app_id,
        article_id=article_id,
        author_id=article_to_delete.get("author_id") if article_to_delete else None
    )
    
    return True

async def list_articles(page: int, page_size: int, app_id: Optional[str] = None) -> List[dict]:
    # Try to get from cache using new cache API
    cached_articles = await get_cache(
        CACHE_KEYS["articles_home"], 
        app_id=app_id, 
        page=page, 
        page_size=page_size
    )
    
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
        # Cache the dicts using new cache API
        await set_cache(
            CACHE_KEYS["articles_home"], 
            article_dicts, 
            app_id=app_id, 
            ttl=CACHE_TTL["home"],
            page=page,
            page_size=page_size
        )
        return article_dicts
    
    return []
    
async def increment_article_views(article_id: str, app_id: Optional[str] = None):
    await article_repo.increment_article_views(article_id)
    # await clear_affected_caches(operation="view", app_id=app_id, article_id=article_id)

async def increment_article_dislikes(article_id: str, app_id: Optional[str] = None):
    await article_repo.increment_article_dislikes(article_id)
    await clear_affected_caches(operation="dislike", app_id=app_id, article_id=article_id)

async def increment_article_likes(article_id: str, app_id: Optional[str] = None):
    await article_repo.increment_article_likes(article_id)
    await clear_affected_caches(operation="like", app_id=app_id, article_id=article_id)

async def decrement_article_likes(article_id: str, app_id: Optional[str] = None):
    await article_repo.decrement_article_likes(article_id)
    await clear_affected_caches(operation="unlike", app_id=app_id, article_id=article_id)

async def decrement_article_dislikes(article_id: str, app_id: Optional[str] = None):
    await article_repo.decrement_article_dislikes(article_id)
    await clear_affected_caches(operation="undislike", app_id=app_id, article_id=article_id)

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
    # Try to get from cache using new cache API
    cached_articles = await get_cache(
        CACHE_KEYS["articles_author"], 
        app_id=app_id, 
        author_id=author_id,
        page=page, 
        page_size=page_size
    )
    
    if cached_articles:
        print(f"✍️ Redis Cache HIT for author {author_id} articles")
        return cached_articles

    print(f"✍️ Redis Cache MISS for author {author_id} articles - Loading from DB...")
    articles_result = await article_repo.get_article_by_author(author_id, page, page_size, app_id=app_id)
    
    # Extract the articles list from the repository response
    articles = articles_result.get("items", []) if isinstance(articles_result, dict) else articles_result
    
    if articles:
        # Convert to dicts
        article_dicts = [await _convert_to_article_dto(article) for article in articles]
        # Cache the dicts using new cache API
        await set_cache(
            CACHE_KEYS["articles_author"], 
            article_dicts, 
            app_id=app_id, 
            ttl=CACHE_TTL["author"],
            author_id=author_id,
            page=page,
            page_size=page_size
        )
        return article_dicts
    
    return []


async def get_total_articles_count_by_author(author_id: str, app_id: Optional[str] = None):
    """Get total count of published articles by specific author."""
    return await article_repo.get_total_articles_count_by_author(author_id, app_id)


async def list_articles_with_pagination(page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> dict:
    """Get articles with pagination metadata."""
    try:
        # Try to get from cache first using new cache API
        cached_result = await get_cache(
            CACHE_KEYS["articles_home"], 
            app_id=app_id, 
            page=page, 
            page_size=page_size
        )
        
        if cached_result:
            print(f"📋 Redis Cache HIT for paginated articles page {page} (app_id: {app_id or 'all'})")
            # Return the complete cached response structure
            return cached_result
        
        print(f"📋 Redis Cache MISS for paginated articles page {page} (app_id: {app_id or 'all'}) - Loading from DB...")
        
        # Get articles data with pagination info from repository
        result = await article_repo.list_articles(page, page_size, app_id=app_id)
        
        # Extract articles and pagination info
        articles = result.get("items", []) if isinstance(result, dict) else result
        total_items = result.get("totalItems", 0) if isinstance(result, dict) else 0
        total_pages = result.get("totalPages", 1) if isinstance(result, dict) else 1
        
        # Convert to DTOs
        if articles:
            article_dicts = [await _convert_to_article_dto(article) for article in articles]
        else:
            article_dicts = []
        
        # Build the complete response structure
        response_data = {
            "success": True,
            "data": article_dicts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_pages,  # total pages
                "total_results": total_items  # total result count
            }
        }
        
        # Cache the complete response structure using new cache API
        await set_cache(
            CACHE_KEYS["articles_home"], 
            response_data, 
            app_id=app_id, 
            ttl=CACHE_TTL["home"],
            page=page,
            page_size=page_size
        )
        print(f"📋 Redis Cache SET for paginated articles page {page} (app_id: {app_id or 'all'})")
        
        return response_data
    except Exception as e:
        print(f"Error in list_articles_with_pagination: {e}")
        return {
            "success": False,
            "data": {"error": str(e)}
        }


async def get_popular_articles_with_pagination(page: int = 1, page_size: int = 10, app_id: Optional[str] = None) -> dict:
    """Get popular articles with pagination metadata."""
    try:
        # For popular articles, we need to get all active articles first to sort by popularity
        # then apply pagination. This is because popularity is calculated at runtime.
        
        # Get all active articles to calculate popularity scores
        all_articles_result = await article_repo.list_articles(page=1, page_size=1000, app_id=app_id)
        
        # Extract articles from repository result
        if isinstance(all_articles_result, dict):
            all_articles = all_articles_result.get("items", [])
            total_active_articles = all_articles_result.get("totalItems", 0)
        else:
            all_articles = all_articles_result if all_articles_result else []
            total_active_articles = len(all_articles)
        
        if not all_articles:
            return {
                "success": True,
                "data": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_results": 0
                }
            }
        
        # Calculate popularity scores
        now = datetime.utcnow()
        for article in all_articles:
            views = int(article.get("views", 0))
            likes = int(article.get("likes", 0))
            created_at = article.get("created_at")
            
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = now
            elif not isinstance(created_at, datetime):
                created_at = now
                
            days_old = (now - created_at).days
            time_factor = max(0.1, 1 - (days_old / 30))  # Decay over 30 days
            popularity_score = (views * 0.3 + likes * 0.7) * time_factor
            article["popularity_score"] = popularity_score
        
        # Sort by popularity score descending
        sorted_articles = sorted(all_articles, key=lambda x: x.get("popularity_score", 0), reverse=True)
        
        # Apply pagination to sorted results
        total_items = len(sorted_articles)
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_articles = sorted_articles[start_idx:end_idx]
        
        # Convert to DTOs
        article_dicts = [await _convert_to_article_dto(article) for article in paginated_articles]
        
        return {
            "success": True,
            "data": article_dicts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_pages,  # total pages
                "total_results": total_items  # total result count
            }
        }
    except Exception as e:
        print(f"Error in get_popular_articles_with_pagination: {e}")
        return {
            "success": False,
            "data": {"error": "Failed to fetch popular articles"}
        }


async def get_articles_by_author_with_pagination(author_id: str, page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> dict:
    """Get articles by author with pagination metadata."""
    try:
        # Get articles by author from repository (1-indexed)
        articles_result = await article_repo.get_article_by_author(author_id, page, page_size, app_id=app_id)
        
        # Extract articles and pagination info from repository result
        articles = articles_result.get("items", []) if isinstance(articles_result, dict) else articles_result
        total_items = articles_result.get("totalItems", 0) if isinstance(articles_result, dict) else 0
        total_pages = articles_result.get("totalPages", 1) if isinstance(articles_result, dict) else 1
        
        # Convert to DTOs
        if articles:
            article_dicts = [await _convert_to_article_dto(article) for article in articles]
        else:
            article_dicts = []
        
        return {
            "success": True,
            "data": article_dicts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_pages,  # total pages
                "total_results": total_items  # total result count
            }
        }
    except Exception as e:
        print(f"Error in get_articles_by_author_with_pagination: {e}")
        return {
            "success": False,
            "data": {"error": str(e)}
        }

async def get_popular_articles(page: int = 1, page_size: int = 10, app_id: Optional[str] = None) -> List[dict]:
    # Try to get from cache using new cache API
    cached_articles = await get_cache(
        CACHE_KEYS["articles_popular"], 
        app_id=app_id, 
        page=page, 
        page_size=page_size
    )
    
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
        
        # Cache the dicts using new cache API
        await set_cache(
            CACHE_KEYS["articles_popular"], 
            article_dicts, 
            app_id=app_id, 
            ttl=CACHE_TTL["popular"],
            page=page,
            page_size=page_size
        )
        
        return article_dicts
        
    except Exception as e:
        print(f"❌ Error in get_popular_articles: {e}")
        return []

async def search_response_articles(data: Dict, app_id: Optional[str] = None) -> List[dict]:
    article_ids = [article["id"] for article in data.get("results", [])]
    articles = await article_repo.get_articles_by_ids(article_ids)
    
    # Filter by app_id if specified for security
    if app_id:
        articles = [article for article in articles if article.get("app_id") == app_id]
        print(f"🔒 Filtered search results by app_id {app_id}: {len(articles)} articles remaining")
    
    # Convert to dicts
    return [await _convert_to_article_dto(article) for article in articles]


async def get_summary(app_id: Optional[str] = None) -> Dict:
    """Aggregate basic articles summary for dashboards with caching.

    Optimized version using efficient database count queries instead of fetching all articles.
    """
    # Check Redis cache first using new cache API
    cached_stats = await get_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
    
    if cached_stats:
        print(f"📊 Redis Cache HIT for statistics (app_id: {app_id or 'all'})")
        return cached_stats
    
    print(f"📊 Redis Cache MISS for statistics (app_id: {app_id or 'all'}) - Loading from DB...")
    
    try:
        # Use efficient count queries instead of fetching all articles
        count_stats = await article_repo.get_article_summary_counts(app_id=app_id)
        aggregation_stats = await article_repo.get_article_summary_aggregations(app_id=app_id)
        
        # Combine the results
        stats_data = {
            **count_stats,
            **aggregation_stats,
        }
        
        # Cache the results using new cache API
        await set_cache(CACHE_KEYS["homepage_statistics"], stats_data, app_id=app_id, ttl=180)
        print(f"📊 Redis Cache SET for statistics (app_id: {app_id or 'all'})")
        
        return stats_data
    except Exception as e:
        print(f"❌ Error in get_summary: {e}")
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
    return await article_repo.get_total_articles_count(app_id)

async def get_categories(app_id: Optional[str] = None) -> List[Dict]:
    """Get all available categories and their article counts with caching."""
    # Check Redis cache first using new cache API
    cached_categories = await get_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
    
    if cached_categories:
        print("🏷️ Redis Cache HIT for categories")
        return cached_categories
    
    print("🏷️ Redis Cache MISS for categories - Loading from DB...")
    try:
        # Try to get data from repository
        try:
            categories_result = await article_repo.get_categories_with_counts(app_id)
            
        except Exception as db_error:
            print(f"Repository failed, using sample data fallback for categories: {db_error}")
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
        
        # Cache the results using new cache API
        await set_cache(CACHE_KEYS["homepage_categories"], categories_result, app_id=app_id, ttl=180)
        print("🏷️ Redis Cache SET for categories")
        
        return categories_result
    except Exception as e:
        print(f"Error fetching categories: {e}")
        # Return default categories as fallback
        return [
            {"name": "Technology", "count": 15},
            {"name": "Design", "count": 12},
            {"name": "Business", "count": 10},
            {"name": "Science", "count": 8},
            {"name": "Health", "count": 6},
            {"name": "Lifestyle", "count": 5}
        ]


async def get_articles_by_category(
    category_name: str,
    page: int = 1,
    limit: int = 10,
    app_id: Optional[str] = None
) -> dict:
    """Get articles by category with pagination."""
    try:
        result = await article_repo.get_articles_by_category(category_name, page, limit, app_id)
        
        return {
            "success": True,
            "data": result["items"],
            "pagination": {
                "page": result["current_page"],
                "limit": result["page_size"],
                "total": result["total_pages"],  # total pages
                "total_results": result["total_items"]  # total result count
            }
        }
    except Exception as e:
        print(f"Error fetching articles by category: {e}")
        return {
            "success": False,
            "data": {"error": str(e)}
        }