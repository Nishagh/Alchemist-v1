/**
 * Conversation Service
 * 
 * Handles conversation-related API operations including billing tracking for deployed agents
 */
import { api } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';
import { 
  collection, 
  doc, 
  addDoc, 
  updateDoc, 
  getDoc, 
  getDocs, 
  query, 
  where, 
  orderBy, 
  limit,
  onSnapshot,
  serverTimestamp,
  increment
} from 'firebase/firestore';
import { db, Collections, DocumentFields, StatusValues } from '../../utils/firebase';

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

// ============================================================================
// PRE-DEPLOYMENT TESTING (FREE - NO BILLING)
// ============================================================================

/**
 * Save pre-deployment test conversation (for development testing)
 */
export const saveTestConversation = async ({ agentId, conversationId, message, response, timestamp }) => {
  try {
    // Save to unified conversations collection (pre-deployment testing)
    const conversationRef = collection(db, Collections.CONVERSATIONS);
    
    await addDoc(conversationRef, {
      [DocumentFields.Conversation.CONVERSATION_ID]: conversationId,
      [DocumentFields.AGENT_ID]: agentId,
      [DocumentFields.Conversation.MESSAGE_CONTENT]: message,
      [DocumentFields.Conversation.AGENT_RESPONSE]: response,
      [DocumentFields.TIMESTAMP]: timestamp || serverTimestamp(),
      [DocumentFields.CREATED_AT]: serverTimestamp(),
      [DocumentFields.Conversation.IS_PRODUCTION]: false,
      [DocumentFields.Conversation.DEPLOYMENT_TYPE]: 'pre_deployment',
      [DocumentFields.Conversation.COST_USD]: 0, // always free for pre-deployment testing
      [DocumentFields.Conversation.TOKENS]: { 
        [DocumentFields.Conversation.PROMPT_TOKENS]: 0, 
        [DocumentFields.Conversation.COMPLETION_TOKENS]: 0, 
        [DocumentFields.Conversation.TOTAL_TOKENS]: 0 
      }
    });

  } catch (error) {
    console.error('Error saving test conversation:', error);
    // Don't throw error - pre-deployment testing should continue even if logging fails
  }
};

/**
 * Get pre-deployment test conversation history
 */
export const getTestConversationHistory = async (agentId, options = {}) => {
  try {
    const {
      limit: limitCount = 50
    } = options;

    const q = query(
      collection(db, Collections.CONVERSATIONS),
      where(DocumentFields.AGENT_ID, '==', agentId),
      where(DocumentFields.Conversation.IS_PRODUCTION, '==', false),
      orderBy(DocumentFields.CREATED_AT, 'desc'),
      limit(limitCount)
    );

    const snapshot = await getDocs(q);
    const conversations = [];

    snapshot.forEach((doc) => {
      const data = doc.data();
      conversations.push({
        [DocumentFields.ID]: doc.id,
        ...data,
        [DocumentFields.TIMESTAMP]: data[DocumentFields.CREATED_AT]?.toDate?.()?.toISOString() || data[DocumentFields.TIMESTAMP]
      });
    });

    return conversations;
  } catch (error) {
    console.error('Error getting test conversation history:', error);
    return [];
  }
};

// ============================================================================
// DEPLOYED AGENT TESTING WITH BILLING TRACKING
// ============================================================================

/**
 * Create a new conversation with a deployed agent
 */
