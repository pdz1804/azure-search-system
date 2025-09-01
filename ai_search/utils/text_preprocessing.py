"""
Text preprocessing utilities for optimizing article content for embeddings and search.

This module provides comprehensive text cleaning and preprocessing capabilities
to improve embedding quality and search relevance by removing noise and 
standardizing text format while preserving sentiment and context.
"""

import re
import html
from typing import Optional, List
from html.parser import HTMLParser


class AdvancedHTMLStripper(HTMLParser):
    """Advanced HTML tag stripper that handles embedded content and preserves text."""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self.skip_content = False
        self.skip_tags = {
            'script', 'style', 'noscript', 'iframe', 'object', 'embed', 
            'video', 'audio', 'img', 'svg', 'canvas', 'map', 'area',
            'link', 'meta', 'head', 'title'
        }

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.skip_tags:
            self.skip_content = True

    def handle_endtag(self, tag):
        if tag.lower() in self.skip_tags:
            self.skip_content = False

    def handle_data(self, data):
        if not self.skip_content:
            self.fed.append(data)

    def get_data(self):
        return ''.join(self.fed)


def strip_html_tags(text: str) -> str:
    """
    Remove HTML tags while preserving text content.
    Handles nested tags, embedded content (img, video, iframe etc.), and CSS/JS.
    
    Args:
        text: Input text with potential HTML tags
        
    Returns:
        Text with HTML tags removed and text content preserved
    """
    if not text:
        return ""
    
    # First decode HTML entities to normalize the text
    text = html.unescape(text)
    
    # Remove CSS and JavaScript blocks entirely
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove embedded content blocks entirely (iframe, object, embed, video, audio, etc.)
    embed_tags = r'<(?:iframe|object|embed|video|audio|img|svg|canvas|map|area)[^>]*(?:/>|>.*?</(?:iframe|object|embed|video|audio|img|svg|canvas|map|area)>)'
    text = re.sub(embed_tags, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove self-closing embedded tags
    text = re.sub(r'<(?:img|area|meta|link|br|hr|input)[^>]*/?>', '', text, flags=re.IGNORECASE)
    
    # Remove meta tags and link tags
    text = re.sub(r'<(?:meta|link)[^>]*/?>', '', text, flags=re.IGNORECASE)
    
    # Simple regex-based HTML tag removal for remaining tags
    # This is more reliable than HTMLParser for malformed HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()


def remove_urls(text: str) -> str:
    """
    Remove URLs from text while preserving context.
    
    Args:
        text: Input text with potential URLs
        
    Returns:
        Text with URLs removed
    """
    if not text:
        return ""
    
    # Remove full URL tokens (including trailing punctuation)
    url_pattern = r'\b(?:https?://|www\.)\S+'
    text = re.sub(url_pattern, '', text, flags=re.IGNORECASE)
    
    # Remove standalone domain patterns, but NOT if preceded by @
    # This prevents removing domains that are part of email addresses
    domain_pattern = r'(?<!@)\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    text = re.sub(domain_pattern, '', text, flags=re.IGNORECASE)
    
    return text


def remove_emails(text: str) -> str:
    """
    Remove email addresses from text.
    
    Args:
        text: Input text with potential email addresses
        
    Returns:
        Text with email addresses removed
    """
    if not text:
        return ""
    
    # More specific email pattern - must have valid domain structure
    # Match: user@domain.tld but not chars@#$!
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    return re.sub(email_pattern, '', text, flags=re.IGNORECASE)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace by replacing multiple spaces, tabs, and newlines with single spaces.
    
    Args:
        text: Input text with irregular whitespace
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple whitespace characters with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def remove_special_characters(text: str, preserve_basic_punctuation: bool = True) -> str:
    """
    Remove special characters while optionally preserving basic punctuation.
    
    Args:
        text: Input text with special characters
        preserve_basic_punctuation: If True, keeps periods, commas, question marks, etc.
        
    Returns:
        Text with special characters removed
    """
    if not text:
        return ""
    
    if preserve_basic_punctuation:
        # Keep alphanumeric, spaces, and basic punctuation (exclude parentheses)
        # Tests expect parentheses to be removed, so don't allow them here.
        text = re.sub(r'[^\w\s.!?,:;\-]', '', text)
    else:
        # Keep only alphanumeric and spaces
        text = re.sub(r'[^\w\s]', '', text)
    
    return text


def remove_excessive_punctuation(text: str) -> str:
    """
    Remove excessive punctuation (multiple consecutive punctuation marks).
    
    Args:
        text: Input text with potential excessive punctuation
        
    Returns:
        Text with excessive punctuation normalized
    """
    if not text:
        return ""
    
    # Replace multiple consecutive punctuation marks with single ones
    text = re.sub(r'[.]{2,}', '.', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    text = re.sub(r'[,]{2,}', ',', text)
    text = re.sub(r'[-]{2,}', '-', text)
    
    return text


def clean_and_normalize_text(
    text: str,
    remove_html: bool = True,
    remove_urls_flag: bool = True,
    remove_emails_flag: bool = True,
    remove_special_chars: bool = True,
    preserve_punctuation: bool = True,
    normalize_ws: bool = True,
    remove_excess_punct: bool = True
) -> str:
    """
    Apply comprehensive text cleaning and normalization.
    
    Args:
        text: Input text to clean
        remove_html: Remove HTML tags
        remove_urls_flag: Remove URLs
        remove_emails_flag: Remove email addresses
        remove_special_chars: Remove special characters
        preserve_punctuation: Preserve basic punctuation when removing special chars
        normalize_ws: Normalize whitespace
        remove_excess_punct: Remove excessive punctuation
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Apply cleaning steps
    if remove_html:
        text = strip_html_tags(text)
    
    if remove_urls_flag:
        text = remove_urls(text)
    
    if remove_emails_flag:
        text = remove_emails(text)

    # Remove common cue words that are often used with URLs/emails
    # This helps clean up orphaned words after URL/email removal
    cue_words = [
        r'\bvisit\b', r'\bcheck\s+out\b', r'\bgo\s+to\b', r'\bsee\b', 
        r'\blinks?\b', r'\bcontact\s+us\s+at\b', r'\bcontact\s+at\b',
        r'\bcontact\b(?=\s*$)', r'\bemail\s+us\s+at\b', r'\bemail\s+at\b',
        r'\bfor\s+more\s+(?:info|information|details)\b'
    ]
    
    for pattern in cue_words:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    if remove_special_chars:
        text = remove_special_characters(text, preserve_punctuation)
    
    if remove_excess_punct:
        text = remove_excessive_punctuation(text)
    
    # Remove standalone punctuation tokens but preserve sentence-ending periods
    # Only remove punctuation that's not at the end of words/sentences
    text = re.sub(r'\s+[!?:;,\-()#$%^&*@]+\s+', ' ', text)  # Between words
    text = re.sub(r'\s+[!?:;,\-()#$%^&*@]+$', '', text)     # At end with space
    text = re.sub(r'[!?:;,\-()#$%^&*@]+$', '', text)        # At end without space
    text = re.sub(r'^[!?:;,\-()#$%^&*@]+\s+', '', text)     # At beginning
    
    # Remove multiple symbols but keep single periods at word endings
    text = re.sub(r'[#$%^&*@]{2,}', '', text)  # Multiple symbols
    text = re.sub(r'[!]{2,}', '', text)        # Multiple exclamations
    
    # Clean up orphaned single punctuation (except periods at sentence ends)
    text = re.sub(r'\s+[,;:\-()]+\s+', ' ', text)
    text = re.sub(r'\s+\.\s+', ' ', text)  # Orphaned periods between words
    text = re.sub(r'^\s*[,;:\-()]\s*', '', text)  # Leading punctuation
    
    if normalize_ws:
        text = normalize_whitespace(text)
    
    return text


def prepare_searchable_text(
    title: str = "",
    abstract: str = "",
    content: str = "",
    separator: str = " ",
    max_length: Optional[int] = None
) -> str:
    """
    Prepare optimized searchable text from article components.
    
    This function combines and preprocesses title, abstract, and content
    to create text optimized for embedding generation and search indexing.
    
    Args:
        title: Article title
        abstract: Article abstract/summary
        content: Article main content
        separator: Separator between components
        max_length: Maximum length of output text (truncates if exceeded)
        
    Returns:
        Preprocessed searchable text optimized for embeddings
    """
    # Clean individual components
    title_clean = clean_and_normalize_text(title) if title else ""
    abstract_clean = clean_and_normalize_text(abstract) if abstract else ""
    content_clean = clean_and_normalize_text(content) if content else ""
    
    # Combine non-empty components
    components = [comp for comp in [title_clean, abstract_clean, content_clean] if comp.strip()]
    
    if not components:
        return ""
    
    # Join components
    searchable_text = separator.join(components)
    
    # Apply final normalization
    searchable_text = normalize_whitespace(searchable_text)
    
    # Truncate if necessary
    if max_length and len(searchable_text) > max_length:
        searchable_text = searchable_text[:max_length].rsplit(' ', 1)[0]  # Truncate at word boundary
    
    return searchable_text


def generate_preprocessed_content(article_data: dict) -> str:
    """
    Generate preprocessed searchable content for an article.
    
    This is the main function to call when processing articles for search indexing.
    It extracts title, abstract, and content from article data and returns
    optimized searchable text.
    
    Args:
        article_data: Dictionary containing article data with 'title', 'abstract', 'content' keys
        
    Returns:
        Preprocessed searchable text optimized for embeddings and search
    """
    title = article_data.get("title", "")
    abstract = article_data.get("abstract", "")
    content = article_data.get("content", "")
    
    return prepare_searchable_text(
        title=title,
        abstract=abstract,
        content=content,
        separator=" "
        # max_length=8000  # Reasonable limit for embeddings
    )
