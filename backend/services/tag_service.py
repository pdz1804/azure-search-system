"""
Auto-tagging service for articles using LLM with KeyBERT fallback
"""
import os
import re
from typing import List, Dict, Any
from openai import AsyncAzureOpenAI
from backend.config.tag_prompts import TAG_GENERATION_PROMPT, TAG_VALIDATION_RULES

from ai_search.config.settings import SETTINGS

class TagGenerationService:
    def __init__(self):
        self.llm_client = None
        self.keybert_model = None
        self._init_llm()
    
    def _init_llm(self):
        try:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            
            kwargs = {
                "api_key": SETTINGS.azure_openai_key,
                "api_version": SETTINGS.azure_openai_api_version,
                "azure_deployment": "gpt-4o-mini",
            }
            
            if api_key and endpoint:
                self.llm_client = AsyncAzureOpenAI(**kwargs)
        except Exception:
            pass
    
    def _init_keybert(self):
        if self.keybert_model is None:
            try:
                from keybert import KeyBERT
                self.keybert_model = KeyBERT()
            except ImportError:
                self.keybert_model = None
            except Exception:
                pass
    
    def _clean_text_for_tagging(self, text: str) -> str:
        if not text:
            return ""
        
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text[:2000]
    
    def _format_tag(self, tag: str) -> str:
        if not tag:
            return ""
        
        clean_tag = tag.strip().lower()
        
        clean_tag = re.sub(r'[^\w\s-]', '', clean_tag)
        
        clean_tag = re.sub(r'\s+', '-', clean_tag)
        
        clean_tag = re.sub(r'-+', '-', clean_tag)
        
        clean_tag = clean_tag.strip('-')
        
        parts = clean_tag.split('-')
        if len(parts) > TAG_VALIDATION_RULES["max_words"]:
            clean_tag = '-'.join(parts[:TAG_VALIDATION_RULES["max_words"]])
        
        return clean_tag
    
    def _validate_and_format_tags(self, raw_tags: List[str], existing_tags: List[str]) -> List[str]:
        formatted_tags = []
        existing_lower = [tag.lower() for tag in existing_tags]
        
        for tag in raw_tags:
            formatted_tag = self._format_tag(tag)
            
            if (formatted_tag and 
                len(formatted_tag) >= 2 and 
                formatted_tag not in existing_lower and
                formatted_tag not in [t.lower() for t in formatted_tags]):
                formatted_tags.append(formatted_tag)
        
        return formatted_tags
    
    async def generate_tags_llm(self, title: str, abstract: str, content: str, existing_tags: List[str]) -> List[str]:
        if not self.llm_client:
            raise Exception("LLM client not available")
        
        clean_title = self._clean_text_for_tagging(title)
        clean_abstract = self._clean_text_for_tagging(abstract)
        clean_content = self._clean_text_for_tagging(content)
        
        formatted_existing = self._validate_and_format_tags(existing_tags, [])
        
        existing_count = len(formatted_existing)
        needed_count = min(TAG_VALIDATION_RULES["max_total_tags"] - existing_count, TAG_VALIDATION_RULES["max_total_tags"])
        
        if needed_count <= 0:
            return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
        
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
            
            raw_new_tags = [tag.strip() for tag in generated_text.split(',') if tag.strip()]
            new_tags = self._validate_and_format_tags(raw_new_tags, formatted_existing)
            
            all_tags = formatted_existing + new_tags[:needed_count]
            return all_tags[:TAG_VALIDATION_RULES["max_total_tags"]]
            
        except Exception:
            return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
    
    def generate_tags_keybert(self, title: str, abstract: str, content: str, existing_tags: List[str]) -> List[str]:
        self._init_keybert()
        
        formatted_existing = self._validate_and_format_tags(existing_tags, [])
        
        if not self.keybert_model:
            return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
        
        try:
            full_text = f"{title} {abstract} {self._clean_text_for_tagging(content)}"
            
            if not full_text.strip():
                return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
            
            existing_count = len(formatted_existing)
            needed_count = min(TAG_VALIDATION_RULES["max_total_tags"] - existing_count, TAG_VALIDATION_RULES["max_total_tags"])
            
            if needed_count <= 0:
                return formatted_existing[:TAG_VALIDATION_RULES["max_total_tags"]]
            
            keywords = self.keybert_model.extract_keywords(
                full_text,
                keyphrase_ngram_range=(1, 3),
                stop_words='english',
                top_k=needed_count * 3,
                use_maxsum=True,
                nr_candidates=30
            )
            
            raw_new_tags = []
            for keyword, _ in keywords:
                raw_new_tags.append(keyword)
                
                if len(raw_new_tags) >= needed_count * 2:
                    break
            
            new_tags = self._validate_and_format_tags(raw_new_tags, formatted_existing)
            
            all_tags = formatted_existing + new_tags[:needed_count]
            return all_tags[:TAG_VALIDATION_RULES["max_total_tags"]]
            
        except Exception:
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
        
        existing_tags = []
        if user_tags:
            for tag in user_tags[:TAG_VALIDATION_RULES["max_user_tags"]]:
                clean_tag = tag.strip()
                if clean_tag and len(clean_tag) > 0:
                    existing_tags.append(clean_tag)
        
        existing_tags = self._validate_and_format_tags(existing_tags, [])
        
        try:
            tags = await self.generate_tags_llm(title, abstract, content, existing_tags)
            method_used = "llm"
            
        except Exception:
            
            try:
                tags = self.generate_tags_keybert(title, abstract, content, existing_tags)
                method_used = "keybert_fallback"
                
            except Exception:
                tags = existing_tags[:4]
                method_used = "user_tags_only"
        
        return {
            "success": True,
            "tags": tags,
            "user_tags_count": len(existing_tags),
            "total_tags_count": len(tags),
            "method_used": method_used
        }

tag_service = TagGenerationService()
