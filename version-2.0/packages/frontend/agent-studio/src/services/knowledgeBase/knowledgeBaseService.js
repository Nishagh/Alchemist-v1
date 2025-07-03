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
 * Upload a file to the knowledge base with new workflow support
 */
export const uploadKnowledgeBaseFile = async (agentId, file, autoIndex = false) => {
  try {
    // Create FormData for the file upload
    const formData = new FormData();
    formData.append('agent_id', agentId); // Backend expects agent_id as a form field
    formData.append('file', file);
    formData.append('auto_index', autoIndex); // New parameter for workflow control
    
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
    
    // Return the response data - the backend should return complete file object
    if (response.data && response.data.file) {
      return { success: true, file: response.data.file };
    } else if (response.data && response.data.id) {
      // If no file object, create one with proper data from response and original file
      const newFile = {
        id: response.data.id,
        filename: file.name,
        size: file.size,
        content_type: file.type || 'application/octet-stream',
        agent_id: response.data.agent_id,
        upload_date: new Date().toISOString(),
        indexed: response.data.indexed || false,
        indexing_status: response.data.indexing_status || 'pending',
        indexing_phase: response.data.indexing_phase || null,
        progress_percent: response.data.progress_percent || 0,
        chunk_count: response.data.chunk_count || 0,
        service: "alchemist-knowledge-vault"
      };
      return { success: true, file: newFile };
    } else {
      throw new Error('Invalid response from upload endpoint');
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
 * Search knowledge base content using semantic search
 */
export const searchKnowledgeBase = async (agentId, query) => {
  try {
    console.log(`Searching knowledge base for agent ${agentId} with query: "${query}"`);
    
    // Try semantic search first
    try {
      const searchResults = await getKnowledgeBaseSearchResults(agentId, query, {
        top_k: 10 // Limit results
      });
      
      if (searchResults && searchResults.length > 0) {
        console.log('Using semantic search results:', searchResults.length, 'results');
        return searchResults.map(result => ({
          file_name: result.filename || result.file_name || 'Unnamed File',
          file_id: result.file_id,
          score: result.score || result.similarity_score || 0,
          text: result.content || result.text || `File: ${result.filename || result.file_name || 'Unnamed File'}`,
          indexed: true, // Results from semantic search are indexed
          service: 'alchemist-knowledge-vault'
        }));
      }
    } catch (searchError) {
      console.warn('Semantic search failed, falling back to filename search:', searchError);
    }
    
    // Fallback to filename search if semantic search fails
    const files = await getAgentKnowledgeBase(agentId);
    console.log('Files for fallback search:', files);
    
    if (!files || !Array.isArray(files) || files.length === 0) {
      return [];
    }
    
    // Simple filename search as fallback
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
        score: 0.5, // Lower score for filename-only matches
        text: `File: ${file.filename || file.name || 'Unnamed File'}`,
        indexed: file.indexed,
        service: file.service || 'alchemist-knowledge-vault'
      }));
    
    console.log('Fallback search results:', results);
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

/**
 * Reprocess a file with enhanced cleaning pipeline
 */
export const reprocessKnowledgeBaseFile = async (fileId) => {
  try {
    const response = await kbApi.post(`${ENDPOINTS.KB_FILES}/${fileId}/reprocess`);
    
    console.log('File reprocess response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error reprocessing file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Get detailed processing status for a file
 */
export const getFileProcessingStatus = async (fileId) => {
  try {
    const response = await kbApi.get(`${ENDPOINTS.KB_FILES}/${fileId}/status`);
    
    console.log('File status response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error getting processing status for file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Get processing statistics for all files of an agent
 */
export const getAgentProcessingStats = async (agentId) => {
  try {
    const response = await kbApi.get(`${ENDPOINTS.KNOWLEDGE_BASE}/${agentId}/stats`);
    
    console.log('Agent processing stats response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error getting processing stats for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Get file content preview (original vs processed)
 */
export const getFileContentPreview = async (fileId) => {
  try {
    const response = await kbApi.get(`${ENDPOINTS.KB_FILES}/${fileId}/preview`);
    
    console.log('File content preview response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error getting content preview for file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Batch reprocess multiple files
 */
export const batchReprocessFiles = async (fileIds) => {
  try {
    const response = await kbApi.post(`${ENDPOINTS.KB_FILES}/batch-reprocess`, {
      file_ids: fileIds
    });
    
    console.log('Batch reprocess response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error batch reprocessing files:`, error);
    throw error;
  }
};

/**
 * Get enhanced embedding statistics with quality metrics
 */
export const getEnhancedEmbeddingStats = async (agentId) => {
  try {
    const response = await kbApi.get(`${ENDPOINTS.KNOWLEDGE_BASE}/${agentId}/embeddings/stats`);
    
    console.log('Enhanced embedding stats response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error getting enhanced embedding stats for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Update file content
 */
export const updateFileContent = async (fileId, content) => {
  try {
    const response = await kbApi.put(`${ENDPOINTS.KB_FILES}/${fileId}/content`, {
      content
    });
    
    console.log('File content update response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error updating content for file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Clean and re-index a file with user-controlled content cleaning
 */
export const cleanAndReindexFile = async (fileId, enableCleaning = false) => {
  try {
    const response = await kbApi.post(`${ENDPOINTS.KB_FILES}/${fileId}/clean-and-reindex`, {
      enable_cleaning: enableCleaning
    });
    
    console.log('Clean and reindex response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error cleaning and reindexing file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Batch clean and re-index multiple files with user-controlled content cleaning
 */
export const batchCleanAndReindexFiles = async (fileIds, enableCleaning = false) => {
  try {
    const response = await kbApi.post(`${ENDPOINTS.KB_FILES}/batch-clean-and-reindex`, {
      file_ids: fileIds,
      enable_cleaning: enableCleaning
    });
    
    console.log('Batch clean and reindex response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error batch cleaning and reindexing files:`, error);
    throw error;
  }
};

/**
 * Preview content cleaning for a file without applying changes
 */
export const previewContentCleaning = async (fileId, enableCleaning = false) => {
  try {
    const response = await kbApi.post(`${ENDPOINTS.KB_FILES}/${fileId}/preview-cleaning`, {
      enable_cleaning: enableCleaning
    });
    
    console.log('Preview content cleaning response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error previewing content cleaning for file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Get detailed chunk analysis for a file
 */
export const getFileChunkAnalysis = async (fileId) => {
  try {
    console.log('Requesting chunk analysis for file:', fileId);
    console.log('Using endpoint:', `${ENDPOINTS.KB_FILES}/${fileId}/chunk-analysis`);
    console.log('Base URL:', kbApi.defaults.baseURL);
    
    const response = await kbApi.get(`${ENDPOINTS.KB_FILES}/${fileId}/chunk-analysis`);
    
    console.log('File chunk analysis response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error getting chunk analysis for file ${fileId}:`, error);
    console.error('Error details:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      url: error.config?.url
    });
    throw error;
  }
};

// === NEW WORKFLOW API METHODS ===

/**
 * Assess content quality and relevance for an uploaded file without indexing
 * This provides original vs cleaned content comparison and recommendations
 */
export const assessFileQuality = async (fileId) => {
  try {
    console.log('Assessing quality for file:', fileId);
    
    const response = await kbApi.post(`${ENDPOINTS.KB_FILES}/${fileId}/assess-quality`);
    
    console.log('File quality assessment response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error assessing quality for file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Index a previously uploaded file with user-specified cleaning options
 * This allows users to control whether content cleaning is applied before indexing
 */
export const indexUploadedFile = async (fileId, enableCleaning = false) => {
  try {
    console.log(`Indexing file ${fileId} with cleaning ${enableCleaning ? 'enabled' : 'disabled'}`);
    
    const response = await kbApi.post(`${ENDPOINTS.KB_FILES}/${fileId}/index`, {
      enable_cleaning: enableCleaning
    });
    
    console.log('File indexing response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error indexing file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Get agent-specific relevance analysis for a file
 * Provides comprehensive relevance assessment for the agent's domain and purpose
 */
export const getFileRelevanceAnalysis = async (fileId) => {
  try {
    console.log('Getting relevance analysis for file:', fileId);
    
    const response = await kbApi.get(`${ENDPOINTS.KB_FILES}/${fileId}/relevance-analysis`);
    
    console.log('File relevance analysis response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error getting relevance analysis for file ${fileId}:`, error);
    throw error;
  }
};

/**
 * Check if a file is ready for quality assessment
 * Returns true if file is uploaded but not indexed
 */
export const isFileReadyForAssessment = (file) => {
  return file && 
         file.indexing_status === 'uploaded' && 
         !file.indexed;
};

/**
 * Check if a file is ready for indexing
 * Returns true if file is uploaded but not indexed
 */
export const isFileReadyForIndexing = (file) => {
  return file && 
         file.indexing_status === 'uploaded' && 
         !file.indexed;
};

/**
 * Get the workflow status display for a file
 * Returns user-friendly status message for the new workflow
 */
export const getFileWorkflowStatus = (file) => {
  if (!file) return 'Unknown';
  
  switch (file.indexing_status) {
    case 'uploaded':
      return file.indexed ? 'Indexed' : 'Ready for Quality Assessment';
    case 'processing':
      return 'Indexing in Progress';
    case 'complete':
      return 'Indexed and Ready';
    case 'failed':
      return 'Processing Failed';
    case 'uploading':
      return 'Uploading...';
    default:
      return file.indexing_status || 'Unknown';
  }
};