import { apiClient, apiClientFormData, createFormData, setAuthToken, removeAuthToken } from './config';

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
      const userResponse = await apiClient.get(`/users/${user_id}`);
      const userObj = userResponse.data?.data || userResponse.data;
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
      const userResponse = await apiClient.get(`/users/${user_id}`);
      const userObj = userResponse.data?.data || userResponse.data;
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
      
      const response = await apiClient.get(`/users/${userId}`);
      localStorage.setItem('user', JSON.stringify(response.data?.data || response.data));
      
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
      
      const response = await apiClient.get(`/users/${userId}`);
      return response.data;
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

      const response = await apiClient.get(`/users/${userId}`);
      return {
        success: true,
        data: response.data?.data || response.data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch user profile'
      };
    }
  }
};
