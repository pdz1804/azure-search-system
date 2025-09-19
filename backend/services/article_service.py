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

async def clear_affected_caches(
    operation: str,
    app_id: Optional[str] = None,
    article_id: Optional[str] = None,
    author_id: Optional[str] = None,
    updated_fields: Optional[List[str]] = None
):

    if article_id:
        await delete_cache(CACHE_KEYS["article_detail"], app_id=app_id, article_id=article_id)
    
    if operation == "create":
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
        if author_id:
            author_pattern = CACHE_KEYS["articles_author"].format(author_id=author_id) + "*"
            await delete_cache_pattern(author_pattern, app_id=app_id)
    
    elif operation == "delete":
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
        if author_id:
            author_pattern = CACHE_KEYS["articles_author"].format(author_id=author_id) + "*"
            await delete_cache_pattern(author_pattern, app_id=app_id)
    
    elif operation == "update" and updated_fields:
        fields_set = set(updated_fields)
        
        if fields_set <= {'recommended', 'recommended_time'}:
            pass
        
        elif 'status' in fields_set:
            await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
            await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
            await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
            if author_id:
                author_pattern = CACHE_KEYS["articles_author"].format(author_id=author_id) + "*"
                await delete_cache_pattern(author_pattern, app_id=app_id)
        
        elif 'tags' in fields_set:
            await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
            
        elif 'abstract' in fields_set:
            await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
            await delete_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)

        elif any(field in fields_set for field in ['title', 'content', 'abstract', 'image']):
            await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)

    elif operation in ["like", "unlike", "view"]:
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache_pattern(CACHE_KEYS["articles_popular"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
    
    elif operation in ["dislike", "undislike"]:
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)
        await delete_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
    
    elif operation in ["bookmark", "unbookmark"]:
        await delete_cache_pattern(CACHE_KEYS["articles_home"] + "*", app_id=app_id)

async def _convert_to_author_dto(article: dict) -> AuthorDTO:
    author_id = article.get("author_id", "")
    author_name = article.get("author_name", "")
    
    return AuthorDTO(
        id=author_id,
        name=author_name,
        avatar_url=None
    )

async def _convert_to_author_dto_with_avatar(article: dict) -> AuthorDTO:
    author_id = article.get("author_id", "")
    author_name = article.get("author_name", "")
    
    author_avatar = None
    try:
        from backend.services.user_service import get_user_by_id
        user_info = await get_user_by_id(author_id)
        if user_info and hasattr(user_info, 'avatar_url'):
            author_avatar = user_info.avatar_url
    except Exception:
        pass
    
    return AuthorDTO(
        id=author_id,
        name=author_name,
        avatar_url=author_avatar
    )

async def _convert_to_article_dto(article: dict) -> dict:
    author_dto = await _convert_to_author_dto(article)
    
    return {
        "app_id": article.get("app_id", ""),
        "article_id": article.get("id", ""),
        "title": article.get("title", ""),
        "abstract": article.get("abstract"),
        "image": article.get("image"),
        "tags": article.get("tags", []),
        "status": article.get("status", "published"),
        "author": author_dto.model_dump(),
        "created_date": article.get("created_at"),
        "total_like": article.get("likes", 0),
        "total_view": article.get("views", 0)
    }

async def _convert_to_article_detail_dto(article: dict, recommended_dtos: Optional[List[dict]] = None, app_id: Optional[str] = None) -> dict:
    _ = app_id  # Explicitly acknowledge unused parameter
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
        "author": author_dto.model_dump(),
        "created_date": article.get("created_at"),
        "updated_date": article.get("updated_at"),
        "total_like": article.get("likes", 0),
        "total_view": article.get("views", 0),
        "total_dislike": article.get("dislikes", 0),
        "recommended": recommended_dtos if recommended_dtos else None,
        "recommended_time": article.get("recommended_time")
    }

async def create_article(doc: dict, app_id: Optional[str] = None) -> dict:
    now = datetime.utcnow().isoformat()
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["id"] = uuid.uuid4().hex
    doc["is_active"] = True
    doc.setdefault("likes", 0)
    doc.setdefault("dislikes", 0)
    doc.setdefault("views", 0)
    
    if app_id:
        doc["app_id"] = app_id

    inserted_id = await article_repo.insert_article(doc)
    art = await article_repo.get_article_by_id(inserted_id, app_id=app_id)
    
    await clear_affected_caches(
        operation="create",
        app_id=app_id,
        author_id=doc.get("author_id")
    )
    
    return await _convert_to_article_detail_dto(art, None, app_id=app_id)

