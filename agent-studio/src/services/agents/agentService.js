/**
 * Agent Service
 * 
 * Handles all agent-related API operations
 */
import { auth } from '../../utils/firebase';
import { api } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';

/**
 * Create a new agent
 */
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
    
    const response = await api.post(ENDPOINTS.AGENTS, agentData);
    return response.data;
  } catch (error) {
    console.error('Error creating agent:', error);
    throw error;
  }
};

/**
 * Update an existing agent
 */
export const updateAgent = async (agentId, agentData) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    const response = await api.put(`${ENDPOINTS.AGENTS}/${agentId}`, agentData);
    return response.data;
  } catch (error) {
    console.error(`Error updating agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Get an agent by ID
 */
export const getAgent = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Get agent from Firestore directly since it's more reliable
    const { db } = await import('../../utils/firebase');
    const { doc, getDoc } = await import('firebase/firestore');
    
    const agentRef = doc(db, 'alchemist_agents', agentId);
    const agentDoc = await getDoc(agentRef);
    
    if (!agentDoc.exists()) {
      throw new Error('Agent not found');
    }
    
    const agentData = agentDoc.data();
    
    // Check if user owns this agent
    if (agentData.userId !== userId) {
      throw new Error('Access denied: You do not own this agent');
    }
    
    return {
      id: agentDoc.id,
      agent_id: agentDoc.id,
      ...agentData
    };
  } catch (error) {
    console.error(`Error getting agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Delete an agent
 */
export const deleteAgent = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    const response = await api.delete(`${ENDPOINTS.AGENTS}/${agentId}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Execute an action on an agent
 */
export const executeAgentAction = async (agentId, action, payload = {}) => {
  try {
    // Determine which endpoint to use based on agent type
    const endpoint = `${ENDPOINTS.AGENTS}/${agentId}/action`;
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

/**
 * Execute an action on a user agent
 */
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

/**
 * Get available agent types
 * Returns predefined agent types since the backend doesn't provide this endpoint
 */
export const getAgentTypes = () => {
  // Return static agent types since the backend doesn't have this endpoint
  return Promise.resolve([
    { id: 'general', name: 'General Assistant', description: 'A versatile AI assistant' },
    { id: 'code', name: 'Code Assistant', description: 'Specialized in programming tasks' },
    { id: 'research', name: 'Research Assistant', description: 'Focused on research and analysis' },
    { id: 'writing', name: 'Writing Assistant', description: 'Specialized in content creation and editing' },
    { id: 'data', name: 'Data Analyst', description: 'Focused on data analysis and insights' },
    { id: 'customer', name: 'Customer Support', description: 'Designed for customer service interactions' }
  ]);
};

/**
 * Get agent prompt
 */
export const getAgentPrompt = async (agentId) => {
  try {
    const response = await api.get(`${ENDPOINTS.AGENT_PROMPTS}/${agentId}`);
    console.log('API response for agent prompt:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error getting prompt for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Update agent prompt
 */
export const updateAgentPrompt = async (agentId, promptData) => {
  try {
    const response = await api.put(`${ENDPOINTS.AGENT_PROMPTS}/${agentId}`, promptData);
    console.log('API response for updating agent prompt:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error updating prompt for agent ${agentId}:`, error);
    throw error;
  }
};