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
import unicodedata
import re
import math
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import HttpResponseError

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'ai_search'))

from ai_search.app.services.llm_service import LLMService
from ai_search.app.services.scoring import fuse_articles, fuse_authors, business_freshness
from ai_search.app.services.embeddings import encode
from ai_search.config.settings import SETTINGS
from ai_search.app.clients import articles_client, authors_client

class BackendSearchService:
    def __init__(self, articles_sc: SearchClient, authors_sc: SearchClient):

        if not articles_sc or not authors_sc:
            raise ValueError("Both articles_sc and authors_sc SearchClient instances are required")

        self.articles = articles_sc
        self.authors = authors_sc
        self.azure_search_available = True
        
        try:
            self.llm_service = LLMService()
        except Exception as e:
            self.llm_service = None
        
        self.semantic_enabled = self._test_semantic_search()

        self.executor = ThreadPoolExecutor(max_workers=4)

        if self.semantic_enabled:
            pass
        else:
            pass

    def _apply_score_threshold(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply score threshold filtering to search results.
        
        Args:
            results: List of search results with _final scores
            
        Returns:
            Filtered list of results above the score threshold
        """
        if not SETTINGS.enable_score_filtering:
            return results
        
        if SETTINGS.score_threshold <= 0.0:
            return results
        
        original_count = len(results)
        filtered_results = [r for r in results if r.get("_final", 0.0) >= SETTINGS.score_threshold]
        filtered_count = len(filtered_results)
        
        if filtered_count < original_count:
            pass
        
        return filtered_results
    
    def _get_app_id_filter(self, app_id: str = None) -> str:
        """
        Get the app_id filter string for the current application.
        
        Args:
            app_id: Application ID to filter by
        
        Returns:
            Filter string for app_id, or empty string if not provided
        """
        if not app_id:
            return ""
        
        app_filter = f"app_id eq '{app_id}'"
        return app_filter
    
    def _merge_filters(self, existing_filter: str, app_filter: str) -> str:
        """
        Merge existing filter with app_id filter.
        
        Args:
            existing_filter: Existing filter string
            app_filter: App ID filter string
            
        Returns:
            Combined filter string
        """
        if not app_filter:
            return existing_filter
        
        if not existing_filter:
            return app_filter
        
        return f"({existing_filter}) and ({app_filter})"
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for better fuzzy matching by removing diacritics and standardizing.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text without diacritics, lowercase, and cleaned
        """
        if not text:
            return ""
        
        text = text.lower()
        
        normalized = unicodedata.normalize('NFD', text)
        without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        cleaned = re.sub(r'[^\w\s]', ' ', without_accents)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def search(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None, app_id: str = None) -> Dict[str, Any]:
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
            app_id: Application ID for filtering results (optional)
            
        Returns:
            Dict containing search results with unified format
        """
        
        if self.llm_service:
            plan = self.llm_service.plan_query(query)
        else:
            plan = {
                "isMeaningful": True,
                "search_type": "articles",
                "normalized_query": query,
                "search_parameters": {}
            }
        
        if not plan.get("isMeaningful", True):
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
        
        search_type = plan.get("search_type", "articles")

        if search_type == "authors":
            return self._search_authors_planned(query, plan, k, page_index, page_size, app_id)
        elif search_type == "articles":
            return self._search_articles_planned(query, plan, k, page_index, page_size, app_id)
        else:
            return self._search_articles_planned(query, plan, k, page_index, page_size, app_id)
    
    def search_articles(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None, app_id: str = None) -> Dict[str, Any]:
        """
        Search for articles using LLM planning for query enhancement.
        
        Args:
            query: User search query
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            app_id: Application ID for filtering results (optional)
            
        Returns:
            Dict containing articles search results
        """
        
        if self.llm_service:
            plan = self.llm_service.plan_query(query)
        else:
            plan = {
                "isMeaningful": True,
                "search_type": "articles", 
                "normalized_query": query,
                "search_parameters": {}
            }
        
        plan["search_type"] = "articles"
        
        if not plan.get("isMeaningful", True):
            
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
        
        return self._search_articles_planned(query, plan, k, page_index, page_size, app_id)

    def search_authors(self, query: str, k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None, app_id: str = None) -> Dict[str, Any]:
        """
        Search for authors using LLM planning for query enhancement.
        
        Args:
            query: User search query
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            app_id: Application ID for filtering results (optional)
            
        Returns:
            Dict containing authors search results
        """
        
        if self.llm_service:
            plan = self.llm_service.plan_query(query)
        else:
            plan = {
                "isMeaningful": True,
                "search_type": "authors", 
                "normalized_query": query,
                "search_parameters": {}
            }
        
        plan["search_type"] = "authors"
        
        if not plan.get("isMeaningful", True):
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
        
        return self._search_authors_planned(query, plan, k, page_index, page_size, app_id)
    
    def _test_semantic_search(self) -> bool:
        try:
            test_result = self.articles.search(
                search_text="test",
                query_type="semantic",
                semantic_configuration_name="articles-semantic",
                top=1
            )
            try:
                next(iter(test_result))
                return True
            except StopIteration:
                return True
        except HttpResponseError as e:
            if "SemanticQueriesNotAvailable" in str(e) or "FeatureNotSupportedInService" in str(e):
                return False
            raise
        except Exception:
            return False
    
    def _batch_get_documents(self, client: SearchClient, document_ids: List[str], app_id: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Batch retrieve documents by IDs to avoid N+1 query problem.
        
        Args:
            client: SearchClient instance (articles or authors)
            document_ids: List of document IDs to retrieve
            app_id: Application ID for filtering results (optional)
            
        Returns:
            Dict mapping document ID to document data
        """
        if not document_ids:
            return {}

        try:
            id_filter = " or ".join([f"id eq '{doc_id}'" for doc_id in document_ids])
            
            app_filter = self._get_app_id_filter(app_id)
            if app_filter:
                final_filter = self._merge_filters(id_filter, app_filter)
            else:
                final_filter = id_filter
            
            results = client.search(
                search_text="*",
                filter=final_filter,
                top=len(document_ids),
                select=["*"]
            )
            
            doc_dict = {doc["id"]: doc for doc in results}
            return doc_dict
            
        except Exception as e:
            doc_dict = {}
            for doc_id in document_ids:
                try:
                    doc_dict[doc_id] = client.get_document(doc_id)
                except Exception as individual_error:
                    pass
            return doc_dict

    def _search_authors_planned(self, original_query: str, plan: Dict[str, Any], k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None, app_id: str = None) -> Dict[str, Any]:
        """
        Internal authors search function that uses pre-planned query data.
        
        Args:
            original_query: Original user query
            plan: Query plan from LLM containing normalized_query and search_parameters
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            app_id: Application ID for filtering results (optional)
            
        Returns:
            Dict containing authors search results
        """
        normalized_query = plan["normalized_query"]
        
        if page_index is not None and page_size is not None:
            offset = page_index * page_size
            total_needed = offset + page_size
            search_k = max(k * 4, 100)
        else:
            search_k = k
            offset = 0
        
        try:
            all_authors = self._get_all_authors(app_id)
            
            fuzzy_matches = self._fuzzy_match_authors(normalized_query, all_authors, search_k)
            
            rows: List[Dict[str, Any]] = []
            for i, (author_doc, score) in enumerate(fuzzy_matches):
                rows.append({
                    "id": author_doc["id"], 
                    "doc": author_doc,
                    "_bm25": score,
                    "_semantic": 0.0, 
                    "_vector": 0.0, 
                    "_business": 0.0
                })

            all_fused_results = fuse_authors(rows)
            
            all_fused_results = self._apply_score_threshold(all_fused_results)
            try:
                all_fused_results = sorted(all_fused_results, key=lambda r: r.get("_final", 0.0), reverse=True)
            except Exception:
                pass
            total_results = len(all_fused_results)
            
            if page_index is not None and page_size is not None:
                start_idx = offset
                end_idx = start_idx + page_size
                paginated_results = all_fused_results[start_idx:end_idx]

                return {
                    "results": paginated_results,
                    "normalized_query": normalized_query,
                    "pagination": {
                        "page_index": page_index,
                        "page_size": page_size,
                        "total_results": total_results,
                        "total_pages": math.ceil(total_results / page_size) if total_results > 0 else 1,
                        "has_next": end_idx < total_results,
                        "has_previous": page_index > 0
                    },
                    "search_type": "authors"
                }
            else:
                final_results = all_fused_results[:k]

                return {
                    "results": final_results,
                    "normalized_query": normalized_query,
                    "pagination": None,
                    "search_type": "authors"
                }
                
        except Exception as e:
            raise
    
    def _search_articles_planned(self, original_query: str, plan: Dict[str, Any], k: int = 10, page_index: Optional[int] = None, page_size: Optional[int] = None, app_id: str = None) -> Dict[str, Any]:
        """
        Internal articles search function that uses pre-planned query data.
        
        Args:
            original_query: Original user query
            plan: Query plan from LLM containing normalized_query and search_parameters
            k: Number of results to return
            page_index: Page index for pagination (optional)
            page_size: Page size for pagination (optional)
            app_id: Application ID for filtering results (optional)
            
        Returns:
            Dict containing articles search results
        """
        normalized_query = plan["normalized_query"]
        search_params = plan["search_parameters"]
        
        if page_index is not None and page_size is not None:
            offset = page_index * page_size
            total_needed = offset + page_size
            search_k = max(k * 4, 200)
        else:
            search_k = k
            offset = 0
        
        try:
            def run_text_search():
                if self.semantic_enabled:
                    try:
                        search_kwargs = {
                            "search_text": normalized_query,
                            "query_type": "semantic",
                            "semantic_configuration_name": "articles-semantic",
                            "top": int(search_k*1.1),
                            "select": ["id","title","abstract","author_name","business_date"],
                            "highlight_fields": search_params.get("highlight_fields", "searchable_text")
                        }
                        
                        if search_params.get("filter"):
                            search_kwargs["filter"] = search_params["filter"]
                        if search_params.get("order_by"):
                            search_kwargs["order_by"] = search_params["order_by"]
                        if search_params.get("search_fields"):
                            search_kwargs["search_fields"] = search_params["search_fields"]
                        
                        app_filter = self._get_app_id_filter(app_id)
                        if app_filter:
                            existing_filter = search_kwargs.get("filter", "")
                            search_kwargs["filter"] = self._merge_filters(existing_filter, app_filter)

                        text_res_local = self.articles.search(**search_kwargs)
                    except HttpResponseError as he:
                        if "SemanticQueriesNotAvailable" in str(he) or "FeatureNotSupportedInService" in str(he):
                            self.semantic_enabled = False
                            
                            search_kwargs = {
                                "search_text": normalized_query,
                                "query_type": "simple",
                                "top": int(search_k*1.1),
                                "select": ["id","title","abstract","author_name","business_date"],
                                "highlight_fields": "searchable_text"
                            }
                            
                            if search_params.get("filter"):
                                search_kwargs["filter"] = search_params["filter"]
                            if search_params.get("order_by"):
                                search_kwargs["order_by"] = search_params["order_by"]
                            if search_params.get("search_fields"):
                                search_kwargs["search_fields"] = search_params["search_fields"]
                            
                            app_filter = self._get_app_id_filter(app_id)
                            if app_filter:
                                existing_filter = search_kwargs.get("filter", "")
                                search_kwargs["filter"] = self._merge_filters(existing_filter, app_filter)

                            text_res_local = self.articles.search(**search_kwargs)
                        else:
                            raise
                else:
                    search_kwargs = {
                        "search_text": normalized_query,
                        "query_type": "simple",
                        "top": int(search_k*1.3),
                        "select": ["id","title","abstract","author_name","business_date"],
                        "highlight_fields": "searchable_text"
                    }
                    
                    if search_params.get("filter"):
                        search_kwargs["filter"] = search_params["filter"]
                    if search_params.get("order_by"):
                        search_kwargs["order_by"] = search_params["order_by"]
                    if search_params.get("search_fields"):
                        search_kwargs["search_fields"] = search_params["search_fields"]
                    
                    app_filter = self._get_app_id_filter(app_id)
                    if app_filter:
                        existing_filter = search_kwargs.get("filter", "")
                        search_kwargs["filter"] = self._merge_filters(existing_filter, app_filter)

                    text_res_local = self.articles.search(**search_kwargs)
                
                rows_local: List[Dict[str, Any]] = []
                text_count_local = 0
                
                for d in text_res_local:
                    text_count_local += 1
                    rows_local.append({
                        "id": d["id"],
                        "doc": d,
                        "_bm25": d["@search.score"],
                        "_semantic": d.get("@search.rerankerScore", 0.0),
                        "_vector": 0.0,
                        "_business": business_freshness(d.get("business_date")),
                    })
                return rows_local, text_count_local

            def run_vector_search():
                qvec = encode(normalized_query)

                vector_search_kwargs = {
                    "search_text": None,
                    "vector_queries": [VectorizedQuery(vector=qvec, fields="abstract_vector")],
                    "top": int(search_k * 1.2),
                    "select": ["id", "title", "abstract", "author_name", "business_date"]
                }

                if search_params.get("filter"):
                    vector_search_kwargs["filter"] = search_params["filter"]
                if search_params.get("order_by"):
                    vector_search_kwargs["order_by"] = search_params["order_by"]
                
                app_filter = self._get_app_id_filter(app_id)
                if app_filter:
                    existing_filter = vector_search_kwargs.get("filter", "")
                    vector_search_kwargs["filter"] = self._merge_filters(existing_filter, app_filter)

                return list(self.articles.search(**vector_search_kwargs))

            text_future = self.executor.submit(run_text_search)
            vector_future = self.executor.submit(run_vector_search)

            rows, text_count = text_future.result()
            vec_res = vector_future.result()
            
            id_to_row = {r["id"]: r for r in rows}
            vec_count = len(vec_res)

            for d in vec_res:
                try:
                    article_id = d.get("id")
                    if not article_id:
                        continue
                    score = d.get("@search.score", 0.0)
                    
                    if article_id in id_to_row:
                        id_to_row[article_id]["_vector"] = score
                    else:
                        id_to_row[article_id] = {
                            "id": article_id,
                            "doc": d,
                            "_bm25": 0.0,
                            "_semantic": 0.0,
                            "_vector": score,
                            "_business": 0.0,
                        }
                except Exception:
                    continue

            missing_article_ids = [aid for aid, row in id_to_row.items() if row.get("doc") is None]
            if missing_article_ids:
                batch_articles = self._batch_get_documents(self.articles, missing_article_ids, app_id)
                for aid in missing_article_ids:
                    if aid in batch_articles:
                        article_doc = batch_articles[aid]
                        id_to_row[aid]["doc"] = article_doc
                        id_to_row[aid]["_business"] = business_freshness(article_doc.get("business_date"))

            all_fused_results = fuse_articles(list(id_to_row.values()))

            all_fused_results = self._apply_score_threshold(all_fused_results)

            if page_index is not None and page_size is not None:
                total_results = len(all_fused_results)
                start_idx = offset
                end_idx = start_idx + page_size
                paginated_results = all_fused_results[start_idx:end_idx]

                return {
                    "results": paginated_results,
                    "normalized_query": normalized_query,
                    "pagination": {
                        "page_index": page_index,
                        "page_size": page_size,
                        "total_results": total_results,
                        "total_pages": math.ceil(total_results / page_size) if total_results > 0 else 1,
                        "has_next": end_idx < total_results,
                        "has_previous": page_index > 0
                    },
                    "search_type": "articles",
                }
            else:
                final_results = all_fused_results[:k]
                
                return {
                    "results": final_results,
                    "normalized_query": normalized_query,
                    "pagination": None,
                    "search_type": "articles"
                }
                
        except Exception as e:
            raise

    def _get_all_authors(self, app_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all authors from the index for fuzzy matching.
        Args:
            app_id: Application ID for filtering results (optional)
        
        Returns:
            List of all author documents
        """
        try:
            search_kwargs = {
                "search_text": "*",
                "query_type": "simple",
                "select": ["id", "full_name"]
            }
            
            app_filter = self._get_app_id_filter(app_id)
            if app_filter:
                search_kwargs["filter"] = app_filter
            
            all_results = self.authors.search(**search_kwargs)
            
            authors = []
            for doc in all_results:
                authors.append(doc)
            
            return authors
            
        except Exception as e:
            return []
    
    def _fuzzy_match_authors(self, query: str, all_authors: List[Dict[str, Any]], k: int) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform robust fuzzy matching against all author names with Unicode and diacritic support.
        
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
        
        query_normalized = self._normalize_text(query)
        query_words = query_normalized.split()
        
        for author in all_authors:
            full_name = author.get("full_name", "")
            if not full_name:
                continue
                
            name_normalized = self._normalize_text(full_name)
            name_words = name_normalized.split()
            
            exact_match_score = 0.0
            if query_normalized == name_normalized:
                exact_match_score = 1.0
            
            full_similarity = SequenceMatcher(None, query_normalized, name_normalized).ratio()
            
            word_match_score = 0.0
            if query_words and name_words:
                matched_words = 0
                total_query_words = len(query_words)
                
                for query_word in query_words:
                    if query_word in name_words:
                        matched_words += 1
                    else:
                        for name_word in name_words:
                            if len(query_word) >= 3 and query_word in name_word:
                                matched_words += 0.7
                                break
                            elif len(name_word) >= 3 and name_word in query_word:
                                matched_words += 0.7
                                break
                            else:
                                word_sim = SequenceMatcher(None, query_word, name_word).ratio()
                                if word_sim >= 0.8:
                                    matched_words += word_sim
                                    break
                
                word_match_score = matched_words / total_query_words if total_query_words > 0 else 0.0
            
            substring_score = 0.0
            if query_normalized in name_normalized:
                substring_score = 0.9 * (len(query_normalized) / len(name_normalized))
            elif name_normalized in query_normalized:
                substring_score = 0.8 * (len(name_normalized) / len(query_normalized))
            
            initials_score = 0.0
            if len(query_words) <= 3 and len(name_words) >= len(query_words):
                initials_match = True
                for i, query_word in enumerate(query_words):
                    if i < len(name_words):
                        if not name_words[i].startswith(query_word[0]):
                            initials_match = False
                            break
                if initials_match:
                    initials_score = 0.7
            
            final_score = max(
                exact_match_score * 1.0,
                full_similarity * 0.9,
                word_match_score * 0.95,
                substring_score * 0.85,
                initials_score * 0.7
            )
            
            if final_score > 0.5 and len(name_normalized) <= len(query_normalized) + 5:
                final_score = min(1.0, final_score * 1.1)
            
            if final_score > 0.05:
                matches.append((author, final_score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:k]

search_service = None

def get_search_service() -> BackendSearchService:
    global search_service
    if search_service is None:
        try:
            pass
            
            import os
            if not os.getenv("AZURE_SEARCH_ENDPOINT") or not os.getenv("AZURE_SEARCH_KEY"):
                raise ValueError("Missing Azure Search environment variables")
            
            articles_sc = articles_client()
            authors_sc = authors_client()
            
            search_service = BackendSearchService(articles_sc, authors_sc)
        except Exception as e:
            raise
    return search_service
