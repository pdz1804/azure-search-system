import apiClient from './config';

export const userApi = {
  // Lấy thông tin user hiện tại
  getMe: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  // Lấy thông tin user
  getUser: async (id) => {
    const response = await apiClient.get(`/users/${id}`);
    return response.data;
  },

  // Follow user
  followUser: async (id) => {
    const response = await apiClient.post(`/users/${id}/follow`);
    return response.data;
  },

  // Unfollow user
  unfollowUser: async (id) => {
    const response = await apiClient.post(`/users/${id}/unfollow`);
    return response.data;
  },

  // Kiểm tra follow status
  checkFollowStatus: async (id) => {
    const response = await apiClient.get(`/users/${id}/is_following`);
    return response.data;
  },
};
