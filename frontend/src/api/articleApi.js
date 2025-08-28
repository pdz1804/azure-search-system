import { apiClient, apiClientFormData, createFormData } from './config';
import { invalidateAuthorStats } from '../hooks/useAuthorStats';
import { APP_ID } from '../config/appConfig';

// Helper function to normalize article data from backend
const normalizeArticleData = (article) => {
  if (!article) return article;
  
  // Create a normalized copy
  const normalized = { ...article };
  
  // Map backend field names to frontend expectations
  if (article.article_id && !article.id) {
    normalized.id = article.article_id;
  }
  if (article.created_date && !article.created_at) {
    normalized.created_at = article.created_date;
  }
  if (article.total_like !== undefined && article.likes === undefined) {
    normalized.likes = article.total_like;
  }
  if (article.total_view !== undefined && article.views === undefined) {
    normalized.views = article.total_view;
  }
  
  return normalized;
};

// Helper function to normalize article arrays
const normalizeArticleArray = (articles) => {
  if (!Array.isArray(articles)) return articles;
  return articles.map(normalizeArticleData);
};

export const articleApi = {
  // Get all articles (supports both (page, limit, status) and (paramsObject))
  getArticles: async (...args) => {
    try {
      let params;
      if (args.length === 0) {
        params = { page: 1, limit: 12 };
      } else if (typeof args[0] === 'object') {
        const p = { ...args[0] };
        // Map to backend alias param names
        params = {
          'page[page]': p.page || p.current || 1,
          'page[page_size]': p.page_size || p.limit || p.pageSize || 12,
          'page[q]': p.q || undefined,
          'page[status]': p.status || undefined,
          'page[sort_by]': p.sort_by || p.sortBy || undefined,
          limit: p.limit // backend still reads 'limit' as default size
        };
      } else {
        const [page = 1, limit = 10, status = null] = args;
        params = { 'page[page]': page, 'page[page_size]': limit, limit };
        if (status) params.status = status;
      }
      // Add app_id to all article listing requests
      params.app_id = APP_ID;
      const response = await apiClient.get('/articles/', { params });
      
      // Normalize article data to ensure consistent field names
      if (response.data && response.data.success && response.data.data) {
        const normalizedData = {
          ...response.data,
          data: normalizeArticleArray(response.data.data)
        };
        return normalizedData;
      }
      
      return response.data;
    } catch (error) {
      console.error('Get articles error:', error);
      return { success: false, data: [], error: 'Failed to fetch articles' };
    }
  },

  // Get article by ID
  getArticleById: async (id) => {
    try {
      const response = await apiClient.get(`/articles/${id}`, {
        params: { app_id: APP_ID }
      });
      return response.data;
    } catch (error) {
      console.error('Get article error:', error);
      return { success: false, error: 'Failed to fetch article' };
    }
  },

  // Get articles by author
  getArticlesByAuthor: async (authorId, page = 1, limit = 10) => {
    try {
      const response = await apiClient.get(`/articles/author/${authorId}`, {
        params: { page, limit, app_id: APP_ID }
      });
      
      // Normalize article data to ensure consistent field names
      if (response.data && response.data.success && response.data.data) {
        const normalizedData = {
          ...response.data,
          data: normalizeArticleArray(response.data.data)
        };
        return normalizedData;
      }
      
      return response.data;
    } catch (error) {
      console.error('Get articles by author error:', error);
      return { success: false, data: [], error: 'Failed to fetch articles by author' };
    }
  },

  // Create article
  createArticle: async (articleData) => {
    try {
      // backend expects form fields (Form & UploadFile), so send multipart/form-data
      const form = createFormData(articleData);
      // Add app_id to article creation
      form.append('app_id', APP_ID);
      // If image exists on articleData but wasn't added by createFormData, add it explicitly
      try {
        let hasImage = false;
        for (const pair of form.entries()) {
          if (pair[0] === 'image') {
            hasImage = true;
            break;
          }
        }
        if (!hasImage && articleData && articleData.image) {
          const img = articleData.image;
          // if AntD wrapper, get originFileObj
          const fileObj = img.originFileObj ? img.originFileObj : img;
          form.append('image', fileObj);
          // eslint-disable-next-line no-console
          console.log('[DEBUG] createArticle - appended image manually to FormData', { name: fileObj.name, size: fileObj.size });
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error('[DEBUG] createArticle - failed to ensure image in FormData', e);
      }
      // DEBUG: list form entries before sending to help trace missing file
      try {
        // eslint-disable-next-line no-console
        console.log('[DEBUG] createArticle - FormData entries:');
        for (const pair of form.entries()) {
          // pair[1] can be a File object; log minimal info
          const val = pair[1];
          if (val && typeof val === 'object' && (val.name || val.size)) {
            // eslint-disable-next-line no-console
            console.log(pair[0], { name: val.name, size: val.size, type: val.type });
          } else {
            // eslint-disable-next-line no-console
            console.log(pair[0], val);
          }
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error('[DEBUG] Failed to log FormData entries', e);
      }
    const response = await apiClientFormData.post('/articles/', form);
      
      // Invalidate author stats cache for the article's author
      const userId = localStorage.getItem('user_id');
      if (userId) {
        invalidateAuthorStats(userId);
      }
      
      // Backend returns wrapper { success: true, data: {...} }
      if (response.data && response.data.success && response.data.data) {
        return { success: true, data: response.data.data };
      }
      return response.data;
    } catch (error) {
      console.error('Create article error:', error);
      return { success: false, error: 'Failed to create article' };
    }
  },

  // Update article
  updateArticle: async (id, articleData) => {
    try {
      // send as multipart/form-data so backend Form(...) parameters are populated
      const form = createFormData(articleData);
      // Add app_id to article updates
      form.append('app_id', APP_ID);
      const response = await apiClientFormData.put(`/articles/${id}`, form);
      
      // Invalidate author stats cache for the article's author
      const userId = localStorage.getItem('user_id');
      if (userId) {
        invalidateAuthorStats(userId);
      }
      
      // Backend returns wrapper { success: true, data: {...} }
      if (response.data && response.data.success && response.data.data) {
        return { success: true, data: response.data.data };
      }
      return response.data;
    } catch (error) {
      console.error('Update article error:', error);
      return { success: false, error: 'Failed to update article' };
    }
  },

  // Delete article
  deleteArticle: async (id) => {
    try {
      const response = await apiClient.delete(`/articles/${id}`, {
        params: { app_id: APP_ID }
      });
      
      // Invalidate author stats cache for the article's author
      const userId = localStorage.getItem('user_id');
      if (userId) {
        invalidateAuthorStats(userId);
      }
      
      return response.data;
    } catch (error) {
      console.error('Delete article error:', error);
      return { success: false, error: 'Failed to delete article' };
    }
  },

  // AI-powered search articles (allowed endpoint only)
  searchArticles: async (query, limit = 12, page = 1, maxResults = 60) => {
    try {
      const response = await apiClient.get('/search/articles', {
        params: {
          q: query,
          k: Math.min(limit, maxResults),
          page_index: page - 1, // Backend expects 0-based page index
          page_size: Math.min(limit, maxResults),
          app_id: APP_ID
        }
      });
      
      // Normalize article data to ensure consistent field names
      if (response.data && response.data.success && response.data.data) {
        const normalizedData = {
          ...response.data,
          data: normalizeArticleArray(response.data.data)
        };
        return normalizedData;
      }
      
      return response.data;
    } catch (error) {
      console.error('AI search articles error:', error);
      return { success: false, data: [], error: 'Search failed' };
    }
  },


  // Get popular articles
  getPopularArticles: async (limit = 10) => {
    try {
      const response = await apiClient.get('/articles/popular', {
        params: { limit, app_id: APP_ID }
      });
      
      // Normalize article data to ensure consistent field names
      if (response.data && response.data.success && response.data.data) {
        const normalizedData = {
          ...response.data,
          data: normalizeArticleArray(response.data.data)
        };
        return normalizedData;
      }
      
      return response.data;
    } catch (error) {
      console.error('Get popular articles error:', error);
      return { success: false, data: [], error: 'Failed to fetch popular articles' };
    }
  },

  // Get statistics
  getStatistics: async () => {
    try {
      const response = await apiClient.get('/articles/stats', {
        params: { app_id: APP_ID }
      });
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
      const response = await apiClient.get('/articles/categories', {
        params: { app_id: APP_ID }
      });
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
        params: { page, limit, app_id: APP_ID }
      });
      
      // Normalize article data to ensure consistent field names
      if (response.data && response.data.success && response.data.data) {
        const normalizedData = {
          ...response.data,
          data: normalizeArticleArray(response.data.data)
        };
        return normalizedData;
      }
      
      return response.data;
    } catch (error) {
      console.error('Get articles by category error:', error);
      return { success: false, data: [], error: 'Failed to fetch articles by category' };
    }
  },

  // Get article by ID
  getArticle: async (id) => {
    try {
      const response = await apiClient.get(`/articles/${id}`, {
        params: { app_id: APP_ID }
      });
      return response.data;
    } catch (error) {
      console.error('Get article error:', error);
      return { success: false, error: 'Failed to fetch article' };
    }
  }
};
