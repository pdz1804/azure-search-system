from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import math
from pydantic import BaseModel
from backend.services.article_service import search_response_articles
from backend.services.search_service import get_search_service
from backend.services.user_service import search_response_users
from backend.services.cache_service import get_cache, set_cache


class ArticleHit(BaseModel):
    id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    author_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]
    highlights: Optional[Dict[str, Any]] = None


class AuthorHit(BaseModel):
    id: str
    full_name: Optional[str] = None
    score_final: float
    scores: Dict[str, float]


search = APIRouter(prefix="/api/search", tags=["search"])

@search.get("/")
async def search_general(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(60, ge=1, le=1000, description="Number of results to return (default 5 pages * 12)"),
    page_index: int = Query(0, ge=0, description="Page index (0-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Number of results per page (default 12)"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    try:
        cache_key = f"search:general:{q}:{k}:{page_index}:{page_size}:{app_id or 'none'}"
        cached = await get_cache(cache_key)

        if cached is not None:
            return cached

        search_service = get_search_service()
        result = search_service.search(q, k, page_index, page_size, app_id)

        if not result or not result.get("results"):
            raise HTTPException(status_code=500, detail="Search failed - no results returned")

        search_type = result.get("search_type", "articles")
        
        if search_type == "authors":
            docs = await search_response_users(result)
        else:
            docs = await search_response_articles(result, app_id)
        
        pagination = result.get("pagination") or {}
        total_results = pagination.get("total_results", len(docs))
        total_pages = math.ceil(total_results / page_size) if page_size else 1
        mapped_pagination = {
            "page": (pagination.get("page_index") or page_index) + 1,
            "page_size": pagination.get("page_size") or page_size,
            "total": total_pages,
            "total_results": total_results,
        }

        response = {
            "success": True, 
            "data": docs, 
            "results": docs, 
            "pagination": mapped_pagination,
            "normalized_query": result.get("normalized_query", q),
            "search_type": search_type
        }

        await set_cache(cache_key, response, ttl=300)
        
        return response
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": str(e)}})

@search.get("/articles")
async def search_articles(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(60, ge=1, le=1000, description="Number of results to return (default 5 pages * 12)"),
    page_index: int = Query(0, ge=0, description="Page index (0-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Number of results per page (default 12)"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    try:
        cache_key = f"search:articles:{q}:{k}:{page_index}:{page_size}:{app_id or 'none'}"
        cached = await get_cache(cache_key)
        
        if cached is not None:
            return cached

        search_service = get_search_service()
        result = search_service.search_articles(q, k, page_index, page_size, app_id)

        if not result or not result.get("results"):
            return JSONResponse(status_code=500, content={"success": False, "data": {"error": "Search failed - no results returned"}})
        
        docs = await search_response_articles(result, app_id)
        
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
        
        await set_cache(cache_key, response, ttl=300)
        
        return response
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": str(e)}})

@search.get("/authors")
async def search_authors(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(60, ge=1, le=1000, description="Number of results to return (default 5 pages * 12)"),
    page_index: int = Query(0, ge=0, description="Page index (0-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Number of results per page (default 12)"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    try:
        cache_key = f"search:authors:{q}:{k}:{page_index}:{page_size}:{app_id or 'none'}"
        cached = await get_cache(cache_key)
        if cached is not None:
            return cached

        search_service = get_search_service()
        result = search_service.search_authors(q, k, page_index, page_size, app_id)

        if not result or not result.get("results"):
            return JSONResponse(status_code=500, content={"success": False, "data": {"error": "Search failed - no results returned"}})

        docs = await search_response_users(result)
        
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
        
        await set_cache(cache_key, response, ttl=300)
        
        return response
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "data": {"error": str(e)}})
