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
    const initAuth = async () => {
      const savedToken = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');
      
      if (savedToken && savedUser) {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      }
      
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authApi.login(email, password);
      const { access_token, user_id, role } = response;
      
      // Create user object from response
      const userData = {
        id: user_id,
        role: role,
        email: email, // We know the email from login form
        full_name: `User ${user_id.slice(0, 8)}` // Temporary name, will be updated when fetching user details
      };
      
      setToken(access_token);
      setUser(userData);
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      // Fetch full user details after login
      try {
        const fullUserData = await authApi.getMe();
        setUser(fullUserData);
        localStorage.setItem('user', JSON.stringify(fullUserData));
      } catch (error) {
        console.warn('Could not fetch user details:', error);
      }
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Đăng nhập thất bại' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authApi.register(userData);
      const { access_token, user_id, role } = response;
      
      // Create user object from response  
      const newUserData = {
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
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Đăng ký thất bại' 
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
