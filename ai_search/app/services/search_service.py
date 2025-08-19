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

import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import HttpResponseError

from ai_search.app.services.llm_service import LLMService
from ai_search.app.services.scoring import fuse_articles, fuse_authors, business_freshness
from ai_search.app.services.embeddings import encode
from ai_search.config.settings import SETTINGS

class SearchService:
    def __init__(self, articles_sc: SearchClient, authors_sc: SearchClient):
        print("🔧 Initializing SearchService...")
        self.articles = articles_sc
        self.authors = authors_sc
        
        # Initialize LLM service for query enhancement and answer generation
        self.llm_service = LLMService()
        
        # Check semantic search capability
        self.semantic_enabled = self._test_semantic_search()
        
        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        if self.semantic_enabled:
            print("✅ Semantic search is available")
        else:
            print("⚠️ Semantic search is not available")
        
        print("✅ SearchService initialized successfully")
    
    def search(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        General search function that uses LLM planning to classify and route queries.
        
        This is the main entry point for all search operations. It:
        1. Uses LLM to plan the query (classify type and normalize)
        2. Routes to appropriate search function based on classification
        3. Returns unified response format
        
        Args:
            query: User search query
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            
        Returns:
            Dict containing search results with unified format
        """
        print(f"🔍 General search initiated: '{query}'")
        
        # Step 1: Plan the query using LLM
        plan = self.llm_service.plan_query(query)
        
        # Step 2: Handle non-meaningful queries
        if not plan.get("isMeaningful", True):
            print(f"❌ Query classified as non-meaningful")
            return {
                "results": [],
                "normalized_query": "I'm sorry, but your query doesn't appear to be meaningful or searchable. Please try rephrasing your question with clear, specific terms.",
                "pagination": {
                    "page_index": page_index,
                    "page_size": page_size,
                    "total_results": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False
                } if page_index is not None and page_size is not None else None,
                "search_type": plan.get("search_type", "unmeaningful")
            }
        
        # Step 3: Route to appropriate search function based on classification
        search_type = plan.get("search_type", "articles")
        
        if search_type == "authors":
            print(f"📋 Routing to authors search")
            return self._search_authors_planned(query, plan, k, page_index, page_size)
        elif search_type == "articles":
            print(f"📋 Routing to articles search")
            return self._search_articles_planned(query, plan, k, page_index, page_size)
        else:
            # Fallback for unmeaningful or unknown types
            print(f"❓ Unknown search type: {search_type}, defaulting to articles")
            return self._search_articles_planned(query, plan, k, page_index, page_size)
    
    def search_articles(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for articles using LLM planning for query enhancement.
        
        Args:
            query: User search query
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            
        Returns:
            Dict containing articles search results
        """
        print(f"📖 Articles search: '{query}'")
        
        # Use LLM planning to enhance the query
        plan = self.llm_service.plan_query(query)
        
        # Force search type to articles for this endpoint
        plan["search_type"] = "articles"
        
        # Handle non-meaningful queries
        if not plan.get("isMeaningful", True):
            print(f"❌ Query is not meaningful: '{query}'")
            
            return {
                "results": [],
                "normalized_query": "I'm sorry, but your query doesn't appear to be meaningful or searchable. Please try rephrasing your question with clear, specific terms.",
                "pagination": {
                    "page_index": page_index,
                    "page_size": page_size,
                    "total_results": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False
                } if page_index is not None and page_size is not None else None,
                "search_type": "articles",
                "confidence": plan.get("confidence", 0.0),
                "explanation": plan.get("explanation", "Query appears to be meaningless")
            }
        
        # Use the planned search function
        return self._search_articles_planned(query, plan, k, page_index, page_size)

    def search_authors(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for authors using LLM planning for query enhancement.
        
        Args:
            query: User search query
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            
        Returns:
            Dict containing authors search results
        """
        print(f"👤 Authors search: '{query}'")
        
        # Use LLM planning to enhance the query
        plan = self.llm_service.plan_query(query)
        
        # Force search type to authors for this endpoint
        plan["search_type"] = "authors"
        
        # Handle non-meaningful queries
        if not plan.get("isMeaningful", True):
            print(f"❌ Query is not meaningful: '{query}'")
            return {
                "results": [],
                "normalized_query": "I'm sorry, but your query doesn't appear to be meaningful or searchable. Please try rephrasing your question with clear, specific terms.",
                "pagination": {
                    "page_index": page_index,
                    "page_size": page_size,
                    "total_results": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False
                } if page_index is not None and page_size is not None else None,
                "search_type": "authors"
            }
        
        # Use the planned search function
        return self._search_authors_planned(query, plan, k, page_index, page_size)
    
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
    
    def _batch_get_documents(self, client: SearchClient, document_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch retrieve documents by IDs to avoid N+1 query problem.
        
        Args:
            client: SearchClient instance (articles or authors)
            document_ids: List of document IDs to retrieve
            
        Returns:
            Dict mapping document ID to document data
        """
        if not document_ids:
            return {}
        
        print(f"📦 Batch retrieving {len(document_ids)} documents")
        
        try:
            # Use search with ID filter to batch retrieve documents
            id_filter = " or ".join([f"id eq '{doc_id}'" for doc_id in document_ids])
            
            results = client.search(
                search_text="*",
                filter=id_filter,
                top=len(document_ids),
                select=["*"]  # Get all fields
            )
            
            # Convert to dict for fast lookup
            doc_dict = {doc["id"]: doc for doc in results}
            print(f"✅ Successfully retrieved {len(doc_dict)} documents")
            return doc_dict
            
        except Exception as e:
            print(f"⚠️ Batch document retrieval failed: {e}")
            # Fallback to individual retrieval
            doc_dict = {}
            for doc_id in document_ids:
                try:
                    doc_dict[doc_id] = client.get_document(doc_id)
                except Exception as individual_error:
                    print(f"⚠️ Failed to retrieve document {doc_id}: {individual_error}")
            return doc_dict

    def _search_authors_planned(self, original_query: str, plan: Dict[str, Any], k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Internal authors search function that uses pre-planned query data.
        
        Args:
            original_query: Original user query
            plan: Query plan from LLM containing normalized_query and search_parameters
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            
        Returns:
            Dict containing authors search results
        """
        normalized_query = plan["normalized_query"]
        
        # Handle pagination parameters
        if page_index is not None and page_size is not None:
            offset = page_index * page_size
            total_needed = offset + page_size
            search_k = max(total_needed, k * 2)
            print(f"👤 Starting planned authors search: query='{normalized_query}', page_index={page_index}, page_size={page_size}, search_k={search_k}")
        else:
            search_k = k
            offset = 0
            print(f"👤 Starting planned authors search: query='{normalized_query}', k={k}")
        
        try:
            # Get all authors and perform fuzzy matching (as per established approach)
            print("🔍 Getting all authors from index for fuzzy matching...")
            all_authors = self._get_all_authors()
            print(f"📋 Retrieved {len(all_authors)} authors from index")
            
            # Perform fuzzy matching
            print(f"🔍 Performing fuzzy matching for query: '{normalized_query}'")
            fuzzy_matches = self._fuzzy_match_authors(normalized_query, all_authors, search_k)
            
            # Convert fuzzy matches to the expected format for fuse_authors
            rows: List[Dict[str, Any]] = []
            for i, (author_doc, score) in enumerate(fuzzy_matches):
                rows.append({
                    "id": author_doc["id"], 
                    "doc": author_doc,
                    "_bm25": score,  # Use fuzzy match score as BM25 score
                    "_semantic": 0.0, 
                    "_vector": 0.0, 
                    "_business": 0.0
                })
            
            print(f"✅ Fuzzy matching returned {len(rows)} results")
            
            # Fuse results
            print("⚖️ Fusing author scores...")
            all_fused_results = fuse_authors(rows)
            total_results = len(all_fused_results)
            
            # Apply pagination if requested
            if page_index is not None and page_size is not None:
                start_idx = offset
                end_idx = start_idx + page_size
                paginated_results = all_fused_results[start_idx:end_idx]
                
                print(f"✅ Authors search completed: {len(paginated_results)} results (page {page_index + 1}, total: {total_results})")
                
                # Generate final answer
                # final_answer = self.llm_service.generate_answer(original_query, paginated_results, "authors")
                
                return {
                    "results": paginated_results,
                    "normalized_query": normalized_query,
                    # "final_answer": final_answer,
                    "pagination": {
                        "page_index": page_index,
                        "page_size": page_size,
                        "total_results": total_results,
                        "total_pages": (total_results + page_size - 1) // page_size,
                        "has_next": end_idx < total_results,
                        "has_previous": page_index > 0
                    },
                    "search_type": "authors"
                }
            else:
                final_results = all_fused_results[:k]
                print(f"✅ Authors search completed: {len(final_results)} final results")
                
                # Generate final answer
                # final_answer = self.llm_service.generate_answer(original_query, final_results, "authors")
                
                return {
                    "results": final_results,
                    "normalized_query": normalized_query,
                    # "final_answer": final_answer,
                    "pagination": None,
                    "search_type": "authors"
                }
                
        except Exception as e:
            print(f"❌ Authors search failed: {e}")
            raise
    
    def _search_articles_planned(self, original_query: str, plan: Dict[str, Any], k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Internal articles search function that uses pre-planned query data.
        
        Args:
            original_query: Original user query
            plan: Query plan from LLM containing normalized_query and search_parameters
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            
        Returns:
            Dict containing articles search results
        """
        normalized_query = plan["normalized_query"]
        search_params = plan["search_parameters"]
        
        # Handle pagination parameters
        if page_index is not None and page_size is not None:
            # Calculate offset and adjust k for pagination
            offset = page_index * page_size
            total_needed = offset + page_size
            search_k = max(total_needed, k * 2)
            print(f"📖 Starting planned articles search: query='{normalized_query}', page_index={page_index}, page_size={page_size}, search_k={search_k}")
        else:
            search_k = k
            offset = 0
            print(f"📖 Starting planned articles search: query='{normalized_query}', k={k}")
        
        # Continue with existing search logic but without normalization step
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
                        "top": int(search_k*1.1),
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
                            "top": int(search_k*1.1),
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
            
            # B) Vector KNN - Run in parallel with text search
            def run_vector_search():
                print("🧮 Generating query embedding for vector search...")
                qvec = encode(normalized_query)
                print(f"✅ Generated embedding vector (dim={len(qvec)})")
                
                print("🔍 Executing vector search for articles...")
                
                # Apply same enhanced search parameters to vector search for consistency
                vector_search_kwargs = {
                    "search_text": None,
                    "vector_queries": [VectorizedQuery(vector=qvec, k=int(search_k*1.1), fields="content_vector")],
                    "top": int(search_k*1.1),
                    "select": ["id"]
                }
                
                # Add same filter, order_by parameters from LLM enhancement for consistent results
                if search_params.get("filter"):
                    vector_search_kwargs["filter"] = search_params["filter"]
                if search_params.get("order_by"):
                    vector_search_kwargs["order_by"] = search_params["order_by"]
                
                print(f"Vector search params: {vector_search_kwargs}")
                
                return self.articles.search(**vector_search_kwargs)
            
            # Run vector search in parallel with text search processing
            vector_future = self.executor.submit(run_vector_search)
            vec_res = vector_future.result()
            
            id_to_row = {r["id"]: r for r in rows}
            vec_count = 0
            vec_new_ids = []
            
            for d in vec_res:
                vec_count += 1
                vid = d["id"]
                vscore = d["@search.score"]  # cosine sim ~ [0,1] after normalization in Azure
                if vid in id_to_row:
                    id_to_row[vid]["_vector"] = vscore
                else:
                    vec_new_ids.append((vid, vscore))
            
            # Batch retrieve new documents found only in vector search
            if vec_new_ids:
                new_doc_ids = [vid for vid, _ in vec_new_ids]
                batch_docs = self._batch_get_documents(self.articles, new_doc_ids)
                
                for vid, vscore in vec_new_ids:
                    if vid in batch_docs:
                        full = batch_docs[vid]
                        id_to_row[vid] = {
                            "id": vid, "doc": full,
                            "_bm25": 0.0, "_semantic": 0.0, "_vector": vscore,
                            "_business": business_freshness(full.get("business_date"))
                        }
            
            vec_new_count = len(vec_new_ids)
            print(f"✅ Vector search returned {vec_count} results ({vec_new_count} new documents)")
            
            print("⚖️ Fusing article scores...")
            all_fused_results = fuse_articles(list(id_to_row.values()))
            
            # Step 2: Generate final answer using LLM
            # final_answer = self.llm_service.generate_answer(query, all_fused_results, "articles")
            
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
                    # "final_answer": final_answer,
                    "pagination": {
                        "page_index": page_index,
                        "page_size": page_size,
                        "total_results": total_results,
                        "total_pages": (total_results + page_size - 1) // page_size,
                        "has_next": end_idx < total_results,
                        "has_previous": page_index > 0
                    },
                    "search_type": "articles",
                    # "confidence": plan.get("confidence", 0.8)
                }
            else:
                final_results = all_fused_results[:k]
                print(f"✅ Articles search completed: {len(final_results)} final results")
                
                return {
                    "results": final_results,
                    "normalized_query": normalized_query,
                    # "final_answer": final_answer,
                    "pagination": None,
                    "search_type": "articles"
                }
                
        except Exception as e:
            print(f"❌ Articles search failed: {e}")
            raise

    def _get_all_authors(self) -> List[Dict[str, Any]]:
        """
        Get all authors from the index for fuzzy matching.
        
        Returns:
            List of all author documents
        """
        try:
            # Use wildcard search to get all authors
            all_results = self.authors.search(
                search_text="*",
                query_type="simple",
                # top=10000,  # Large number to get all authors
                select=["id", "full_name"]
            )
            
            authors = []
            for doc in all_results:
                authors.append(doc)
            
            return authors
            
        except Exception as e:
            print(f"❌ Failed to retrieve all authors: {e}")
            return []
    
    def _fuzzy_match_authors(self, query: str, all_authors: List[Dict[str, Any]], k: int) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform fuzzy matching against all author names.
        
        Args:
            query: Search query
            all_authors: List of all author documents
            k: Number of top matches to return
            
        Returns:
            List of tuples (author_doc, similarity_score) sorted by score descending
        """
        if not all_authors:
            return []
        
        matches = []
        query_lower = query.lower().strip()
        
        for author in all_authors:
            full_name = author.get("full_name", "").lower()
            
            # Calculate similarity scores for different fields
            name_similarity = SequenceMatcher(None, query_lower, full_name).ratio()
            
            # Check for partial matches (substring matching)
            partial_name_match = 0.0
            
            if query_lower in full_name:
                partial_name_match = 0.8  # High score for substring match
            elif any(word in full_name for word in query_lower.split()):
                partial_name_match = 0.6  # Medium score for word match
             
            # Combine scores with weights favoring name matches
            final_score = max(
                name_similarity * 1.0,           # Full name similarity
                partial_name_match               # Partial name matches
            )
            
            # Only include matches above a threshold
            if final_score > 0.1:
                matches.append((author, final_score))
        
        # Sort by score descending and return top k
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:k]
