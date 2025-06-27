import axios from 'axios';
import { auth } from './firebase';

// Create an axios instance with a base URL
const api = axios.create({
  baseURL: process.env.REACT_APP_AGENT_ENGINE_URL || window.location.origin,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add authentication interceptor to add the token to each request
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  
  if (user) {
    try {
      const token = await user.getIdToken();
      config.headers.Authorization = `Bearer ${token}`;
    } catch (error) {
      console.error('Error getting auth token:', error);
    }
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

// API functions
export const getUserProfile = async () => {
  try {
    const response = await api.get('/api/user/profile');
    return response.data;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
};

export const healthCheck = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

// Google Sign-In token exchange
export const exchangeGoogleToken = async (idToken) => {
  try {
    const response = await api.post('/api/auth/google-signin', { idToken });
    return response.data;
  } catch (error) {
    console.error('Google token exchange failed:', error);
    throw error;
  }
};

export default api; 