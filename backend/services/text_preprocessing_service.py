"""
Text preprocessing service for backend article processing.

This service provides text preprocessing functionality for the backend,
integrating with the ai_search text preprocessing utilities.
"""

import sys
import os

# Add ai_search module to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
ai_search_path = os.path.join(project_root, 'ai_search')
if ai_search_path not in sys.path:
    sys.path.append(ai_search_path)

from ai_search.utils.text_preprocessing import generate_preprocessed_content


def preprocess_article_text(article_data: dict) -> str:
    """
    Preprocess article text for search optimization.
    
    This function serves as the main entry point for preprocessing article
    text in the backend service layer.
    
    Args:
        article_data: Dictionary containing article data with keys:
                     - title (str): Article title
                     - abstract (str, optional): Article abstract
                     - content (str): Article content
                     
    Returns:
        str: Preprocessed and optimized searchable text
    """
    try:
        return generate_preprocessed_content(article_data)
    except Exception as e:
        print(f"⚠️ Error preprocessing article text: {e}")
        # Fallback to simple concatenation if preprocessing fails
        title = article_data.get("title", "")
        abstract = article_data.get("abstract", "")
        content = article_data.get("content", "")
        return " ".join([title, abstract, content]).strip()


def should_regenerate_preprocessed_text(
    current_preprocessed: str,
    title: str,
    abstract: str = "",
    content: str = ""
) -> bool:
    """
    Determine if preprocessed text needs to be regenerated.
    
    This function checks if the current preprocessed text is still valid
    based on the current article content.
    
    Args:
        current_preprocessed: Current preprocessed text
        title: Current article title
        abstract: Current article abstract
        content: Current article content
        
    Returns:
        bool: True if preprocessing should be regenerated
    """
    if not current_preprocessed:
        return True
    
    # Generate new preprocessed text and compare
    article_data = {
        "title": title,
        "abstract": abstract,
        "content": content
    }
    
    new_preprocessed = preprocess_article_text(article_data)
    return current_preprocessed != new_preprocessed
