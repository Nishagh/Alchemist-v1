/**
 * Agent Tuning Service API Client
 * 
 * Service for communicating with the alchemist-agent-tuning backend
 */

import { getApiConfig } from '../config/apiConfig';
import { getAuthToken } from '../auth/authService';

// API Configuration
const getServiceConfig = () => {
  const config = getApiConfig();
  return {
    baseUrl: config.tuningService?.url || 'http://localhost:8080',
    timeout: config.tuningService?.timeout || 30000
  };
};

// API Client Class
class TuningService {
  constructor() {
    this.config = getServiceConfig();
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    // Skip authentication for conversation endpoints as they work without auth
    const isConversationEndpoint = endpoint.includes('/conversation/');
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: this.config.timeout
    };
    
    // Add authentication only for non-conversation endpoints
    if (!isConversationEndpoint) {
      const token = await getAuthToken();
      defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  // Training Jobs API
  async createTrainingJob(jobData) {
    return this.makeRequest('/api/training/jobs', {
      method: 'POST',
      body: JSON.stringify(jobData)
    });
  }

  async getTrainingJobs(filters = {}) {
    const params = new URLSearchParams();
    if (filters.agentId) params.append('agent_id', filters.agentId);
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit.toString());

    const endpoint = `/api/training/jobs${params.toString() ? `?${params.toString()}` : ''}`;
    return this.makeRequest(endpoint);
  }

  async getTrainingJob(jobId) {
    return this.makeRequest(`/api/training/jobs/${jobId}`);
  }

  async getJobStatus(jobId) {
    return this.makeRequest(`/api/training/jobs/${jobId}/status`);
  }

  async startTrainingJob(jobId) {
    return this.makeRequest(`/api/training/jobs/${jobId}/start`, {
      method: 'POST'
    });
  }

  async cancelTrainingJob(jobId) {
    return this.makeRequest(`/api/training/jobs/${jobId}/cancel`, {
      method: 'POST'
    });
  }

  async deleteTrainingJob(jobId) {
    return this.makeRequest(`/api/training/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  // Training Data API
  async validateTrainingData(trainingPairs) {
    return this.makeRequest('/api/training/data/validate', {
      method: 'POST',
      body: JSON.stringify(trainingPairs)
    });
  }

  async processTrainingData(processRequest) {
    return this.makeRequest('/api/training/data/process', {
      method: 'POST',
      body: JSON.stringify(processRequest)
    });
  }

  async getAgentTrainingData(agentId, batchId = null) {
    const endpoint = `/api/training/data/${agentId}${batchId ? `?batch_id=${batchId}` : ''}`;
    return this.makeRequest(endpoint);
  }

  async exportTrainingData(agentId, format = 'json') {
    return this.makeRequest(`/api/training/data/${agentId}/export`, {
      method: 'POST',
      body: JSON.stringify({ format })
    });
  }

  // Models API
  async getAgentModels(agentId) {
    return this.makeRequest(`/api/training/models/${agentId}`);
  }

  async getModelDetails(agentId, modelId) {
    return this.makeRequest(`/api/training/models/${agentId}/${modelId}`);
  }

  async activateModel(agentId, modelId) {
    return this.makeRequest(`/api/training/models/${agentId}/${modelId}/activate`, {
      method: 'POST'
    });
  }

  async deactivateModel(agentId, modelId) {
    return this.makeRequest(`/api/training/models/${agentId}/${modelId}/deactivate`, {
      method: 'POST'
    });
  }

  async deleteModel(agentId, modelId) {
    return this.makeRequest(`/api/training/models/${agentId}/${modelId}`, {
      method: 'DELETE'
    });
  }

  // Query Generation API
  async generateQueries(agentContext, querySettings) {
    return this.makeRequest('/api/training/queries/generate', {
      method: 'POST',
      body: JSON.stringify({
        agent_context: agentContext,
        query_settings: querySettings
      })
    });
  }

  async analyzeAgentContext(agentId) {
    return this.makeRequest(`/api/training/queries/analyze-agent?agent_id=${agentId}`, {
      method: 'POST'
    });
  }

  async getQueryCategories() {
    return this.makeRequest('/api/training/queries/categories');
  }

  async getQueryDifficulties() {
    return this.makeRequest('/api/training/queries/difficulties');
  }

  // Conversation Training API
  async startConversationTraining(agentId, autoTrainingConfig = null) {
    return this.makeRequest('/api/training/conversation/start', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: agentId,
        auto_training_config: autoTrainingConfig
      })
    });
  }

  async generateAndRespond(sessionId, queryRequest) {
    return this.makeRequest('/api/training/conversation/generate-and-respond', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        query_request: queryRequest
      })
    });
  }

  async addTrainingPair(sessionId, query, response, queryMetadata = null) {
    return this.makeRequest('/api/training/conversation/add-pair', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        query: query,
        response: response,
        query_metadata: queryMetadata
      })
    });
  }

  async getConversationSessions(agentId = null, status = null, limit = 50) {
    const params = new URLSearchParams();
    if (agentId) params.append('agent_id', agentId);
    if (status) params.append('status_filter', status);
    if (limit) params.append('limit', limit.toString());

    const endpoint = `/api/training/conversation/sessions${params.toString() ? `?${params.toString()}` : ''}`;
    return this.makeRequest(endpoint);
  }

  async getConversationSession(sessionId) {
    return this.makeRequest(`/api/training/conversation/sessions/${sessionId}`);
  }

  async updateAutoTrainingConfig(agentId, config) {
    return this.makeRequest(`/api/training/conversation/auto-config/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(config)
    });
  }

  async getTrainingStats(agentId) {
    return this.makeRequest(`/api/training/conversation/stats/${agentId}`);
  }

  // Health Check
  async healthCheck() {
    return this.makeRequest('/health/');
  }

  // Utility Methods
  formatTrainingPairs(conversationPairs) {
    return conversationPairs.map((pair, index) => ({
      id: pair.id || `pair_${index}_${Date.now()}`,
      query: pair.query || pair.user_message || '',
      response: pair.response || pair.assistant_message || '',
      query_type: pair.query_type || pair.type || 'general',
      context: pair.context || '',
      timestamp: pair.timestamp || new Date().toISOString(),
      approved: pair.approved !== undefined ? pair.approved : true,
      metadata: pair.metadata || {}
    }));
  }

  createJobConfig(options = {}) {
    return {
      model_provider: options.model_provider || 'openai',
      base_model: options.base_model || 'gpt-3.5-turbo-1106',
      training_format: options.training_format || 'openai_chat',
      epochs: options.epochs || 3,
      batch_size: options.batch_size || 32,
      learning_rate: options.learning_rate || 0.0001,
      validation_split: options.validation_split || 0.1,
      temperature: options.temperature || 1.0,
      max_tokens: options.max_tokens || 2048,
      suffix: options.suffix || null
    };
  }

  // Real-time progress monitoring
  async monitorJobProgress(jobId, onProgress, interval = 5000) {
    const checkProgress = async () => {
      try {
        const progress = await this.getJobStatus(jobId);
        onProgress(progress);
        
        // Continue monitoring if job is still active
        if (['pending', 'validating', 'queued', 'running'].includes(progress.status)) {
          setTimeout(checkProgress, interval);
        }
      } catch (error) {
        console.error('Error monitoring job progress:', error);
        onProgress({ error: error.message });
      }
    };

    // Start monitoring
    checkProgress();
  }
}

