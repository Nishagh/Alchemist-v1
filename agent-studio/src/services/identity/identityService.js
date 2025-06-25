/**
 * Agent Identity Service
 * 
 * Service for fetching and managing agent identity data from the Global Narrative Framework.
 */

import { getApiConfig } from '../config/apiConfig';

class IdentityService {
  constructor() {
    this.timeout = 30000; // 30 seconds
    this._baseUrl = null; // Lazy-loaded
  }

  get baseUrl() {
    if (!this._baseUrl) {
      const apiConfig = getApiConfig();
      console.log('Lazy loading API config:', apiConfig);
      this._baseUrl = apiConfig?.baseUrl || 'https://global-narrative-framework-backend-851487020021.us-central1.run.app';
      console.log('BaseUrl set to:', this._baseUrl);
    }
    return this._baseUrl;
  }

  /**
   * Fetch agent identity data from GNF
   * @param {string} agentId - The agent ID
   * @returns {Promise<Object>} Agent identity data
   */
  async getAgentIdentity(agentId) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      console.log(this.baseUrl)
      const response = await fetch(`${this.baseUrl}/agents/${agentId}/identity`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        if (response.status === 404) {
          // Agent identity not found - return basic structure
          return this._createDefaultIdentity(agentId);
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      // Handle the new API response format
      if (data.success && data.identity) {
        return this._processIdentityData(data.identity);
      }
      return this._processIdentityData(data);
    } catch (error) {
      console.error('Failed to fetch agent identity:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      
      if (error.message.includes('Failed to fetch')) {
        throw new Error('Network error - please check your connection');
      }
      
      throw error;
    }
  }

  /**
   * Fetch agent interactions from GNF
   * @param {string} agentId - The agent ID
   * @param {number} limit - Maximum number of interactions to fetch
   * @returns {Promise<Array>} Array of interactions
   */
  async getAgentInteractions(agentId, limit = 50) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      const response = await fetch(`${this.baseUrl}/agents/${agentId}/interactions?limit=${limit}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        if (response.status === 404) {
          return [];
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data.interactions || [];
    } catch (error) {
      console.error('Failed to fetch agent interactions:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      
      throw error;
    }
  }

  /**
   * Fetch agent responsibility report from GNF
   * @param {string} agentId - The agent ID
   * @param {number} days - Number of days to include in the report
   * @returns {Promise<Object>} Responsibility report data
   */
  async getResponsibilityReport(agentId, days = 30) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      const response = await fetch(`${this.baseUrl}/agents/${agentId}/responsibility/report?days=${days}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        if (response.status === 404) {
          return this._createDefaultResponsibilityReport();
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      // Handle the new API response format
      if (data.success && data.report) {
        return data.report;
      }
      return data;
    } catch (error) {
      console.error('Failed to fetch responsibility report:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      
      throw error;
    }
  }

  /**
   * Create GNF identity for an agent
   * @param {string} agentId - The agent ID
   * @param {Object} identityData - Identity configuration
   * @returns {Promise<Object>} Created identity data
   */
  async createAgentIdentity(agentId, identityData) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      const response = await fetch(`${this.baseUrl}/agents/${agentId}/identity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(identityData),
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return this._processIdentityData(data);
    } catch (error) {
      console.error('Failed to create agent identity:', error);
      throw error;
    }
  }

  /**
   * Update agent identity
   * @param {string} agentId - The agent ID
   * @param {Object} updates - Identity updates
   * @returns {Promise<Object>} Updated identity data
   */
  async updateAgentIdentity(agentId, updates) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      const response = await fetch(`${this.baseUrl}/agents/${agentId}/identity`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return this._processIdentityData(data);
    } catch (error) {
      console.error('Failed to update agent identity:', error);
      throw error;
    }
  }

  /**
   * Process and normalize identity data from GNF
   * @private
   */
  _processIdentityData(data) {
    // Ensure all expected fields exist with defaults
    return {
      agent_id: data.agent_id || '',
      development_stage: data.development_stage || 'nascent',
      narrative_coherence_score: data.narrative_coherence_score || 0.5,
      responsibility_score: data.responsibility_score || 0.5,
      experience_points: data.experience_points || 0,
      total_narrative_interactions: data.total_interactions || 0,
      defining_moments_count: data.defining_moments || 0,
      current_narrative_arc: data.current_arc || null,
      dominant_personality_traits: data.key_traits?.map(t => t.name || t) || [],
      core_values: data.core_values || [],
      primary_goals: data.primary_goals || [],
      identity_summary: data.identity_summary || {},
      ...data
    };
  }

  /**
   * Create default identity structure for agents without GNF identity
   * @private
   */
  _createDefaultIdentity(agentId) {
    return {
      agent_id: agentId,
      development_stage: 'nascent',
      narrative_coherence_score: 0.5,
      responsibility_score: 0.5,
      experience_points: 0,
      total_narrative_interactions: 0,
      defining_moments_count: 0,
      current_narrative_arc: null,
      dominant_personality_traits: ['helpful', 'responsive'],
      core_values: ['assistance', 'accuracy'],
      primary_goals: ['help users', 'provide information'],
      identity_summary: {
        name: `Agent-${agentId}`,
        development_stage: 'nascent',
        created_at: new Date().toISOString()
      },
      is_default: true
    };
  }

  /**
   * Create default responsibility report
   * @private
   */
  _createDefaultResponsibilityReport() {
    return {
      total_actions: 0,
      success_rate: 0,
      avg_ethical_weight: 0,
      avg_responsibility_score: 0.5,
      responsibility_trends: [],
      consequence_analysis: {},
      learning_progress: {},
      strengths_and_weaknesses: {
        strengths: [],
        weaknesses: []
      },
      recommendations: []
    };
  }
}

// Create singleton instance
const identityService = new IdentityService();

export default identityService;