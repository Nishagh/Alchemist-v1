/**
 * Agent Editor Helper Functions
 * 
 * Utility functions for the Agent Editor components
 */

/**
 * Format file size to human readable format
 */
export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Convert Firestore timestamp to JavaScript Date
 */
export const convertTimestamp = (timestamp) => {
  if (!timestamp) return null;
  
  // Handle Firestore Timestamp objects
  if (timestamp && typeof timestamp.toDate === 'function') {
    return timestamp.toDate();
  }
  
  // Handle already converted Date objects
  if (timestamp instanceof Date) {
    return timestamp;
  }
  
  // Handle timestamp strings or numbers
  if (typeof timestamp === 'string' || typeof timestamp === 'number') {
    const date = new Date(timestamp);
    return isNaN(date.getTime()) ? null : date;
  }
  
  return null;
};

/**
 * Format date to readable string
 */
export const formatDate = (date) => {
  if (!date) return 'Unknown';
  
  const convertedDate = convertTimestamp(date);
  if (!convertedDate) return 'Unknown';
  
  try {
    return convertedDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid Date';
  }
};

/**
 * Get relative time string (e.g., "2 hours ago")
 */
export const getRelativeTime = (date) => {
  if (!date) return 'Unknown';
  
  const convertedDate = convertTimestamp(date);
  if (!convertedDate) return 'Unknown';
  
  try {
    const now = new Date();
    const diffInSeconds = Math.floor((now - convertedDate) / 1000);
    
    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 2592000) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 31536000) {
      const months = Math.floor(diffInSeconds / 2592000);
      return `${months} month${months > 1 ? 's' : ''} ago`;
    } else {
      const years = Math.floor(diffInSeconds / 31536000);
      return `${years} year${years > 1 ? 's' : ''} ago`;
    }
  } catch (error) {
    console.error('Error calculating relative time:', error);
    return 'Unknown';
  }
};

/**
 * Validate file type for uploads
 */
export const isValidFileType = (file, allowedTypes = []) => {
  if (!file || !allowedTypes.length) return true;
  
  const extension = file.name.split('.').pop()?.toLowerCase();
  return allowedTypes.includes(extension);
};

/**
 * Truncate text to specified length
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * Generate unique ID for components
 */
export const generateId = () => {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
};

/**
 * Debounce function for search inputs
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Validate agent configuration
 */
export const validateAgentConfig = (agent) => {
  const errors = [];
  
  if (!agent.name || agent.name.trim().length === 0) {
    errors.push('Agent name is required');
  }
  
  if (agent.name && agent.name.length > 100) {
    errors.push('Agent name must be less than 100 characters');
  }
  
  if (agent.description && agent.description.length > 500) {
    errors.push('Agent description must be less than 500 characters');
  }
  
  if (!agent.type) {
    errors.push('Agent type is required');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Format deployment status for display
 */
export const formatDeploymentStatus = (status) => {
  if (!status) return 'Unknown';
  
  const statusMap = {
    'pending': 'Pending',
    'deploying': 'Deploying',
    'deployed': 'Deployed',
    'failed': 'Failed',
    'stopped': 'Stopped',
    'error': 'Error'
  };
  
  return statusMap[status.toLowerCase()] || status;
};

/**
 * Extract error message from API error
 */
export const extractErrorMessage = (error) => {
  if (typeof error === 'string') return error;
  
  if (error?.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error?.response?.data?.detail) {
    if (Array.isArray(error.response.data.detail)) {
      return error.response.data.detail.map(d => d.msg || d.message || d).join(', ');
    }
    return error.response.data.detail;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

/**
 * Scroll to element smoothly
 */
export const scrollToElement = (elementId, behavior = 'smooth') => {
  const element = document.getElementById(elementId);
  if (element) {
    element.scrollIntoView({ behavior, block: 'start' });
  }
};

/**
 * Copy text to clipboard
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    
    // Fallback for older browsers
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    } catch (fallbackError) {
      console.error('Fallback copy failed:', fallbackError);
      return false;
    }
  }
};