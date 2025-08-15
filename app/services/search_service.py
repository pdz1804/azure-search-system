"""
High-level search service:
 - Articles: semantic + bm25 + vector + business
 - Authors : semantic + bm25 (+ optional vector/business if weights > 0)
"""

from typing import List, Dict, Any
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import HttpResponseError

from config.settings import SETTINGS
from .scoring import business_freshness, fuse_articles, fuse_authors
from app.services.embeddings import encode

class SearchService:
    def __init__(self, articles_sc: SearchClient, authors_sc: SearchClient):
        print("🔧 Initializing SearchService...")
        self.articles = articles_sc
        self.authors = authors_sc
        
        # Test semantic search capability on startup
        self.semantic_enabled = self._test_semantic_search()
        if self.semantic_enabled:
            print("✅ Semantic search is available")
        else:
            print("⚠️ Semantic search is not available - will use BM25 only for text search")
        
        print("✅ SearchService initialized successfully")
    
    def _test_semantic_search(self) -> bool:
        """Test if semantic search is available on this service."""
        try:
            # Try a simple semantic search to test capability
            test_result = self.articles.search(
                search_text="test",
                query_type="semantic",
                semantic_configuration_name="articles-semantic",
                top=1
            )
            # The SDK returns a pageable object without performing the request until iterated.
            # Force iteration (or a single next()) so any HttpResponseError is raised here.
            try:
                next(iter(test_result))
                # If iteration succeeded (even with zero results), semantic queries are supported
                return True
            except StopIteration:
                # No results in the index but the semantic query executed successfully
                return True
        except HttpResponseError as e:
            if "SemanticQueriesNotAvailable" in str(e) or "FeatureNotSupportedInService" in str(e):
                return False
            # Re-raise other errors as they're unexpected
            raise
        except Exception:
            # For any other errors, assume semantic search is not available
            return False

    def search_articles(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        print(f"📖 Starting articles search: query='{query}', k={k}")
        
        try:
            # A) Text search with semantic reranker if available
            if self.semantic_enabled:
                print("🔍 Executing semantic+BM25 search for articles...")
                try:
                    text_res = self.articles.search(
                        search_text=query,
                        query_type="semantic",
                        semantic_configuration_name="articles-semantic",
                        top=int(k*1.3), # search more candidates
                        select=["id","title","abstract","author_name","business_date"],
                        highlight_fields="searchable_text"
                    )
                except HttpResponseError as he:
                    # Service doesn't actually support semantic at runtime - fallback
                    if "SemanticQueriesNotAvailable" in str(he) or "FeatureNotSupportedInService" in str(he):
                        print("⚠️ Semantic search rejected by service at runtime - falling back to BM25")
                        self.semantic_enabled = False
                        text_res = self.articles.search(
                            search_text=query,
                            query_type="simple",
                            top=int(k*1.3),
                            select=["id","title","abstract","author_name","business_date"],
                            highlight_fields="searchable_text"
                        )
                    else:
                        raise
            else:
                print("🔍 Executing BM25-only search for articles (semantic not available)...")
                text_res = self.articles.search(
                    search_text=query,
                    query_type="simple",
                    top=int(k*1.3),
                    select=["id","title","abstract","author_name","business_date"],
                    highlight_fields="searchable_text"
                )
            
            rows: List[Dict[str, Any]] = []
            text_count = 0
            for d in text_res:
                text_count += 1
                rows.append({
                    "id": d["id"],
                    "doc": d,
                    "_bm25": d["@search.score"],
                    "_semantic": d.get("@search.rerankerScore", 0.0),  # Will be 0.0 if no semantic search
                    "_vector": 0.0,
                    "_business": business_freshness(d.get("business_date")),
                })
            print(f"✅ Text search returned {text_count} results")

            # B) Vector KNN
            print("🧮 Generating query embedding for vector search...")
            qvec = encode(query)
            print(f"✅ Generated embedding vector (dim={len(qvec)})")
            
            print("🔍 Executing vector search for articles...")
            vec_res = self.articles.search(
                search_text=None,
                vector_queries=[VectorizedQuery(vector=qvec, k=int(k*1.3), fields="content_vector")],
                top=int(k*1.3), select=["id"]
            )
            
            id_to_row = {r["id"]: r for r in rows}
            vec_count = 0
            vec_new_count = 0
            
            for d in vec_res:
                vec_count += 1
                vid = d["id"]
                vscore = d["@search.score"]  # cosine sim ~ [0,1] after normalization in Azure
                if vid in id_to_row:
                    id_to_row[vid]["_vector"] = vscore
                else:
                    vec_new_count += 1
                    # pull minimal doc to compute business freshness
                    full = self.articles.get_document(vid)
                    id_to_row[vid] = {
                        "id": vid, "doc": full,
                        "_bm25": 0.0, "_semantic": 0.0, "_vector": vscore,
                        "_business": business_freshness(full.get("business_date"))
                    }
            
            print(f"✅ Vector search returned {vec_count} results ({vec_new_count} new documents)")
            
            print("⚖️ Fusing article scores...")
            fused_results = fuse_articles(list(id_to_row.values()))[:k]
            print(f"✅ Articles search completed: {len(fused_results)} final results")
            
            return fused_results
            
        except Exception as e:
            print(f"❌ Articles search failed: {e}")
            raise

    def search_authors(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        print(f"👤 Starting authors search: query='{query}', k={k}")
        
        try:
            if self.semantic_enabled:
                print("🔍 Executing semantic+BM25 search for authors...")
                try:
                    text_res = self.authors.search(
                        search_text=query,
                        query_type="semantic",
                        semantic_configuration_name="authors-semantic",
                        top=k,
                        select=["id","full_name"]
                    )
                except HttpResponseError as he:
                    if "SemanticQueriesNotAvailable" in str(he) or "FeatureNotSupportedInService" in str(he):
                        print("⚠️ Semantic search rejected by service at runtime for authors - falling back to BM25")
                        self.semantic_enabled = False
                        text_res = self.authors.search(
                            search_text=query,
                            query_type="simple",
                            top=k,
                            select=["id","full_name"]
                        )
                    else:
                        raise
            else:
                print("🔍 Executing BM25-only search for authors (semantic not available)...")
                text_res = self.authors.search(
                    search_text=query,
                    query_type="simple",
                    top=k,
                    select=["id","full_name"]
                )
            
            rows: List[Dict[str, Any]] = []
            text_count = 0
            for d in text_res:
                text_count += 1
                rows.append({
                    "id": d["id"], "doc": d,
                    "_bm25": d["@search.score"],
                    "_semantic": d.get("@search.rerankerScore", 0.0),  # Will be 0.0 if no semantic search
                    "_vector": 0.0, "_business": 0.0
                })
            print(f"✅ Text search returned {text_count} results")

            if SETTINGS.aw_vector > 0.0:
                print("🧮 Vector search enabled for authors, generating embedding...")
                qvec = encode(query)
                print(f"✅ Generated embedding vector (dim={len(qvec)})")
                
                print("🔍 Executing vector search for authors...")
                vec_res = self.authors.search(
                    search_text=None,
                    vector_queries=[VectorizedQuery(vector=qvec, k=k, fields="name_vector")],
                    top=k, select=["id"]
                )
                
                id_to_row = {r["id"]: r for r in rows}
                vec_count = 0
                vec_new_count = 0
                
                for d in vec_res:
                    vec_count += 1
                    uid, vscore = d["id"], d["@search.score"]
                    if uid in id_to_row:
                        id_to_row[uid]["_vector"] = vscore
                    else:
                        vec_new_count += 1
                        full = self.authors.get_document(uid)
                        id_to_row[uid] = {"id": uid, "doc": full, "_bm25": 0.0, "_semantic": 0.0, "_vector": vscore, "_business": 0.0}
                
                print(f"✅ Vector search returned {vec_count} results ({vec_new_count} new documents)")
                rows = list(id_to_row.values())
            else:
                print("⚠️ Vector search disabled for authors (weight = 0.0)")

            print("⚖️ Fusing author scores...")
            fused_results = fuse_authors(rows)[:k]
            print(f"✅ Authors search completed: {len(fused_results)} final results")
            
            return fused_results
            
        except Exception as e:
            print(f"❌ Authors search failed: {e}")
            raise



