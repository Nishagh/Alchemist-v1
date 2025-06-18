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
};