import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/authApi';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  useEffect(() => {
    let mounted = true;
    
    const initAuth = async () => {
      const savedToken = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');
      
      if (savedToken && mounted) {
        setToken(savedToken);
        if (savedUser) {
          try {
            setUser(JSON.parse(savedUser));
          } catch {
            // ignore JSON parse errors and refetch
          }
        }

        // If user is still not available, fetch it from API using stored user_id
        if (!savedUser && mounted) {
          try {
            const me = await authApi.getCurrentUser();
            // authApi.getCurrentUser returns { success: true, data: user }
            if (me.success && me.data) {
              setUser(me.data);
              localStorage.setItem('user', JSON.stringify(me.data));
            }
          } catch {
            // silent
          }
        }
      }
      
      if (mounted) {
        setLoading(false);
      }
    };

    initAuth();
    
    return () => {
      mounted = false;
    };
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authApi.login(email, password);
      console.log('Login API Response:', response);
      
      if (!response.success) {
        return { 
          success: false, 
          error: response.error || 'Login failed' 
        };
      }
      
      const { access_token, user_id, role, user: userData } = response.data;
      
      // normalize user object
      const userInfo = userData || {
        id: user_id,
        role: role,
        email: email,
        full_name: `User ${user_id?.slice ? user_id.slice(0, 8) : user_id}`
      };

      setToken(access_token);
      setUser(userInfo);

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userInfo));
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.message || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authApi.register(userData);
      console.log('Register API Response:', response);
      
      if (!response.success) {
        return { 
          success: false, 
          error: response.error || 'Registration failed' 
        };
      }
      
      const { access_token, user_id, role, user: userInfo } = response.data;
      
      // Create user object from response  
      const newUserData = userInfo || {
        id: user_id,
        role: role,
        email: userData.email,
        full_name: userData.full_name
      };
      
      setToken(access_token);
      setUser(newUserData);
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(newUserData));
      
      return { success: true };
    } catch (error) {
      console.error('Register error:', error);
      return { 
        success: false, 
        error: error.message || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  };

  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const refreshUser = async () => {
    try {
      const response = await authApi.getCurrentUser();
      if (response.success && response.data) {
        setUser(response.data);
        localStorage.setItem('user', JSON.stringify(response.data));
        return response.data;
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
    return null;
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const hasRole = (role) => {
    return user?.role === role;
  };

  const canEditArticle = (article) => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    return article.author_id === user.id;
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateUser,
    refreshUser,
    isAuthenticated,
    hasRole,
    canEditArticle,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
