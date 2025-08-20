import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Tạo axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Tạo axios instance riêng cho file upload
const apiClientFormData = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for file uploads
});

// Interceptor để thêm token vào header
const addAuthInterceptor = (client) => {
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );
};

// Interceptor để xử lý response và errors
const addResponseInterceptor = (client) => {
  client.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      const { response } = error;
      
      if (response?.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('user_id');
        localStorage.removeItem('role');
        toast.error('Session expired. Please login again.');
        window.location.href = '/login';
      } else if (response?.status === 403) {
        toast.error('You do not have permission to perform this action.');
      } else if (response?.status === 404) {
        toast.error('Resource not found.');
      } else if (response?.status >= 500) {
        toast.error('Server error. Please try again later.');
      } else if (response?.data?.detail) {
        toast.error(response.data.detail);
      } else if (error.code === 'ECONNABORTED') {
        toast.error('Request timeout. Please try again.');
      } else if (!navigator.onLine) {
        toast.error('No internet connection.');
      } else {
        toast.error('An unexpected error occurred.');
      }
      
      return Promise.reject(error);
    }
  );
};

// Apply interceptors
addAuthInterceptor(apiClient);
addAuthInterceptor(apiClientFormData);
addResponseInterceptor(apiClient);
addResponseInterceptor(apiClientFormData);

// Utility functions
export const getAuthToken = () => localStorage.getItem('access_token');
export const setAuthToken = (token) => localStorage.setItem('access_token', token);
export const removeAuthToken = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  localStorage.removeItem('user_id');
  localStorage.removeItem('role');
};

export const isAuthenticated = () => {
  const token = getAuthToken();
  return !!token;
};

export const getCurrentUser = () => {
  try {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  } catch {
    return null;
  }
};

export const getCurrentRole = () => {
  return localStorage.getItem('role') || 'user';
};

export const getUserId = () => {
  return localStorage.getItem('user_id');
};

// Helper function to create FormData for file uploads
export const createFormData = (data) => {
  const formData = new FormData();
  
  Object.keys(data).forEach(key => {
    const value = data[key];
    if (value !== null && value !== undefined) {
      if (value instanceof File) {
        formData.append(key, value);
      } else if (Array.isArray(value)) {
        formData.append(key, value.join(','));
      } else {
        formData.append(key, value.toString());
      }
    }
  });
  
  return formData;
};

// API response wrapper
export const apiResponse = {
  success: (data, message = 'Success') => ({ data, message, success: true }),
  error: (error, message = 'Error occurred') => ({ 
    error, 
    message: error?.response?.data?.detail || message, 
    success: false 
  })
};

export { apiClient, apiClientFormData };
export default apiClient;
