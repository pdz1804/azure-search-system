"""
LLM Service for Query Enhancement and Answer Generation

This module provides two main capabilities:
1. Query normalization and enhancement with search parameters
2. Answer generation from search results

The service uses Azure OpenAI to intelligently process user queries and generate
comprehensive answers based on retrieved search results.
"""

from typing import Dict, Any, Optional, List
from openai import AzureOpenAI
from config.settings import SETTINGS
from config.prompts import (
    SYSTEM_PROMPT_NORMALIZE,
    SYSTEM_PROMPT_ANSWER,
    USER_PROMPT_NORMALIZE,
    USER_PROMPT_ANSWER,
)
import json

class LLMService:
    """Service for LLM-powered query enhancement and answer generation."""
    
    def __init__(self):
        """Initialize the LLM service with Azure OpenAI client."""
        print("🤖 Initializing LLM Service...")
        self.client = AzureOpenAI(
            api_key=SETTINGS.azure_openai_key,
            api_version=SETTINGS.azure_openai_api_version,
            azure_endpoint=SETTINGS.azure_openai_endpoint
        )
        print("✅ LLM Service initialized successfully")
    
    def normalize_query(self, user_query: str, search_type: str = "articles") -> Dict[str, Any]:
        """
        Normalize and enhance user query for better search results.
        
        Args:
            user_query: Raw user query
            search_type: Type of search ("articles" or "authors")
            
        Returns:
            Dict containing normalized query and search parameters
        """
        print(f"🔄 Normalizing query: '{user_query}' for {search_type}")
        
        # Build fields/filterable/sortable hints for the normalize prompt
        if search_type == "articles":
            fields = "- title (string, searchable, sortable), abstract (string, searchable), content (string, searchable), author_name (string, searchable, sortable, filterable), status (string, filterable, facetable), tags (collection of strings, filterable, facetable), business_date (DateTimeOffset, filterable, sortable), searchable_text (string, searchable)"
            filterable = "- author_name (string), status (string), tags (collection), business_date (DateTimeOffset)"
            sortable = "- title, author_name, business_date"
        else:
            fields = "- full_name (string, searchable, sortable), role (string, filterable, facetable), searchable_text (string, searchable)"
            filterable = "- role (string)"
            sortable = "- full_name"

        system_prompt = SYSTEM_PROMPT_NORMALIZE.format(search_type=search_type, fields=fields, filterable=filterable, sortable=sortable)

        user_prompt = USER_PROMPT_NORMALIZE.format(user_query=user_query)
        
        try:
            response = self.client.chat.completions.create(
                model=SETTINGS.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            print(f"✅ Query normalized: '{result['normalized_query']}'")
            return result
            
        except Exception as e:
            print(f"⚠️ Query normalization failed: {e}")
            # Fallback to original query
            return {
                "normalized_query": user_query,
                "search_parameters": {},
                "explanation": "Using original query due to normalization error"
            }
    
    def generate_answer(self, user_query: str, search_results: List[Dict[str, Any]], search_type: str = "articles") -> str:
        """
        Generate a comprehensive answer based on search results.
        
        Args:
            user_query: Original user query
            search_results: List of search result documents
            search_type: Type of search ("articles" or "authors")
            
        Returns:
            Generated answer string
        """
        print(f"🤖 Generating answer for query: '{user_query}' using {len(search_results)} {search_type}")
        
        # Prepare context from search results
        context_items = []
        for i, result in enumerate(search_results, 1):  # Use all results
            doc = result.get('doc', {})
            if search_type == "articles":
                title = doc.get('title', 'Untitled')
                abstract = doc.get('abstract', '')
                author = doc.get('author_name', 'Unknown')
                context_items.append(f"{i}. **{title}** by {author}\n   {abstract}")
            else:  # authors
                name = doc.get('full_name', 'Unknown')
                role = doc.get('role', 'Unknown role')
                context_items.append(f"{i}. **{name}** - {role}")
        
        context = "\n\n".join(context_items)

        system_prompt = SYSTEM_PROMPT_ANSWER.format(search_type=search_type)

        user_prompt = USER_PROMPT_ANSWER.format(user_query=user_query, context=context)

        try:
            response = self.client.chat.completions.create(
                model=SETTINGS.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            answer = response.choices[0].message.content.strip()
            print(f"✅ Generated answer ({len(answer)} characters)")
            return answer

        except Exception as e:
            print(f"⚠️ Answer generation failed: {e}")
            # Fallback response
            return f"I found {len(search_results)} relevant {search_type} for your query '{user_query}', but I'm unable to generate a detailed answer at the moment. Please review the search results directly."
