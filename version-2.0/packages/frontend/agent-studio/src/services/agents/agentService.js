/**
 * Agent Service
 * 
 * Handles all agent-related API operations
 */
import { auth, Collections, DocumentFields, ErrorMessages } from '../../utils/firebase';
import { api } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';
import identityService from '../identity/identityService';

/**
 * Create a new agent
 */
export const createAgent = async (agentData) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error(ErrorMessages.USER_NOT_AUTHENTICATED);
    }
    
    // Add current user id as owner if not already set
    if (!agentData[DocumentFields.Agent.OWNER_ID]) {
      agentData[DocumentFields.Agent.OWNER_ID] = userId;
    }
    
    const response = await api.post(ENDPOINTS.AGENTS, agentData);
    const createdAgent = response.data;
    
    // Trigger GNF tracking when agent is given a name
    if (agentData.name && agentData.name.trim()) {
      try {
        const agentId = createdAgent.id || createdAgent.agent_id;
        if (agentId) {
          console.log('Creating GNF identity for agent:', agentId, 'with name:', agentData.name);
          
          // Create initial identity data for GNF
          const identityData = {
            agent_id: agentId,
            name: agentData.name.trim(),
            personality: {
              traits: ['helpful', 'responsive', 'curious'],
              values: ['assistance', 'accuracy', 'learning'],
              goals: ['help users', 'provide accurate information', 'learn from interactions']
            },
            capabilities: {
              skills: ['conversation', 'problem-solving'],
              knowledge_domains: ['general']
            },
            background: {
              origin: 'alchemist-platform',
              creation_date: new Date().toISOString(),
              created_by: userId
            }
          };
          
          // Create GNF identity - this will start tracking the agent (non-blocking)
          identityService.createAgentIdentity(agentId, identityData)
            .then(() => {
              console.log('GNF identity created successfully for agent:', agentId);
            })
            .catch((gnfError) => {
              console.warn('Failed to create GNF identity for agent:', gnfError.message);
            });
        }
      } catch (gnfError) {
        // Log GNF error but don't fail agent creation
        console.warn('Failed to create GNF identity for agent:', gnfError.message);
      }
    }
    
    return createdAgent;
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
    const updatedAgent = response.data;
    
    // If agent is being given a name for the first time, create GNF identity
    if (agentData.name && agentData.name.trim()) {
      try {
        // Check if GNF identity already exists
        const existingIdentity = await identityService.getAgentIdentity(agentId);
        
        // Only create identity if it doesn't exist or is a default identity
        if (!existingIdentity || existingIdentity.is_default) {
          console.log('Creating/updating GNF identity for agent:', agentId, 'with name:', agentData.name);
          
          const identityData = {
            agent_id: agentId,
            name: agentData.name.trim(),
            personality: {
              traits: ['helpful', 'responsive', 'curious'],
              values: ['assistance', 'accuracy', 'learning'],
              goals: ['help users', 'provide accurate information', 'learn from interactions']
            },
            capabilities: {
              skills: ['conversation', 'problem-solving'],
              knowledge_domains: ['general']
            },
            background: {
              origin: 'alchemist-platform',
              creation_date: new Date().toISOString(),
              created_by: userId
            }
          };
          
          if (existingIdentity && existingIdentity.is_default) {
            // Update existing default identity (non-blocking)
            identityService.updateAgentIdentity(agentId, identityData)
              .then(() => {
                console.log('GNF identity updated successfully for agent:', agentId);
              })
              .catch((gnfError) => {
                console.warn('Failed to update GNF identity for agent:', gnfError.message);
              });
          } else {
            // Create new identity (non-blocking)
            identityService.createAgentIdentity(agentId, identityData)
              .then(() => {
                console.log('GNF identity created successfully for agent:', agentId);
              })
              .catch((gnfError) => {
                console.warn('Failed to create GNF identity for agent:', gnfError.message);
              });
          }
        }
      } catch (gnfError) {
        // Log GNF error but don't fail agent update
        console.warn('Failed to create/update GNF identity for agent:', gnfError.message);
      }
    }
    
    return updatedAgent;
  } catch (error) {
    console.error(`Error updating agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Get all agents for the current user (excluding deleted ones)
 */
export const getActiveAgents = async () => {
  try {
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error(ErrorMessages.USER_NOT_AUTHENTICATED);
    }
    
    const { db } = await import('../../utils/firebase');
    const { collection, query, where, getDocs, orderBy } = await import('firebase/firestore');
    
    const agentsRef = collection(db, Collections.AGENTS);
    const agentsQuery = query(
      agentsRef,
      where(DocumentFields.Agent.OWNER_ID, '==', userId),
      where('status', '!=', 'deleted'),
      orderBy('status'),
      orderBy('created_at', 'desc')
    );
    
    const snapshot = await getDocs(agentsQuery);
    const agents = [];
    
    snapshot.forEach((doc) => {
      const agentData = doc.data();
      agents.push({
        [DocumentFields.ID]: doc.id,
        [DocumentFields.AGENT_ID]: doc.id,
        ...agentData
      });
    });
    
    return agents;
  } catch (error) {
    console.error('Error getting active agents:', error);
    throw error;
  }
};

/**
 * Get deleted agents for the current user (archives)
 */
export const getDeletedAgents = async () => {
  try {
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error(ErrorMessages.USER_NOT_AUTHENTICATED);
    }
    
    const { db } = await import('../../utils/firebase');
    const { collection, query, where, getDocs, orderBy } = await import('firebase/firestore');
    
    const agentsRef = collection(db, Collections.AGENTS);
    const agentsQuery = query(
      agentsRef,
      where(DocumentFields.Agent.OWNER_ID, '==', userId),
      where('status', '==', 'deleted'),
      orderBy('deleted_at', 'desc')
    );
    
    const snapshot = await getDocs(agentsQuery);
    const deletedAgents = [];
    
    snapshot.forEach((doc) => {
      const agentData = doc.data();
      deletedAgents.push({
        [DocumentFields.ID]: doc.id,
        [DocumentFields.AGENT_ID]: doc.id,
        ...agentData
      });
    });
    
    return deletedAgents;
  } catch (error) {
    console.error('Error getting deleted agents:', error);
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
      throw new Error(ErrorMessages.USER_NOT_AUTHENTICATED);
    }
    
    // Get agent from Firestore directly since it's more reliable
    const { db } = await import('../../utils/firebase');
    const { doc, getDoc } = await import('firebase/firestore');
    
    const agentRef = doc(db, Collections.AGENTS, agentId);
    const agentDoc = await getDoc(agentRef);
    
    if (!agentDoc.exists()) {
      throw new Error(ErrorMessages.AGENT_NOT_FOUND);
    }
    
    const agentData = agentDoc.data();
    
    // Check if user owns this agent (check both owner_id and legacy userId field)
    const ownerId = agentData[DocumentFields.Agent.OWNER_ID] || agentData.userId;
    if (ownerId !== userId) {
      throw new Error(ErrorMessages.AGENT_ACCESS_DENIED);
    }
    
    return {
      [DocumentFields.ID]: agentDoc.id,
      [DocumentFields.AGENT_ID]: agentDoc.id,
      ...agentData
    };
  } catch (error) {
    console.error(`Error getting agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Mark an agent as deleted (soft delete)
 */
export const markAgentAsDeleted = async (agentId) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    // Get agent data first to verify ownership
    const agent = await getAgent(agentId);
    if (!agent) {
      throw new Error('Agent not found');
    }
    
    // Update agent status to 'deleted' and add deletion timestamp
    const deletionData = {
      status: 'deleted',
      deleted_at: new Date().toISOString(),
      deleted_by: userId
    };
    
    // Update via API
    const response = await api.put(`${ENDPOINTS.AGENTS}/${agentId}`, deletionData);
    
    // Also update Firestore directly to ensure consistency
    const { db } = await import('../../utils/firebase');
    const { doc, updateDoc } = await import('firebase/firestore');
    
    const agentRef = doc(db, Collections.AGENTS, agentId);
    await updateDoc(agentRef, deletionData);
    
    // Create lifecycle event for agent deletion
    await createAgentDeletionEvent(agentId, userId, agent.name);
    
    return response.data;
  } catch (error) {
    console.error(`Error marking agent ${agentId} as deleted:`, error);
    throw error;
  }
};

