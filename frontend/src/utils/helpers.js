// Format date
export const formatDate = (dateString) => {
  if (!dateString) return 'No date';

  // Try native parsing first
  let date = new Date(dateString);

  // Some backend timestamps use 'YYYY-MM-DD HH:mm:ss' which is not universally parseable.
  // Try a few fallbacks before giving up.
  if (isNaN(date.getTime())) {
    // Replace space between date and time with 'T'
    const tForm = dateString.replace(' ', 'T');
    date = new Date(tForm);
  }

  if (isNaN(date.getTime())) {
    // Try Date.parse (some environments handle more formats)
    const parsed = Date.parse(dateString);
    if (!isNaN(parsed)) {
      date = new Date(parsed);
    }
  }

  if (isNaN(date.getTime())) return 'Invalid date';

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Format number
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
  return 'An unknown error occurred';
};
