import { apiClient } from './config';
import { APP_ID } from '../config/appConfig';

// Helper function to normalize user data from backend to frontend format
const normalizeUserData = (user) => {
  if (!user) return user;
  
  const normalized = { ...user };
  
  // Map backend field names to frontend expectations
  if (user.user_id && !user.id) {
    normalized.id = user.user_id;
  }
  
  if (user.full_name && !user.name) {
    normalized.name = user.full_name;
  }
  
  // Ensure we have both fields for compatibility
  if (user.full_name && !normalized.full_name) {
    normalized.full_name = user.full_name;
  }
  
  if (user.name && !normalized.full_name) {
    normalized.full_name = user.name;
  }
  
  // Handle followers/following counts
  if (user.total_followers !== undefined && user.num_followers === undefined) {
    normalized.num_followers = user.total_followers;
  }
  
  if (user.total_following !== undefined && user.num_following === undefined) {
    normalized.num_following = user.total_following;
  }
  
  // Map followers field for frontend compatibility
  if (user.total_followers !== undefined && !normalized.followers) {
    normalized.followers = user.total_followers;
  }
  
  // Handle article statistics
  if (user.articles_count !== undefined) {
    normalized.articles_count = user.articles_count;
  }
  
  if (user.total_views !== undefined) {
    normalized.total_views = user.total_views;
  }
  
  return normalized;
};

// Helper function to normalize user arrays
const normalizeUserArray = (users) => {
  if (!Array.isArray(users)) return users;
  return users.map(normalizeUserData);
};

