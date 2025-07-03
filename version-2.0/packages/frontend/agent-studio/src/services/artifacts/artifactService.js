/**
 * Artifact Service
 * 
 * Handles artifact-related API operations
 */
import { api } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';

/**
 * Get artifacts for an agent
 */
export const getAgentArtifacts = async (agentId) => {
  try {
    const response = await api.get(`${ENDPOINTS.AGENTS}/${agentId}/artifacts`);
    console.log('API response for agent artifacts:', response.data);
    return response.data.artifacts || [];
  } catch (error) {
    console.error(`Error getting artifacts for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Create a new artifact
 */
export const createArtifact = async (agentId, artifactData) => {
  try {
    const response = await api.post(`${ENDPOINTS.AGENTS}/${agentId}/artifacts`, artifactData);
    console.log('API response for creating artifact:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error creating artifact for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Update an artifact
 */
export const updateArtifact = async (agentId, artifactId, artifactData) => {
  try {
    const response = await api.put(`${ENDPOINTS.ARTIFACTS}/${artifactId}`, artifactData);
    console.log('API response for updating artifact:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error updating artifact ${artifactId}:`, error);
    throw error;
  }
};

/**
 * Delete an artifact
 */
export const deleteArtifact = async (artifactId) => {
  try {
    const response = await api.delete(`${ENDPOINTS.ARTIFACTS}/${artifactId}`);
    console.log('API response for deleting artifact:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error deleting artifact ${artifactId}:`, error);
    throw error;
  }
};