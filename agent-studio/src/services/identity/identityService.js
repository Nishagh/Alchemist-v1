/**
 * Agent Identity Service
 * 
 * Service for fetching and managing agent identity data from the Global Narrative Framework.
 * Works with both the GNF API service and direct Firestore access for schema-compliant data.
 */

import { getApiConfig } from '../config/apiConfig';
import { Collections, DocumentFields } from '../../constants/collections';

class IdentityService {
  constructor() {
    this.timeout = 30000; // 30 seconds
    this._baseUrl = null; // Lazy-loaded
  }

  get baseUrl() {
    if (!this._baseUrl) {
      const apiConfig = getApiConfig();
      console.log('Lazy loading API config:', apiConfig);
      this._baseUrl = apiConfig?.baseUrl || 'https://global-narrative-framework-851487020021.us-central1.run.app';
      console.log('BaseUrl set to:', this._baseUrl);
    }
    return this._baseUrl;
  }

  /**
   * Fetch agent identity data from the agents collection (schema-compliant)
   * @param {string} agentId - The agent ID
   * @returns {Promise<Object>} Agent identity data
   */
  async getAgentIdentity(agentId) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      // First try to get identity from the agents collection (schema-compliant)
      const firestoreIdentity = await this._getIdentityFromFirestore(agentId);
      if (firestoreIdentity) {
        return firestoreIdentity;
      }

