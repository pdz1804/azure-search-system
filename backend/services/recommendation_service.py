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

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from backend.services.search_service import get_search_service
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
        """Initialize the recommendation service with search capabilities."""
        self.search_service = get_search_service()
        self.cache_duration_minutes = 60  # Cache duration in minutes
        print("✅ RecommendationService initialized with 60-minute cache")

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
            
            # Cache is valid if less than configured minutes old
            is_valid = time_diff.total_seconds() < self.cache_duration_minutes * 60
            
            if is_valid:
                print(f"✅ Cache valid: {time_diff.total_seconds():.0f}s old")
            else:
                print(f"⏰ Cache expired: {time_diff.total_seconds():.0f}s old (max {self.cache_duration_minutes * 60}s)")
            
            return is_valid
        except (ValueError, TypeError) as e:
            print(f"⚠️ Error parsing recommended_time '{article.get('recommended_time')}': {e}")
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
        print(f"🔍 Generating fresh recommendations for article: {article.get('title', 'Unknown')[:50]}...")
        
        try:
            # Create search query from article title and abstract
            title_text = article.get('title', '')
            abstract_text = article.get('abstract', '')
            content_query = f"{title_text} {abstract_text}".strip()
            
            if not content_query:
                print("⚠️ No title or abstract available for recommendation generation")
                return []
            
            # Search for similar articles (request more to ensure we get enough after filtering)
            # Increased from 15 to 25 to account for potential filtering and ensure we get 10+ recommendations
            search_results = self.search_service.search_articles(
                query=content_query,
                k=25,  # Request more to ensure we get 10+ after filtering
                page_index=None,
                page_size=None,
                app_id=app_id  # Filter by app_id for multi-tenant support
            )
            
            # Extract only article IDs and scores, filter out the current article
            recommendations = []
            if search_results and 'results' in search_results:
                for result in search_results['results']:
                    if result.get('id') != article_id:  # Exclude the current article
                        # Store only ID and score to save database space
                        recommendations.append({
                            'article_id': result.get('id'),
                            'score': result.get('score', 0.0)
                        })
                    
                    # Stop when we have 10 recommendations
                    if len(recommendations) >= 10:
                        break
            
            # If we don't have enough recommendations, try a broader search
            if len(recommendations) < 8:  # Threshold for "not enough" recommendations
                print(f"⚠️ Only got {len(recommendations)} recommendations, trying broader search...")
                
                # Try a broader search with just the title
                if title_text:
                    broader_results = self.search_service.search_articles(
                        query=title_text,
                        k=30,  # Request even more for broader search
                        page_index=None,
                        page_size=None,
                        app_id=app_id
                    )
                    
                    if broader_results and 'results' in broader_results:
                        # Add more recommendations from broader search
                        for result in broader_results['results']:
                            result_id = result.get('id')
                            # Skip if already in recommendations or is the current article
                            if result_id != article_id and not any(r['article_id'] == result_id for r in recommendations):
                                recommendations.append({
                                    'article_id': result_id,
                                    'score': result.get('score', 0.0) * 0.8  # Slightly lower score for broader matches
                                })
                                
                                if len(recommendations) >= 10:
                                    break
                
                print(f"📊 After broader search: {len(recommendations)} recommendations")
            
            print(f"📊 Generated {len(recommendations)} recommendations (IDs only)")
            return recommendations
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
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
                print("Fresh recommendations generated")
                
        Note:
            - Returns empty list if article not found or generation fails
            - Cached recommendations returned as fallback if fresh generation fails
            - Database automatically updated with fresh recommendations and timestamp
        """
        print(f"📖 Getting recommendations for article: {article_id}")
        
        try:
            # Fetch the current article using repository to avoid circular dependency
            article = await get_article_by_id_repo(article_id)
            if not article:
                print(f"❌ Article {article_id} not found")
                return [], False
            
            # Check if we have valid cached recommendations
            cached_recommendations = article.get('recommended', [])
            recommended_time = article.get('recommended_time')
            
            if cached_recommendations and self.is_recommendations_cache_valid(article):
                # Return cached recommendations
                print(f"💾 Using cached recommendations ({len(cached_recommendations)} items)")
                return cached_recommendations, False
            
            # Generate fresh recommendations
            print("🔄 Generating fresh recommendations...")
            fresh_recommendations = self._generate_fresh_recommendations(article, app_id)
            
            if not fresh_recommendations:
                # If generation failed, return cached ones if available
                if cached_recommendations:
                    print("⚠️ Fresh generation failed, using cached recommendations")
                    return cached_recommendations, False
                else:
                    print("⚠️ No recommendations available")
                    return [], False
            
            # Update the article with fresh recommendations
            now = datetime.utcnow().isoformat()
            update_data = {
                'recommended': fresh_recommendations,
                'recommended_time': now
            }
            
            print(f"🔄 About to update article {article_id} with recommendations in Cosmos DB")
            print(f"📝 Update data keys: {list(update_data.keys())}")
            
            updated_article = await update_article(article_id, update_data)
            print(f"💾 Updated article with {len(fresh_recommendations)} fresh recommendations")
            
            # Verify the update was successful
            if updated_article and updated_article.get('recommended_time') == now:
                print(f"✅ Database update verified: recommended_time = {updated_article.get('recommended_time')}")
            else:
                print(f"⚠️ Database update verification failed")
                print(f"   Expected recommended_time: {now}")
                print(f"   Actual recommended_time: {updated_article.get('recommended_time') if updated_article else 'None'}")
            
            return fresh_recommendations, True
            
        except Exception as e:
            print(f"❌ Error getting recommendations for article {article_id}: {e}")
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
            # detailed_recs[0] contains full article + recommendation_score: 0.85
            
        Note:
            - Silently skips articles that can't be fetched (deleted, private, etc.)
            - Preserves recommendation scores for ranking and display
            - Used by frontend to get rich article metadata for display
        """
        from backend.repositories.article_repo import get_article_by_id as get_article_by_id_repo
        
        detailed_recommendations = []
        
        for rec in recommendations:
            article_id = rec.get('article_id')
            score = rec.get('score', 0.0)
            
            try:
                # Use app_id filtering when fetching article details
                article_details = await get_article_by_id_repo(article_id, app_id=app_id)
                if article_details:
                    # Additional app_id check for safety
                    if app_id and article_details.get('app_id') != app_id:
                        print(f"🔒 Filtering recommendation {article_id} - different app_id: {article_details.get('app_id')} != {app_id}")
                        continue
                    
                    article_details['recommendation_score'] = score
                    detailed_recommendations.append(article_details)
                else:
                    print(f"⚠️ Article {article_id} not found or filtered out by app_id")
            except Exception as e:
                print(f"⚠️ Failed to fetch article {article_id}: {e}")
                continue
        
        print(f"📊 Fetched {len(detailed_recommendations)} detailed recommendations (filtered by app_id: {app_id})")
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
        
        # Take first 10 recommendations and split into top 5 and more 5
        top_10 = detailed_recommendations[:10]
        
        formatted_top5 = []
        formatted_more5 = []
        
        for i, article in enumerate(top_10):
            formatted_rec = {
                "id": article.get("id"),
                "title": article.get("title", "Untitled"),
                "abstract": article.get("abstract", "")[:200],  # Truncate abstract
                "author": article.get("author_name", "Unknown Author"),  # Fixed field name
                "image": article.get("image", "/default-image.jpg"),  # Fixed field name
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
        print(f"🔄 Batch refreshing recommendations for {len(article_ids)} articles")
        
        results = {}
        for article_id in article_ids:
            try:
                _, was_refreshed = await self.get_article_recommendations(article_id, app_id)
                results[article_id] = was_refreshed
            except Exception as e:
                print(f"❌ Failed to refresh recommendations for {article_id}: {e}")
                results[article_id] = False
        
        success_count = sum(results.values())        
        print(f"✅ Batch refresh completed: {sum(results.values())}/{len(article_ids)} successful")
        return results


# Singleton Pattern Implementation
# This ensures only one RecommendationService instance exists throughout the application
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
