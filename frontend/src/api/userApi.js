import { apiClient } from './config';

export const userApi = {
  // Get current user info (legacy method)
  getMe: async () => {
    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        throw new Error('No user ID found');
      }
      const response = await apiClient.get(`/users/${userId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Get user profile by ID
  getUser: async (id) => {
    try {
      const response = await apiClient.get(`/users/${id}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Enhanced version with error handling
  getUserById: async (userId) => {
    try {
      const response = await apiClient.get(`/users/${userId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'User not found'
      };
    }
  },

  // Follow a user
  followUser: async (id) => {
    try {
      const response = await apiClient.post(`/users/${id}/follow`);
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
      const response = await apiClient.post(`/users/reactions/${articleId}/${reactionType}`);
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
      const response = await apiClient.delete(`/users/unreactions/${articleId}/${reactionType}`);
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
      const response = await apiClient.get(`/users/check_article_status/${articleId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to check reaction status'
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
  }
};
