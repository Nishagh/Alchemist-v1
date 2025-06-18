/**
 * Authentication Service
 * 
 * Handles authentication tokens and request/response interceptors
 */
import { auth } from '../../utils/firebase';
import { api, kbApi, mcpApi } from '../config/apiConfig';

// Track token refresh promises to prevent multiple simultaneous refresh attempts
let refreshTokenPromise = null;

/**
 * Get a fresh authentication token
 */
export const getAuthToken = async () => {
  try {
    // If there's already a refresh in progress, wait for it
    if (refreshTokenPromise) {
      return await refreshTokenPromise;
    }
    
    const currentUser = auth.currentUser;
    if (!currentUser) {
      console.warn('No user is logged in when trying to get auth token');
      return null;
    }
    
    // Create a new promise for this refresh
    refreshTokenPromise = currentUser.getIdToken(true); // Force refresh
    const token = await refreshTokenPromise;
    // Clear the promise after completion
    refreshTokenPromise = null;
    return token;
  } catch (error) {
    console.error('Error getting fresh auth token:', error);
    refreshTokenPromise = null;
    return null;
  }
};

/**
 * Add authentication token to requests
 */
const addAuthInterceptor = (axiosInstance) => {
  axiosInstance.interceptors.request.use(async config => {
    try {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
      
      // Force token refresh to ensure we have a valid token
      const token = await getAuthToken();
      
      if (token) {
        console.log(`Adding auth token to request (truncated): ${token.substring(0, 15)}...`);
        config.headers.Authorization = `Bearer ${token}`;
        
        // Add userId to all requests if the user is logged in
        if (auth.currentUser?.uid) {
          // For GET requests, add as query parameter if not already present
          if (config.method === 'get') {
            config.params = config.params || {};
            // Only add userId if it's not already in the params
            if (!config.params.userId) {
              config.params.userId = auth.currentUser.uid;
              console.log(`Adding userId to query params: ${auth.currentUser.uid}`);
            }
          } 
          // For other methods, add to the request body if it's JSON and userId isn't already present
          else if (config.data && typeof config.data === 'object' && !(config.data instanceof FormData)) {
            if (!config.data.userId) {
              config.data.userId = auth.currentUser.uid;
              console.log(`Adding userId to request body: ${auth.currentUser.uid}`);
            }
          }
          // For FormData, append userId if not already present
          else if (config.data instanceof FormData && !config.data.has('userId')) {
            config.data.append('userId', auth.currentUser.uid);
            console.log(`Adding userId to FormData: ${auth.currentUser.uid}`);
          }
        }
      } else {
        console.warn('No auth token available for request');
      }
    } catch (error) {
      console.error('Error in request interceptor:', error);
    }
    return config;
  }, error => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  });
};

/**
 * Handle response errors
 */
const addResponseInterceptor = (axiosInstance) => {
  axiosInstance.interceptors.response.use(
    response => {
      console.log(`API Response: ${response.status} for ${response.config.method?.toUpperCase()} ${response.config.url}`);
      return response;
    }, 
    async error => {
      console.error('API Error:', error.response?.status, error.config?.url);
      
      // Handle 401 Unauthorized errors
      if (error.response && error.response.status === 401) {
        console.log('Received 401 Unauthorized, checking authentication state');
        
        // If user is logged in but token is invalid, try to refresh token and retry request
        if (auth.currentUser) {
          try {
            console.log('User is logged in, attempting to refresh token and retry request');
            // Force token refresh
            await auth.currentUser.getIdToken(true);
            
            // Retry the original request with fresh token
            const originalRequest = error.config;
            const token = await auth.currentUser.getIdToken();
            originalRequest.headers.Authorization = `Bearer ${token}`;
            
            console.log('Retrying request with fresh token');
            return axiosInstance(originalRequest);
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError);
          }
        } else {
          console.log('User is not logged in, cannot refresh token');
        }
      }
      
      return Promise.reject(error);
    }
  );
};

/**
 * Initialize authentication interceptors for all axios instances
 */
export const initializeAuthInterceptors = () => {
  addAuthInterceptor(api);
  addAuthInterceptor(kbApi);
  addAuthInterceptor(mcpApi);
  
  addResponseInterceptor(api);
  addResponseInterceptor(kbApi);
  addResponseInterceptor(mcpApi);
};

/**
 * Verify token with server
 */
export const verifyTokenWithServer = async (token) => {
  try {
    const response = await api.get('/api/health', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    if (response.status === 200) {
      console.log("Successfully verified token with server");
      return true;
    } else {
      console.warn(`Token verification failed with status: ${response.status}`);
      return false;
    }
  } catch (error) {
    console.error("Error verifying token with server:", error);
    return false;
  }
};

// Initialize interceptors when this module is imported
initializeAuthInterceptors();