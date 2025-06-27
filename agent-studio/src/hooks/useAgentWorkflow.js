/**
 * Agent Workflow Hook
 * 
 * Manages the complete agent development workflow with stage validation,
 * progress tracking, and guided navigation.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAgentState } from './useAgentState';
import { DEPLOYMENT_STATUS } from '../constants/workflowStates';

// Define the workflow stages
export const WORKFLOW_STAGES = [
  {
    id: 'definition',
    name: 'Agent Definition',
    description: 'Configure your agent\'s core settings and behavior',
    icon: 'Smart-Toy',
    phase: 'creation',
    required: true,
    route: '/agent-editor/:agentId'
  },
  {
    id: 'knowledge',
    name: 'Knowledge Base',
    description: 'Upload documents and configure knowledge sources',
    icon: 'Storage',
    phase: 'creation',
    required: false,
    route: '/knowledge-base/:agentId'
  },
  {
    id: 'api-integration',
    name: 'API Integration',
    description: 'Connect external APIs and MCP servers',
    icon: 'Api',
    phase: 'creation',
    required: false,
    route: '/api-integration/:agentId'
  },
  {
    id: 'pre-testing',
    name: 'Pre-deployment Testing',
    description: 'Test your agent functionality before deployment',
    icon: 'BugReport',
    phase: 'creation',
    required: false,
    route: '/agent-testing/:agentId'
  },
  {
    id: 'fine-tuning',
    name: 'Fine-tuning',
    description: 'Optimize agent responses with custom training data',
    icon: 'Tune',
    phase: 'creation',
    required: false,
    route: '/agent-fine-tuning/:agentId'
  },
  {
    id: 'deployment',
    name: 'Agent Deployment',
    description: 'Deploy your agent to production',
    icon: 'Rocket-Launch',
    phase: 'deployment',
    required: true,
    route: '/agent-deployment/:agentId'
  },
  {
    id: 'post-testing',
    name: 'Production Testing',
    description: 'Test your deployed agent with billing tracking',
    icon: 'PlayArrow',
    phase: 'deployment',
    required: false,
    route: '/agent-testing/:agentId'
  },
  {
    id: 'integration',
    name: 'Integration Setup',
    description: 'Configure WhatsApp, webhooks, and website widgets',
    icon: 'Integration-Instructions',
    phase: 'integration',
    required: false,
    route: '/agent-integration/:agentId'
  },
  {
    id: 'analytics',
    name: 'Analytics & Monitoring',
    description: 'Monitor usage, performance, and billing',
    icon: 'Analytics',
    phase: 'integration',
    required: false,
    route: '/agent-analytics/:agentId'
  }
];

export const WORKFLOW_PHASES = [
  {
    id: 'creation',
    name: 'Creation & Configuration',
    description: 'Build and configure your AI agent'
  },
  {
    id: 'deployment',
    name: 'Deployment & Testing',
    description: 'Deploy and validate your agent'
  },
  {
    id: 'integration',
    name: 'Integration & Analytics',
    description: 'Connect integrations and monitor performance'
  }
];

export const useAgentWorkflow = (agentId) => {
  const { agent, loading, error } = useAgentState(agentId);
  const [currentStage, setCurrentStage] = useState('definition');
  const [completedStages, setCompletedStages] = useState(new Set());
  const [stageValidation, setStageValidation] = useState({});
  const [workflowProgress, setWorkflowProgress] = useState(0);

  // Stage validation rules
  const validateStage = useCallback((stageId, agentData) => {
    const validations = {
      definition: {
        completed: !!(agentData?.name && agentData?.system_prompt && agentData?.model),
        requirements: ['Agent name', 'System prompt', 'Model selection'],
        canProceed: true
      },
      knowledge: {
        completed: true, // Optional stage - always considered complete
        requirements: [],
        canProceed: true
      },
      'api-integration': {
        completed: true, // Optional stage - always considered complete
        requirements: [],
        canProceed: true
      },
      'pre-testing': {
        completed: true, // Optional stage - always considered complete
        requirements: [],
        canProceed: true
      },
      'fine-tuning': {
        completed: true, // Optional stage - always considered complete
        requirements: [],
        canProceed: true
      },
      deployment: {
        completed: !!(agentData?.deployment_status === DEPLOYMENT_STATUS.COMPLETED || agentData?.deployment_status === DEPLOYMENT_STATUS.DEPLOYED),
        requirements: ['Completed agent definition'],
        canProceed: !!(agentData?.name && agentData?.system_prompt && agentData?.model)
      },
      'post-testing': {
        completed: !!(agentData?.deployment_status === DEPLOYMENT_STATUS.COMPLETED || agentData?.deployment_status === DEPLOYMENT_STATUS.DEPLOYED),
        requirements: ['Successful deployment'],
        canProceed: !!(agentData?.deployment_status === DEPLOYMENT_STATUS.COMPLETED || agentData?.deployment_status === DEPLOYMENT_STATUS.DEPLOYED)
      },
      integration: {
        completed: !!(agentData?.integrations_configured),
        requirements: ['Successful deployment'],
        canProceed: !!(agentData?.deployment_status === DEPLOYMENT_STATUS.COMPLETED || agentData?.deployment_status === DEPLOYMENT_STATUS.DEPLOYED)
      },
      analytics: {
        completed: true, // Always accessible once deployed
        requirements: ['Successful deployment'],
        canProceed: !!(agentData?.deployment_status === DEPLOYMENT_STATUS.COMPLETED || agentData?.deployment_status === DEPLOYMENT_STATUS.DEPLOYED)
      }
    };

    return validations[stageId] || { completed: false, requirements: [], canProceed: false };
  }, []);

  // Update stage completion status
  useEffect(() => {
    if (!agent) return;

    const newCompletedStages = new Set();
    const newValidation = {};
    
    WORKFLOW_STAGES.forEach(stage => {
      const validation = validateStage(stage.id, agent);
      newValidation[stage.id] = validation;
      
      if (validation.completed) {
        newCompletedStages.add(stage.id);
      }
    });

    setCompletedStages(newCompletedStages);
    setStageValidation(newValidation);

    // Calculate overall progress
    const totalStages = WORKFLOW_STAGES.length;
    const completedCount = newCompletedStages.size;
    setWorkflowProgress(Math.round((completedCount / totalStages) * 100));

  }, [agent, validateStage]);

  // Stage navigation helpers
  const canAccessStage = useCallback((stageId) => {
    return stageValidation[stageId]?.canProceed || false;
  }, [stageValidation]);

  const getNextStage = useCallback(() => {
    const currentIndex = WORKFLOW_STAGES.findIndex(stage => stage.id === currentStage);
    if (currentIndex < WORKFLOW_STAGES.length - 1) {
      return WORKFLOW_STAGES[currentIndex + 1];
    }
    return null;
  }, [currentStage]);

  const getPreviousStage = useCallback(() => {
    const currentIndex = WORKFLOW_STAGES.findIndex(stage => stage.id === currentStage);
    if (currentIndex > 0) {
      return WORKFLOW_STAGES[currentIndex - 1];
    }
    return null;
  }, [currentStage]);

  const navigateToStage = useCallback((stageId) => {
    if (canAccessStage(stageId)) {
      setCurrentStage(stageId);
      return true;
    }
    return false;
  }, [canAccessStage]);

  // Get stage status
  const getStageStatus = useCallback((stageId) => {
    const validation = stageValidation[stageId];
    if (!validation) return 'pending';
    
    if (validation.completed) return 'completed';
    if (validation.canProceed) return 'available';
    return 'locked';
  }, [stageValidation]);

  // Get current phase
  const getCurrentPhase = useCallback(() => {
    const stage = WORKFLOW_STAGES.find(s => s.id === currentStage);
    return stage?.phase || 'creation';
  }, [currentStage]);

  // Get phase progress
  const getPhaseProgress = useCallback((phaseId) => {
    const phaseStages = WORKFLOW_STAGES.filter(stage => stage.phase === phaseId);
    const completedInPhase = phaseStages.filter(stage => completedStages.has(stage.id));
    return {
      completed: completedInPhase.length,
      total: phaseStages.length,
      percentage: Math.round((completedInPhase.length / phaseStages.length) * 100)
    };
  }, [completedStages]);

  // Check if workflow is complete
  const isWorkflowComplete = useCallback(() => {
    const requiredStages = WORKFLOW_STAGES.filter(stage => stage.required);
    return requiredStages.every(stage => completedStages.has(stage.id));
  }, [completedStages]);

  // Get workflow summary
  const getWorkflowSummary = useCallback(() => {
    const total = WORKFLOW_STAGES.length;
    const completed = completedStages.size;
    const required = WORKFLOW_STAGES.filter(stage => stage.required).length;
    const requiredCompleted = WORKFLOW_STAGES
      .filter(stage => stage.required)
      .filter(stage => completedStages.has(stage.id)).length;

    return {
      totalStages: total,
      completedStages: completed,
      requiredStages: required,
      requiredCompleted: requiredCompleted,
      overallProgress: workflowProgress,
      isComplete: isWorkflowComplete(),
      canDeploy: requiredCompleted === required
    };
  }, [completedStages, workflowProgress, isWorkflowComplete]);

  return {
    // Current state
    agent,
    loading,
    error,
    currentStage,
    completedStages,
    stageValidation,
    workflowProgress,

    // Stage information
    stages: WORKFLOW_STAGES,
    phases: WORKFLOW_PHASES,

    // Navigation methods
    setCurrentStage,
    navigateToStage,
    canAccessStage,
    getNextStage,
    getPreviousStage,

    // Status methods
    getStageStatus,
    getCurrentPhase,
    getPhaseProgress,
    isWorkflowComplete,
    getWorkflowSummary,

    // Helper methods
    validateStage
  };
};

export default useAgentWorkflow;