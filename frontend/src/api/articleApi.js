import { apiClient, apiClientFormData, createFormData } from './config';

export const articleApi = {
  // Get all articles with pagination
  getArticles: async (params = {}) => {
    try {
      // Handle both old and new parameter formats
      if (typeof params === 'number') {
        const page = arguments[0] || 1;
        const pageSize = arguments[1] || 20;
        const search = arguments[2] || '';
        params = { page, page_size: pageSize };
        if (search) params.q = search;
      } else {
        params = {
          page: params.page || 1,
          page_size: params.page_size || 20,
          ...params
        };
      }
      
      // Remove undefined values
      Object.keys(params).forEach(key => {
        if (params[key] === undefined || params[key] === '') {
          delete params[key];
        }
      });
      
      const response = await apiClient.get('/articles', { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch articles'
      };
    }
  },

  // Get popular articles with time-decay algorithm
  getPopularArticles: async (page = 1, pageSize = 10) => {
    try {
      const response = await apiClient.get(`/articles/popular?page=${page}&page_size=${pageSize}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch popular articles'
      };
    }
  },

  // Get article by ID (increments view count)
  getArticle: async (id) => {
    try {
      const response = await apiClient.get(`/articles/${id}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Article not found'
      };
    }
  },

  // Legacy method name for backward compatibility
  getArticleById: async (id) => {
    return await articleApi.getArticle(id);
  },

  // Create new article (WRITER/ADMIN only)
  createArticle: async (articleData) => {
    try {
      const formData = new FormData();
      formData.append('title', articleData.title);
      formData.append('abstract', articleData.abstract);
      formData.append('content', articleData.content);
      if (articleData.tags) {
        formData.append('tags', Array.isArray(articleData.tags) ? articleData.tags.join(',') : articleData.tags);
      }
      if (articleData.image) {
        formData.append('image', articleData.image);
      }
      
      const response = await apiClientFormData.post('/articles/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create article'
      };
    }
  },

  // Update existing article (owner or ADMIN)
  updateArticle: async (id, articleData) => {
    try {
      const formData = new FormData();
      if (articleData.title) formData.append('title', articleData.title);
      if (articleData.abstract) formData.append('abstract', articleData.abstract);
      if (articleData.content) formData.append('content', articleData.content);
      if (articleData.tags) {
        formData.append('tags', Array.isArray(articleData.tags) ? articleData.tags.join(',') : articleData.tags);
      }
      if (articleData.status) formData.append('status', articleData.status);
      if (articleData.image) formData.append('image', articleData.image);
      
      const response = await apiClientFormData.put(`/articles/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update article'
      };
    }
  },

  // Delete article (owner or ADMIN)
  deleteArticle: async (id) => {
    try {
      const response = await apiClient.delete(`/articles/${id}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to delete article'
      };
    }
  },

  // Get articles by author
  getArticlesByAuthor: async (authorId, page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get(`/articles/author/${authorId}`, {
        params: { page, page_size: pageSize }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch author articles'
      };
    }
  },

  // Search articles by keyword
  searchArticles: async (keyword, k = 10, page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get(
        `/articles/search/${encodeURIComponent(keyword)}?k=${k}&page=${page}&page_size=${pageSize}`
      );
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Search failed'
      };
    }
  },

  // Legacy like/dislike methods (for backward compatibility)
  likeArticle: async (id) => {
    try {
      const response = await apiClient.post(`/users/reactions/${id}/like`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  dislikeArticle: async (id) => {
    try {
      const response = await apiClient.post(`/users/reactions/${id}/dislike`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // View article (legacy method - view count is now automatically incremented on getArticle)
  viewArticle: async (id) => {
    try {
      // This is now handled automatically by getArticle endpoint
      const response = await apiClient.get(`/articles/${id}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Get article statistics and summary
  getSummary: async () => {
    try {
      const response = await apiClient.get('/articles/summary');
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};