async def get_article_by_id(article_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    return await article_repo.get_article_by_id(article_id, app_id=app_id)

async def get_article_detail(article_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    cached_article = await get_cache(CACHE_KEYS["article_detail"], app_id=app_id, article_id=article_id)
    
    if cached_article:
        cached_recommended = cached_article.get('recommended', [])
        if cached_recommended is None:
            cached_recommended = []
        return cached_article
    else:
        article = await article_repo.get_article_by_id(article_id, app_id=app_id)
        if article:
            recommended_list = article.get('recommended', [])
            if recommended_list is None:
                recommended_list = []
        else:
            recommended_list = []
    
    if article:
        if app_id and article.get('app_id') != app_id:
            return None
        
        recommended_ids = []
        recommended_dtos = []
        
        existing_recommendations = article.get("recommended", [])
        if existing_recommendations is None:
            existing_recommendations = []
        recommended_time = article.get("recommended_time")
        
        should_refresh_recommendations = False
        if existing_recommendations and recommended_time:
            try:
                last_recommended = datetime.fromisoformat(recommended_time)
                current_time = datetime.utcnow()
                time_diff = current_time - last_recommended
                minutes_since_recommendation = time_diff.total_seconds() / 60

                if minutes_since_recommendation >= 60:
                    should_refresh_recommendations = True
                else:
                    should_refresh_recommendations = False
            except Exception: 
                should_refresh_recommendations = True
        
        if existing_recommendations and not should_refresh_recommendations:
            recommended_ids = [rec.get("article_id") for rec in existing_recommendations if rec.get("article_id")]
        else:
            try:
                from backend.services.recommendation_service import get_recommendation_service
                recommendation_service = get_recommendation_service()
                            
                if not existing_recommendations:
                    recommendations, was_refreshed = await recommendation_service.get_article_recommendations(article_id, app_id)
                else:
                    recommendations, was_refreshed = await recommendation_service.get_article_recommendations(article_id, app_id)
                            
                if recommendations and was_refreshed:
                    recommended_ids = [rec.get("article_id") for rec in recommendations if rec.get("article_id")]
                else:
                    recommended_ids = []
                    if existing_recommendations:
                        recommended_ids = [rec.get("article_id") for rec in existing_recommendations if rec.get("article_id")]
                            
            except Exception:
                recommended_ids = []
        
        if recommended_ids:
            try:
                from backend.services.recommendation_service import get_recommendation_service
                recommendation_service = get_recommendation_service()
                
                lightweight_recommendations = []
                for rec_id in recommended_ids:
                    original_rec = next((rec for rec in existing_recommendations if rec.get('article_id') == rec_id), None)
                    score = original_rec.get('score', 0.0) if original_rec else 0.0
                    lightweight_recommendations.append({
                        'article_id': rec_id,
                        'score': score
                    })
                
                detailed_recommendations = await recommendation_service.fetch_article_details_for_recommendations(lightweight_recommendations, app_id)
                
                for rec_article in detailed_recommendations:
                    if rec_article:
                        if app_id and rec_article.get('app_id') != app_id:
                            continue
                        
                        rec_dto = await _convert_to_article_dto(rec_article)
                        recommended_dtos.append(rec_dto)
                
            except Exception:
                recommended_dtos = []
        
        article_dict = await _convert_to_article_detail_dto(article, recommended_dtos, app_id=app_id)
        
        recommended_list = article_dict.get('recommended', [])
        if recommended_list is None:
            recommended_list = []
        
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
    if not (set(update_doc.keys()) <= {'recommended', 'recommended_time'}):
        update_doc["updated_at"] = datetime.utcnow().isoformat()

    original_article = await article_repo.get_article_by_id(article_id)

    updated_article = await article_repo.update_article(article_id, update_doc)
    
    await clear_affected_caches(
        operation="update",
        app_id=app_id,
        article_id=article_id,
        author_id=original_article.get("author_id") if original_article else None,
        updated_fields=list(update_doc.keys())
    )
    
    if updated_article:
        return await _convert_to_article_detail_dto(updated_article, None, app_id=app_id)
    return None

async def delete_article(article_id: str, app_id: Optional[str] = None):
    article_to_delete = await article_repo.get_article_by_id(article_id, app_id)
    
    if not article_to_delete:
        return False
    
    await article_repo.delete_article(article_id)
    await user_service.delete_reaction(article_id)
    
    if not app_id and article_to_delete:
        app_id = article_to_delete.get("app_id")
    
    await clear_affected_caches(
        operation="delete",
        app_id=app_id,
        article_id=article_id,
        author_id=article_to_delete.get("author_id") if article_to_delete else None
    )
    
    return True

async def list_articles(page: int, page_size: int, app_id: Optional[str] = None) -> List[dict]:
    cached_articles = await get_cache(
        CACHE_KEYS["articles_home"], 
        app_id=app_id, 
        page=page, 
        page_size=page_size
    )
    
    if cached_articles:
        return cached_articles
    
    result = await article_repo.list_articles(page, page_size, app_id=app_id)
    
    articles = result.get("items", []) if isinstance(result, dict) else result
    
    if articles:
        article_dicts = [await _convert_to_article_dto(article) for article in articles]
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
    _ = app_id  # Explicitly acknowledge unused parameter
    await article_repo.increment_article_views(article_id)

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

async def get_articles_by_author(author_id: str, page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> List[dict]:
    cached_articles = await get_cache(
        CACHE_KEYS["articles_author"], 
        app_id=app_id, 
        author_id=author_id,
        page=page, 
        page_size=page_size
    )
    
    if cached_articles:
        return cached_articles

    articles_result = await article_repo.get_article_by_author(author_id, page, page_size, app_id=app_id)
    
    articles = articles_result.get("items", []) if isinstance(articles_result, dict) else articles_result
    
    if articles:
        article_dicts = [await _convert_to_article_dto(article) for article in articles]
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
    return await article_repo.get_total_articles_count_by_author(author_id, app_id)

async def list_articles_with_pagination(page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> dict:
    try:
        cached_result = await get_cache(
            CACHE_KEYS["articles_home"], 
            app_id=app_id, 
            page=page, 
            page_size=page_size
        )
        
        if cached_result:
            return cached_result

        result = await article_repo.list_articles(page, page_size, app_id=app_id)
        
        articles = result.get("items", []) if isinstance(result, dict) else result
        total_items = result.get("totalItems", 0) if isinstance(result, dict) else 0
        total_pages = result.get("totalPages", 1) if isinstance(result, dict) else 1
        
        if articles:
            article_dicts = [await _convert_to_article_dto(article) for article in articles]
        else:
            article_dicts = []
        
        response_data = {
            "success": True,
            "data": article_dicts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_pages,
                "total_results": total_items
            }
        }
        
        await set_cache(
            CACHE_KEYS["articles_home"], 
            response_data, 
            app_id=app_id, 
            ttl=CACHE_TTL["home"],
            page=page,
            page_size=page_size
        )
        
        return response_data
    except Exception as e:
        return {
            "success": False,
            "data": {"error": str(e)}
        }

async def get_popular_articles_with_pagination(page: int = 1, page_size: int = 10, app_id: Optional[str] = None) -> dict:
    try:
        all_articles_result = await article_repo.list_articles(page=1, page_size=1000, app_id=app_id)
        
        if isinstance(all_articles_result, dict):
            all_articles = all_articles_result.get("items", [])
        else:
            all_articles = all_articles_result if all_articles_result else []
        
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
        
        now = datetime.utcnow()
        for article in all_articles:
            views = int(article.get("views", 0))
            likes = int(article.get("likes", 0))
            created_at = article.get("created_at")
            
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    created_at = now
            elif not isinstance(created_at, datetime):
                created_at = now
                
            days_old = (now - created_at).days
            time_factor = max(0.1, 1 - (days_old / 30))
            popularity_score = (views * 0.3 + likes * 0.7) * time_factor
            article["popularity_score"] = popularity_score
        
        sorted_articles = sorted(all_articles, key=lambda x: x.get("popularity_score", 0), reverse=True)
        
        total_items = len(sorted_articles)
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_articles = sorted_articles[start_idx:end_idx]
        
        article_dicts = [await _convert_to_article_dto(article) for article in paginated_articles]
        
        return {
            "success": True,
            "data": article_dicts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_pages,
                "total_results": total_items
            }
        }
    except Exception:
        return {
            "success": False,
            "data": {"error": "Failed to fetch popular articles"}
        }

async def get_articles_by_author_with_pagination(author_id: str, page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> dict:
    try:
        articles_result = await article_repo.get_article_by_author(author_id, page, page_size, app_id=app_id)
        
        articles = articles_result.get("items", []) if isinstance(articles_result, dict) else articles_result
        total_items = articles_result.get("totalItems", 0) if isinstance(articles_result, dict) else 0
        total_pages = articles_result.get("totalPages", 1) if isinstance(articles_result, dict) else 1
        
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
                "total": total_pages,
                "total_results": total_items
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {"error": str(e)}
        }

async def get_popular_articles(page: int = 1, page_size: int = 10, app_id: Optional[str] = None) -> List[dict]:
    cached_articles = await get_cache(
        CACHE_KEYS["articles_popular"], 
        app_id=app_id, 
        page=page, 
        page_size=page_size
    )
    
    if cached_articles:
        return cached_articles
    
    try:
        articles_data = await article_repo.list_articles(page=1, page_size=page_size * 3, app_id=app_id)
        
        if isinstance(articles_data, dict):
            articles = articles_data.get("items", [])
        elif isinstance(articles_data, list):
            articles = articles_data
        else:
            return []
        
        if not articles:
            return []

        now = datetime.utcnow()
        
        for article in articles:
            article.setdefault("likes", 0)
            article.setdefault("views", 0)
            
            created_at = article.get("created_at")
            if isinstance(created_at, str):
                try:
                    if created_at.endswith('Z'):
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        created_date = datetime.fromisoformat(created_at)
                except Exception:
                    created_date = now
            else:
                created_date = now
            
            days_old = (now - created_date).days
            
            time_factor = max(0.1, 0.95 ** days_old)
            
            likes = int(article.get("likes", 0))
            views = int(article.get("views", 0))
            base_score = likes * 3 + views
            
            popularity_score = base_score * time_factor
            article["popularity_score"] = popularity_score

        articles.sort(key=lambda x: x.get("popularity_score", 0), reverse=True)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        result = articles[start_idx:end_idx]
        
        for article in result:
            article.pop("popularity_score", None)
        
        article_dicts = [await _convert_to_article_dto(article) for article in result]
        
        await set_cache(
            CACHE_KEYS["articles_popular"], 
            article_dicts, 
            app_id=app_id, 
            ttl=CACHE_TTL["popular"],
            page=page,
            page_size=page_size
        )
        
        return article_dicts
        
    except Exception:
        return []

async def search_response_articles(data: Dict, app_id: Optional[str] = None) -> List[dict]:
    article_ids = [article["id"] for article in data.get("results", [])]
    articles = await article_repo.get_articles_by_ids(article_ids)
    
    if app_id:
        articles = [article for article in articles if article.get("app_id") == app_id]
    
    return [await _convert_to_article_dto(article) for article in articles]

async def get_summary(app_id: Optional[str] = None) -> Dict:
    cached_stats = await get_cache(CACHE_KEYS["homepage_statistics"], app_id=app_id)
    
    if cached_stats:
        return cached_stats

    try:
        count_stats = await article_repo.get_article_summary_counts(app_id=app_id)
        aggregation_stats = await article_repo.get_article_summary_aggregations(app_id=app_id)
        stats_data = {
            **count_stats,
            **aggregation_stats,
        }
        
        await set_cache(CACHE_KEYS["homepage_statistics"], stats_data, app_id=app_id, ttl=180)
        
        return stats_data
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
    return await article_repo.get_total_articles_count(app_id)

async def get_categories(app_id: Optional[str] = None) -> List[Dict]:
    cached_categories = await get_cache(CACHE_KEYS["homepage_categories"], app_id=app_id)
    
    if cached_categories:
        return cached_categories
    
    try:
        try:
            categories_result = await article_repo.get_categories_with_counts(app_id)
            
        except Exception:
            import json
            import os
            from collections import Counter
            
            sample_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ai_search', 'data', 'articles.json')
            
            if os.path.exists(sample_file_path):
                with open(sample_file_path, 'r', encoding='utf-8') as f:
                    sample_articles = json.load(f)
                
                all_tags = []
                for article in sample_articles:
                    if app_id and article.get('app_id') != app_id:
                        continue
                    if article.get('tags'):
                        all_tags.extend(article['tags'])
                
                tag_counts = Counter(all_tags)
                categories_result = [
                    {"name": tag, "count": count} 
                    for tag, count in tag_counts.most_common(10)
                ]
            else:
                categories_result = [
                    {"name": "Technology", "count": 15},
                    {"name": "Design", "count": 12},
                    {"name": "Business", "count": 10},
                    {"name": "Science", "count": 8},
                    {"name": "Health", "count": 6},
                    {"name": "Lifestyle", "count": 5}
                ]
        
        if not categories_result:
            categories_result = [
                {"name": "Technology", "count": 15},
                {"name": "Design", "count": 12},
                {"name": "Business", "count": 10},
                {"name": "Science", "count": 8},
                {"name": "Health", "count": 6},
                {"name": "Lifestyle", "count": 5}
            ]
        
        await set_cache(CACHE_KEYS["homepage_categories"], categories_result, app_id=app_id, ttl=180)
        
        return categories_result
    except Exception:
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
    try:
        result = await article_repo.get_articles_by_category(category_name, page, limit, app_id)
        
        return {
            "success": True,
            "data": result["items"],
            "pagination": {
                "page": result["current_page"],
                "limit": result["page_size"],
                "total": result["total_pages"],
                "total_results": result["total_items"]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {"error": str(e)}
        }
