/**
 * Workforce Service
 * 
 * Real backend integration for AI agent cost management and billing
 */
import { gnfApi, api, billingApi } from '../config/apiConfig';
import { db } from '../../utils/firebase';
import { collection, query, where, getDocs, doc, getDoc } from 'firebase/firestore';

class WorkforceService {
  
  /**
   * Get comprehensive agent data with real backend integration
   */
  async getAgentWorkforceData(agentId, userId) {
    try {
      const data = {};
      
      // Get agent identity from GNF
      try {
        const identityResponse = await gnfApi.get(`/agents/${agentId}/identity`);
        data.identity = identityResponse.data.identity || identityResponse.data;
      } catch (error) {
        console.warn(`Identity not found for agent ${agentId}:`, error);
        data.identity = null;
      }

      // Get agent evolution data from GNF
      try {
        const evolutionResponse = await gnfApi.get(`/agents/${agentId}/evolution`);
        data.evolution = evolutionResponse.data;
      } catch (error) {
        console.warn(`Evolution data not found for agent ${agentId}:`, error);
        data.evolution = null;
      }

      // Get agent story/narrative from GNF
      try {
        const storyResponse = await gnfApi.get(`/agents/${agentId}/story`);
        data.story = storyResponse.data;
      } catch (error) {
        console.warn(`Story not found for agent ${agentId}:`, error);
        data.story = null;
      }

      // Get EA3 status from agent-engine
      try {
        const ea3Response = await api.get(`/api/agents/${agentId}/ea3-status`);
        data.ea3Status = ea3Response.data;
      } catch (error) {
        console.warn(`EA3 status not found for agent ${agentId}:`, error);
        data.ea3Status = null;
      }

      // Get agent conversations/interactions from agent-engine
      try {
        const conversationsResponse = await api.get(`/api/agents/${agentId}/conversations`);
        data.conversations = conversationsResponse.data.conversations || [];
      } catch (error) {
        console.warn(`Conversations not found for agent ${agentId}:`, error);
        data.conversations = [];
      }

      // Get billing/usage data from billing service
      try {
        const billingResponse = await billingApi.get(`/api/v1/usage/${agentId}?user_id=${userId}`);
        data.billing = billingResponse.data;
      } catch (error) {
        console.warn(`Billing data not found for agent ${agentId}:`, error);
        data.billing = null;
      }

      return data;
    } catch (error) {
      console.error(`Error fetching workforce data for agent ${agentId}:`, error);
      throw error;
    }
  }

  /**
   * Get all agent workforce data for a user
   */
  async getAllAgentWorkforceData(userId) {
    try {
      // Get all agents for user from Firebase
      const agentsRef = collection(db, 'agents');
      const agentsQuery = query(agentsRef, where('userId', '==', userId));
      const agentsSnapshot = await getDocs(agentsQuery);
      
      const agents = [];
      const workforceData = {};

      for (const doc of agentsSnapshot.docs) {
        const agentData = { id: doc.id, ...doc.data() };
        agents.push(agentData);
        
        // Get comprehensive workforce data for each agent
        workforceData[doc.id] = await this.getAgentWorkforceData(doc.id, userId);
      }

      return {
        agents,
        workforceData
      };
    } catch (error) {
      console.error('Error fetching all workforce data:', error);
      throw error;
    }
  }

  /**
   * Calculate real performance metrics based on actual data
   */
  calculatePerformanceMetrics(agentData) {
    const { conversations, ea3Status, identity } = agentData;
    
    if (!conversations || conversations.length === 0) {
      return {
        totalTasks: 0,
        successRate: 0,
        averageResponseTime: 0,
        userSatisfactionScore: 0,
        reliabilityScore: 0
      };
    }

    // Calculate success rate from actual conversations
    const successfulConversations = conversations.filter(conv => 
      conv.status === 'completed' || conv.outcome === 'successful'
    ).length;
    
    const successRate = conversations.length > 0 ? successfulConversations / conversations.length : 0;

    // Calculate average response time from conversation metadata
    const responseTimes = conversations
      .filter(conv => conv.response_time_ms)
      .map(conv => conv.response_time_ms);
    
    const averageResponseTime = responseTimes.length > 0 
      ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length / 1000 // Convert to seconds
      : 0;

    // Get reliability score from EA3 status
    const reliabilityScore = ea3Status?.reliability_score || 0;

    // Calculate user satisfaction from conversation ratings
    const ratingsArray = conversations
      .filter(conv => conv.user_rating)
      .map(conv => conv.user_rating);
    
    const userSatisfactionScore = ratingsArray.length > 0
      ? ratingsArray.reduce((sum, rating) => sum + rating, 0) / ratingsArray.length
      : 0;

    return {
      totalTasks: conversations.length,
      successRate: Math.round(successRate * 100),
      averageResponseTime: Math.round(averageResponseTime * 10) / 10,
      userSatisfactionScore: Math.round(userSatisfactionScore * 10) / 10,
      reliabilityScore: Math.round(reliabilityScore * 100)
    };
  }

