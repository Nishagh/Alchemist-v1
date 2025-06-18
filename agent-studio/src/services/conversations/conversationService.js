/**
 * Conversation Service
 * 
 * Handles conversation-related API operations
 */
import { api } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';

/**
 * Get conversations for an agent
 */
export const getAgentConversations = async (agentId) => {
  try {
    const response = await api.get(`${ENDPOINTS.AGENTS}/${agentId}/conversations`);
    console.log('API response for conversations:', response.data);
    return response.data.conversations || [];
  } catch (error) {
    // Handle 405 Method Not Allowed - this endpoint might not exist or be disabled
    if (error.response?.status === 405) {
      console.warn(`Conversations endpoint not available for agent ${agentId} (405), returning empty conversations`);
      return [];
    }
    console.error(`Error getting conversations for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Get messages for a specific conversation
 */
export const getConversationMessages = async (conversationId) => {
  try {
    const response = await api.get(`${ENDPOINTS.CONVERSATIONS}/${conversationId}/messages`);
    console.log('API response for conversation messages:', response.data);
    return response.data.messages || [];
  } catch (error) {
    console.error(`Error getting messages for conversation ${conversationId}:`, error);
    throw error;
  }
};

/**
 * Create a new conversation
 */
export const createConversation = async (agentId, conversationData) => {
  try {
    const response = await api.post(`${ENDPOINTS.AGENTS}/${agentId}/conversations`, conversationData);
    console.log('API response for creating conversation:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error creating conversation for agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Delete a conversation
 */
export const deleteConversation = async (conversationId) => {
  try {
    const response = await api.delete(`${ENDPOINTS.CONVERSATIONS}/${conversationId}`);
    console.log('API response for deleting conversation:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error deleting conversation ${conversationId}:`, error);
    throw error;
  }
};