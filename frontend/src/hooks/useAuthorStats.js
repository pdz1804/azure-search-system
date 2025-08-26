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
  const response = await articleApi.getArticlesByAuthor(userId, 1, limit);
  
  if (!response.success) {
    throw new Error(response.error || 'Failed to fetch articles');
  }

  const articles = response.data?.items || (Array.isArray(response.data) ? response.data : []) || [];
  
  const published_articles = articles.filter(a => a.status === 'published').length;
  const draft_articles = articles.filter(a => a.status === 'draft').length;
  const total_views = articles.reduce((sum, a) => sum + (a.views || 0), 0);
  const total_likes = articles.reduce((sum, a) => sum + (a.likes || 0), 0);
  const avg_views = articles.length > 0 ? Math.round(total_views / articles.length) : 0;

  return {
    total_articles: articles.length,
    published_articles,
    draft_articles,
    total_views,
    total_likes,
    avg_views,
    articles: articles.slice(0, 50) // Keep only first 50 for memory efficiency
  };
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