export const userApi = {
  // Get current user info (legacy method)
  getMe: async () => {
    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        throw new Error('No user ID found');
      }
      const response = await apiClient.get(`/users/${userId}`, {
        params: { app_id: APP_ID }
      });
      
      let userData = response.data?.data || response.data;
      
      return normalizeUserData(userData);
    } catch (error) {
      throw error;
    }
  },

  // AI-powered user search
  searchUsersAI: async (params = {}) => {
          try {
        // Use the backend search API instead of the AI search API for better compatibility
        const response = await apiClient.get('/search/authors', { 
        params: {
          q: params.q,
          k: params.limit || 10,
          page_index: (params.page || 1) - 1, // Convert to 0-based for backend
          page_size: params.limit || 10,
          app_id: APP_ID
        }
      });
      
      // Backend search API returns { success: true, data: [...] } format
      if (response.data && response.data.success && response.data.data) {
        const users = normalizeUserArray(response.data.data);
        return { success: true, data: users, results: users };
      }
      
      // Fallback for other response formats
      if (response.data && response.data.results) {
        const users = normalizeUserArray(response.data.results);
        return { success: true, data: users, results: users };
      }
      
      return { success: false, data: [], results: [] };
    } catch (error) {
      console.error('Backend search users error:', error);
      return { success: false, data: [], results: [], error: 'Failed to search users' };
    }
  },

  // Get user profile by ID
  getUser: async (id) => {
    try {
      const response = await apiClient.get(`/users/${id}`, {
        params: { app_id: APP_ID }
      });
      
      // Backend returns { success: true, data: { user_id, full_name, ... } }
      // Frontend expects { id, full_name, ... }
      if (response.data && response.data.success && response.data.data) {
        const userData = normalizeUserData(response.data.data);
        return { success: true, data: userData };
      }
      
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Enhanced version with error handling
  getUserById: async (userId) => {
    try {
      const response = await apiClient.get(`/users/${userId}`, {
        params: { app_id: APP_ID }
      });
      
      let userData = response.data?.data || response.data;
      
      return {
        success: true,
        data: normalizeUserData(userData)
      };
    } catch (error) {
      // Handle specific error cases
      if (error.response?.status === 404) {
        return {
          success: false,
          error: 'user_not_found',
          message: 'User not found'
        };
      } else if (error.response?.status === 410) {
        return {
          success: false,
          error: 'account_deleted',
          message: error.response?.data?.message || 'This account has been deleted'
        };
      }
      
      return {
        success: false,
        error: error.response?.data?.detail || 'User not found'
      };
    }
  },

  // Follow a user
  followUser: async (id) => {
    try {
      const response = await apiClient.post(`/users/${id}/follow`, {});
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Unfollow a user (updated to match API documentation)
  unfollowUser: async (id) => {
    try {
      const response = await apiClient.delete(`/users/${id}/follow`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Check follow status (updated to match API documentation)
  checkFollowStatus: async (id) => {
    try {
      const response = await apiClient.get(`/users/${id}/follow/status`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Add reaction to article (like/dislike/bookmark)
  addReaction: async (articleId, reactionType) => {
    try {
      const response = await apiClient.post(`/users/reactions/${articleId}/${reactionType}`, {}, {
        params: { app_id: APP_ID }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || `Failed to ${reactionType} article`
      };
    }
  },

  // Remove reaction from article
  removeReaction: async (articleId, reactionType) => {
    try {
      const response = await apiClient.delete(`/users/unreactions/${articleId}/${reactionType}`, {
        params: { app_id: APP_ID }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || `Failed to remove ${reactionType}`
      };
    }
  },

  // Check user's reaction status for article
  checkArticleReactionStatus: async (articleId) => {
    try {
      const response = await apiClient.get(`/users/check_article_status/${articleId}`, {
        params: { app_id: APP_ID }
      });
      // backend returns { success: true, data: { reaction_type, is_bookmarked } }
      return {
        success: true,
        data: response.data?.data || response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to check reaction status'
      };
    }
  },

  // Get full bookmarked articles for current user
  getBookmarkedArticles: async () => {
    try {
      const response = await apiClient.get('/users/bookmarks', {
        params: { app_id: APP_ID }
      });
      console.log('Raw bookmarks API response:', response.data);
      
      // Handle different possible response structures
      if (response.data?.success && response.data?.data) {
        // If backend returns { success: true, data: [...articles] }
        return { success: true, data: response.data.data };
      } else if (Array.isArray(response.data)) {
        // If backend returns articles array directly
        return { success: true, data: response.data };
      } else if (response.data?.data && Array.isArray(response.data.data)) {
        // If backend returns { data: [...articles] }
        return { success: true, data: response.data.data };
      } else {
        // Fallback to raw response data
        return { success: true, data: response.data || [] };
      }
    } catch (error) {
      console.error('Bookmarks API error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.response?.data?.message || 'Failed to load bookmarks'
      };
    }
  },

  // Specific reaction methods for convenience
  likeArticle: async (articleId) => {
    return await userApi.addReaction(articleId, 'like');
  },

  unlikeArticle: async (articleId) => {
    return await userApi.removeReaction(articleId, 'like');
  },

  dislikeArticle: async (articleId) => {
    return await userApi.addReaction(articleId, 'dislike');
  },

  undislikeArticle: async (articleId) => {
    return await userApi.removeReaction(articleId, 'dislike');
  },

  bookmarkArticle: async (articleId) => {
    return await userApi.addReaction(articleId, 'bookmark');
  },

  unbookmarkArticle: async (articleId) => {
    return await userApi.removeReaction(articleId, 'bookmark');
  },

  // Get all users
  getAllUsers: async (page = 1, limit = 20, featured = false) => {
    try {
      const response = await apiClient.get('/users', {
        params: { page, limit, featured, app_id: APP_ID }
      });
      
      // Backend returns { success: true, data: [...] }
      if (response.data && response.data.success && response.data.data) {
        const users = normalizeUserArray(response.data.data);
        return { ...response.data, data: users };
      }
      
      return response.data;
    } catch (error) {
      console.error('Get all users error:', error);
      return { success: false, data: [], error: 'Failed to fetch users' };
    }
  },

  // Admin-only: Get all users with full details
  getAllUsersAdmin: async (page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get('/users/admin/all', {
        params: { page, page_size: pageSize, app_id: APP_ID }
      });
      
      // Backend returns { success: true, data: [...], pagination: {...} }
      if (response.data && response.data.success && response.data.data) {
        const users = normalizeUserArray(response.data.data);
        return { 
          success: true,
          data: users,
          pagination: response.data.pagination
        };
      }
      
      return response.data;
    } catch (error) {
      console.error('Get all users admin error:', error);
      return { 
        success: false, 
        data: [], 
        pagination: { page, page_size: pageSize, total: 0, total_results: 0 },
        error: 'Failed to fetch users' 
      };
    }
  },

  // Admin-only: Update user role and status
  updateUser: async (userId, updateData) => {
    try {
      const response = await apiClient.put(`/users/${userId}`, updateData, {
        params: { app_id: APP_ID }
      });
      return response.data;
    } catch (error) {
      console.error('Update user error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Failed to update user' 
      };
    }
  },

  // Admin-only: Delete user (soft delete - sets is_active=false)
  deleteUser: async (userId) => {
    try {
      const response = await apiClient.delete(`/users/${userId}`, {
        params: { app_id: APP_ID }
      });
      return response.data;
    } catch (error) {
      console.error('Delete user error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Failed to delete user' 
      };
    }
  }
};