/**
 * Create a lifecycle event for agent deletion
 * 
 * STANDARDIZED: This follows the exact format used by the backend AgentLifecycleService
 * to ensure consistency across all lifecycle event recording.
 */
const createAgentDeletionEvent = async (agentId, userId, agentName) => {
  try {
    const { db } = await import('../../utils/firebase');
    const { collection, addDoc, serverTimestamp } = await import('firebase/firestore');
    
    // Follow exact AgentLifecycleService format for consistency
    const eventData = {
      agent_id: agentId,
      event_type: 'agent_deleted',
      title: 'Agent Deleted',
      description: `Agent "${agentName}" has been marked as deleted and removed from active use`,
      user_id: userId,
      timestamp: serverTimestamp(), // Use server timestamp for consistency
      metadata: {
        agent_name: agentName,
        deleted_by: userId,
        deletion_reason: 'user_initiated',
        final_status: 'deleted',
        deletion_method: 'frontend_service'
      },
      priority: 'high' // Matches AgentLifecycleService.record_agent_deleted priority
    };
    
    const eventsRef = collection(db, 'agent_lifecycle_events');
    const docRef = await addDoc(eventsRef, eventData);
    
    // Update document with its own ID (matching backend pattern)
    const { updateDoc, doc } = await import('firebase/firestore');
    await updateDoc(doc(db, 'agent_lifecycle_events', docRef.id), {
      event_id: docRef.id
    });
    
    console.log('Agent deletion lifecycle event created:', agentId, 'Event ID:', docRef.id);
    
    // TODO: Consider migrating to use backend lifecycle API endpoint for better consistency
    // This would eliminate direct Firebase access from frontend
    
  } catch (error) {
    console.error('Error creating agent deletion lifecycle event:', error);
    // Log additional context for debugging
    console.error('Event data that failed:', {
      agent_id: agentId,
      user_id: userId,
      agent_name: agentName
    });
    // Don't throw error here as it's not critical for the deletion process
  }
};

/**
 * Delete an agent (hard delete - use with caution)
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