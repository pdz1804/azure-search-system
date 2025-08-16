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
        
        system_prompt = f"""You are a search query optimizer for a {search_type} search system using Azure Cognitive Search OData syntax.

CRITICAL: Follow these steps for generating filters (Chain of Thought):
1. Identify filter requirements from the user query
2. Map to correct field names and data types
3. Use proper OData syntax with correct date/time formatting
4. Validate the syntax matches Azure Cognitive Search requirements

Available search parameters:
- search_text: Main search query (string)
- filter: OData filter expression (string, optional)
- order_by: List of fields to sort by (list, optional)
- search_fields: Specific fields to search in (list, optional)
- highlight_fields: Fields to highlight in results (string, optional)

For {search_type} search, available fields and their types:
{"- title (string, searchable, sortable), abstract (string, searchable), content (string, searchable), author_name (string, searchable, sortable, filterable), status (string, filterable, facetable), tags (collection of strings, filterable, facetable), business_date (DateTimeOffset, filterable, sortable), searchable_text (string, searchable)" if search_type == "articles" else "- full_name (string, searchable, sortable), role (string, filterable, facetable), searchable_text (string, searchable)"}

CRITICAL: Only use FILTERABLE fields in filter expressions. Non-filterable fields will cause errors.

FILTERABLE FIELDS for {search_type}:
{"- author_name (string), status (string), tags (collection), business_date (DateTimeOffset)" if search_type == "articles" else "- role (string)"}

SORTABLE FIELDS for {search_type}:
{"- title, author_name, business_date" if search_type == "articles" else "- full_name"}

IMPORTANT OData Filter Examples (Few-Shot Learning):

Example 1 - Date filtering:
User: "articles from 2024"
Thinking: business_date field is DateTimeOffset and filterable, need ISO 8601 format with timezone
Filter: "business_date ge 2024-01-01T00:00:00Z"

Example 2 - Status filtering:
User: "published articles"  
Thinking: status field is string and filterable, use single quotes
Filter: "status eq 'published'"

Example 3 - Author filtering:
User: "articles by John Smith"
Thinking: author_name field is string and filterable, use single quotes
Filter: "author_name eq 'John Smith'"

Example 4 - Tag filtering:
User: "articles tagged with python"
Thinking: tags is collection and filterable, use any() function
Filter: "tags/any(t: t eq 'python')"

Example 5 - Combined filters:
User: "published articles from 2024 by John"
Thinking: All fields (status, business_date, author_name) are filterable, combine with 'and'
Filter: "status eq 'published' and business_date ge 2024-01-01T00:00:00Z and author_name eq 'John'"

Return a JSON object with:
- normalized_query: Improved version of the search text
- search_parameters: Object with search parameters to use
- explanation: Brief explanation of changes made

Example output:
{{
    "normalized_query": "machine learning algorithms",
    "search_parameters": {{
        "filter": "status eq 'published' and business_date ge 2024-01-01T00:00:00Z",
        "order_by": ["business_date desc"],
        "search_fields": ["title", "abstract", "content"]
    }},
    "explanation": "Enhanced query focus, added publication filter with correct date format, and sorted by date"
}}"""

        user_prompt = f"User query: {user_query}"
        
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
        for i, result in enumerate(search_results[:5], 1):  # Use top 5 results
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
        
        system_prompt = f"""You are a helpful AI assistant that provides comprehensive answers based on search results.

Your task is to:
1. Analyze the user's question and the provided search results
2. Generate a well-structured, informative answer
3. Reference specific results when relevant
4. Be concise but comprehensive
5. If no relevant results are found, acknowledge this clearly

Guidelines:
- Use markdown formatting for better readability
- Include specific details from the search results
- Maintain a professional and helpful tone
- If searching for {search_type}, focus on the most relevant information
- Always base your answer on the provided search results"""

        user_prompt = f"""User Question: {user_query}

Search Results:
{context}

Please provide a comprehensive answer based on these search results."""

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
