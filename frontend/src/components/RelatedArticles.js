import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import { EyeIcon, HeartIcon, ClockIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { articleApi } from '../api/articleApi';
import LoadingSpinner from './LoadingSpinner';
import { getRandomDefaultImage } from '../utils/defaultImage';

const RelatedArticles = ({ currentArticleId, authorId, tags = [] }) => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRelatedArticles = async () => {
      try {
        setLoading(true);
        
        // Try to get articles by the same author first
        let relatedArticles = [];
        
        if (authorId) {
          const authorResponse = await articleApi.getArticlesByAuthor(authorId, 1, 6);
          if (authorResponse.success && authorResponse.data.items) {
            relatedArticles = authorResponse.data.items.filter(
              article => (article.id || article.article_id) !== currentArticleId
            );
          }
        }
        
        // If we don't have enough articles, get popular articles
        if (relatedArticles.length < 3) {
          const popularResponse = await articleApi.getPopularArticles(1, 6);
          if (popularResponse.success) {
            const popularArticles = Array.isArray(popularResponse.data) 
              ? popularResponse.data 
              : popularResponse.data.items || [];
            
            const filteredPopular = popularArticles.filter(
              article => (article.id || article.article_id) !== currentArticleId && 
                       !relatedArticles.some(existing => (existing.id || existing.article_id) === (article.id || article.article_id))
            );
            
            relatedArticles = [...relatedArticles, ...filteredPopular];
          }
        }
        
        // Limit to 4 articles
        setArticles(relatedArticles.slice(0, 4));
      } catch (error) {
        console.error('Error fetching related articles:', error);
      } finally {
        setLoading(false);
      }
    };

    if (currentArticleId) {
      fetchRelatedArticles();
    }
  }, [currentArticleId, authorId, tags]);

  const calculateReadingTime = (content) => {
    if (!content || typeof content !== 'string') return 1; // Default to 1 min if no content
    const wordsPerMinute = 200;
    const words = content.trim().split(/\s+/).filter(word => word.length > 0).length;
    return Math.max(1, Math.ceil(words / wordsPerMinute)); // Minimum 1 minute
  };
  
  // Get content for reading time calculation (fallback to abstract if content is missing)
  const getContentForReading = (article) => {
    return article.content || article.abstract || '';
  };

  if (loading) {
    return (
  <div className="bg-surface rounded-lg shadow-sm p-6 border-surface" style={{ borderWidth: 1 }}>
        <h3 className="text-xl font-bold text-gray-900 mb-6">Related Articles</h3>
        <LoadingSpinner text="Loading related articles..." />
      </div>
    );
  }

  if (!articles.length) {
    return null;
  }

  return (
    <div className="bg-surface rounded-lg shadow-sm p-6 border-surface" style={{ borderWidth: 1 }}>
      <h3 className="text-xl font-bold text-surface mb-6">Related Articles</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {articles.map((article) => (
          <Link
            key={article.id || article.article_id}
            to={`/articles/${article.id || article.article_id}`}
            className="group block"
          >
            <article className="bg-surface-2 rounded-lg overflow-hidden hover:shadow-md transition-shadow border-surface" style={{ borderWidth: 1 }}>
              {/* Article Image */}
              {article.image && (
                <div className="aspect-video overflow-hidden">
                  <img
                    src={article.image}
                    alt={article.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => {
                      console.log('Related article image failed to load:', article.image);
                      e.target.src = getRandomDefaultImage();
                    }}
                  />
                </div>
              )}
              
              <div className="p-4">
                {/* Tags */}
                {article.tags && article.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {article.tags.slice(0, 2).map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                
                {/* Title */}
                <h4 className="font-semibold text-surface group-hover:text-blue-400 transition-colors mb-2 line-clamp-2">
                  {article.title}
                </h4>
                
                {/* Abstract */}
                {article.abstract && (
                  <p className="text-muted text-sm mb-3 line-clamp-2">
                    {article.abstract}
                  </p>
                )}
                
                {/* Meta Info */}
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-3">
                    <span className="flex items-center">
                      <EyeIcon className="w-3 h-3 mr-1" />
                      {article.views?.toLocaleString() || 0}
                    </span>
                    <span className="flex items-center">
                      <HeartIcon className="w-3 h-3 mr-1" />
                      {article.likes || 0}
                    </span>
                                         <span className="flex items-center">
                       <ClockIcon className="w-3 h-3 mr-1" />
                       {calculateReadingTime(getContentForReading(article))} min
                     </span>
                  </div>
                  
                  <span>
                    {(article.created_date || article.created_at) ? format(new Date(article.created_date || article.created_at), 'MMM dd') : 'Recently'}
                  </span>
                </div>
              </div>
            </article>
          </Link>
        ))}
      </div>
      
      {authorId && (
        <div className="mt-6 text-center">
          <Link
            to={`/profile/${authorId}`}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View all articles by this author
          </Link>
        </div>
      )}
    </div>
  );
};

export default RelatedArticles;
