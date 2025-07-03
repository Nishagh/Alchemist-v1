/**
 * Alchemist Service
 * 
 * Handles direct interactions with the Alchemist agent
 */
import { auth } from '../../utils/firebase';
import { api } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';

/**
 * Interact directly with the Alchemist agent
 */
export const interactWithAlchemist = async (message, agentId = null) => {
  try {
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    const payload = {
      message,
      agent_id: agentId,
      user_id: userId
    };
    
    const response = await api.post(`${ENDPOINTS.ALCHEMIST}/interact`, payload);
    console.log('API response for Alchemist interaction:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error interacting with Alchemist agent:', error);
    throw error;
  }
};

/**
 * Get Alchemist conversation history
 */
export const getAlchemistConversations = async (agentId = null) => {
  try {
    const params = agentId ? { agent_id: agentId } : {};
    const response = await api.get(`${ENDPOINTS.ALCHEMIST}/conversations`, { params });
    console.log('API response for Alchemist conversations:', response.data);
    return response.data.conversations || [];
  } catch (error) {
    console.error('Error getting Alchemist conversations:', error);
    throw error;
  }
};

/**
 * Clear Alchemist conversation history
 */
export const clearAlchemistConversation = async (agentId = null) => {
  try {
    const payload = agentId ? { agent_id: agentId } : {};
    const response = await api.delete(`${ENDPOINTS.ALCHEMIST}/conversations`, { data: payload });
    console.log('API response for clearing Alchemist conversation:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error clearing Alchemist conversation:', error);
    throw error;
  }
};