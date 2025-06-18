/**
 * Knowledge Base Service
 * 
 * Handles knowledge base-related API operations
 */
import { kbApi } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';

/**
 * Get knowledge base files for an agent
 */
export const getAgentKnowledgeBase = async (agentId) => {
  try {
    // Use the dedicated knowledge base files endpoint
    const response = await kbApi.get(`${ENDPOINTS.KNOWLEDGE_BASE}/${agentId}/files`);
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

/**
 * Upload a file to the knowledge base
 */
export const uploadKnowledgeBaseFile = async (agentId, file) => {
  try {
    // Create FormData for the file upload
    const formData = new FormData();
    formData.append('agent_id', agentId); // Backend expects agent_id as a form field
    formData.append('file', file);
    
    // Use the correct knowledge base upload endpoint
    const response = await kbApi.post(
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

/**
 * Delete a file from the knowledge base
 */
export const deleteKnowledgeBaseFile = async (agentId, fileId) => {
  try {
    // Use the correct endpoint path with URL parameters for agent_id and file_id
    const response = await kbApi.delete(`${ENDPOINTS.KB_FILES}/${fileId}`);
    
    console.log('File delete response:', response.data);
    
    return { success: true, ...response.data };
  } catch (error) {
    console.error(`Error deleting file from knowledge base for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Search knowledge base content
 */
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

/**
 * Get knowledge base search results (dedicated endpoint)
 */
export const getKnowledgeBaseSearchResults = async (agentId, query, options = {}) => {
  try {
    const response = await kbApi.post(`${ENDPOINTS.KB_SEARCH}/${agentId}`, {
      query,
      ...options
    });
    
    console.log('Knowledge base search response:', response.data);
    return response.data.results || [];
  } catch (error) {
    console.error(`Error performing knowledge base search for agent ${agentId}:`, error);
    throw error;
  }
};