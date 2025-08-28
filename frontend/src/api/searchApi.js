import { apiClient } from './config';
import { APP_ID } from '../config/appConfig';

export const searchApi = {
  // General AI-powered search (routes automatically to articles or authors)
  search: async (query, limit = 12, page = 1, maxResults = 60) => {
    try {
      const response = await apiClient.get('/search/', {
        params: {
          q: query,
          k: Math.min(limit, maxResults),
          page_index: page - 1, // Backend expects 0-based page index
          page_size: Math.min(limit, maxResults),
          app_id: APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('General search error:', error);
      return { success: false, data: [], error: 'Search failed' };
    }
  },

  // Search articles specifically
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
      return response.data;
    } catch (error) {
      console.error('Articles search error:', error);
      return { success: false, data: [], error: 'Articles search failed' };
    }
  },

  // Search authors specifically
  searchAuthors: async (query, limit = 12, page = 1, maxResults = 60) => {
    try {
      const response = await apiClient.get('/search/authors', {
        params: {
          q: query,
          k: Math.min(limit, maxResults),
          page_index: page - 1, // Backend expects 0-based page index
          page_size: Math.min(limit, maxResults),
          app_id: APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('Authors search error:', error);
      return { success: false, data: [], error: 'Authors search failed' };
    }
  }
};

export default searchApi;
