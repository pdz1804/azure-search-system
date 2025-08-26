"""
Auto-tagging service for articles using LLM with KeyBERT fallback
"""
import asyncio
import json
import os
import re
from typing import List, Dict, Any, Optional
from openai import AsyncAzureOpenAI
from backend.config.tag_prompts import TAG_GENERATION_PROMPT, TAG_VALIDATION_RULES

from ai_search.config.settings import SETTINGS

class TagGenerationService:
    def __init__(self):
        self.llm_client = None
        self.keybert_model = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize Azure OpenAI client"""
        try:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            
            kwargs = {
                "api_key": SETTINGS.azure_openai_key,
                "api_version": SETTINGS.azure_openai_api_version,
                "azure_deployment": "gpt-4o-mini",
            }
            print(f"🌐 Using Azure OpenAI endpoint: {SETTINGS.azure_openai_endpoint}")
            
            if api_key and endpoint:
                self.llm_client = AsyncAzureOpenAI(**kwargs)
                print("🤖 Tag service: Azure OpenAI client initialized")
        except Exception as e:
            print(f"⚠️ Tag service: Failed to initialize LLM client: {e}")
    
    def _init_keybert(self):
        """Initialize KeyBERT model (lazy loading)"""
        if self.keybert_model is None:
            try:
                from keybert import KeyBERT
                self.keybert_model = KeyBERT()
                print("🔑 Tag service: KeyBERT model initialized")
            except ImportError:
                print("⚠️ Tag service: KeyBERT not available, install with: pip install keybert")
            except Exception as e:
                print(f"⚠️ Tag service: KeyBERT initialization failed: {e}")
    
    def _clean_text_for_tagging(self, text: str) -> str:
        """Clean HTML and normalize text for tag generation"""
        if not text:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        # Limit length for processing
        return clean_text[:2000]
    
    def _format_tag(self, tag: str) -> str:
        """Format tag according to rules: lowercase with hyphens, max 3 words"""
        if not tag:
            return ""
        
        # Clean and normalize
        clean_tag = tag.strip().lower()
        
        # Remove special characters except hyphens and spaces
        clean_tag = re.sub(r'[^\w\s-]', '', clean_tag)
        
        # Replace spaces with hyphens
        clean_tag = re.sub(r'\s+', '-', clean_tag)
        
        # Remove multiple consecutive hyphens
        clean_tag = re.sub(r'-+', '-', clean_tag)
        
        # Remove leading/trailing hyphens
        clean_tag = clean_tag.strip('-')
        
        # Limit to max 3 words (by counting hyphens)
        parts = clean_tag.split('-')
        if len(parts) > TAG_VALIDATION_RULES["max_words"]:
            clean_tag = '-'.join(parts[:TAG_VALIDATION_RULES["max_words"]])
        
        return clean_tag
    
    def _validate_and_format_tags(self, raw_tags: List[str], existing_tags: List[str]) -> List[str]:
        """Validate and format a list of tags"""
        formatted_tags = []
        existing_lower = [tag.lower() for tag in existing_tags]
        
        for tag in raw_tags:
            formatted_tag = self._format_tag(tag)
            
            # Skip empty, too short, or duplicate tags
            if (formatted_tag and 
                len(formatted_tag) >= 2 and 
                formatted_tag not in existing_lower and
                formatted_tag not in [t.lower() for t in formatted_tags]):
                formatted_tags.append(formatted_tag)
        
        return formatted_tags
    
    async def generate_tags_llm(self, title: str, abstract: str, content: str, existing_tags: List[str]) -> List[str]:
        """Generate tags using Azure OpenAI LLM"""
        if not self.llm_client:
            raise Exception("LLM client not available")
        
        # Clean and prepare text
        clean_title = self._clean_text_for_tagging(title)
        clean_abstract = self._clean_text_for_tagging(abstract)
        clean_content = self._clean_text_for_tagging(content)
        
        # Format existing tags to ensure consistency
        formatted_existing = self._validate_and_format_tags(existing_tags, [])
        
        # Calculate how many more tags needed (max 4 total)
        existing_count = len(formatted_existing)
        needed_count = min(TAG_VALIDATION_RULES["max_total_tags"] - existing_count, TAG_VALIDATION_RULES["max_total_tags"])
        
        if needed_count <= 0:
            return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
        
        # Create prompt using config
        existing_tags_text = ", ".join(formatted_existing) if formatted_existing else "none"
        
        prompt = TAG_GENERATION_PROMPT.format(
            needed_count=needed_count,
            clean_title=clean_title,
            clean_abstract=clean_abstract,
            clean_content=clean_content[:500],
            existing_tags_text=existing_tags_text
        )

        try:
            response = await self.llm_client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Parse and format tags from response
            raw_new_tags = [tag.strip() for tag in generated_text.split(',') if tag.strip()]
            new_tags = self._validate_and_format_tags(raw_new_tags, formatted_existing)
            
            # Combine existing and new tags (max 4 total)
            all_tags = formatted_existing + new_tags[:needed_count]
            return all_tags[:TAG_VALIDATION_RULES["max_total_tags"]]
            
        except Exception as e:
            print(f"❌ Tag service: LLM generation failed: {e}")
            raise
    
    def generate_tags_keybert(self, title: str, abstract: str, content: str, existing_tags: List[str]) -> List[str]:
        """Generate tags using KeyBERT (fallback method)"""
        self._init_keybert()
        
        # Format existing tags to ensure consistency
        formatted_existing = self._validate_and_format_tags(existing_tags, [])
        
        if not self.keybert_model:
            return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
        
        try:
            # Combine all text for keyword extraction
            full_text = f"{title} {abstract} {self._clean_text_for_tagging(content)}"
            
            if not full_text.strip():
                return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
            
            # Calculate how many more tags needed
            existing_count = len(formatted_existing)
            needed_count = min(TAG_VALIDATION_RULES["max_total_tags"] - existing_count, TAG_VALIDATION_RULES["max_total_tags"])
            
            if needed_count <= 0:
                return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
            
            # Extract keywords with KeyBERT
            keywords = self.keybert_model.extract_keywords(
                full_text,
                keyphrase_ngram_range=(1, 3),  # Allow up to 3 words
                stop_words='english',
                top_k=needed_count * 3,  # Extract more to have options
                use_maxsum=True,
                nr_candidates=30
            )
            
            # Process keywords to tags
            raw_new_tags = []
            for keyword, score in keywords:
                raw_new_tags.append(keyword)
                
                if len(raw_new_tags) >= needed_count * 2:
                    break
            
            # Format and validate tags
            new_tags = self._validate_and_format_tags(raw_new_tags, formatted_existing)
            
            # Combine existing and new tags (max 4 total)
            all_tags = formatted_existing + new_tags[:needed_count]
            return all_tags[:TAG_VALIDATION_RULES["max_total_tags"]]
            
        except Exception as e:
            print(f"❌ Tag service: KeyBERT generation failed: {e}")
            return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
    
    async def generate_article_tags(self, 
                                  title: str = "", 
                                  abstract: str = "", 
                                  content: str = "", 
                                  user_tags: List[str] = None) -> Dict[str, Any]:
        """
        Generate article tags with LLM primary and KeyBERT fallback
        
        Args:
            title: Article title
            abstract: Article abstract 
            content: Article content
            user_tags: Tags provided by user (max 2)
            
        Returns:
            Dict with generated tags and metadata
        """
        
        # Validate and clean user tags (max 2)
        existing_tags = []
        if user_tags:
            for tag in user_tags[:TAG_VALIDATION_RULES["max_user_tags"]]:
                clean_tag = tag.strip()
                if clean_tag and len(clean_tag) > 0:
                    existing_tags.append(clean_tag)
        
        # Format user tags to ensure consistency
        existing_tags = self._validate_and_format_tags(existing_tags, [])
        
        try:
            # Try LLM first
            tags = await self.generate_tags_llm(title, abstract, content, existing_tags)
            method_used = "llm"
            
        except Exception as llm_error:
            print(f"🔄 Tag service: LLM failed, falling back to KeyBERT: {llm_error}")
            
            try:
                # Fallback to KeyBERT
                tags = self.generate_tags_keybert(title, abstract, content, existing_tags)
                method_used = "keybert_fallback"
                
            except Exception as keybert_error:
                print(f"❌ Tag service: Both methods failed: {keybert_error}")
                # Final fallback - return user tags only
                tags = existing_tags[:4]
                method_used = "user_tags_only"
        
        return {
            "success": True,
            "tags": tags,
            "user_tags_count": len(existing_tags),
            "total_tags_count": len(tags),
            "method_used": method_used
        }

# Global service instance
tag_service = TagGenerationService()
