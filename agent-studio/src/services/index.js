/**
 * API Services Index
 * 
 * Central export for all API services to maintain backward compatibility
 * and provide a single import point for all API operations
 */

// Identity service import
import identityService from './identity/identityService';

// Core services
export { initializeAuthInterceptors, getAuthToken, verifyTokenWithServer } from './auth/authService';
export { AGENT_ENGINE_URL, KNOWLEDGE_VAULT_URL, TOOL_FORGE_URL, TUNING_SERVICE_URL, ENDPOINTS, api, kbApi, mcpApi, tuningApi, getApiConfig } from './config/apiConfig';

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

// Agent Tuning services
export {
  createTrainingJob,
  getTrainingJobs,
  getTrainingJob,
  getJobStatus,
  startTrainingJob,
  cancelTrainingJob,
  deleteTrainingJob,
  validateTrainingData,
  processTrainingData,
  getAgentTrainingData,
  exportTrainingData,
  getAgentModels,
  getModelDetails,
  activateModel,
  deactivateModel,
  deleteModel,
  formatTrainingPairs,
  createJobConfig,
  monitorJobProgress,
  generateQueries,
  analyzeAgentContext,
  getQueryCategories,
  getQueryDifficulties,
  startConversationTraining,
  generateAndRespond,
  addTrainingPair,
  getConversationSessions,
  getConversationSession,
  updateAutoTrainingConfig,
  getTrainingStats
} from './tuning/tuningService';

// Billing Service (microservice-based)
export {
  billingServiceV2,
  billingServiceV2 as creditsService  // Alias for backward compatibility
} from './billing/billingServiceV2';

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
export * from './tuning/tuningService';

// Identity services (GNF integration)
export const getAgentIdentity = (...args) => identityService.getAgentIdentity(...args);
export const getAgentInteractions = (...args) => identityService.getAgentInteractions(...args);
export const getResponsibilityReport = (...args) => identityService.getResponsibilityReport(...args);
export const createAgentIdentity = (...args) => identityService.createAgentIdentity(...args);
export const updateAgentIdentity = (...args) => identityService.updateAgentIdentity(...args);