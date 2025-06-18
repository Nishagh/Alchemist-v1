/**
 * API Service
 * 
 * Handles all communication with the backend API
 */
import axios from 'axios';
import { auth } from '../utils/firebase';

// Configure the base URL for the API
// In production, this would be your deployed backend URL
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
const KNOWLEDGE_BASE_URL = process.env.REACT_APP_KNOWLEDGE_BASE_URL;
const MCP_MANAGER_URL = process.env.REACT_APP_MCP_MANAGER_URL;
// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

const kb_api = axios.create({
  baseURL: KNOWLEDGE_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Track token refresh promises to prevent multiple simultaneous refresh attempts
let refreshTokenPromise = null;

// Function to get a fresh token
const getAuthToken = async () => {
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

// Add authentication token to requests
api.interceptors.request.use(async config => {
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

// Handle response errors
api.interceptors.response.use(
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
          return axios(originalRequest);
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

// This function creates an agent with the current user as the owner
export const createAgent = async (agentData) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Add current user id as owner if not already set
    if (!agentData.owner_id) {
      agentData.owner_id = userId;
    }
    
    const response = await api.post('/api/agents', agentData);
    return response.data;
  } catch (error) {
    console.error('Error creating agent:', error);
    throw error;
  }
};

export const updateAgent = async (agentId, agentData) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    const response = await api.put(`/api/agents/${agentId}`, agentData);
    return response.data;
  } catch (error) {
    console.error(`Error updating agent ${agentId}:`, error);
    throw error;
  }
};

export const deleteAgent = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    const response = await api.delete(`/api/agents/${agentId}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting agent ${agentId}:`, error);
    throw error;
  }
};

// Agent action API functions
export const executeAgentAction = async (agentId, action, payload = {}) => {
  try {
    // Determine which endpoint to use based on agent type
    const endpoint = `/api/agents/${agentId}/action`;
    const response = await api.post(endpoint, {
      agent_id: agentId,
      action,
      payload
    });
    return response.data;
  } catch (error) {
    console.error(`Error executing action on agent ${agentId}:`, error);
    throw error;
  }
};

// User agent action API function
export const executeUserAgentAction = async (agentId, action, payload = {}) => {
  try {
    const response = await api.post(`/api/user-agents/${agentId}/action`, {
      agent_id: agentId,
      action,
      payload
    });
    return response.data;
  } catch (error) {
    console.error(`Error executing action on user agent ${agentId}:`, error);
    throw error;
  }
};

// Conversation API functions
export const getAgentConversations = async (agentId) => {
  try {
    const response = await api.get(`/api/agents/${agentId}/conversations`);
    console.log('API response for conversations:', response.data);
    return response.data.conversations || [];
  } catch (error) {
    console.error(`Error getting conversations for agent ${agentId}:`, error);
    throw error;
  }
};

// Knowledge Base API Functions
export const getAgentKnowledgeBase = async (agentId) => {
  try {
    // Use the dedicated knowledge base files endpoint
    const response = await kb_api.get(`/api/knowledge-base/${agentId}/files`);
    console.log('Knowledge base files response:', response.data);
    
    // Check if we have files in the response
    if (!response.data || !response.data.files || !Array.isArray(response.data.files)) {
      console.log('No files found in response');
      return [];
    }
    
    // The API should return parsed objects, but handle strings just in case
    return response.data.files.map(file => {
      if (typeof file === 'string') {
        try {
          return JSON.parse(file);
        } catch (e) {
          console.error('Error parsing file JSON:', e);
          return { id: 'error', filename: file, error: true };
        }
      }
      return file;
    });
  } catch (error) {
    console.error(`Error getting knowledge base for agent ${agentId}:`, error);
    throw error;
  }
};

