"""
Azure AI Blog Search API

Integration of Azure AI Search, Cosmos DB, and Embeddings for hybrid search capabilities.

FastAPI REST API endpoints:
 - /search/articles?q={query}&k={limit}&page_index={index}&page_size={size}
 - /search/authors?q={query}&k={limit}&page_index={index}&page_size={size}

CLI commands:
 - create-indexes: Create Azure AI Search indexes
 - ingest: Load data from Cosmos DB into search indexes
 - setup-indexers: Configure Azure Search indexers for Cosmos DB
 - check-indexers: Verify status of indexers
 - serve: Start the FastAPI server

Returns hybrid search results with fused scores from:
 - Semantic search (natural language understanding)
 - BM25 (keyword matching)
 - Vector search (embedding similarity)
 - Business logic (freshness)

All scoring weights are configurable via environment variables.
"""

import sys
import uvicorn
from fastapi import FastAPI, Query
from typing import List, Optional

from ai_search.app.models import ArticleHit, AuthorHit
from ai_search.app.clients import articles_client, authors_client
from ai_search.app.services.search_service import SearchService
from ai_search.utils.cli import parse_args
from ai_search.utils.command_handlers import get_command_handlers

print("🚀 Initializing Blog Search API...")

# Initialize FastAPI app
app = FastAPI(title="Blog Search API", version="1.0.0")

# Global search service instance (lazy initialization)
_search_service = None

def get_search_service() -> SearchService:
    """Get or create the search service instance (lazy initialization)."""
    global _search_service
    if _search_service is None:
        print("📋 Setting up search service...")
        try:
            _search_service = SearchService(articles_client(), authors_client())
            print("✅ Search service initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize search service: {e}")
            raise
    return _search_service

@app.get("/search/articles")
def search_articles(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    page_index: Optional[int] = Query(None, ge=0, description="Page index (0-based)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Number of results per page"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    """Search articles with hybrid scoring and optional pagination.
    
    Returns a combination of semantic, keyword (BM25), vector, and business logic scores
    with configurable weights. Supports pagination with page_index and page_size parameters.
    """
    print(f"🔍 Searching articles: query='{q}', k={k}, page_index={page_index}, page_size={page_size}, app_id={app_id}")
    try:
        # Get search results from service layer
        result = get_search_service().search_articles(q, k, page_index, page_size, app_id)
        
        # Transform results to ArticleHit format for API response
        articles = [
            ArticleHit(
                id=doc["id"],
                title=doc.get("title"),
                abstract=doc.get("abstract"),
                author_name=doc.get("author_name"),
                score_final=result_item["_final"],
                scores={
                    "semantic": result_item["_semantic"], 
                    "bm25": result_item["_bm25"], 
                    "vector": result_item["_vector"], 
                    "business": result_item["_business"]
                },
                highlights=doc.get("@search.highlights")
            ) for result_item in result["results"] 
            if (doc := result_item["doc"])
        ]
        
        response = {
            "articles": articles,
            "pagination": result["pagination"],
            "normalized_query": result["normalized_query"],
            "search_type": result.get("search_type", "articles")
        }
        
        print(f"✅ Articles search completed: {len(articles)} results")
        return response
    except Exception as e:
        print(f"❌ Articles search failed: {e}")
        raise

@app.get("/search/authors")
def search_authors(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    page_index: Optional[int] = Query(None, ge=0, description="Page index (0-based)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Number of results per page"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    """Search authors with hybrid scoring and optional pagination.
    
    Returns a combination of semantic and keyword (BM25) scores with configurable weights.
    Vector and business scoring can be enabled via environment variables.
    Supports pagination with page_index and page_size parameters.
    """
    print(f"🔍 Searching authors: query='{q}', k={k}, page_index={page_index}, page_size={page_size}, app_id={app_id}")
    try:
        # Get search results from service layer
        result = get_search_service().search_authors(q, k, page_index, page_size, app_id)
        
        # Transform results to AuthorHit format for API response
        authors = [
            AuthorHit(
                id=doc["id"],
                full_name=doc.get("full_name"),
                score_final=result_item["_final"],
                scores={
                    "semantic": result_item["_semantic"], 
                    "bm25": result_item["_bm25"], 
                    "vector": result_item.get("_vector", 0.0),
                    "business": result_item.get("_business", 0.0)
                }
            ) for result_item in result["results"]
            if (doc := result_item["doc"])
        ]
        
        response = {
            "results": authors,
            "pagination": result["pagination"],
            "normalized_query": result["normalized_query"],
            "search_type": result.get("search_type", "authors")
        }
        
        print(f"✅ Authors search completed: {len(authors)} results")
        return response
    except Exception as e:
        print(f"❌ Authors search failed: {e}")
        raise

@app.get("/search")
def search_general(
    q: str = Query(..., min_length=1, description="Search query text"), 
    k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    page_index: Optional[int] = Query(None, ge=0, description="Page index (0-based)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Number of results per page"),
    app_id: Optional[str] = Query(None, description="Application ID for filtering results")
):
    """General search endpoint with intelligent query classification and routing.
    
    Uses LLM-powered planning to:
    1. Determine if query is meaningful
    2. Classify query type (articles vs authors)
    3. Route to appropriate search function
    4. Return unified response format
    
    Supports pagination with page_index and page_size parameters.
    """
    print(f"🔍 General search: query='{q}', k={k}, page_index={page_index}, page_size={page_size}, app_id={app_id}")
    try:
        # Get search results from service layer using general search
        result = get_search_service().search(q, k, page_index, page_size, app_id)
        
        # Transform results based on search type
        search_type = result.get("search_type", "articles")
        
        if search_type == "authors":
            # Transform results to AuthorHit format
            items = [
                AuthorHit(
                    id=doc["id"],
                    full_name=doc.get("full_name"),
                    score_final=result_item["_final"],
                    scores={
                        "semantic": result_item.get("_semantic", 0.0), 
                        "bm25": result_item.get("_bm25", 0.0), 
                        "vector": result_item.get("_vector", 0.0),
                        "business": result_item.get("_business", 0.0)
                    }
                ) for result_item in result["results"]
                if (doc := result_item.get("doc", {}))
            ]
        else:
            # Transform results to ArticleHit format (default)
            items = [
                ArticleHit(
                    id=doc["id"],
                    title=doc.get("title"),
                    abstract=doc.get("abstract"),
                    author_name=doc.get("author_name"),
                    score_final=result_item["_final"],
                    scores={
                        "semantic": result_item.get("_semantic", 0.0), 
                        "bm25": result_item.get("_bm25", 0.0), 
                        "vector": result_item.get("_vector", 0.0), 
                        "business": result_item.get("_business", 0.0)
                    },
                    highlights=doc.get("@search.highlights")
                ) for result_item in result["results"] 
                if (doc := result_item.get("doc", {}))
            ]
        
        response = {
            "results": items,
            "pagination": result["pagination"],
            "normalized_query": result["normalized_query"],
            "search_type": search_type
        }
        
        print(f"✅ General search completed: {len(items)} results, type: {search_type}")
        return response
    except Exception as e:
        print(f"❌ General search failed: {e}")
        raise


def main():
    """Main CLI entry point for the Azure AI Blog Search application."""
    try:
        args = parse_args()
        
        # Get command handlers from the dedicated module
        handlers = get_command_handlers()
        
        # Execute the appropriate handler for the command
        if args.command in handlers:
            handlers[args.command](args)
        else:
            print("❌ No command specified. Use --help to see available commands.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



