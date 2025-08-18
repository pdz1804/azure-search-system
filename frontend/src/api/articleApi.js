import apiClient from './config';

export const articleApi = {
  // Lấy danh sách bài viết
  getArticles: async (params = {}) => {
    // Handle both old and new parameter formats
    if (typeof params === 'number') {
      // Old format: getArticles(page, pageSize, search)
      const page = arguments[0] || 1;
      const pageSize = arguments[1] || 20;
      const search = arguments[2] || '';
      params = { page, page_size: pageSize };
      if (search) params.q = search;
    } else {
      // New format: getArticles({ page, page_size, q, status, tags, sort_by })
      params = {
        page: params.page || 1,
        page_size: params.page_size || 20,
        ...params
      };
    }
    
    // Remove undefined values
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key];
      }
    });
    
    const response = await apiClient.get('/articles', { params });
    return response.data;
  },

  // Lấy chi tiết bài viết
  getArticle: async (id) => {
    const response = await apiClient.get(`/articles/${id}`);
    return response.data;
  },

  // Tạo bài viết mới
  createArticle: async (articleData) => {
    const formData = new FormData();
    formData.append('title', articleData.title);
    formData.append('abstract', articleData.abstract);
    formData.append('content', articleData.content);
    if (articleData.tags) {
      formData.append('tags', articleData.tags.join(','));
    }
    if (articleData.image) {
      formData.append('image', articleData.image);
    }
    
    const response = await apiClient.post('/articles', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Cập nhật bài viết
  updateArticle: async (id, articleData) => {
    const formData = new FormData();
    if (articleData.title) formData.append('title', articleData.title);
    if (articleData.abstract) formData.append('abstract', articleData.abstract);
    if (articleData.content) formData.append('content', articleData.content);
    if (articleData.tags) formData.append('tags', articleData.tags.join(','));
    if (articleData.status) formData.append('status', articleData.status);
    if (articleData.image) formData.append('image', articleData.image);
    
    const response = await apiClient.put(`/articles/${id}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Xóa bài viết
  deleteArticle: async (id) => {
    const response = await apiClient.delete(`/articles/${id}`);
    return response.data;
  },

  // Tăng lượt xem
  viewArticle: async (id) => {
    const response = await apiClient.get(`/articles/view/${id}`);
    return response.data;
  },

  // Like bài viết
  likeArticle: async (id) => {
    const response = await apiClient.post(`/articles/${id}/like`);
    return response.data;
  },

  // Dislike bài viết
  dislikeArticle: async (id) => {
    const response = await apiClient.post(`/articles/${id}/dislike`);
    return response.data;
  },

  // Lấy bài viết của tác giả
  getArticlesByAuthor: async (authorId, page = 1, pageSize = 20) => {
    const response = await apiClient.get(`/articles/author/${authorId}`, {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  // Thống kê
  getSummary: async () => {
    const response = await apiClient.get('/articles/summary');
    return response.data;
  },
};
