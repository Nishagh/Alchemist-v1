/**
 * API Services Index
 * 
 * Central export for all API services to maintain backward compatibility
 * and provide a single import point for all API operations
 */

// Core services
export { initializeAuthInterceptors, getAuthToken, verifyTokenWithServer } from './auth/authService';
export { API_BASE_URL, KNOWLEDGE_BASE_URL, MCP_MANAGER_URL, ENDPOINTS, api, kbApi, mcpApi } from './config/apiConfig';

// Agent services
export {
  createAgent,
  updateAgent,
  deleteAgent,
  executeAgentAction,
  executeUserAgentAction,
  getAgentTypes,
  getAgentPrompt,
  updateAgentPrompt
} from './agents/agentService';

// Conversation services
export {
  getAgentConversations,
  getConversationMessages,
  createConversation,
  deleteConversation
} from './conversations/conversationService';

// Knowledge base services
export {
  getAgentKnowledgeBase,
  uploadKnowledgeBaseFile,
  deleteKnowledgeBaseFile,
  searchKnowledgeBase,
  getKnowledgeBaseSearchResults
} from './knowledgeBase/knowledgeBaseService';

// Artifact services
export {
  getAgentArtifacts,
  createArtifact,
  updateArtifact,
  deleteArtifact
} from './artifacts/artifactService';

// Alchemist services
export {
  interactWithAlchemist,
  getAlchemistConversations,
  clearAlchemistConversation
} from './alchemist/alchemistService';

// API Integration services
export {
  uploadApiSpecification,
  getApiIntegrations,
  deleteApiIntegration,
  getApiSpecification,
  downloadApiSpecification,
  getTestableEndpoints,
  testApiEndpoint,
  getApiIntegrationFiles
} from './apiIntegration/apiIntegrationService';

// MCP Server services
export {
  deployMcpServer,
  checkDeploymentStatus,
  getDeploymentLogs,
  deleteMcpServer,
  checkServerStatus,
  getIntegrationSummary,
  getLiveTools,
  testTool
} from './mcpServer/mcpServerService';

// Agent Deployment services
export {
  deployAgent,
  getDeploymentStatus,
  listDeployments,
  cancelDeployment,
  getQueueStatus,
  getServiceHealth,
  pollDeploymentStatus,
  subscribeToDeploymentUpdates,
  getDeployment
} from './deployment/deploymentService';

// Backward compatibility - re-export everything that was in the original apiService
// This allows existing imports to continue working without changes
export * from './agents/agentService';
export * from './conversations/conversationService';
export * from './knowledgeBase/knowledgeBaseService';
export * from './artifacts/artifactService';
export * from './alchemist/alchemistService';
export * from './apiIntegration/apiIntegrationService';
export * from './mcpServer/mcpServerService';
export * from './deployment/deploymentService';