"""
Article Recommendation Service

This service provides intelligent article recommendations with efficient caching and storage:

Key Features:
- 60-minute cache refresh logic for timely recommendations
- Lightweight storage (article IDs + scores only)
- Search-based recommendation generation using AI search
- Dynamic detail fetching for frontend display
- Comprehensive debugging and error handling

Architecture:
- RecommendationService: Main service class
- Storage: Cosmos DB with minimal footprint
- Caching: Time-based validation (60 minutes)
- Frontend Integration: Detailed article info on-demand

Usage:
    service = get_recommendation_service()
    recommendations, was_refreshed = await service.get_article_recommendations(article_id)
    detailed_recs = await service.fetch_article_details_for_recommendations(recommendations)
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from backend.services.article_service import update_article
from backend.repositories.article_repo import get_article_by_id as get_article_by_id_repo

class RecommendationService:
    """
    Service for managing article recommendations with intelligent caching and efficient storage.
    
    This service implements a sophisticated recommendation system that:
    - Generates recommendations using AI search based on article content
    - Stores lightweight recommendation data (IDs + scores only)
    - Implements 60-minute cache refresh for optimal performance
    - Fetches detailed article information on-demand for display
    - Provides comprehensive debugging and error handling
    
    Storage Strategy:
        Instead of storing full article objects in recommendations, we store:
        [{'article_id': str, 'score': float}, ...] 
        This reduces database storage significantly while maintaining functionality.
    
    Cache Strategy:
        - Recommendations expire after 60 minutes
        - Cache validation checks article.recommended_time timestamp
        - Fresh generation triggers when cache is invalid or missing
    
    Frontend Integration:
        - Returns top 10 recommendations split into top5/more5
        - Fetches full article details when needed for display
        - Includes author info, images, dates, and metadata
    """

    def __init__(self):
        try:
            from backend.services.search_service import get_search_service
            self.search_service = get_search_service()
        except ImportError:
            self.search_service = None
        self.cache_duration_minutes = 60

    def is_recommendations_cache_valid(self, article: Dict) -> bool:
        """
        Check if the cached recommendations are still valid (less than 60 minutes old).
        
        Args:
            article (Dict): Article document containing recommended_time field
            
        Returns:
            bool: True if cache is valid and fresh, False if expired or invalid
            
        Note:
            - Cache expires after 60 minutes for optimal freshness
            - Returns False if recommended_time is missing or unparseable
            - Uses UTC time for consistency across timezones
        """
        if not article or not article.get("recommended_time"):
            return False
            
        try:
            recommended_time = datetime.fromisoformat(article["recommended_time"])
            current_time = datetime.utcnow()
            time_diff = current_time - recommended_time
            
            is_valid = time_diff.total_seconds() < self.cache_duration_minutes * 60
            
            if is_valid:
                return True
            else:
                return False
            
            return is_valid
        except (ValueError, TypeError):
            return False

    def _generate_fresh_recommendations(self, article: Dict, app_id: Optional[str] = None) -> List[Dict]:
        """
        Generate fresh recommendations using the AI search service.
        
        This method:
        1. Creates a search query from article title and abstract
        2. Uses the search service to find similar articles
        3. Filters out the current article from results
        4. Returns lightweight recommendation objects (ID + score only)
        
        Args:
            article (Dict): The source article document with title, abstract, and id
            app_id (Optional[str]): Application ID for filtering search results to same app
            
        Returns:
            List[Dict]: List of recommendation objects in format:
                       [{'article_id': str, 'score': float}, ...]
                       Maximum 10 recommendations returned
                       
        Note:
            - Uses article title and abstract for semantic search
            - Excludes the source article from recommendations
            - Stores only minimal data to reduce database footprint
        """
        article_id = article.get('id')
        
        try:
            if not self.search_service:
                return []
                
            title_text = ''
            abstract_text = article.get('abstract', '')
            content_query = f"{title_text} {abstract_text}".strip()
            
            if not content_query:
                return []
            
            search_results = self.search_service.search_articles(
                query=content_query,
                k=25,
                page_index=None,
                page_size=None,
                app_id=app_id
            )
            
            recommendations = []
            if search_results and 'results' in search_results:
                for result in search_results['results']:
                    if result.get('id') != article_id:
                        recommendations.append({
                            'article_id': result.get('id'),
                            'score': result.get('score', 0.0)
                        })
                    
                    if len(recommendations) >= 10:
                        break
            
            if len(recommendations) < 8:
                
                if title_text:
                    broader_results = self.search_service.search_articles(
                        query=title_text,
                        k=30,
                        page_index=None,
                        page_size=None,
                        app_id=app_id
                    )
                    
                    if broader_results and 'results' in broader_results:
                        for result in broader_results['results']:
                            result_id = result.get('id')
                            if result_id != article_id and not any(r['article_id'] == result_id for r in recommendations):
                                recommendations.append({
                                    'article_id': result_id,
                                    'score': result.get('score', 0.0) * 0.8
                                })
                                
                                if len(recommendations) >= 10:
                                    break

            return recommendations
            
        except Exception:
            return []

    async def get_article_recommendations(self, article_id: str, app_id: Optional[str] = None) -> Tuple[List[Dict], bool]:
        """
        Get recommendations for an article with intelligent caching and database persistence.
        
        This is the main entry point for the recommendation system. The workflow:
        1. Fetches the source article from database
        2. Checks if cached recommendations are still valid (< 60 minutes old)
        3. Returns cached recommendations if valid
        4. Generates fresh recommendations if cache expired/missing
        5. Persists fresh recommendations to database with timestamp
        6. Returns recommendations with refresh status
        
        Args:
            article_id (str): Unique identifier of the article to get recommendations for
            app_id (Optional[str]): Application ID for filtering recommendations to same app
            
        Returns:
            Tuple[List[Dict], bool]: 
                - List[Dict]: Recommendation objects [{'article_id': str, 'score': float}, ...]
                - bool: True if recommendations were freshly generated, False if cached
                
        Example:
            recommendations, was_refreshed = await service.get_article_recommendations('abc123')
            if was_refreshed:
                
        Note:
            - Returns empty list if article not found or generation fails
            - Cached recommendations returned as fallback if fresh generation fails
            - Database automatically updated with fresh recommendations and timestamp
        """
        
        try:
            article = await get_article_by_id_repo(article_id)
            if not article:
                return [], False
            
            cached_recommendations = article.get('recommended', [])
            
            if cached_recommendations and self.is_recommendations_cache_valid(article):
                return cached_recommendations, False
            
            fresh_recommendations = self._generate_fresh_recommendations(article, app_id)
            
            if not fresh_recommendations:
                if cached_recommendations:
                    return cached_recommendations, False
                else:
                    return [], False
            
            now = datetime.utcnow().isoformat()
            update_data = {
                'recommended': fresh_recommendations,
                'recommended_time': now
            }

            updated_article = await update_article(article_id, update_data)
            
            if updated_article and updated_article.get('recommended_time') == now:
                pass
            else:
                pass
            
            return fresh_recommendations, True
            
        except Exception:
            return [], False

    async def fetch_article_details_for_recommendations(self, recommendations: List[Dict], app_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch full article details for lightweight recommendation objects.
        
        This method converts minimal recommendation data (ID + score) into full article
        objects with all necessary metadata for frontend display. It:
        1. Iterates through recommendation IDs
        2. Fetches full article details from database
        3. Adds recommendation score to article data
        4. Filters out any articles that couldn't be fetched
        
        Args:
            recommendations (List[Dict]): List of lightweight recommendation objects
                                        Format: [{'article_id': str, 'score': float}, ...]
            
        Returns:
            List[Dict]: List of full article documents with added 'recommendation_score' field
                       Includes: id, title, abstract, author, background_image, created_at, 
                               updated_at, recommendation_score, and all other article fields
                       
        Example:
            minimal_recs = [{'article_id': 'abc123', 'score': 0.85}]
            detailed_recs = await service.fetch_article_details_for_recommendations(minimal_recs)
            
        Note:
            - Silently skips articles that can't be fetched (deleted, private, etc.)
            - Preserves recommendation scores for ranking and display
            - Used by frontend to get rich article metadata for display
        """
        detailed_recommendations = []
        
        for rec in recommendations:
            article_id = rec.get('article_id')
            score = rec.get('score', 0.0)
            
            try:
                article_details = await get_article_by_id_repo(article_id, app_id=app_id)
                if article_details:
                    if app_id and article_details.get('app_id') != app_id:
                        continue
                    
                    article_details['recommendation_score'] = score
                    detailed_recommendations.append(article_details)
                else:
                    pass
            except Exception:
                continue
        
        return detailed_recommendations

    def format_recommendations_for_display(self, detailed_recommendations: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Format detailed recommendations for optimal frontend display and user experience.
        
        This method processes full article objects and creates a structured response
        optimized for the frontend ArticleDetail component. It:
        1. Takes up to 10 full article documents
        2. Splits them into top 5 and additional 5 recommendations  
        3. Formats each recommendation with essential display fields
        4. Truncates abstracts for consistent UI layout
        
        Args:
            detailed_recommendations (List[Dict]): Full article documents with 'recommendation_score'
                                                  Each should contain: id, title, abstract, author, 
                                                  background_image, created_at, updated_at, etc.
            
        Returns:
            Dict[str, List[Dict]]: Structured response with two sections:
                'top5': First 5 recommendations for immediate display
                'more5': Next 5 recommendations for "Show More" functionality
                
        Response Format:
            {
                "top5": [
                    {
                        "id": str,
                        "title": str,
                        "abstract": str (truncated to 200 chars),
                        "author": str,
                        "background_image": str,
                        "score": float,
                        "created_at": str,
                        "updated_at": str
                    }, ...
                ],
                "more5": [...] // Same format as top5
            }
            
        Note:
            - Frontend displays top5 immediately, more5 on user request
            - Abstracts truncated to 200 characters for consistent UI
            - Handles missing fields gracefully with defaults
        """
        if not detailed_recommendations:
            return {"top5": [], "more5": []}
        
        top_10 = detailed_recommendations[:10]
        
        formatted_top5 = []
        formatted_more5 = []
        
        for i, article in enumerate(top_10):
            formatted_rec = {
                "id": article.get("id"),
                "title": article.get("title", "Untitled"),
                "abstract": article.get("abstract", "")[:200],
                "author": article.get("author_name", "Unknown Author"),
                "image": article.get("image", "/default-image.jpg"),
                "score": article.get("recommendation_score", 0),
                "created_at": article.get("created_at"),
                "updated_at": article.get("updated_at")
            }
            
            if i < 5:
                formatted_top5.append(formatted_rec)
            else:
                formatted_more5.append(formatted_rec)
        
        return {
            "top5": formatted_top5,
            "more5": formatted_more5
        }

    async def refresh_recommendations_batch(self, article_ids: List[str], app_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Refresh recommendations for multiple articles in batch for operational efficiency.
        
        This method is useful for:
        - Scheduled maintenance tasks
        - Bulk recommendation updates
        - Content management operations
        - Performance optimization scenarios
        
        Args:
            article_ids (List[str]): List of article IDs to refresh recommendations for
            app_id (Optional[str]): Application ID for filtering recommendations to same app
            
        Returns:
            Dict[str, bool]: Mapping of article_id to success status
                           True = recommendations successfully refreshed
                           False = refresh failed for that article

        """
        
        results = {}
        for article_id in article_ids:
            try:
                _, was_refreshed = await self.get_article_recommendations(article_id, app_id)
                results[article_id] = was_refreshed
            except Exception:
                results[article_id] = False
        
        return results

_recommendation_service = None

def get_recommendation_service() -> RecommendationService:
    """
    Get the singleton instance of RecommendationService.
    
    This function implements the singleton pattern to ensure consistent
    recommendation service behavior across the application. The same
    instance is reused to maintain state and avoid initialization overhead.

    """
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service
