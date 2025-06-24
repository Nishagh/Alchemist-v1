/**
 * API Configuration
 * 
 * Central configuration for all API services
 */
import axios from 'axios';

// Configure the base URLs for different services
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
export const KNOWLEDGE_BASE_URL = process.env.REACT_APP_KNOWLEDGE_BASE_URL;
export const MCP_MANAGER_URL = process.env.REACT_APP_MCP_MANAGER_URL;
export const TUNING_SERVICE_URL = process.env.REACT_APP_TUNING_SERVICE_URL;
export const BILLING_SERVICE_URL = process.env.REACT_APP_BILLING_SERVICE_URL || 'https://billing-service-851487020021.us-central1.run.app';

// Create axios instances with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const kbApi = axios.create({
  baseURL: KNOWLEDGE_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Default axios instance for MCP operations
export const mcpApi = axios.create({
  baseURL: MCP_MANAGER_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Tuning service axios instance
export const tuningApi = axios.create({
  baseURL: TUNING_SERVICE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Billing service axios instance
export const billingApi = axios.create({
  baseURL: BILLING_SERVICE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Common configuration
export const API_CONFIG = {
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// API endpoints
export const ENDPOINTS = {
  // Agent endpoints
  AGENTS: '/api/agents',
  AGENT_ACTIONS: '/api/agent-actions',
  AGENT_PROMPTS: '/api/agent-prompts',
  
  // Conversation endpoints
  CONVERSATIONS: '/api/conversations',
  
  // Knowledge base endpoints
  KNOWLEDGE_BASE: '/api/knowledge-base',
  KB_SEARCH: '/api/knowledge-base/search',
  KB_FILES: '/api/knowledge-base/files',
  
  // Artifact endpoints
  ARTIFACTS: '/api/artifacts',
  
  // Alchemist endpoints
  ALCHEMIST: '/api/alchemist',
  
  // API Integration endpoints
  API_INTEGRATIONS: '/api/api-integrations',
  API_SPECS: '/api/api-specifications',
  API_ENDPOINTS: '/api/api-endpoints',
  
  // MCP Server endpoints
  MCP_SERVERS: '/api/mcp-servers',
  MCP_DEPLOYMENT: '/api/mcp-deployment',
  MCP_TOOLS: '/api/mcp-tools',
  
  // Health check
  HEALTH: '/api/health',
  
  // Agent Tuning Service endpoints
  TUNING_JOBS: '/api/training/jobs',
  TUNING_DATA: '/api/training/data',
  TUNING_MODELS: '/api/training/models',
  TUNING_HEALTH: '/health',
  
  // Billing Service endpoints
  BILLING_CREDITS_BALANCE: '/api/v1/credits/balance',
  BILLING_CREDITS_ACCOUNT: '/api/v1/credits/account',
  BILLING_CREDITS_PACKAGES: '/api/v1/credits/packages',
  BILLING_CREDITS_PURCHASE: '/api/v1/credits/purchase',
  BILLING_CREDITS_ORDERS: '/api/v1/credits/orders',
  BILLING_CREDITS_STATUS: '/api/v1/credits/status',
  BILLING_PAYMENTS_VERIFY: '/api/v1/payments/verify',
  BILLING_TRANSACTIONS: '/api/v1/transactions',
  BILLING_HEALTH: '/api/v1/health',
};

// Get API configuration for services
export const getApiConfig = () => ({
  alchemist: {
    url: API_BASE_URL,
    timeout: 30000
  },
  knowledgeBase: {
    url: KNOWLEDGE_BASE_URL,
    timeout: 60000
  },
  mcpManager: {
    url: MCP_MANAGER_URL,
    timeout: 60000
  },
  tuningService: {
    url: TUNING_SERVICE_URL || 'http://localhost:8080',
    timeout: 60000
  },
  billingService: {
    url: BILLING_SERVICE_URL,
    timeout: 30000
  }
});