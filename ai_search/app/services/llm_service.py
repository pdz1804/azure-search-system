"""
LLM Service for Query Enhancement and Answer Generation

This module provides two main capabilities:
1. Query normalization and enhancement with search parameters
2. Answer generation from search results

The service uses Azure OpenAI to intelligently process user queries and generate
comprehensive answers based on retrieved search results.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from typing import Dict, Any, Optional, List
from openai import AzureOpenAI
from ai_search.config.settings import SETTINGS
from ai_search.config.prompts import (
    SYSTEM_PROMPT_ANSWER, USER_PROMPT_ANSWER,
    SYSTEM_PROMPT_PLANNING_ADVANCED, USER_PROMPT_PLANNING_ADVANCED,
    SYSTEM_PROMPT_PLANNING_SIMPLE, USER_PROMPT_PLANNING_SIMPLE
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
    
    
    def plan_query(self, user_query: str, mode: str = "simple") -> Dict[str, Any]:
        """
        Comprehensive query planning that combines normalization and classification.
        
        This function replaces the separate normalize_query functionality by providing:
        1. Query meaningfulness assessment
        2. Search type classification (articles vs authors)
        3. Query normalization and enhancement
        4. Search parameter generation (advanced mode only)
        
        Args:
            user_query: Raw user query string
            mode: "simple" for basic classification, "advanced" for full search parameters
            
        Returns:
            Dict containing:
            - normalized_query: Enhanced search text
            - search_type: "articles", "authors", or "unmeaningful"
            - search_parameters: Dict with search parameters (advanced mode) or empty dict (simple mode)
            - isMeaningful: Boolean indicating if query has search intent
        """
        print(f"🎯 Planning query: '{user_query}'")
        
        try:
            if mode == "advanced":
                response = self.client.chat.completions.create(
                    model=SETTINGS.azure_openai_deployment,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_PLANNING_ADVANCED},
                        {"role": "user", "content": USER_PROMPT_PLANNING_ADVANCED.format(user_query=user_query)}
                    ],
                    temperature=0.1,
                    max_tokens=800
                )
            else:
                response = self.client.chat.completions.create(
                    model=SETTINGS.azure_openai_deployment,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_PLANNING_SIMPLE},
                        {"role": "user", "content": USER_PROMPT_PLANNING_SIMPLE.format(user_query=user_query)}
                    ],
                    temperature=0.1,
                    max_tokens=800
                )
            
            response_text = response.choices[0].message.content.strip()
            print(f"🤖 LLM planning response: {response_text}")
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
                
                # Ensure required fields exist with defaults
                if "isMeaningful" not in result:
                    result["isMeaningful"] = True
                if "search_parameters" not in result:
                    result["search_parameters"] = {}
                if "search_type" not in result:
                    result["search_type"] = "articles"  # Default to articles
                    
                print(f"✅ Query planned: type='{result.get('search_type')}', meaningful={result.get('isMeaningful')}")
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse LLM planning response: {e}")
                # Fallback response
                return {
                    "normalized_query": user_query,
                    "search_type": "articles",
                    "search_parameters": {},
                    "isMeaningful": True
                }
                
        except Exception as e:
            print(f"❌ Query planning failed: {e}")
            # Fallback response
            return {
                "normalized_query": user_query,
                "search_type": "articles", 
                "search_parameters": {},
                "isMeaningful": True,
                "explanation": f"LLM call failed: {str(e)}",
                "confidence": 0.5
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
