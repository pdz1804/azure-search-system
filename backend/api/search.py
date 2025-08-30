"""
Search API endpoints for the backend.

This module provides AI-powered search functionality for articles and users,
implementing the same API structure as the ai_search service.
"""

from urllib import response
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import time
import math
from pydantic import BaseModel
from backend.services.article_service import  search_response_articles
from backend.services.search_service import get_search_service
from backend.services.user_service import search_response_users
from backend.services.cache_service import get_cache, set_cache

# Pydantic models matching ai_search structure
class ArticleHit(BaseModel):
    """Represents a single article search hit in API responses."""
    id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    author_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]
    highlights: Optional[Dict[str, Any]] = None

class AuthorHit(BaseModel):
    """Represents a single author search hit in API responses."""
    id: str
    full_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]

search = APIRouter(prefix="/api/search", tags=["search"])

# Redis caching is now handled via cache_service - no in-memory cache needed

@search.get("/")
async def search_general(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(60, ge=1, le=1000, description="Number of results to return (default 5 pages * 12)") ,
    page_index: int = Query(0, ge=0, description="Page index (0-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Number of results per page (default 12)"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    """General search endpoint with intelligent query classification and routing.
    
    Uses intelligent planning to:
    1. Determine if query is meaningful
    2. Classify query type (articles vs authors)
    3. Route to appropriate search function
    4. Return unified response format
    
    Supports pagination with page_index and page_size parameters.
    """
    print(f"🔍 General search: query='{q}', k={k}, page_index={page_index}, page_size={page_size}, app_id={app_id}")
    try:
        cache_key = f"search:general:{q}:{k}:{page_index}:{page_size}:{app_id or 'none'}"
        cached = await get_cache(cache_key)

        if cached is not None:
            print(f"🔍 Redis Cache HIT for general search: {q}")
            return cached
        
        print(f"🔍 Redis Cache MISS for general search: {q} - Loading from search service...")

        # Get search results from service layer using general search
        search_service = get_search_service()
        result = search_service.search(q, k, page_index, page_size, app_id)

        if not result or not result.get("results"):
            raise HTTPException(status_code=500, detail="Search failed - no results returned")

        # print(f"Result DEBUG: {result}")

        # Transform results based on search type
        search_type = result.get("search_type", "articles")
        
        if search_type == "authors":
            # Transform results to AuthorHit format
            items = [
                AuthorHit(
                    id=item["doc"]["id"],
                    full_name=item["doc"].get("full_name", ""),
                    score_final=item.get("_final", 1.0),
                    scores={
                        "semantic": item.get("_semantic", 0.0), 
                        "bm25": item.get("_bm25", 0.0), 
                        "vector": item.get("_vector", 0.0),
                        "business": item.get("_business", 0.0)
                    }
                ) for item in result.get("results", [])
            ]
        else:
            # Transform results to ArticleHit format (default)
            items = [
                ArticleHit(
                    id=item["doc"]["id"],
                    title=item["doc"].get("title", ""),
                    abstract=item["doc"].get("abstract", ""),
                    author_name=item["doc"].get("author_name", ""),
                    score_final=item.get("_final", 1.0),
                    scores={
                        "semantic": item.get("_semantic", 0.0), 
                        "bm25": item.get("_bm25", 0.0), 
                        "vector": item.get("_vector", 0.0), 
                        "business": item.get("_business", 0.0)
                    },
                    highlights=item["doc"].get("highlights")
                ) for item in result.get("results", [])
            ]
        
        # Build pagination: "total" should be number of pages. raw total results is in total_results
        pagination = result.get("pagination") or {}
        total_results = pagination.get("total_results", len(items))
        total_pages = math.ceil(total_results / page_size) if page_size else 1

        response = {
            "success": True,
            "data": items,
            "results": items,
            "pagination": {
                "page": page_index + 1,
                "page_size": page_size,
                "total": total_pages,
                "total_results": total_results,
            },
            "normalized_query": result.get("normalized_query", q),
            "search_type": search_type
        }
        
        print(f"🔍 [SEARCH API DEBUG] Returning pagination: {response['pagination']}")
        print(f"🔍 [SEARCH API DEBUG] total_results={total_results}, total_pages={total_pages}, page_size={page_size}")

        # Cache the page so subsequent clicks for the same page are fast
        await set_cache(cache_key, response, ttl=300)
        print(f"🔍 Redis Cache SET for general search: {q}")
        
        print(f"✅ General search completed: {len(items)} results, type: {search_type}")
        return response
    except Exception as e:
        print(f"❌ General search failed: {e}")
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": str(e)}})

@search.get("/articles")
async def search_articles(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(60, ge=1, le=1000, description="Number of results to return (default 5 pages * 12)"),
    page_index: int = Query(0, ge=0, description="Page index (0-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Number of results per page (default 12)"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    """Search articles with hybrid scoring and optional pagination.
    
    Returns a combination of semantic, keyword (BM25), vector, and business logic scores
    with configurable weights. Supports pagination with page_index and page_size parameters.
    """
    print(f"🔍 Searching articles: query='{q}', k={k}, page_index={page_index}, page_size={page_size}, app_id={app_id}")
    try:
        cache_key = f"search:articles:{q}:{k}:{page_index}:{page_size}:{app_id or 'none'}"
        cached = await get_cache(cache_key)
        
        if cached is not None:
            print(f"🔍 Redis Cache HIT for articles search: {q}")
            return cached
        
        print(f"🔍 Redis Cache MISS for articles search: {q} - Loading from search service...")

        # Get search results from service layer
        search_service = get_search_service()
        result = search_service.search_articles(q, k, page_index, page_size, app_id)

        if not result or not result.get("results"):
            return JSONResponse(status_code=500, content={"success": False, "data": {"error": "Search failed - no results returned"}})
        docs = await search_response_articles(result, app_id)
        
        # Transform results to ArticleHit format for API response
        # articles = [
        #     ArticleHit(
        #         id=item["doc"]["id"],
        #         title=item["doc"].get("title"),
        #         abstract=item["doc"].get("abstract"),
        #         author_name=item["doc"].get("author_name"),
        #         score_final=item.get("_final", 1.0),
        #         scores={
        #             "semantic": item.get("_semantic", 0.0), 
        #             "bm25": item.get("_bm25", 0.0), 
        #             "vector": item.get("_vector", 0.0), 
        #             "business": item.get("_business", 0.0)
        #         },
        #         highlights=item["doc"].get("highlights")
        #     ) for item in result.get("results", [])
        # ]
        
        # response = {
        #     "articles": articles,
        #     "pagination": {
        #         "page": page_index + 1 if page_index is not None else 1,
        #         "page_size": page_size or k,
        #         "total": (result.get("pagination") or {}).get("total_results", len(articles))
        #     },
        #     "normalized_query": result.get("normalized_query", q),
        #     "search_type": result.get("search_type", "articles")
        # }
        
        # print(f"✅ Articles search completed: {len(articles)} results")
        pagination = result.get("pagination") or {}
        total_results = pagination.get("total_results", len(docs))
        total_pages = math.ceil(total_results / page_size) if page_size else 1
        mapped_pagination = {
            "page": (pagination.get("page_index") or page_index) + 1,
            "page_size": pagination.get("page_size") or page_size,
            "total": total_pages,
            "total_results": total_results,
        }

        response = {"success": True, "data": docs, "results": docs, "pagination": mapped_pagination}
        
        # Cache the results for 5 minutes (300 seconds)
        await set_cache(cache_key, response, ttl=300)
        print(f"🔍 Redis Cache SET for articles search: {q}")
        
        return response
    except Exception as e:
        print(f"❌ Articles search failed: {e}")
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": str(e)}})

@search.get("/authors")
async def search_authors(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(60, ge=1, le=1000, description="Number of results to return (default 5 pages * 12)"),
    page_index: int = Query(0, ge=0, description="Page index (0-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Number of results per page (default 12)"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    """Search authors with hybrid scoring and optional pagination.
    
    Returns a combination of semantic and keyword (BM25) scores with configurable weights.
    Vector and business scoring can be enabled via environment variables.
    Supports pagination with page_index and page_size parameters.
    """
    print(f"🔍 Searching authors: query='{q}', k={k}, page_index={page_index}, page_size={page_size}, app_id={app_id}")
    try:
        cache_key = f"search:authors:{q}:{k}:{page_index}:{page_size}:{app_id or 'none'}"
        cached = await get_cache(cache_key)
        if cached is not None:
            print(f"👥 Redis Cache HIT for authors search: {q}")
            return cached
        
        print(f"👥 Redis Cache MISS for authors search: {q} - Loading from search service...")

        # Get search results from service layer
        search_service = get_search_service()
        result = search_service.search_authors(q, k, page_index, page_size, app_id)

        if not result or not result.get("results"):
            return JSONResponse(status_code=500, content={"success": False, "data": {"error": "Search failed - no results returned"}})

        # print(f"Result DEBUG: {result}")
        docs = await search_response_users(result)
        # # Transform results to AuthorHit format for API response
        # authors = [
        #     AuthorHit(
        #         id=item["doc"]["id"],
        #         full_name=item["doc"].get("full_name"),
        #         score_final=item.get("_final", 1.0),
        #         scores={
        #             "semantic": item.get("_semantic", 0.0), 
        #             "bm25": item.get("_bm25", 0.0), 
        #             "vector": item.get("_vector", 0.0),
        #             "business": item.get("_business", 0.0)
        #         }
        #     ) for item in result.get("results", [])
        # ]
        
        # response = {
        #     "results": authors,
        #     "pagination": {
        #         "page": page_index + 1 if page_index is not None else 1,
        #         "page_size": page_size or k,
        #         "total": (result.get("pagination") or {}).get("total_results", len(authors))
        #     },
        #     "normalized_query": result.get("normalized_query", q),
        #     "search_type": result.get("search_type", "authors")
        # }
        
        # print(f"✅ Authors search completed: {len(authors)} results")
        pagination = result.get("pagination") or {}
        total_results = pagination.get("total_results", len(docs))
        total_pages = math.ceil(total_results / page_size) if page_size else 1
        mapped_pagination = {
            "page": (pagination.get("page_index") or page_index) + 1,
            "page_size": pagination.get("page_size") or page_size,
            "total": total_pages,
            "total_results": total_results,
        }

        response = {"success": True, "data": docs, "results": docs, "pagination": mapped_pagination}
        
        # Cache the results for 5 minutes (300 seconds)
        await set_cache(cache_key, response, ttl=300)
        print(f"👥 Redis Cache SET for authors search: {q}")
        
        return response
    except Exception as e:
        print(f"❌ Authors search failed: {e}")
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": str(e)}})
