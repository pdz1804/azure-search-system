"""
Search Service for Azure AI Search Integration

This module implements a high-level search service that combines multiple scoring methods 
for both articles and authors:

Articles search combines:
 - Semantic search (natural language understanding)
 - BM25 (keyword matching)
 - Vector search (embedding similarity)
 - Business logic (freshness boost)

Authors search combines:
 - Semantic search (natural language understanding)
 - BM25 (keyword matching)
 - Optional vector/business components if weights > 0

The service handles pagination, error recovery, and score fusion with configurable weights.
"""

from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import HttpResponseError

from ai_search.config.settings import SETTINGS
from ai_search.app.services.scoring import business_freshness, fuse_articles, fuse_authors
from ai_search.app.services.embeddings import encode 
from ai_search.app.services.llm_service import LLMService

class SearchService:
    def __init__(self, articles_sc: SearchClient, authors_sc: SearchClient):
        print("🔧 Initializing SearchService...")
        self.articles = articles_sc
        self.authors = authors_sc
        
        # Initialize LLM service for query enhancement and answer generation
        self.llm_service = LLMService()
        
        # Test semantic search capability on startup
        self.semantic_enabled = self._test_semantic_search()
        if self.semantic_enabled:
            print("✅ Semantic search is available")
        else:
            print("⚠️ Semantic search is not available")
        
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

    def search_articles(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Enhanced search for articles with LLM-powered query normalization and answer generation.
        
        Args:
            query: User search query
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            
        Returns:
            Dict containing articles, normalized_query, final_answer, and pagination info
        """
        # Step 1: Normalize query using LLM
        query_enhancement = self.llm_service.normalize_query(query, "articles")
        normalized_query = query_enhancement["normalized_query"]
        search_params = query_enhancement["search_parameters"]
        
        # Handle pagination parameters
        if page_index is not None and page_size is not None:
            # Calculate offset and adjust k for pagination
            offset = page_index * page_size
            total_needed = offset + page_size
            search_k = max(total_needed, k * 2)  # Search more to ensure we have enough results
            print(f"📖 Starting paginated articles search: query='{normalized_query}', page_index={page_index}, page_size={page_size}, search_k={search_k}")
        else:
            search_k = k
            offset = 0
            print(f"📖 Starting articles search: query='{normalized_query}', k={k}")
        
        try:
            # A) Text search with semantic reranker if available
            if self.semantic_enabled:
                print("🔍 Executing semantic+BM25 search for articles...")
                try:
                    # Apply enhanced search parameters
                    search_kwargs = {
                        "search_text": normalized_query,
                        "query_type": "semantic",
                        "semantic_configuration_name": "articles-semantic",
                        "top": int(search_k*1.3),
                        "select": ["id","title","abstract","author_name","business_date"],
                        "highlight_fields": search_params.get("highlight_fields", "searchable_text")
                    }
                    
                    # Add optional parameters from LLM enhancement
                    if search_params.get("filter"):
                        search_kwargs["filter"] = search_params["filter"]
                    if search_params.get("order_by"):
                        search_kwargs["order_by"] = search_params["order_by"]
                    if search_params.get("search_fields"):
                        search_kwargs["search_fields"] = search_params["search_fields"]
                    
                    print(f"Search params: {search_kwargs}")
                    
                    text_res = self.articles.search(**search_kwargs)
                except HttpResponseError as he:
                    # Service doesn't actually support semantic at runtime - fallback
                    if "SemanticQueriesNotAvailable" in str(he) or "FeatureNotSupportedInService" in str(he):
                        print("⚠️ Semantic search rejected by service at runtime - falling back to BM25")
                        self.semantic_enabled = False
                        
                        # Apply enhanced search parameters
                        search_kwargs = {
                            "search_text": normalized_query,
                            "query_type": "simple",
                            "top": int(search_k*1.3),
                            "select": ["id","title","abstract","author_name","business_date"],
                            "highlight_fields": "searchable_text"
                        }
                        
                        # Add optional parameters from LLM enhancement
                        if search_params.get("filter"):
                            search_kwargs["filter"] = search_params["filter"]
                        if search_params.get("order_by"):
                            search_kwargs["order_by"] = search_params["order_by"]
                        if search_params.get("search_fields"):
                            search_kwargs["search_fields"] = search_params["search_fields"]
                        
                        print(f"Search params: {search_kwargs}")
                        
                        text_res = self.articles.search(**search_kwargs)
                        
                    else:
                        raise
            else:
                print("🔍 Executing BM25-only search for articles (semantic not available)...")
                # Apply enhanced search parameters
                search_kwargs = {
                    "search_text": normalized_query,
                    "query_type": "simple",
                    "top": int(search_k*1.3),
                    "select": ["id","title","abstract","author_name","business_date"],
                    "highlight_fields": "searchable_text"
                }
                
                # Add optional parameters from LLM enhancement
                if search_params.get("filter"):
                    search_kwargs["filter"] = search_params["filter"]
                if search_params.get("order_by"):
                    search_kwargs["order_by"] = search_params["order_by"]
                if search_params.get("search_fields"):
                    search_kwargs["search_fields"] = search_params["search_fields"]
                
                print(f"Search params: {search_kwargs}")
                
                text_res = self.articles.search(**search_kwargs)
            
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
            qvec = encode(normalized_query)
            print(f"✅ Generated embedding vector (dim={len(qvec)})")
            
            print("🔍 Executing vector search for articles...")
            
            # Apply same enhanced search parameters to vector search for consistency
            vector_search_kwargs = {
                "search_text": None,
                "vector_queries": [VectorizedQuery(vector=qvec, k=int(search_k*1.3), fields="content_vector")],
                "top": int(search_k*1.3),
                "select": ["id"]
            }
            
            # Add same filter, order_by parameters from LLM enhancement for consistent results
            if search_params.get("filter"):
                vector_search_kwargs["filter"] = search_params["filter"]
            if search_params.get("order_by"):
                vector_search_kwargs["order_by"] = search_params["order_by"]
            
            print(f"Vector search params: {vector_search_kwargs}")
            
            vec_res = self.articles.search(**vector_search_kwargs)
            
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
            all_fused_results = fuse_articles(list(id_to_row.values()))
            
            # Step 2: Generate final answer using LLM
            final_answer = self.llm_service.generate_answer(query, all_fused_results, "articles")
            
            # Apply pagination if requested
            if page_index is not None and page_size is not None:
                total_results = len(all_fused_results)
                start_idx = offset
                end_idx = start_idx + page_size
                paginated_results = all_fused_results[start_idx:end_idx]
                
                print(f"✅ Articles search completed: {len(paginated_results)} results (page {page_index + 1}, total: {total_results})")
                
                return {
                    "results": paginated_results,
                    "normalized_query": normalized_query,
                    "final_answer": final_answer,
                    "pagination": {
                        "page_index": page_index,
                        "page_size": page_size,
                        "total_results": total_results,
                        "total_pages": (total_results + page_size - 1) // page_size,
                        "has_next": end_idx < total_results,
                        "has_previous": page_index > 0
                    }
                }
            else:
                final_results = all_fused_results[:k]
                print(f"✅ Articles search completed: {len(final_results)} final results")
                
                return {
                    "results": final_results,
                    "normalized_query": normalized_query,
                    "final_answer": final_answer,
                    "pagination": None
                }
            
        except Exception as e:
            print(f"❌ Articles search failed: {e}")
            raise

    def search_authors(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Enhanced search for authors with LLM-powered query normalization and answer generation.
        
        Args:
            query: User search query
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            
        Returns:
            Dict containing authors, normalized_query, final_answer, and pagination info
        """
        # Step 1: Normalize query using LLM
        query_enhancement = self.llm_service.normalize_query(query, "authors")
        normalized_query = query_enhancement["normalized_query"]
        search_params = query_enhancement["search_parameters"]
        
        print(f"Search params: {search_params}")
        
        # Handle pagination parameters
        if page_index is not None and page_size is not None:
            # Calculate offset and adjust k for pagination
            offset = page_index * page_size
            total_needed = offset + page_size
            search_k = max(total_needed, k * 2)  # Search more to ensure we have enough results
            print(f"👤 Starting paginated authors search: query='{normalized_query}', page_index={page_index}, page_size={page_size}, search_k={search_k}")
        else:
            search_k = k
            offset = 0
            print(f"👤 Starting authors search: query='{normalized_query}', k={k}")
        
        try:
            if self.semantic_enabled:
                print("🔍 Executing semantic+BM25 search for authors...")
                try:
                    text_res = self.authors.search(
                        search_text=normalized_query,
                        query_type="semantic",
                        semantic_configuration_name="authors-semantic",
                        top=search_k,
                        select=["id","full_name"]
                    )
                except HttpResponseError as he:
                    if "SemanticQueriesNotAvailable" in str(he) or "FeatureNotSupportedInService" in str(he):
                        print("⚠️ Semantic search rejected by service at runtime for authors - falling back to BM25")
                        self.semantic_enabled = False
                        text_res = self.authors.search(
                            search_text=normalized_query,
                            query_type="simple",
                            top=search_k,
                            select=["id","full_name"]
                        )
                    else:
                        raise
            else:
                print("🔍 Executing BM25-only search for authors (semantic not available)...")
                text_res = self.authors.search(
                    search_text=normalized_query,
                    query_type="simple",
                    top=search_k,
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
                qvec = encode(normalized_query)
                print(f"✅ Generated embedding vector (dim={len(qvec)})")
                
                print("🔍 Executing vector search for authors...")
                vec_res = self.authors.search(
                    search_text=None,
                    vector_queries=[VectorizedQuery(vector=qvec, k=search_k, fields="name_vector")],
                    top=search_k, select=["id"]
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
            all_fused_results = fuse_authors(rows)
            
            # Step 2: Generate final answer using LLM
            final_answer = self.llm_service.generate_answer(query, all_fused_results, "authors")
            
            # Apply pagination if requested
            if page_index is not None and page_size is not None:
                total_results = len(all_fused_results)
                start_idx = offset
                end_idx = start_idx + page_size
                paginated_results = all_fused_results[start_idx:end_idx]
                
                print(f"✅ Authors search completed: {len(paginated_results)} results (page {page_index + 1}, total: {total_results})")
                
                return {
                    "results": paginated_results,
                    "normalized_query": normalized_query,
                    "final_answer": final_answer,
                    "pagination": {
                        "page_index": page_index,
                        "page_size": page_size,
                        "total_results": total_results,
                        "total_pages": (total_results + page_size - 1) // page_size,
                        "has_next": end_idx < total_results,
                        "has_previous": page_index > 0
                    }
                }
            else:
                final_results = all_fused_results[:k]
                print(f"✅ Authors search completed: {len(final_results)} final results")
                
                return {
                    "results": final_results,
                    "normalized_query": normalized_query,
                    "final_answer": final_answer,
                    "pagination": None
                }
            
        except Exception as e:
            print(f"❌ Authors search failed: {e}")
            raise