  /**
   * Calculate real usage costs based on actual performance and usage
   */
  calculateUsageCosts(agentData, performanceMetrics) {
    const { conversations, ea3Status } = agentData;
    
    if (!conversations || conversations.length === 0) {
      return {
        totalCost: 0,
        monthlyAverage: 0,
        dailyAverage: 0,
        costPerTask: 0,
        apiCosts: 0,
        computeCosts: 0,
        storageCosts: 0
      };
    }

    // Cost calculation based on actual usage
    const baseCostPerTask = 12.50; // ₹12.50 per task (API costs)
    const computeCostPerMinute = 1.65; // ₹1.65 per minute of compute
    const storageCostPerMB = 0.08; // ₹0.08 per MB of storage

    // Calculate API costs
    const apiCosts = conversations.length * baseCostPerTask;
    
    // Calculate compute costs based on response times
    const totalComputeMinutes = conversations.reduce((total, conv) => {
      const responseTimeMinutes = (conv.response_time_ms || 2000) / 60000; // Convert ms to minutes
      return total + responseTimeMinutes;
    }, 0);
    const computeCosts = totalComputeMinutes * computeCostPerMinute;
    
    // Calculate storage costs (estimated based on conversation data)
    const avgConversationSizeMB = 0.05; // Estimated 50KB per conversation
    const storageCosts = conversations.length * avgConversationSizeMB * storageCostPerMB;
    
    // Additional EA3 processing costs
    const ea3ProcessingCosts = (ea3Status?.processing_events || 0) * 0.83; // ₹0.83 per EA3 event

    const totalCost = apiCosts + computeCosts + storageCosts + ea3ProcessingCosts;

    // Calculate time-based averages
    const agentCreated = conversations[0]?.created_at || new Date();
    const daysSinceCreation = Math.max(1, Math.floor((Date.now() - new Date(agentCreated).getTime()) / (1000 * 60 * 60 * 24)));
    const monthsSinceCreation = Math.max(1, daysSinceCreation / 30);

    return {
      totalCost: Math.round(totalCost * 100) / 100,
      monthlyAverage: Math.round((totalCost / monthsSinceCreation) * 100) / 100,
      dailyAverage: Math.round((totalCost / daysSinceCreation) * 100) / 100,
      costPerTask: Math.round((totalCost / conversations.length) * 100) / 100,
      apiCosts: Math.round(apiCosts * 100) / 100,
      computeCosts: Math.round(computeCosts * 100) / 100,
      storageCosts: Math.round(storageCosts * 100) / 100
    };
  }

  /**
   * Get real experience data
   */
  calculateExperience(agentData) {
    const { identity, evolution, conversations } = agentData;
    
    // Get actual creation date
    const creationDate = identity?.created_at || evolution?.first_interaction || new Date();
    const now = new Date();
    const experienceMs = now.getTime() - new Date(creationDate).getTime();
    const experienceDays = Math.max(1, Math.floor(experienceMs / (1000 * 60 * 60 * 24)));
    const experienceYears = (experienceDays / 365).toFixed(1);

    // Calculate experience points from actual interactions
    const interactionPoints = conversations.length * 10; // 10 XP per conversation
    const evolutionPoints = evolution?.evolution_events?.length * 50 || 0; // 50 XP per evolution event
    const totalXP = interactionPoints + evolutionPoints;

    return {
      years: experienceYears,
      days: experienceDays,
      totalXP: totalXP,
      level: Math.floor(totalXP / 100) + 1 // Level up every 100 XP
    };
  }

