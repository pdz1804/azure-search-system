import { apiClient } from './config';

export const articleApi = {
  // Get all articles
  getArticles: async (page = 1, limit = 10, status = null) => {
    try {
      const params = { page, limit };
      if (status) params.status = status;
      const response = await apiClient.get('/articles', { params });
      return response.data;
    } catch (error) {
      console.error('Get articles error:', error);
      return { success: false, data: [], error: 'Failed to fetch articles' };
    }
  },

  // Get article by ID
  getArticleById: async (id) => {
    try {
      const response = await apiClient.get(`/articles/${id}`);
      return response.data;
    } catch (error) {
      console.error('Get article error:', error);
      return { success: false, error: 'Failed to fetch article' };
    }
  },

  // Create article
  createArticle: async (articleData) => {
    try {
      const response = await apiClient.post('/articles', articleData);
      return response.data;
    } catch (error) {
      console.error('Create article error:', error);
      return { success: false, error: 'Failed to create article' };
    }
  },

  // Update article
  updateArticle: async (id, articleData) => {
    try {
      const response = await apiClient.put(`/articles/${id}`, articleData);
      return response.data;
    } catch (error) {
      console.error('Update article error:', error);
      return { success: false, error: 'Failed to update article' };
    }
  },

  // Delete article
  deleteArticle: async (id) => {
    try {
      const response = await apiClient.delete(`/articles/${id}`);
      return response.data;
    } catch (error) {
      console.error('Delete article error:', error);
      return { success: false, error: 'Failed to delete article' };
    }
  },

  // AI-powered search articles
  searchArticles: async (query, limit = 10, page = 1, maxResults = 50) => {
    try {
      const response = await apiClient.get('/search/articles', {
        params: {
          q: query,
          k: Math.min(limit, maxResults),
          page_index: page - 1, // Convert to 0-based for backend
          page_size: Math.min(limit, maxResults)
        }
      });
      return response.data;
    } catch (error) {
      console.error('AI search articles error:', error);
      // Fallback to simple search
      try {
        const fallbackResponse = await apiClient.get('/articles/search', {
          params: {
            q: query,
            page,
            limit: Math.min(limit, maxResults)
          }
        });
        return fallbackResponse.data;
      } catch (fallbackError) {
        console.error('Fallback search also failed:', fallbackError);
        return { success: false, data: [], error: 'Search failed' };
      }
    }
  },

  // Simple search articles (fallback)
  searchArticlesSimple: async (query, page = 1, limit = 10) => {
    try {
      const response = await apiClient.get('/articles/search', {
        params: {
          q: query,
          page,
          limit
        }
      });
      return response.data;
    } catch (error) {
      console.error('Simple search articles error:', error);
      return { success: false, data: [], error: 'Search failed' };
    }
  },

  // Get popular articles
  getPopularArticles: async (limit = 10) => {
    try {
      const response = await apiClient.get('/articles/popular', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Get popular articles error:', error);
      return { success: false, data: [], error: 'Failed to fetch popular articles' };
    }
  },

  // Increment view count
  incrementViewCount: async (id) => {
    try {
      const response = await apiClient.post(`/articles/${id}/view`);
      return response.data;
    } catch (error) {
      console.error('Increment view count error:', error);
      return { success: false, error: 'Failed to increment view count' };
    }
  },

  // Get statistics
  getStatistics: async () => {
    try {
      const response = await apiClient.get('/articles/stats');
      return response.data;
    } catch (error) {
      console.error('Get statistics error:', error);
      return { 
        success: false, 
        data: { articles: 0, authors: 0, total_views: 0, bookmarks: 0 },
        error: 'Failed to fetch statistics' 
      };
    }
  },

  // Get categories
  getCategories: async () => {
    try {
      const response = await apiClient.get('/articles/categories');
      return response.data;
    } catch (error) {
      console.error('Get categories error:', error);
      return { success: false, data: [], error: 'Failed to fetch categories' };
    }
  },

  // Get articles by category
  getArticlesByCategory: async (category, page = 1, limit = 10) => {
    try {
      const response = await apiClient.get(`/articles/categories/${category}`, {
        params: { page, limit }
      });
      return response.data;
    } catch (error) {
      console.error('Get articles by category error:', error);
      return { success: false, data: [], error: 'Failed to fetch articles by category' };
    }
  },

  // Get article by ID
  getArticle: async (id) => {
    try {
      const response = await apiClient.get(`/articles/${id}`);
      return response.data;
    } catch (error) {
      console.error('Get article error:', error);
      return { success: false, error: 'Failed to fetch article' };
    }
  }
};