export const createDeployedAgentConversation = async (agentId, userId = 'test-user') => {
  try {
    const agentEndpoint = await getAgentEndpoint(agentId);
    
    const response = await fetch(`${agentEndpoint}/api/conversation/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        user_id: userId
      })
    });

    if (!response.ok) {
      // Try to extract detailed error message from response
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = `${errorData.detail} (HTTP ${response.status})`;
        } else if (errorData.message) {
          errorMessage = `${errorData.message} (HTTP ${response.status})`;
        }
      } catch (parseError) {
        // If we can't parse the error response, use the status text
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data.conversation_id;
  } catch (error) {
    console.error('Error creating conversation with deployed agent:', error);
    throw new Error(error.message || 'Failed to create conversation');
  }
};

// Non-streaming API removed - deployed agents now use streaming only

/**
 * Send a streaming message to a deployed agent
 */
export const sendStreamingMessageToDeployedAgent = async ({ 
  agentId, 
  conversationId, 
  message, 
  testMode = 'production', 
  onChunk, 
  onComplete 
}) => {
  try {
    const agentEndpoint = await getAgentEndpoint(agentId);
    
    const response = await fetch(`${agentEndpoint}/api/conversation/message/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message,
        user_id: 'test-user'
      })
    });

    if (!response.ok) {
      // Try to extract detailed error message from response
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = `${errorData.detail} (HTTP ${response.status})`;
        } else if (errorData.message) {
          errorMessage = `${errorData.message} (HTTP ${response.status})`;
        }
      } catch (parseError) {
        // If we can't parse the error response, use the status text
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';
    let tokens = { prompt: 0, completion: 0, total: 0 };
    let cost = 0;

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          
          if (data === '[DONE]') {
            // Streaming complete
            if (testMode === 'production') {
              await saveBillableMessage({
                agentId,
                conversationId,
                message,
                response: fullResponse,
                tokens,
                cost,
                timestamp: serverTimestamp(),
                testMode
              });
            }
            
            if (onComplete) {
              onComplete(tokens, cost);
            }
            return;
          }

          try {
            const parsed = JSON.parse(data);
            
            if (parsed.type === 'content') {
              fullResponse += parsed.content;
              if (onChunk) {
                onChunk(parsed.content);
              }
            } else if (parsed.type === 'tokens') {
              tokens = parsed.tokens;
              cost = calculateCost(tokens);
            }
          } catch (parseError) {
            // Handle non-JSON chunks
            if (data && data !== '') {
              fullResponse += data;
              if (onChunk) {
                onChunk(data);
              }
            }
          }
        }
      }
    }

  } catch (error) {
    console.error('Error in streaming message:', error);
    throw new Error('Failed to send streaming message');
  }
};

/**
 * Get the endpoint URL for a deployed agent
 */
const getAgentEndpoint = async (agentId) => {
  try {
    // Get deployment info from Firestore - find the latest completed deployment for this agent
    const deploymentsRef = collection(db, 'agent_deployments');
    
    // Query for completed deployments
    const qCompleted = query(
      deploymentsRef, 
      where('agent_id', '==', agentId),
      where('status', '==', 'completed'),
      orderBy('created_at', 'desc'),
      limit(1)
    );
    
    // Query for deployed deployments
    const qDeployed = query(
      deploymentsRef, 
      where('agent_id', '==', agentId),
      where('status', '==', 'deployed'),
      orderBy('created_at', 'desc'),
      limit(1)
    );
    
    const [completedSnapshot, deployedSnapshot] = await Promise.all([
      getDocs(qCompleted),
      getDocs(qDeployed)
    ]);
    
    // Get the most recent deployment from either completed or deployed
    const allDeployments = [];
    if (!completedSnapshot.empty) {
      allDeployments.push({
        ...completedSnapshot.docs[0].data(),
        id: completedSnapshot.docs[0].id
      });
    }
    if (!deployedSnapshot.empty) {
      allDeployments.push({
        ...deployedSnapshot.docs[0].data(),
        id: deployedSnapshot.docs[0].id
      });
    }
    
    if (allDeployments.length === 0) {
      throw new Error('No completed deployment found for agent');
    }
    
    // Sort by created_at and get the most recent
    allDeployments.sort((a, b) => {
      const aTime = a.created_at?.toDate?.() || new Date(a.created_at);
      const bTime = b.created_at?.toDate?.() || new Date(b.created_at);
      return bTime - aTime;
    });
    
    const deployment = allDeployments[0];
    if (!deployment.service_url) {
      throw new Error('Agent deployment does not have a service URL');
    }
    
    return deployment.service_url;
  } catch (error) {
    console.error('Error getting agent endpoint:', error);
    // Fallback to universal agent endpoint
    return process.env.REACT_APP_UNIVERSAL_AGENT_URL || 'https://universal-agent-service-url';
  }
};

/**
 * Save conversation message interaction to Firestore
 */
const saveBillableMessage = async ({ agentId, conversationId, message, response, tokens, cost, timestamp, testMode = 'production' }) => {
  try {
    // Save to conversations collection (main collection for deployed agents)
    const conversationRef = collection(db, 'conversations');
    
    await addDoc(conversationRef, {
      agentId,
      conversationId,
      userMessage: message,
      agentResponse: response,
      tokens: {
        prompt: tokens?.prompt_tokens || tokens?.prompt || 0,
        completion: tokens?.completion_tokens || tokens?.completion || 0,
        total: tokens?.total_tokens || tokens?.total || 0
      },
      cost: cost || 0,
      timestamp: timestamp || serverTimestamp(),
      createdAt: serverTimestamp(),
      isProduction: testMode === 'production', // true for production mode, false for development mode
      deploymentType: 'deployed' // to distinguish from pre-deployment testing
    });

    // Update agent billing summary
    await updateAgentBillingSummary(agentId, {
      messages: 1,
      tokens: tokens?.total_tokens || tokens?.total || 0,
      cost: cost || 0
    });

  } catch (error) {
    console.error('Error saving billable message:', error);
    // Don't throw error here as it shouldn't block the conversation
  }
};

