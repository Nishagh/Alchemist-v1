/**
 * API Integration Service
 * 
 * Handles API integration-related operations including OpenAPI specifications,
 * API testing, and endpoint management
 */
import axios from 'axios';
import { auth } from '../../utils/firebase';
import { getAuthToken } from '../auth/authService';
import { AGENT_ENGINE_URL, TOOL_FORGE_URL, ENDPOINTS } from '../config/apiConfig';

/**
 * Upload an OpenAPI specification or MCP config for an agent
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
    
    // Use axios directly with proper authentication (now calling tool-forge)
    const response = await axios({
      method: 'post',
      url: `${TOOL_FORGE_URL}/api/agents/${agentId}/config`,
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
    const response = await axios({
      method: 'get',
      url: `${AGENT_ENGINE_URL}/api/agents/${agentId}/api-integrations-files`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId
      },
      timeout: 10000
    });
    
    console.log('API integrations response:', response.data);
    
    // Handle different response formats
    if (response.data && response.data.api_integrations && Array.isArray(response.data.api_integrations)) {
      return response.data.api_integrations;
    }
    
    if (Array.isArray(response.data)) {
      return response.data;
    }
    
    if (response.data && Array.isArray(response.data.integrations)) {
      return response.data.integrations;
    }
    
    // Look for the first array property in the response
    if (response.data && typeof response.data === 'object') {
      for (const key in response.data) {
        if (Array.isArray(response.data[key])) {
          console.log(`Found array in response.data.${key}`);
          return response.data[key];
        }
      }
    }
    
    console.warn('Could not find array of integrations in response:', response.data);
    return [];
  } catch (error) {
    console.error('Error fetching API integrations:', error);
    
    // Handle 405 Method Not Allowed - this endpoint might not exist
    if (error.response?.status === 405) {
      console.warn(`API integrations endpoint not available for agent ${agentId} (405), returning empty integrations`);
      return [];
    }
    
    // Check for OpenAPI validation error in the response
    if (
      error.response?.data?.detail?.includes?.('OpenAPIValidationError') ||
      error.response?.data?.message?.includes?.('openapi_spec_validator') ||
      error.message?.includes?.('OpenAPIValidationError')
    ) {
      console.error('OpenAPI validation error detected in the server response');
      
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
    
    const response = await axios({
      method: 'delete',
      url: `${AGENT_ENGINE_URL}/api/agents/${agentId}/api-integrations/${integrationId}`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId
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
    
    const response = await axios({
      method: 'get',
      url: `${AGENT_ENGINE_URL}/api/agents/${agentId}/api-integrations/${apiId}/spec`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId
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
    
    // Return the full URL since this endpoint redirects to the file or serves it directly
    return `${AGENT_ENGINE_URL}/api/agents/${agentId}/api-integrations/${apiId}/download?token=${encodeURIComponent(token)}&userId=${encodeURIComponent(userId)}`;
  } catch (error) {
    console.error('Error generating API spec download URL:', error);
    throw error;
  }
};

/**
 * Get testable endpoints for an API integration
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
    
    const response = await axios({
      method: 'get',
      url: `${AGENT_ENGINE_URL}/api/agents/${agentId}/testable-endpoints`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId
      }
    });
    
    console.log('Testable endpoints response:', response.data);
    
    // Return the endpoints from the response
    if (response.data && response.data.endpoints) {
      return response.data.endpoints;
    } else if (Array.isArray(response.data)) {
      return response.data;
    }
    
    // Look for any array in the response
    if (response.data && typeof response.data === 'object') {
      for (const key in response.data) {
        if (Array.isArray(response.data[key])) {
          console.log(`Found array in response.data.${key}`);
          return response.data[key];
        }
      }
    }
    
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

/**
 * Test an API endpoint
 */
export const testApiEndpoint = async (agentId, endpointId, queryParams = {}, pathParams = {}, headerParams = {}) => {
  try {
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
      url: `${AGENT_ENGINE_URL}/api/agents/${agentId}/api-integrations/${endpointId}/test`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'userId': userId
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
    
    const response = await axios({
      method: 'get',
      url: `${AGENT_ENGINE_URL}/api/agents/${agentId}/api-integrations-files`,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'userId': userId
      }
    });
    
    console.log('API integration files response:', response.data);
    
    // Handle different response formats
    if (response.data && response.data.api_integrations && Array.isArray(response.data.api_integrations)) {
      return response.data.api_integrations;
    }
    
    if (Array.isArray(response.data)) {
      return response.data;
    }
    
    if (response.data && response.data.files && Array.isArray(response.data.files)) {
      return response.data.files;
    }
    
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