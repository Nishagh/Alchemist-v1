/**
 * MCP Server Service
 * 
 * Handles Model Context Protocol (MCP) server operations including deployment,
 * status monitoring, tools management, and testing
 */
import axios from 'axios';
import { auth, db } from '../../utils/firebase';
import { getAuthToken } from '../auth/authService';
import { TOOL_FORGE_URL } from '../config/apiConfig';
import { collection, addDoc, serverTimestamp, doc, onSnapshot, getDoc } from 'firebase/firestore';

/**
 * Deploy MCP server for an agent - Creates deployment request in Firestore
 */
export const deployMcpServer = async (agentId, deploymentConfig = {}) => {
  try {
    // Get current user ID
    const currentUser = auth.currentUser;
    const userId = currentUser?.uid;
    
    if (!userId) {
      throw new Error('User not authenticated');
    }
    
    console.log(`Creating MCP deployment request for agent ${agentId}`);
    
    // Create deployment document in Firestore
    const deploymentData = {
      agent_id: agentId,
      user_id: userId,
      status: 'queued',
      progress: 0,
      current_step: 'Queued for deployment',
      deployment_config: deploymentConfig,
      progress_steps: [
        { step: 'queued', status: 'completed', message: 'Deployment request created' },
        { step: 'validating', status: 'pending', message: 'Validating API specifications' },
        { step: 'building', status: 'pending', message: 'Building MCP server container' },
        { step: 'deploying', status: 'pending', message: 'Deploying to cloud infrastructure' },
        { step: 'testing', status: 'pending', message: 'Testing server connectivity' }
      ],
      created_at: serverTimestamp(),
      updated_at: serverTimestamp()
    };
    
    const deploymentRef = await addDoc(collection(db, 'mcp_deployments'), deploymentData);
    
    console.log('MCP deployment request created:', deploymentRef.id);
    
    return {
      deployment_id: deploymentRef.id,
      status: 'queued',
      message: 'Deployment request created successfully'
    };
  } catch (error) {
    console.error('Error creating MCP deployment request:', error);
    throw error;
  }
};

/**
 * Subscribe to deployment status updates in real-time
 */
export const subscribeToDeploymentStatus = (deploymentId, callback) => {
  try {
    console.log(`Subscribing to deployment status for: ${deploymentId}`);
    
    const deploymentRef = doc(db, 'mcp_deployments', deploymentId);
    
    const unsubscribe = onSnapshot(deploymentRef, (doc) => {
      if (doc.exists()) {
        const data = doc.data();
        console.log('Deployment status update:', data);
        callback({ id: doc.id, ...data });
      } else {
        console.log('Deployment document not found');
        callback(null);
      }
    }, (error) => {
      console.error('Error listening to deployment status:', error);
      callback(null, error);
    });
    
    return unsubscribe;
  } catch (error) {
    console.error('Error setting up deployment status subscription:', error);
    throw error;
  }
};

/**
 * Get deployment status by deployment ID
 */
export const getDeploymentStatus = async (deploymentId) => {
  try {
    const { doc: getDoc } = await import('firebase/firestore');
    const deploymentRef = doc(db, 'mcp_deployments', deploymentId);
    const deploymentDoc = await getDoc(deploymentRef);
    
    if (deploymentDoc.exists()) {
      return { id: deploymentDoc.id, ...deploymentDoc.data() };
    } else {
      throw new Error('Deployment not found');
    }
  } catch (error) {
    console.error('Error getting deployment status:', error);
    throw error;
  }
};

/**
 * Check deployment status using MCP manager (Legacy function - kept for compatibility)
 */
export const checkDeploymentStatus = async (agentId, deploymentId) => {
  try {
    const url = `${TOOL_FORGE_URL}/deployments/${agentId}/${deploymentId}`;
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
      url: `${TOOL_FORGE_URL}/deployments/${agentId}/${deploymentId}`,
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
 */
export const getDeploymentLogs = async (agentId, deploymentId) => {
  try {
    const url = `${TOOL_FORGE_URL}/deployments/${agentId}/${deploymentId}/logs`;
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
      url: `${TOOL_FORGE_URL}/servers/${agentId}`,
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
 */
export const checkServerStatus = async (agentId) => {
  try {
    const url = `${TOOL_FORGE_URL}/servers/${agentId}`;
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
      url: `${TOOL_FORGE_URL}/servers/${agentId}`,
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
      url: `${TOOL_FORGE_URL}/agents/${agentId}/integration-summary`,
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
    
    // Handle 405 Method Not Allowed - this endpoint might not exist
    if (error.response?.status === 405) {
      console.warn(`Integration summary endpoint not available for agent ${agentId} (405), returning null`);
      return null;
    }
    
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error;
  }
};

/**
 * Get live tools data from deployed MCP server
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
      url: `${TOOL_FORGE_URL}/agents/${agentId}/tools`,
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
      url: `${TOOL_FORGE_URL}/agents/${agentId}/tools/${toolName}/test`,
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
 * Get MCP server information from Firestore
 * Fetches server info, endpoints, and tools from mcp_server collection
 */
export const getMcpServerInfo = async (agentId) => {
  try {
    console.log(`Fetching MCP server info for agent ${agentId} from Firestore`);
    
    const serverRef = doc(db, 'mcp_servers', agentId);
    const serverDoc = await getDoc(serverRef);
    
    if (serverDoc.exists()) {
      const data = serverDoc.data();
      console.log('MCP server info fetched:', data);
      return { id: serverDoc.id, ...data };
    } else {
      console.log('No MCP server document found for agent:', agentId);
      return null;
    }
  } catch (error) {
    console.error('Error fetching MCP server info from Firestore:', error);
    throw error;
  }
};