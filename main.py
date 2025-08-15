"""
Blog Search API with Azure AI Search + Cosmos DB + Embeddings

FastAPI entry points:
 - /search/articles?q=...&k=10
 - /search/authors?q=...&k=10

CLI commands:
 - create-indexes: Create Azure AI Search indexes
 - ingest: Load data from Cosmos DB into search indexes  
 - serve: Start the FastAPI server

Returns fused scores: semantic, bm25, vector, business (as configured).
"""

import sys
import uvicorn
from fastapi import FastAPI, Query
from typing import List

from app.models import ArticleHit, AuthorHit
from app.clients import articles_client, authors_client
from app.services.search_service import SearchService
from utils.cli import parse_args

print("🚀 Initializing Blog Search API...")

# Initialize FastAPI app
app = FastAPI(title="Blog Search API", version="1.0.0")

try:
    print("📋 Setting up search service...")
    svc = SearchService(articles_client(), authors_client())
    print("✅ Search service initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize search service: {e}")
    raise

@app.get("/search/articles", response_model=List[ArticleHit])
def search_articles(q: str = Query(..., min_length=1), k: int = 10):
    """Search articles with hybrid scoring: semantic + BM25 + vector + freshness."""
    print(f"🔍 Searching articles: query='{q}', k={k}")
    try:
        fused = svc.search_articles(q, k)
        out: List[ArticleHit] = []
        for r in fused:
            d = r["doc"]
            out.append(ArticleHit(
                id=d["id"],
                title=d.get("title"),
                abstract=d.get("abstract"),
                author_name=d.get("author_name"),
                score_final=r["_final"],
                scores={"semantic": r["_semantic"], "bm25": r["_bm25"], "vector": r["_vector"], "business": r["_business"]},
                highlights=d.get("@search.highlights")
            ))
        print(f"✅ Articles search completed: {len(out)} results")
        return out
    except Exception as e:
        print(f"❌ Articles search failed: {e}")
        raise

@app.get("/search/authors", response_model=List[AuthorHit])
def search_authors(q: str = Query(..., min_length=1), k: int = 10):
    """Search authors with hybrid scoring: semantic + BM25."""
    print(f"🔍 Searching authors: query='{q}', k={k}")
    try:
        fused = svc.search_authors(q, k)
        out: List[AuthorHit] = []
        for r in fused:
            d = r["doc"]
            out.append(AuthorHit(
                id=d["id"],
                full_name=d.get("full_name"),
                score_final=r["_final"],
                scores={"semantic": r["_semantic"], "bm25": r["_bm25"], "vector": r.get("_vector", 0.0)}
            ))
        print(f"✅ Authors search completed: {len(out)} results")
        return out
    except Exception as e:
        print(f"❌ Authors search failed: {e}")
        raise

def main():
    """Main CLI entry point."""
    try:
        args = parse_args()
        
        if args.command == 'create-indexes':
            print("🏗️  Creating Azure AI Search indexes...")
            from search.indexes import create_indexes
            
            reset = args.reset if hasattr(args, 'reset') else True
            verbose = args.verbose if hasattr(args, 'verbose') else False
            
            print(f"📋 Options: reset={reset}, verbose={verbose}")
            create_indexes(reset=reset, verbose=verbose)
            print("✅ Index creation completed successfully")
            
        elif args.command == 'ingest':
            print("📥 Starting data ingestion from Cosmos DB...")
            from search.ingestion import ingest_data
            
            verbose = args.verbose if hasattr(args, 'verbose') else False
            batch_size = args.batch_size if hasattr(args, 'batch_size') else 100
            
            print(f"📋 Options: verbose={verbose}, batch_size={batch_size}")
            ingest_data(verbose=verbose, batch_size=batch_size)
            print("✅ Data ingestion completed successfully")
            
        elif args.command == 'serve':
            print("🌐 Starting FastAPI server...")
            host = args.host if hasattr(args, 'host') else '127.0.0.1'
            port = args.port if hasattr(args, 'port') else 8000
            reload = args.reload if hasattr(args, 'reload') else False
            workers = args.workers if hasattr(args, 'workers') else 1
            
            print(f"📋 Server options: {host}:{port}, reload={reload}, workers={workers}")
            uvicorn.run(
                "main:app", 
                host=host, 
                port=port, 
                reload=reload, 
                workers=workers if not reload else 1  # uvicorn doesn't support workers with reload
            )
            
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
