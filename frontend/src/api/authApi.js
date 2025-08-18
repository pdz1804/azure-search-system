import apiClient from './config';

export const authApi = {
  // Đăng nhập
  login: async (email, password) => {
    const response = await apiClient.post('/auth/login', {
      email,
      password
    });
    return response.data;
  },

  // Đăng ký
  register: async (userData) => {
    const formData = new FormData();
    formData.append('full_name', userData.full_name);
    formData.append('email', userData.email);
    formData.append('password', userData.password);
    if (userData.avatar) {
      formData.append('avatar', userData.avatar);
    }
    
    const response = await apiClient.post('/auth/register', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Lấy thông tin user hiện tại
  getMe: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },
};
