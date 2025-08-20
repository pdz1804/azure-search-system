// Format date
export const formatDate = (dateString) => {
  if (!dateString) return 'Không có ngày';
  
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Ngày không hợp lệ';
  
  return date.toLocaleDateString('vi-VN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Format số lượng
export const formatNumber = (num) => {
  // Handle null, undefined, or non-numeric values
  if (num === null || num === undefined || isNaN(num)) {
    return '0';
  }
  
  const number = Number(num);
  
  if (number >= 1000000) {
    return (number / 1000000).toFixed(1) + 'M';
  }
  if (number >= 1000) {
    return (number / 1000).toFixed(1) + 'K';
  }
  return number.toString();
};

// Truncate text
export const truncateText = (text, maxLength = 100) => {
  if (!text || typeof text !== 'string') return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// Validate email
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Get error message
export const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.message) {
    return error.message;
  }
  return 'Đã xảy ra lỗi không xác định';
};
