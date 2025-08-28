import { useState, useEffect, useRef } from 'react';
import { articleApi } from '../api/articleApi';

// Global cache to prevent duplicate API calls across components
const statsCache = new Map();
const pendingRequests = new Map();

/**
 * Custom hook to fetch and cache author statistics
 * Prevents duplicate API calls when multiple components need the same data
 */
export const useAuthorStats = (userId, options = {}) => {
  const { 
    enabled = true, 
    limit = 1000, // Get all articles for accurate stats
    refetchOnMount = false 
  } = options;
  
  const [stats, setStats] = useState({
    total_articles: 0,
    published_articles: 0,
    draft_articles: 0,
    total_views: 0,
    total_likes: 0,
    avg_views: 0,
    articles: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!enabled || !userId) {
      setLoading(false);
      return;
    }

    const fetchStats = async () => {
      const cacheKey = `author_stats_${userId}`;
      
      // Check if we already have cached data and don't need to refetch
      if (!refetchOnMount && statsCache.has(cacheKey)) {
        const cachedData = statsCache.get(cacheKey);
        if (mountedRef.current) {
          setStats(cachedData);
          setLoading(false);
        }
        return;
      }

      // Check if there's already a pending request for this user
      if (pendingRequests.has(cacheKey)) {
        try {
          const result = await pendingRequests.get(cacheKey);
          if (mountedRef.current) {
            setStats(result);
            setLoading(false);
          }
        } catch (err) {
          if (mountedRef.current) {
            setError(err.message || 'Failed to fetch stats');
            setLoading(false);
          }
        }
        return;
      }

      // Create new request
      setLoading(true);
      setError(null);

      const requestPromise = performFetch(userId, limit);
      pendingRequests.set(cacheKey, requestPromise);

      try {
        const result = await requestPromise;
        
        // Cache the result for 5 minutes
        statsCache.set(cacheKey, result);
        setTimeout(() => {
          statsCache.delete(cacheKey);
        }, 5 * 60 * 1000);

        if (mountedRef.current) {
          setStats(result);
          setLoading(false);
        }
      } catch (err) {
        console.error('Error fetching author stats:', err);
        if (mountedRef.current) {
          setError(err.message || 'Failed to fetch stats');
          setLoading(false);
        }
      } finally {
        pendingRequests.delete(cacheKey);
      }
    };

    fetchStats();
  }, [userId, enabled, limit, refetchOnMount]);

  return { stats, loading, error };
};

/**
 * Internal function to fetch and calculate stats
 */
const performFetch = async (userId, limit) => {
  console.log('🔍 performFetch called for userId:', userId, 'limit:', limit);
  
  try {
    const response = await articleApi.getArticlesByAuthor(userId, 1, limit);
    console.log('🔍 getArticlesByAuthor response:', response);
    
    if (!response.success) {
      console.error('❌ API response not successful:', response);
      throw new Error(response.error || 'Failed to fetch articles');
    }

    // Handle different response structures from backend
    let articles = [];
    if (response.data?.data?.items) {
      // Backend returns { success: true, data: { items: [...] } }
      articles = response.data.data.items;
    } else if (response.data?.items) {
      // Backend returns { items: [...] }
      articles = response.data.items;
    } else if (Array.isArray(response.data?.data)) {
      // Backend returns { success: true, data: [...] }
      articles = response.data.data;
    } else if (Array.isArray(response.data)) {
      // Backend returns [...] directly
      articles = response.data;
    }
    
    console.log('🔍 Parsed articles:', articles);
    console.log('🔍 Articles count:', articles.length);
    
    if (articles.length > 0) {
      console.log('🔍 First article sample:', {
        id: articles[0].id,
        title: articles[0].title,
        status: articles[0].status,
        views: articles[0].views,
        likes: articles[0].likes,
        total_view: articles[0].total_view,
        total_like: articles[0].total_like
      });
    }
    
    const published_articles = articles.filter(a => a.status === 'published').length;
    const draft_articles = articles.filter(a => a.status === 'draft').length;
    const total_views = articles.reduce((sum, a) => {
      const views = a.views || a.total_view || 0;
      console.log(`🔍 Article ${a.id}: views=${a.views}, total_view=${a.total_view}, final=${views}`);
      return sum + views;
    }, 0);
    const total_likes = articles.reduce((sum, a) => {
      const likes = a.likes || a.total_like || 0;
      console.log(`🔍 Article ${a.id}: likes=${a.likes}, total_like=${a.total_like}, final=${likes}`);
      return sum + likes;
    }, 0);
    const avg_views = articles.length > 0 ? Math.round(total_views / articles.length) : 0;

    const stats = {
      total_articles: articles.length,
      published_articles,
      draft_articles,
      total_views,
      total_likes,
      avg_views,
      articles: articles.slice(0, 50) // Keep only first 50 for memory efficiency
    };
    
    console.log('📊 Calculated stats:', stats);
    console.log('📊 Articles status breakdown:', articles.map(a => ({ id: a.id, status: a.status, views: a.views || a.total_view, likes: a.likes || a.total_like })));
    
    return stats;
  } catch (error) {
    console.error('❌ Error in performFetch:', error);
    throw error;
  }
};

/**
 * Function to invalidate cache for a specific user
 * Call this after creating/updating/deleting articles
 */
export const invalidateAuthorStats = (userId) => {
  const cacheKey = `author_stats_${userId}`;
  statsCache.delete(cacheKey);
  if (pendingRequests.has(cacheKey)) {
    pendingRequests.delete(cacheKey);
  }
};

/**
 * Function to clear all cached stats
 */
export const clearAllAuthorStats = () => {
  statsCache.clear();
  pendingRequests.clear();
};