export const uploadKnowledgeBaseFile = async (agentId, file) => {
  try {
    // Create FormData for the file upload
    const formData = new FormData();
    formData.append('agent_id', agentId); // Backend expects agent_id as a form field
    formData.append('file', file);
    
    // Use the correct knowledge base upload endpoint
    const response = await kb_api.post(
      `/api/upload-knowledge-base`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    
    console.log('File upload response:', response.data);
    
    // Return the response data or construct a file object if response doesn't include one
    if (response.data && response.data.file) {
      return { success: true, file: response.data.file };
    } else {
      // If the API doesn't return the file object, create one with the information we have
      const newFile = {
        id: response.data?.id || Date.now().toString(),
        filename: file.name,
        service: "knowledge-base-service",
        indexed: true
      };
      return { success: true, file: newFile };
    }
  } catch (error) {
    console.error(`Error uploading file to knowledge base for agent ${agentId}:`, error);
    throw error;
  }
};

export const deleteKnowledgeBaseFile = async (agentId, fileId) => {
  try {
    // Use the correct endpoint path with URL parameters for agent_id and file_id
    const response = await kb_api.delete(`/api/knowledge-base/files/${fileId}`);
    
    console.log('File delete response:', response.data);
    
    return { success: true, ...response.data };
  } catch (error) {
    console.error(`Error deleting file from knowledge base for agent ${agentId}:`, error);
    throw error;
  }
};

export const searchKnowledgeBase = async (agentId, query) => {
  try {
    // Get files from knowledge base (already parsed from JSON strings in getAgentKnowledgeBase)
    const files = await getAgentKnowledgeBase(agentId);
    console.log('Files for search:', files);
    
    if (!files || !Array.isArray(files) || files.length === 0) {
      return [];
    }
    
    // Simple filename search
    const normalizedQuery = query.toLowerCase();
    const results = files
      .filter(file => {
        if (!file) return false;
        const filename = file.filename || file.name || '';
        return filename.toLowerCase().includes(normalizedQuery);
      })
      .map(file => ({
        file_name: file.filename || file.name || 'Unnamed File',
        file_id: file.id,
        score: 1.0, // Mock score
        text: `File: ${file.filename || file.name || 'Unnamed File'}`, // No content access yet
        indexed: file.indexed,
        service: file.service || 'Unknown'
      }));
    
    console.log('Search results:', results);
    return results;
  } catch (error) {
    console.error(`Error searching knowledge base for agent ${agentId}:`, error);
    throw error;
  }
};

// Note: Each agent has only one conversation with messages included directly in the response
// from getAgentConversations

// Artifact API functions
export const getAgentArtifacts = async (agentId) => {
  try {
    const response = await api.get(`/api/agents/${agentId}/artifacts`);
    return response.data.artifacts;
  } catch (error) {
    console.error(`Error getting artifacts for agent ${agentId}:`, error);
    throw error;
  }
};

// Agent types API function
export const getAgentTypes = async () => {
  try {
    const response = await api.get('/api/agent-types');
    return response.data.agent_types;
  } catch (error) {
    console.error('Error getting agent types:', error);
    throw error;
  }
};

// Alchemist direct interaction API function
export const interactWithAlchemist = async (message, agentId = null) => {
  try {
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    const payload = {
      message,
      agent_id: agentId,
      user_id: userId
    };
    
    const response = await api.post('/api/alchemist/interact', payload);
    return response.data;
  } catch (error) {
    console.error('Error interacting with Alchemist agent:', error);
    throw error;
  }
};

/**
 * Upload an OpenAPI specification or MCP config for an agent
 * @param {string} agentId - The ID of the agent
 * @param {File} file - The OpenAPI specification or MCP config file (YAML)
 * @returns {Promise<Object>} - The response data
 */
export const uploadApiSpecification = async (agentId, file) => {
  try {
    // Get current user ID and auth token
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    // Create form data with all required fields
    const formData = new FormData();
    
    // Validate that we have a valid file
    if (!file || !(file instanceof File)) {
      throw new Error('Invalid file provided');
    }
    
    // Add required form fields matching backend API definition
    formData.append('file', file);
    formData.append('userId', userId);
    
    console.log(`Uploading config file for agent ${agentId} with userId ${userId}`);
    console.log('File details:', { name: file.name, size: file.size, type: file.type });
    
    // Log all form data fields to debug
    const formEntries = [...formData.entries()];
    console.log('Form data fields:', formEntries.map(entry => `${entry[0]}: ${entry[1] instanceof File ? entry[1].name : entry[1]}`));
    
    // Use axios directly with proper authentication
    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/api/agents/${agentId}/config`,
      data: formData,
      headers: {
        'Authorization': `Bearer ${token}`
        // Don't set Content-Type manually for FormData, let axios set it with boundary
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error uploading config file:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
      
      // More detailed logging for 422 errors
      if (error.response.status === 422 && error.response.data.detail) {
        const details = error.response.data.detail || [];
        details.forEach(detail => {
          if (detail.loc && Array.isArray(detail.loc)) {
            console.error(`Field ${detail.loc.join('.')} error: ${detail.msg}`);
          } else {
            console.error('Validation error:', detail);
          }
        });
      }
    }
    throw error;
  }
};

/**
 * Get API integrations for an agent
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Array>} - Array of API integrations
 */
export const getApiIntegrations = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Fetching API integrations for agent ${agentId}, userId: ${userId}`);
    
    // Use axios directly instead of the api instance to avoid interceptor issues
    // Match exactly the API endpoint specification: GET /api/agents/{agent_id}/api-integrations with userId header
    const response = await axios({
      method: 'get',
      url: `${API_BASE_URL}/api/agents/${agentId}/api-integrations-files`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId  // Include userId as a header as specified
      },
      // Add timeout to prevent long loading times if server is having issues
      timeout: 10000
    });
    
    console.log('API integrations response:', response.data);
    
    // The API returns { status: "success", api_integrations: [...] }
    if (response.data && response.data.api_integrations && Array.isArray(response.data.api_integrations)) {
      return response.data.api_integrations;
    }
    
    // If the response data is an array, return it directly
    if (Array.isArray(response.data)) {
      return response.data;
    }
    
    // If the response has a data property that's an array, return that
    if (response.data && Array.isArray(response.data.integrations)) {
      return response.data.integrations;
    }
    
    // If the response has a data property but no specific array property, check all properties
    if (response.data && typeof response.data === 'object') {
      // Look for the first array property in the response
      for (const key in response.data) {
        if (Array.isArray(response.data[key])) {
          console.log(`Found array in response.data.${key}`);
          return response.data[key];
        }
      }
    }
    
    // If we couldn't find an array, log the full response and return an empty array
    console.warn('Could not find array of integrations in response:', response.data);
    return [];
  } catch (error) {
    console.error('Error fetching API integrations:', error);
    
    // Check for OpenAPI validation error in the response
    if (
      error.response?.data?.detail?.includes?.('OpenAPIValidationError') ||
      error.response?.data?.message?.includes?.('openapi_spec_validator') ||
      error.message?.includes?.('OpenAPIValidationError')
    ) {
      console.error('OpenAPI validation error detected in the server response');
      
      // Rethrow with more descriptive error message
      const err = new Error('Server error with OpenAPI validator. This is a backend issue.');
      err.response = error.response;
      err.isOpenApiValidationError = true;
      throw err;
    }
    
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Delete an API integration
 * @param {string} agentId - The ID of the agent
 * @param {string} integrationId - The ID of the API integration to delete
 * @returns {Promise<Object>} - The response data
 */
export const deleteApiIntegration = async (agentId, integrationId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Deleting API integration ${integrationId} for agent ${agentId}`);
    
    // Use axios directly instead of the api instance to avoid interceptor issues
    const response = await axios({
      method: 'delete',
      url: `${API_BASE_URL}/api/agents/${agentId}/api-integrations/${integrationId}`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId  // Include userId as a header as specified
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error deleting API integration:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Get API specification content
 * @param {string} agentId - The ID of the agent
 * @param {string} apiId - The ID of the API integration
 * @returns {Promise<Object>} - The API specification content
 */
export const getApiSpecification = async (agentId, apiId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Fetching API specification content for agent ${agentId}, API ${apiId}`);
    
    // Use the specified endpoint: GET /api/agents/{agent_id}/api-integrations/{api_id}/spec
    const response = await axios({
      method: 'get',
      url: `${API_BASE_URL}/api/agents/${agentId}/api-integrations/${apiId}/spec`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId  // Include userId as a header as specified
      }
    });
    
    console.log('API specification content response received');
    return response.data;
  } catch (error) {
    console.error('Error fetching API specification content:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Download API specification file
 * @param {string} agentId - The ID of the agent
 * @param {string} apiId - The ID of the API integration
 * @returns {Promise<string>} - The URL to download the file
 */
export const downloadApiSpecification = async (agentId, apiId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Generating download URL for API spec: agent ${agentId}, API ${apiId}`);
    
    // Use the specified endpoint: GET /api/agents/{agent_id}/api-integrations/{api_id}/download
    // Note: We return the full URL since this endpoint redirects to the file or serves it directly
    return `${API_BASE_URL}/api/agents/${agentId}/api-integrations/${apiId}/download?token=${encodeURIComponent(token)}&userId=${encodeURIComponent(userId)}`;
  } catch (error) {
    console.error('Error generating API spec download URL:', error);
    throw error;
  }
};

/**
 * Get testable endpoints for an API integration
 * @param {string} agentId - The ID of the agent
 * @param {string} apiId - The ID of the API integration
 * @returns {Promise<Array>} - Array of testable endpoints
 */
export const getTestableEndpoints = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Fetching testable endpoints for agent ${agentId}`);
    
    // Use the specified endpoint: GET /api/agents/{agent_id}/api-integrations/{api_id}/testable-endpoints
    const response = await axios({
      method: 'get',
      url: `${API_BASE_URL}/api/agents/${agentId}/testable-endpoints`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId  // Include userId as a header as specified
      }
    });
    
    console.log('Testable endpoints response:', response.data);
    
    // Return the endpoints from the response
    if (response.data && response.data.endpoints) {
      return response.data.endpoints;
    } else if (Array.isArray(response.data)) {
      return response.data;
    }
    
    // If we can't find a clear array of endpoints, look for any array in the response
    if (response.data && typeof response.data === 'object') {
      for (const key in response.data) {
        if (Array.isArray(response.data[key])) {
          console.log(`Found array in response.data.${key}`);
          return response.data[key];
        }
      }
    }
    
    // If no endpoints found, return empty array
    console.warn('No testable endpoints found in response:', response.data);
    return [];
  } catch (error) {
    console.error('Error fetching testable endpoints:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

// Test an API endpoint
export const testApiEndpoint = async (agentId, endpointId, queryParams = {}, pathParams = {}, headerParams = {}) => {
  try {
    // Get the Firebase ID token for authentication
    // Force token refresh to ensure we have a valid token
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }

    const response = await axios({
      method: 'post',
      url: `${API_BASE_URL}/api/agents/${agentId}/api-integrations/${endpointId}/test`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId  // Include userId as a header as specified
      },
      data: {
        query_params: queryParams,
        path_params: pathParams,
        header_params: headerParams
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error testing API endpoint:', error);
    throw error;
  }
};

/**
 * Get API integration files for an agent
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Array>} - Array of API integration files
 */
export const getApiIntegrationFiles = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Fetching API integration files for agent ${agentId}`);
    
    // Use the specified endpoint: GET /api/agents/{agent_id}/api-integration-files
    const response = await axios({
      method: 'get',
      url: `${API_BASE_URL}/api/agents/${agentId}/api-integrations-files`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'userId': userId  // Pass userId as header instead of query parameter
      }
    });
    
    console.log('API integration files response:', response.data);
    
    // Handle different response formats
    if (response.data && response.data.api_integrations && Array.isArray(response.data.api_integrations)) {
      return response.data.api_integrations;
    }
    
    // If the response data is an array, return it directly
    if (Array.isArray(response.data)) {
      return response.data;
    }
    
    // If the response has a files property that's an array, return that
    if (response.data && response.data.files && Array.isArray(response.data.files)) {
      return response.data.files;
    }
    
    // If we couldn't find an array, log the full response and return an empty array
    console.warn('Could not find array of API integration files in response:', response.data);
    return [];
  } catch (error) {
    console.error('Error fetching API integration files:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Deploy MCP server for an agent
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Object>} - The response data
 */
export const deployMcpServer = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Deploying MCP server for agent ${agentId}`);
    
    // Use axios directly to deploy MCP server
    const response = await axios({
      method: 'post',
      url: `${MCP_MANAGER_URL}/deploy`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'userId': userId
      },
      data: {
        agent_id: agentId
      }
    });
    
    console.log('MCP deployment response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error deploying MCP server:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Check deployment status using MCP manager
 * @param {string} agentId - The ID of the agent
 * @param {string} deploymentId - The ID of the deployment
 * @returns {Promise<Object>} - The deployment status
 */
export const checkDeploymentStatus = async (agentId, deploymentId) => {
  try {
    const url = `${MCP_MANAGER_URL}/deployments/${agentId}/${deploymentId}`;
    console.log('Checking deployment status URL:', url);
    
    const response = await axios({
      method: 'get',
      url: url,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 10000 // 10 second timeout
    });
    
    console.log('Deployment status response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error checking deployment status:', error);
    console.error('Error details:', {
      message: error.message,
      url: `${MCP_MANAGER_URL}/deployments/${agentId}/${deploymentId}`,
      agentId,
      deploymentId
    });
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Get deployment logs using MCP manager
 * @param {string} agentId - The ID of the agent
 * @param {string} deploymentId - The ID of the deployment
 * @returns {Promise<Object>} - The deployment logs
 */
export const getDeploymentLogs = async (agentId, deploymentId) => {
  try {
    const url = `${MCP_MANAGER_URL}/deployments/${agentId}/${deploymentId}/logs`;
    console.log('Getting deployment logs URL:', url);
    
    const response = await axios({
      method: 'get',
      url: url,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 15000 // 15 second timeout
    });
    
    console.log('Deployment logs response received');
    return response.data;
  } catch (error) {
    console.error('Error getting deployment logs:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Delete MCP server using MCP manager
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Object>} - The deletion result
 */
export const deleteMcpServer = async (agentId) => {
  try {
    // Get current user ID and auth token
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Deleting MCP server for agent ${agentId}`);
    
    const response = await axios({
      method: 'delete',
      url: `${MCP_MANAGER_URL}/servers/${agentId}`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'userId': userId
      },
      timeout: 30000 // 30 second timeout for deletion
    });
    
    console.log('MCP server deletion response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error deleting MCP server:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Check server status using MCP manager
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Object>} - The server status
 */
export const checkServerStatus = async (agentId) => {
  try {
    const url = `${MCP_MANAGER_URL}/servers/${agentId}`;
    console.log('Checking server status URL:', url);
    
    const response = await axios({
      method: 'get',
      url: url,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 10000 // 10 second timeout
    });
    
    console.log('Server status response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error checking server status:', error);
    console.error('Error details:', {
      message: error.message,
      url: `${MCP_MANAGER_URL}/servers/${agentId}`,
      agentId
    });
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Get integration summary from MCP Manager
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Object>} - The integration summary
 */
export const getIntegrationSummary = async (agentId) => {
  try {
    // Get current user ID and auth token
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Fetching integration summary for agent ${agentId}`);
    
    const response = await axios({
      method: 'get',
      url: `${MCP_MANAGER_URL}/agents/${agentId}/integration-summary`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'userId': userId
      },
      timeout: 15000 // 15 second timeout
    });
    
    console.log('Integration summary response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching integration summary:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Get live tools data from deployed MCP server
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Array>} - Array of available tools
 */
export const getLiveTools = async (agentId) => {
  try {
    // Get current user ID and auth token
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Fetching live tools for agent ${agentId}`);
    
    const response = await axios({
      method: 'get',
      url: `${MCP_MANAGER_URL}/agents/${agentId}/tools`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'userId': userId
      },
      timeout: 15000 // 15 second timeout
    });
    
    console.log('Live tools response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching live tools:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Test a specific tool from the deployed MCP server
 * @param {string} agentId - The ID of the agent
 * @param {string} toolName - The name of the tool to test
 * @param {Object} testParams - Parameters for testing the tool
 * @returns {Promise<Object>} - Test result
 */
export const testTool = async (agentId, toolName, testParams = {}) => {
  try {
    // Get current user ID and auth token
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Force token refresh to ensure we have a valid token
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication token is missing or invalid');
    }
    
    console.log(`Testing tool ${toolName} for agent ${agentId} with params:`, testParams);
    
    const response = await axios({
      method: 'post',
      url: `${MCP_MANAGER_URL}/agents/${agentId}/tools/${toolName}/test`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'userId': userId
      },
      data: testParams,
      timeout: 30000 // 30 second timeout for tool testing
    });
    
    console.log('Tool test response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error testing tool:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Get agent prompt
 * @param {string} agentId - The ID of the agent
 * @returns {Promise<Object>} - The agent prompt
 */
export const getAgentPrompt = async (agentId) => {
  try {
    const response = await api.get(`/api/agents/${agentId}/prompt`);
    return response.data;
  } catch (error) {
    console.error(`Error getting agent prompt for ${agentId}:`, error);
    throw error;
  }
};

/**
 * Update agent prompt
 * @param {string} agentId - The ID of the agent
 * @param {string} prompt - The new prompt
 * @returns {Promise<Object>} - The response data
 */
export const updateAgentPrompt = async (agentId, prompt) => {
  try {
    const response = await api.put(`/api/agents/${agentId}/prompt`, { prompt });
    return response.data;
  } catch (error) {
    console.error(`Error updating agent prompt for ${agentId}:`, error);
    throw error;
  }
};