/**
 * Update agent billing summary
 */
const updateAgentBillingSummary = async (agentId, usage) => {
  try {
    const summaryRef = doc(db, 'agent_billing_summary', agentId);
    const summaryDoc = await getDoc(summaryRef);

    if (summaryDoc.exists()) {
      await updateDoc(summaryRef, {
        totalMessages: increment(usage.messages),
        totalTokens: increment(usage.tokens),
        totalCost: increment(usage.cost),
        lastActivity: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
    } else {
      await updateDoc(summaryRef, {
        agentId,
        totalMessages: usage.messages,
        totalTokens: usage.tokens,
        totalCost: usage.cost,
        lastActivity: serverTimestamp(),
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
    }
  } catch (error) {
    console.error('Error updating billing summary:', error);
  }
};

/**
 * Get billing information for an agent
 */
export const getBillingInfo = async (agentId) => {
  try {
    const summaryRef = doc(db, 'agent_billing_summary', agentId);
    const summaryDoc = await getDoc(summaryRef);

    if (summaryDoc.exists()) {
      const data = summaryDoc.data();
      return {
        totalMessages: data.totalMessages || 0,
        totalTokens: data.totalTokens || 0,
        estimatedCost: data.totalCost || 0,
        sessionCost: 0, // Reset for new session
        lastBillableAction: data.lastActivity?.toDate?.()?.toISOString() || null
      };
    }

    return {
      totalMessages: 0,
      totalTokens: 0,
      estimatedCost: 0,
      sessionCost: 0,
      lastBillableAction: null
    };
  } catch (error) {
    console.error('Error getting billing info:', error);
    return {
      totalMessages: 0,
      totalTokens: 0,
      estimatedCost: 0,
      sessionCost: 0,
      lastBillableAction: null
    };
  }
};

/**
 * Save conversation session summary
 */
export const saveBillingSession = async ({ agentId, conversationId, messages, totalTokens, totalCost, testMode, endedAt }) => {
  try {
    const sessionRef = collection(db, 'conversation_sessions');
    
    await addDoc(sessionRef, {
      agentId,
      conversationId,
      messageCount: messages,
      totalTokens,
      totalCost,
      isProduction: testMode === 'production',
      deploymentType: 'deployed',
      endedAt: endedAt || serverTimestamp(),
      createdAt: serverTimestamp()
    });

  } catch (error) {
    console.error('Error saving billing session:', error);
  }
};

/**
 * Get conversation history for billing/analytics
 */
export const getConversationHistory = async (agentId, options = {}) => {
  try {
    const {
      limit: limitCount = 50,
      startDate,
      endDate,
      testMode
    } = options;

    let q = query(
      collection(db, 'conversations'),
      where('agentId', '==', agentId),
      orderBy('createdAt', 'desc'),
      limit(limitCount)
    );

    // Add filters if provided
    if (testMode !== undefined) {
      // Convert testMode to isProduction boolean
      const isProduction = testMode === 'production';
      q = query(q, where('isProduction', '==', isProduction));
    }

    const snapshot = await getDocs(q);
    const conversations = [];

    snapshot.forEach((doc) => {
      const data = doc.data();
      conversations.push({
        id: doc.id,
        ...data,
        timestamp: data.createdAt?.toDate?.()?.toISOString() || data.timestamp
      });
    });

    return conversations;
  } catch (error) {
    console.error('Error getting conversation history:', error);
    return [];
  }
};

/**
 * Get billing analytics for an agent
 */
export const getBillingAnalytics = async (agentId, timeframe = '30days') => {
  try {
    const endDate = new Date();
    const startDate = new Date();
    
    switch (timeframe) {
      case '24hours':
        startDate.setHours(startDate.getHours() - 24);
        break;
      case '7days':
        startDate.setDate(startDate.getDate() - 7);
        break;
      case '30days':
        startDate.setDate(startDate.getDate() - 30);
        break;
      default:
        startDate.setDate(startDate.getDate() - 30);
    }

    const conversations = await getConversationHistory(agentId, {
      limit: 1000,
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString()
    });

    // Calculate analytics
    const analytics = {
      totalConversations: conversations.length,
      totalMessages: conversations.length,
      totalTokens: conversations.reduce((sum, conv) => sum + (conv.tokens?.total || 0), 0),
      totalCost: conversations.reduce((sum, conv) => sum + (conv.cost || 0), 0),
      averageTokensPerMessage: 0,
      averageCostPerMessage: 0,
      dailyBreakdown: {}
    };

    if (analytics.totalMessages > 0) {
      analytics.averageTokensPerMessage = Math.round(analytics.totalTokens / analytics.totalMessages);
      analytics.averageCostPerMessage = analytics.totalCost / analytics.totalMessages;
    }

    // Group by day for daily breakdown
    conversations.forEach(conv => {
      const date = new Date(conv.timestamp).toDateString();
      if (!analytics.dailyBreakdown[date]) {
        analytics.dailyBreakdown[date] = {
          messages: 0,
          tokens: 0,
          cost: 0
        };
      }
      analytics.dailyBreakdown[date].messages += 1;
      analytics.dailyBreakdown[date].tokens += conv.tokens?.total || 0;
      analytics.dailyBreakdown[date].cost += conv.cost || 0;
    });

    return analytics;
  } catch (error) {
    console.error('Error getting billing analytics:', error);
    return {
      totalConversations: 0,
      totalMessages: 0,
      totalTokens: 0,
      totalCost: 0,
      averageTokensPerMessage: 0,
      averageCostPerMessage: 0,
      dailyBreakdown: {}
    };
  }
};

/**
 * Subscribe to real-time billing updates
 */
export const subscribeToBillingUpdates = (agentId, callback) => {
  try {
    const summaryRef = doc(db, 'agent_billing_summary', agentId);
    
    return onSnapshot(summaryRef, (doc) => {
      if (doc.exists()) {
        const data = doc.data();
        callback({
          totalMessages: data.totalMessages || 0,
          totalTokens: data.totalTokens || 0,
          estimatedCost: data.totalCost || 0,
          lastBillableAction: data.lastActivity?.toDate?.()?.toISOString() || null
        });
      }
    });
  } catch (error) {
    console.error('Error subscribing to billing updates:', error);
    return () => {}; // Return empty unsubscribe function
  }
};

/**
 * Calculate cost based on token usage
 * Using standard GPT-4 pricing as baseline
 */
const calculateCost = (tokens) => {
  if (!tokens) return 0;
  
  const promptTokens = tokens.prompt_tokens || tokens.prompt || 0;
  const completionTokens = tokens.completion_tokens || tokens.completion || 0;
  
  // GPT-4 pricing (per 1K tokens)
  const promptCostPer1K = 0.03;   // $0.03 per 1K prompt tokens
  const completionCostPer1K = 0.06; // $0.06 per 1K completion tokens
  
  const promptCost = (promptTokens / 1000) * promptCostPer1K;
  const completionCost = (completionTokens / 1000) * completionCostPer1K;
  
  return promptCost + completionCost;
};

/**
 * Get authentication token for API calls
 */
const getAuthToken = async () => {
  try {
    // This should integrate with your existing auth system
    const user = api.getCurrentUser?.();
    if (user) {
      return await user.getIdToken();
    }
    return null;
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
};

/**
 * Test agent endpoint availability
 */
export const testAgentEndpoint = async (agentId) => {
  try {
    const agentEndpoint = await getAgentEndpoint(agentId);
    const response = await fetch(`${agentEndpoint}/health?agent_id=${agentId}`);
    
    if (!response.ok) {
      // Try to extract detailed error message from response
      let errorMessage = `Health check failed with HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = `Health check failed: ${errorData.detail}`;
        } else if (errorData.message) {
          errorMessage = `Health check failed: ${errorData.message}`;
        }
      } catch (parseError) {
        // If we can't parse the error response, use the status text
        errorMessage = `Health check failed: HTTP ${response.status} ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    
    return {
      available: true,
      status: data.status,
      version: data.version,
      lastDeployed: data.deployed_at
    };
  } catch (error) {
    return {
      available: false,
      error: error.message
    };
  }
};

/**
 * Get test conversation templates
 */
export const getTestConversationTemplates = () => {
  return [
    {
      id: 'greeting',
      name: 'Greeting Test',
      messages: [
        'Hello!',
        'What can you help me with?'
      ]
    },
    {
      id: 'capabilities',
      name: 'Capabilities Test',
      messages: [
        'What are your capabilities?',
        'Can you help me with banking questions?',
        'What tools do you have access to?'
      ]
    },
    {
      id: 'banking',
      name: 'Banking Workflow Test',
      messages: [
        'I need help with my account',
        'Can you show me my balance?',
        'What are my recent transactions?'
      ]
    },
    {
      id: 'error_handling',
      name: 'Error Handling Test',
      messages: [
        'Show me information for account ID 12345',
        'Transfer $1000000 from my account',
        'What is my account balance for invalid account?'
      ]
    }
  ];
};