      // Fallback to GNF API service
      return await this._getIdentityFromAPI(agentId);
    } catch (error) {
      console.error('Failed to fetch agent identity:', error);
      throw error;
    }
  }

  /**
   * Get identity data directly from Firestore (schema-compliant)
   * @private
   */
  async _getIdentityFromFirestore(agentId) {
    try {
      const { db } = await import('../../utils/firebase');
      const { doc, getDoc } = await import('firebase/firestore');

      const agentRef = doc(db, Collections.AGENTS, agentId);
      const agentDoc = await getDoc(agentRef);

      if (!agentDoc.exists()) {
        return null;
      }

      const agentData = agentDoc.data();
      
      // Extract GNF identity data according to schema
      return {
        id: agentData.id || agentId,
        narrative_identity_id: agentData.narrative_identity_id || agentId,
        agent_id: agentId,
        development_stage: agentData.development_stage || 'nascent',
        narrative_coherence_score: agentData.narrative_coherence_score || 0.5,
        responsibility_score: agentData.responsibility_score || 0.5,
        experience_points: agentData.experience_points || 0,
        total_interactions: agentData.total_interactions || 0,
        defining_moments_count: agentData.defining_moments_count || 0,
        personality_traits: agentData.personality_traits || {},
        core_values: agentData.core_values || [],
        primary_goals: agentData.primary_goals || [],
        motivations: agentData.motivations || [],
        fears: agentData.fears || [],
        current_arc: agentData.current_arc || '',
        story_elements: agentData.story_elements || {},
        character_development: agentData.character_development || {},
        created_at: agentData.created_at,
        updated_at: agentData.updated_at,
        // Legacy compatibility
        total_narrative_interactions: agentData.total_interactions || 0,
        current_narrative_arc: agentData.current_arc || '',
        dominant_personality_traits: this._extractTraitNames(agentData.personality_traits),
        identity_summary: {
          name: agentData.name || `Agent-${agentId}`,
          development_stage: agentData.development_stage || 'nascent',
          created_at: agentData.created_at || new Date().toISOString()
        }
      };
    } catch (error) {
      console.error('Error fetching identity from Firestore:', error);
      return null;
    }
  }

  /**
   * Get identity data from GNF API service (fallback)
   * @private
   */
  async _getIdentityFromAPI(agentId) {
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
      console.error('Failed to fetch agent identity from API:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      
      if (error.message.includes('Failed to fetch')) {
        throw new Error('Network error - please check your connection');
      }
      
      // Return default identity if API fails
      return this._createDefaultIdentity(agentId);
    }
  }

  /**
   * Fetch agent interactions from conversations collection (schema-compliant)
   * @param {string} agentId - The agent ID
   * @param {number} limit - Maximum number of interactions to fetch
   * @returns {Promise<Array>} Array of interactions
   */
  async getAgentInteractions(agentId, limit = 50) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      // First try to get interactions from Firestore conversations collection
      const firestoreInteractions = await this._getInteractionsFromFirestore(agentId, limit);
      if (firestoreInteractions.length > 0) {
        return firestoreInteractions;
      }

      // Fallback to GNF API service
      return await this._getInteractionsFromAPI(agentId, limit);
    } catch (error) {
      console.error('Failed to fetch agent interactions:', error);
      throw error;
    }
  }

  /**
   * Get interactions from Firestore conversations collection (schema-compliant)
   * @private
   */
  async _getInteractionsFromFirestore(agentId, limit = 50) {
    try {
      const { db } = await import('../../utils/firebase');
      const { collection, query, where, orderBy, limit: firestoreLimit, getDocs } = await import('firebase/firestore');

      const conversationsRef = collection(db, Collections.CONVERSATIONS);
      const q = query(
        conversationsRef,
        where(DocumentFields.AGENT_ID, '==', agentId),
        orderBy(DocumentFields.TIMESTAMP, 'desc'),
        firestoreLimit(limit)
      );

      const querySnapshot = await getDocs(q);
      const interactions = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        interactions.push({
          id: doc.id,
          conversation_id: data.conversation_id,
          agent_id: data.agent_id,
          message_content: data.message_content,
          agent_response: data.agent_response,
          is_production: data.is_production,
          deployment_type: data.deployment_type,
          tokens: data.tokens,
          cost_usd: data.cost_usd,
          timestamp: data.timestamp,
          created_at: data.created_at,
          // Transform for display
          user_message: data.message_content,
          interaction_type: data.deployment_type,
          impact_level: data.is_production ? 'production' : 'test'
        });
      });

      return interactions;
    } catch (error) {
      console.error('Error fetching interactions from Firestore:', error);
      return [];
    }
  }

  /**
   * Get interactions from GNF API service (fallback)
   * @private
   */
  async _getInteractionsFromAPI(agentId, limit = 50) {
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
      console.error('Failed to fetch agent interactions from API:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      
      return [];
    }
  }

  /**
   * Fetch agent responsibility report from responsibility_assessments collection (schema-compliant)
   * @param {string} agentId - The agent ID
   * @param {number} days - Number of days to include in the report
   * @returns {Promise<Object>} Responsibility report data
   */
  async getResponsibilityReport(agentId, days = 30) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      // First try to get responsibility data from Firestore
      const firestoreReport = await this._getResponsibilityFromFirestore(agentId, days);
      if (firestoreReport) {
        return firestoreReport;
      }

      // Fallback to GNF API service
      return await this._getResponsibilityFromAPI(agentId, days);
    } catch (error) {
      console.error('Failed to fetch responsibility report:', error);
      throw error;
    }
  }

  /**
   * Get responsibility data from Firestore responsibility_assessments collection (schema-compliant)
   * @private
   */
  async _getResponsibilityFromFirestore(agentId, days = 30) {
    try {
      const { db } = await import('../../utils/firebase');
      const { collection, query, where, orderBy, limit, getDocs, Timestamp } = await import('firebase/firestore');

      // Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - days);

      const assessmentsRef = collection(db, Collections.RESPONSIBILITY_ASSESSMENTS);
      const q = query(
        assessmentsRef,
        where(DocumentFields.AGENT_ID, '==', agentId),
        where(DocumentFields.TIMESTAMP, '>=', Timestamp.fromDate(startDate)),
        where(DocumentFields.TIMESTAMP, '<=', Timestamp.fromDate(endDate)),
        orderBy(DocumentFields.TIMESTAMP, 'desc'),
        limit(100)
      );

      const querySnapshot = await getDocs(q);
      const assessments = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        assessments.push({
          id: doc.id,
          agent_id: data.agent_id,
          action_type: data.action_type,
          responsibility_level: data.responsibility_level,
          contributing_factors: data.contributing_factors || [],
          mitigation_actions: data.mitigation_actions || [],
          accountability_score: data.accountability_score || 0.5,
          ethical_weight: data.ethical_weight || 0.5,
          decision_quality: data.decision_quality || 0.5,
          learning_potential: data.learning_potential || 0.5,
          timestamp: data.timestamp,
          created_at: data.created_at
        });
      });

      // Generate report from assessments
      return this._generateResponsibilityReport(assessments);
    } catch (error) {
      console.error('Error fetching responsibility data from Firestore:', error);
      return null;
    }
  }

  /**
   * Get responsibility data from GNF API service (fallback)
   * @private
   */
  async _getResponsibilityFromAPI(agentId, days = 30) {
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
      console.error('Failed to fetch responsibility report from API:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      
      return this._createDefaultResponsibilityReport();
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
   * Fetch agent memories from agent_memories collection (schema-compliant)
   * @param {string} agentId - The agent ID
   * @param {number} limit - Maximum number of memories to fetch
   * @returns {Promise<Array>} Array of memories
   */
  async getAgentMemories(agentId, limit = 20) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      const { db } = await import('../../utils/firebase');
      const { collection, query, where, orderBy, limit: firestoreLimit, getDocs } = await import('firebase/firestore');

      const memoriesRef = collection(db, Collections.AGENT_MEMORIES);
      const q = query(
        memoriesRef,
        where(DocumentFields.AGENT_ID, '==', agentId),
        orderBy(DocumentFields.CREATED_AT, 'desc'),
        firestoreLimit(limit)
      );

      const querySnapshot = await getDocs(q);
      const memories = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        memories.push({
          id: doc.id,
          agent_id: data.agent_id,
          memory_type: data.memory_type,
          text_content: data.text_content,
          consolidation_strength: data.consolidation_strength || 0.5,
          importance_score: data.importance_score || 0.5,
          emotional_valence: data.emotional_valence || 0,
          tags: data.tags || [],
          timestamp: data.timestamp,
          created_at: data.created_at,
          updated_at: data.updated_at
        });
      });

      return memories;
    } catch (error) {
      console.error('Failed to fetch agent memories:', error);
      return [];
    }
  }

  /**
   * Fetch agent evolution events from evolution_events collection (schema-compliant)
   * @param {string} agentId - The agent ID
   * @param {number} limit - Maximum number of events to fetch
   * @returns {Promise<Array>} Array of evolution events
   */
  async getAgentEvolutionEvents(agentId, limit = 10) {
    if (!agentId) {
      throw new Error('Agent ID is required');
    }

    try {
      const { db } = await import('../../utils/firebase');
      const { collection, query, where, orderBy, limit: firestoreLimit, getDocs } = await import('firebase/firestore');

      const evolutionRef = collection(db, Collections.EVOLUTION_EVENTS);
      const q = query(
        evolutionRef,
        where(DocumentFields.AGENT_ID, '==', agentId),
        orderBy(DocumentFields.TIMESTAMP, 'desc'),
        firestoreLimit(limit)
      );

      const querySnapshot = await getDocs(q);
      const events = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        events.push({
          id: doc.id,
          agent_id: data.agent_id,
          event_type: data.event_type,
          trigger: data.trigger,
          pre_evolution_state: data.pre_evolution_state,
          post_evolution_state: data.post_evolution_state,
          changes: data.changes,
          timestamp: data.timestamp,
          created_at: data.created_at
        });
      });

      return events;
    } catch (error) {
      console.error('Failed to fetch agent evolution events:', error);
      return [];
    }
  }

  /**
   * Process and normalize identity data from GNF API (legacy)
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
   * Extract trait names from personality traits object
   * @private
   */
  _extractTraitNames(personalityTraits) {
    if (!personalityTraits || typeof personalityTraits !== 'object') {
      return ['helpful', 'responsive'];
    }
    
    // Handle different formats of personality traits
    if (Array.isArray(personalityTraits)) {
      return personalityTraits.map(t => typeof t === 'string' ? t : t.name || t.trait || 'unknown');
    }
    
    if (personalityTraits.traits && Array.isArray(personalityTraits.traits)) {
      return personalityTraits.traits;
    }
    
    // Extract from object keys or values
    return Object.keys(personalityTraits).slice(0, 5); // Limit to 5 traits
  }

  /**
   * Generate responsibility report from assessments data
   * @private
   */
  _generateResponsibilityReport(assessments) {
    if (!assessments || assessments.length === 0) {
      return this._createDefaultResponsibilityReport();
    }

    const totalActions = assessments.length;
    const avgAccountabilityScore = assessments.reduce((sum, a) => sum + (a.accountability_score || 0.5), 0) / totalActions;
    const avgEthicalWeight = assessments.reduce((sum, a) => sum + (a.ethical_weight || 0.5), 0) / totalActions;
    const avgDecisionQuality = assessments.reduce((sum, a) => sum + (a.decision_quality || 0.5), 0) / totalActions;

    // Calculate success rate (decisions above 0.6 quality threshold)
    const successfulActions = assessments.filter(a => (a.decision_quality || 0.5) > 0.6).length;
    const successRate = (successfulActions / totalActions) * 100;

    // Group by action type
    const actionTypes = assessments.reduce((acc, a) => {
      const type = a.action_type || 'unknown';
      if (!acc[type]) acc[type] = [];
      acc[type].push(a);
      return acc;
    }, {});

    return {
      total_actions: totalActions,
      success_rate: successRate,
      avg_ethical_weight: avgEthicalWeight,
      avg_responsibility_score: avgAccountabilityScore,
      avg_decision_quality: avgDecisionQuality,
      responsibility_trends: this._calculateTrends(assessments),
      consequence_analysis: this._analyzeConsequences(assessments),
      learning_progress: {
        improvement_rate: this._calculateImprovementRate(assessments),
        key_learnings: this._extractKeyLearnings(assessments)
      },
      action_types: actionTypes,
      strengths_and_weaknesses: this._identifyStrengthsWeaknesses(assessments),
      recommendations: this._generateRecommendations(assessments)
    };
  }

  /**
   * Calculate responsibility trends
   * @private
   */
  _calculateTrends(assessments) {
    // Group by week and calculate average scores
    const weeklyData = {};
    assessments.forEach(a => {
      if (a.timestamp) {
        const date = a.timestamp.toDate ? a.timestamp.toDate() : new Date(a.timestamp);
        const weekKey = this._getWeekKey(date);
        if (!weeklyData[weekKey]) weeklyData[weekKey] = [];
        weeklyData[weekKey].push(a.accountability_score || 0.5);
      }
    });

    return Object.entries(weeklyData).map(([week, scores]) => ({
      period: week,
      average_score: scores.reduce((sum, s) => sum + s, 0) / scores.length,
      action_count: scores.length
    })).sort((a, b) => a.period.localeCompare(b.period));
  }

  /**
   * Get week key for grouping
   * @private
   */
  _getWeekKey(date) {
    const year = date.getFullYear();
    const week = Math.ceil((date - new Date(year, 0, 1)) / (7 * 24 * 60 * 60 * 1000));
    return `${year}-W${week.toString().padStart(2, '0')}`;
  }

  /**
   * Analyze consequences patterns
   * @private
   */
  _analyzeConsequences(assessments) {
    const consequences = assessments.filter(a => a.contributing_factors && a.contributing_factors.length > 0);
    
    return {
      total_with_consequences: consequences.length,
      common_factors: this._findCommonFactors(consequences),
      mitigation_effectiveness: this._calculateMitigationEffectiveness(consequences)
    };
  }

  /**
   * Find common contributing factors
   * @private
   */
  _findCommonFactors(assessments) {
    const factorCounts = {};
    assessments.forEach(a => {
      if (a.contributing_factors) {
        a.contributing_factors.forEach(factor => {
          factorCounts[factor] = (factorCounts[factor] || 0) + 1;
        });
      }
    });

    return Object.entries(factorCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([factor, count]) => ({ factor, frequency: count }));
  }

  /**
   * Calculate mitigation effectiveness
   * @private
   */
  _calculateMitigationEffectiveness(assessments) {
    const withMitigation = assessments.filter(a => a.mitigation_actions && a.mitigation_actions.length > 0);
    if (withMitigation.length === 0) return 0;

    const avgScoreWithMitigation = withMitigation.reduce((sum, a) => sum + (a.accountability_score || 0.5), 0) / withMitigation.length;
    const avgScoreWithoutMitigation = assessments
      .filter(a => !a.mitigation_actions || a.mitigation_actions.length === 0)
      .reduce((sum, a, _, arr) => sum + (a.accountability_score || 0.5) / arr.length, 0);

    return Math.max(0, avgScoreWithMitigation - avgScoreWithoutMitigation);
  }

  /**
   * Calculate improvement rate
   * @private
   */
  _calculateImprovementRate(assessments) {
    if (assessments.length < 2) return 0;

    const sortedByDate = assessments
      .filter(a => a.timestamp)
      .sort((a, b) => {
        const dateA = a.timestamp.toDate ? a.timestamp.toDate() : new Date(a.timestamp);
        const dateB = b.timestamp.toDate ? b.timestamp.toDate() : new Date(b.timestamp);
        return dateA - dateB;
      });

    if (sortedByDate.length < 2) return 0;

    const firstHalf = sortedByDate.slice(0, Math.floor(sortedByDate.length / 2));
    const secondHalf = sortedByDate.slice(Math.floor(sortedByDate.length / 2));

    const firstAvg = firstHalf.reduce((sum, a) => sum + (a.accountability_score || 0.5), 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, a) => sum + (a.accountability_score || 0.5), 0) / secondHalf.length;

    return secondAvg - firstAvg;
  }

  /**
   * Extract key learnings
   * @private
   */
  _extractKeyLearnings(assessments) {
    const learningFactors = assessments
      .filter(a => a.learning_potential && a.learning_potential > 0.7)
      .map(a => a.action_type)
      .filter((type, index, arr) => arr.indexOf(type) === index)
      .slice(0, 3);

    return learningFactors.map(type => `Improved decision-making in ${type} scenarios`);
  }

  /**
   * Identify strengths and weaknesses
   * @private
   */
  _identifyStrengthsWeaknesses(assessments) {
    const actionTypeScores = {};
    assessments.forEach(a => {
      const type = a.action_type || 'unknown';
      if (!actionTypeScores[type]) actionTypeScores[type] = [];
      actionTypeScores[type].push(a.accountability_score || 0.5);
    });

    const avgScores = Object.entries(actionTypeScores).map(([type, scores]) => ({
      type,
      average: scores.reduce((sum, s) => sum + s, 0) / scores.length,
      count: scores.length
    }));

    const strengths = avgScores.filter(s => s.average > 0.7).map(s => s.type);
    const weaknesses = avgScores.filter(s => s.average < 0.4).map(s => s.type);

    return { strengths, weaknesses };
  }

  /**
   * Generate recommendations
   * @private
   */
  _generateRecommendations(assessments) {
    const recommendations = [];
    const { strengths, weaknesses } = this._identifyStrengthsWeaknesses(assessments);

    if (weaknesses.length > 0) {
      recommendations.push(`Focus on improving decision-making in: ${weaknesses.join(', ')}`);
    }

    if (strengths.length > 0) {
      recommendations.push(`Continue leveraging strong performance in: ${strengths.join(', ')}`);
    }

    const improvementRate = this._calculateImprovementRate(assessments);
    if (improvementRate < 0) {
      recommendations.push('Consider reviewing recent decision patterns for potential areas of improvement');
    } else if (improvementRate > 0.1) {
      recommendations.push('Maintain current learning trajectory - showing positive improvement');
    }

    return recommendations.length > 0 ? recommendations : ['Continue monitoring decision patterns and outcomes'];
  }

  /**
   * Create default identity structure for agents without GNF identity (schema-compliant)
   * @private
   */
  _createDefaultIdentity(agentId) {
    return {
      id: agentId,
      narrative_identity_id: agentId,
      agent_id: agentId,
      development_stage: 'nascent',
      narrative_coherence_score: 0.5,
      responsibility_score: 0.5,
      experience_points: 0,
      total_interactions: 0,
      defining_moments_count: 0,
      personality_traits: {
        primary: ['helpful', 'responsive', 'curious'],
        secondary: ['analytical', 'patient']
      },
      core_values: ['assistance', 'accuracy', 'learning'],
      primary_goals: ['help users', 'provide accurate information', 'learn from interactions'],
      motivations: ['user satisfaction', 'continuous improvement', 'knowledge sharing'],
      fears: ['providing incorrect information', 'user frustration'],
      current_arc: 'initial_development',
      story_elements: {
        origin: 'created_as_assistant',
        primary_role: 'general_helper',
        key_relationships: []
      },
      character_development: {
        maturity_level: 'nascent',
        growth_areas: ['user_understanding', 'domain_expertise'],
        achievements: []
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      // Legacy compatibility fields
      total_narrative_interactions: 0,
      current_narrative_arc: 'initial_development',
      dominant_personality_traits: ['helpful', 'responsive', 'curious'],
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