  /**
   * Generate job title based on real agent data
   */
  generateJobTitle(agentData) {
    const { identity, conversations } = agentData;
    
    if (!identity) return 'AI Specialist';
    
    const stage = identity.development_stage || 'nascent';
    const traits = identity.dominant_personality_traits || [];
    const totalTasks = conversations.length;
    
    // Determine seniority based on actual experience
    let seniority = 'Junior';
    if (totalTasks > 100) seniority = 'Senior';
    else if (totalTasks > 50) seniority = 'Mid-level';
    
    // Determine role based on personality traits and conversation patterns
    if (traits.includes('analytical') || traits.includes('logical')) {
      return `${seniority} Data Analyst`;
    } else if (traits.includes('creative') || traits.includes('innovative')) {
      return `${seniority} Innovation Specialist`;
    } else if (traits.includes('helpful') || traits.includes('supportive')) {
      return `${seniority} Customer Success Manager`;
    } else if (traits.includes('technical') || traits.includes('problem-solving')) {
      return `${seniority} Technical Specialist`;
    }
    
    return `${seniority} AI Specialist`;
  }


  /**
   * Get deployment status from Firebase and backend
   */
  async getDeploymentStatus(agentId) {
    try {
      // Check Firebase for deployment records
      const deploymentRef = doc(db, 'agent_deployments', agentId);
      const deploymentDoc = await getDoc(deploymentRef);
      
      if (deploymentDoc.exists()) {
        return deploymentDoc.data();
      }
      
      return {
        status: 'not_deployed',
        platforms: [],
        last_deployed: null
      };
    } catch (error) {
      console.error(`Error getting deployment status for ${agentId}:`, error);
      return {
        status: 'unknown',
        platforms: [],
        last_deployed: null
      };
    }
  }

  /**
   * Calculate cost efficiency metrics for an agent
   */
  calculateCostEfficiency(agentData) {
    const performance = this.calculatePerformanceMetrics(agentData);
    const costs = this.calculateUsageCosts(agentData, performance);
    
    if (performance.totalTasks === 0) {
      return {
        efficiency: 0,
        costPerSuccessfulTask: 0,
        roi: 0,
        recommendation: 'Needs activity'
      };
    }

    const successfulTasks = Math.round((performance.successRate / 100) * performance.totalTasks);
    const costPerSuccessfulTask = successfulTasks > 0 ? costs.totalCost / successfulTasks : costs.totalCost;
    
    // Calculate efficiency score (lower cost per successful task = higher efficiency)
    const efficiency = costPerSuccessfulTask > 0 ? Math.min(100, (1 / costPerSuccessfulTask) * 10) : 0;
    
    // Calculate ROI (placeholder - would need business value metrics)
    const assumedValuePerTask = 415.00; // Assumed ₹415 value per completed task
    const totalValue = successfulTasks * assumedValuePerTask;
    const roi = costs.totalCost > 0 ? ((totalValue - costs.totalCost) / costs.totalCost) * 100 : 0;
    
    let recommendation = 'Optimal';
    if (efficiency < 30) recommendation = 'Optimize usage';
    else if (efficiency < 60) recommendation = 'Monitor costs';
    
    return {
      efficiency: Math.round(efficiency),
      costPerSuccessfulTask: Math.round(costPerSuccessfulTask * 100) / 100,
      roi: Math.round(roi * 100) / 100,
      recommendation
    };
  }

  /**
   * Get budget tracking and alerts
   */
  async getBudgetStatus(userId, agentId = null) {
    try {
      let endpoint = `/api/v1/budget/status?user_id=${userId}`;
      if (agentId) {
        endpoint += `&agent_id=${agentId}`;
      }
      
      const response = await billingApi.get(endpoint);
      return response.data;
    } catch (error) {
      console.warn('Budget status not available:', error);
      return {
        budget: 0,
        spent: 0,
        remaining: 0,
        percentage: 0,
        alerts: []
      };
    }
  }

  /**
   * Get cost optimization suggestions
   */
  getCostOptimizationSuggestions(agentData, costs) {
    const suggestions = [];
    
    if (costs.apiCosts > costs.totalCost * 0.7) {
      suggestions.push({
        type: 'api_optimization',
        title: 'High API costs detected',
        description: 'Consider optimizing prompts to reduce API usage',
        priority: 'high'
      });
    }
    
    if (costs.computeCosts > costs.totalCost * 0.3) {
      suggestions.push({
        type: 'compute_optimization',
        title: 'High compute costs',
        description: 'Agent response times are high. Consider performance tuning',
        priority: 'medium'
      });
    }
    
    const performance = this.calculatePerformanceMetrics(agentData);
    if (performance.successRate < 70) {
      suggestions.push({
        type: 'performance_improvement',
        title: 'Low success rate',
        description: 'Improve agent training to reduce failed tasks and wasted costs',
        priority: 'high'
      });
    }
    
    return suggestions;
  }
}

export const workforceService = new WorkforceService();
export default workforceService;