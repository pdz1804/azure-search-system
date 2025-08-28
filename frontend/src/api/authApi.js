import { apiClient, apiClientFormData, createFormData, setAuthToken, removeAuthToken } from './config';
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
  
  return normalized;
};

export const authApi = {
  // Login with email and password
  login: async (email, password) => {
    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password
      });
      
      const { access_token, user_id, role } = response.data;
      
      // Store authentication data
      setAuthToken(access_token);
      localStorage.setItem('user_id', user_id);
      localStorage.setItem('role', role);
      
      // Fetch full user profile
      const userResponse = await apiClient.get(`/users/${user_id}`, {
        params: { app_id: APP_ID }
      });
      let userObj = userResponse.data?.data || userResponse.data;
      
      // Normalize user data
      userObj = normalizeUserData(userObj);
      
      // persist normalized user object
      localStorage.setItem('user', JSON.stringify(userObj));
      
      return {
        success: true,
        data: {
          access_token,
          user_id,
          role,
          // return the normalized user object (not the wrapper)
          user: userObj
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      };
    }
  },

  // Register new user with optional avatar
  register: async (userData) => {
    try {
      const formData = createFormData(userData);
      
      // Add app_id to the registration data
      formData.set('app_id', APP_ID);
      
      // Ensure avatar file is properly attached if it exists
      if (userData.avatar) {
        const avatarFile = userData.avatar.originFileObj ? userData.avatar.originFileObj : userData.avatar;
        formData.set('avatar', avatarFile); // use set to replace any existing avatar entry
      }
      
      const response = await apiClientFormData.post('/auth/register', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const { access_token, user_id, role } = response.data;
      
      // Store authentication data
      setAuthToken(access_token);
      localStorage.setItem('user_id', user_id);
      localStorage.setItem('role', role);
      
      // Fetch full user profile
      const userResponse = await apiClient.get(`/users/${user_id}`, {
        params: { app_id: APP_ID }
      });
      let userObj = userResponse.data?.data || userResponse.data;
      
      // Normalize user data
      userObj = normalizeUserData(userObj);
      
      localStorage.setItem('user', JSON.stringify(userObj));
      
      return {
        success: true,
        data: {
          access_token,
          user_id,
          role,
          user: userObj
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      };
    }
  },

  // Logout user
  logout: async () => {
    try {
      removeAuthToken();
      return { success: true };
    } catch (error) {
      return { success: false, error: 'Logout failed' };
    }
  },

  // Verify token validity
  verifyToken: async () => {
    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        throw new Error('No user ID found');
      }
      
      const response = await apiClient.get(`/users/${userId}`, {
        params: { app_id: APP_ID }
      });
      let userObj = response.data?.data || response.data;
      
      // Normalize user data
      userObj = normalizeUserData(userObj);
      
      localStorage.setItem('user', JSON.stringify(userObj));
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      removeAuthToken();
      return {
        success: false,
        error: 'Token verification failed'
      };
    }
  },

  // Get current user profile (legacy method for backward compatibility)
  getMe: async () => {
    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        throw new Error('No user ID found');
      }
      
      const response = await apiClient.get(`/users/${userId}`, {
        params: { app_id: APP_ID }
      });
      let userObj = response.data?.data || response.data;
      
      return normalizeUserData(userObj);
    } catch (error) {
      throw error;
    }
  },

  // Get current user profile
  getCurrentUser: async () => {
    try {
      // Prefer stored user_id; if missing, try to read from stored user
      let userId = localStorage.getItem('user_id');
      if (!userId) {
        const user = localStorage.getItem('user');
        if (user) {
          try { userId = JSON.parse(user)?.id; } catch {}
        }
      }
      if (!userId) throw new Error('No user ID found');

      const response = await apiClient.get(`/users/${userId}`, {
        params: { app_id: APP_ID }
      });
      let userObj = response.data?.data || response.data;
      
      return {
        success: true,
        data: normalizeUserData(userObj)
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch user profile'
      };
    }
  }
};