// Create singleton instance
const tuningService = new TuningService();

// Export individual methods for easier usage
export const createTrainingJob = (jobData) => tuningService.createTrainingJob(jobData);
export const getTrainingJobs = (filters) => tuningService.getTrainingJobs(filters);
export const getTrainingJob = (jobId) => tuningService.getTrainingJob(jobId);
export const getJobStatus = (jobId) => tuningService.getJobStatus(jobId);
export const startTrainingJob = (jobId) => tuningService.startTrainingJob(jobId);
export const cancelTrainingJob = (jobId) => tuningService.cancelTrainingJob(jobId);
export const deleteTrainingJob = (jobId) => tuningService.deleteTrainingJob(jobId);

export const validateTrainingData = (trainingPairs) => tuningService.validateTrainingData(trainingPairs);
export const processTrainingData = (processRequest) => tuningService.processTrainingData(processRequest);
export const getAgentTrainingData = (agentId, batchId) => tuningService.getAgentTrainingData(agentId, batchId);
export const exportTrainingData = (agentId, format) => tuningService.exportTrainingData(agentId, format);

export const getAgentModels = (agentId) => tuningService.getAgentModels(agentId);
export const getModelDetails = (agentId, modelId) => tuningService.getModelDetails(agentId, modelId);
export const activateModel = (agentId, modelId) => tuningService.activateModel(agentId, modelId);
export const deactivateModel = (agentId, modelId) => tuningService.deactivateModel(agentId, modelId);
export const deleteModel = (agentId, modelId) => tuningService.deleteModel(agentId, modelId);

export const generateQueries = (agentContext, querySettings) => tuningService.generateQueries(agentContext, querySettings);
export const analyzeAgentContext = (agentId) => tuningService.analyzeAgentContext(agentId);
export const getQueryCategories = () => tuningService.getQueryCategories();
export const getQueryDifficulties = () => tuningService.getQueryDifficulties();

export const startConversationTraining = (agentId, autoTrainingConfig) => tuningService.startConversationTraining(agentId, autoTrainingConfig);
export const generateAndRespond = (sessionId, queryRequest) => tuningService.generateAndRespond(sessionId, queryRequest);
export const addTrainingPair = (sessionId, query, response, queryMetadata) => tuningService.addTrainingPair(sessionId, query, response, queryMetadata);
export const getConversationSessions = (agentId, status, limit) => tuningService.getConversationSessions(agentId, status, limit);
export const getConversationSession = (sessionId) => tuningService.getConversationSession(sessionId);
export const updateAutoTrainingConfig = (agentId, config) => tuningService.updateAutoTrainingConfig(agentId, config);
export const getTrainingStats = (agentId) => tuningService.getTrainingStats(agentId);

export const formatTrainingPairs = (conversationPairs) => tuningService.formatTrainingPairs(conversationPairs);
export const createJobConfig = (options) => tuningService.createJobConfig(options);
export const monitorJobProgress = (jobId, onProgress, interval) => tuningService.monitorJobProgress(jobId, onProgress, interval);

export default tuningService;