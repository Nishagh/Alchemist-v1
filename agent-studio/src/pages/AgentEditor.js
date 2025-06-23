/**
 * Agent Editor (Refactored with Sidebar Navigation)
 * 
 * Main agent editor page using the new sidebar navigation architecture
 */
import React, { useState, useEffect } from 'react';
import { CircularProgress, Box, Typography, IconButton } from '@mui/material';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';

// Import the new component architecture
import AgentEditorLayout from '../components/AgentEditor/AgentEditorLayout';
import AgentSidebarNavigation from '../components/AgentEditor/AgentSidebarNavigation';
import NotificationSystem, { createNotification } from '../components/shared/NotificationSystem';
import WorkflowProgressIndicator from '../components/AgentEditor/WorkflowProgress/WorkflowProgressIndicator';

// Import feature components
import AgentConversationPanel from '../components/AgentEditor/AgentConversation/AgentConversationPanel';
import AgentConfigurationForm from '../components/AgentEditor/AgentConfiguration/AgentConfigurationForm';
import KnowledgeBaseManager from '../components/AgentEditor/KnowledgeBase/KnowledgeBaseManager';
import ApiIntegrationManager from '../components/AgentEditor/ApiIntegration/ApiIntegrationManager';
import AgentTestingInterface from '../components/AgentEditor/AgentTesting/AgentTestingInterface';
import AgentFineTuningInterface from '../components/AgentEditor/AgentFineTuning/AgentFineTuningInterface';

// Import hooks and services
import useAgentState from '../hooks/useAgentState';
import { useAgentWorkflow, WORKFLOW_STAGES } from '../hooks/useAgentWorkflow';
import { updateAgent } from '../services';

const AgentEditor = () => {
  const navigate = useNavigate();
  const { agentId } = useParams();
  const location = useLocation();
  
  // Core state management
  const { 
    agent, 
    loading, 
    error, 
    saving, 
    updateAgentLocal, 
    setSaving, 
    setError, 
    clearError 
  } = useAgentState(agentId);

  // Workflow management
  const workflow = useAgentWorkflow(agentId);

  // Determine initial section from route
  const getInitialSection = () => {
    const path = location.pathname;
    if (path.includes('/knowledge-base/')) return 'knowledge';
    if (path.includes('/api-integration/')) return 'api-integration';
    if (path.includes('/agent-testing/')) return 'pre-testing';
    if (path.includes('/agent-fine-tuning/')) return 'fine-tuning';
    return 'definition';
  };

  // UI state
  const [activeSection, setActiveSection] = useState(getInitialSection());
  const [notification, setNotification] = useState(null);

  // Agent conversation state
  const [messages, setMessages] = useState([]);
  const [thoughtProcess, setThoughtProcess] = useState([]);

  // Handle agent configuration updates
  const handleAgentUpdate = (updatedAgent) => {
    updateAgentLocal(updatedAgent);
    clearError();
  };

  // Handle saving agent configuration
  const handleAgentSave = async (agentData) => {
    if (!agentId) return;

    setSaving(true);
    try {
      const updatedAgent = await updateAgent(agentId, agentData);
      updateAgentLocal(updatedAgent);
      
      setNotification(createNotification(
        'Agent configuration saved successfully',
        'success'
      ));
    } catch (err) {
      console.error('Error saving agent:', err);
      setError('Failed to save agent configuration');
      
      setNotification(createNotification(
        'Failed to save agent configuration',
        'error'
      ));
    } finally {
      setSaving(false);
    }
  };

  // Handle notifications
  const handleNotification = (newNotification) => {
    setNotification(newNotification);
  };

  const handleCloseNotification = () => {
    setNotification(null);
  };

  // Handle section changes with workflow navigation
  const handleSectionChange = (newSection) => {
    // Map UI sections to workflow stages
    const sectionToStageMap = {
      'definition': 'definition',
      'knowledge': 'knowledge',
      'api': 'api-integration',
      'testing': 'pre-testing',
      'fine-tuning': 'fine-tuning'
    };

    const stageId = sectionToStageMap[newSection];
    if (stageId && workflow.canAccessStage(stageId)) {
      setActiveSection(newSection);
      workflow.navigateToStage(stageId);
    }
  };

  // Handle workflow stage clicks from progress indicator
  const handleWorkflowStageClick = (stage) => {
    // Map workflow stages to UI sections or external routes
    const stageToSectionMap = {
      'definition': 'definition',
      'knowledge': 'knowledge',
      'api-integration': 'api',
      'pre-testing': 'testing',
      'fine-tuning': 'fine-tuning'
    };

    const section = stageToSectionMap[stage.id];
    if (section) {
      // Internal section within AgentEditor
      setActiveSection(section);
      workflow.navigateToStage(stage.id);
    } else {
      // External page - navigate directly
      const route = stage.route.replace(':agentId', agentId);
      navigate(route);
    }
  };

  // Handle back navigation
  const handleBackClick = () => {
    navigate('/agents');
  };

  // Show loading spinner while agent data is loading
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Render active section content
  const renderSectionContent = () => {
    switch (activeSection) {
      case 'definition':
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Sticky Header */}
            <Box sx={{ 
              position: 'sticky',
              top: 0,
              zIndex: 100,
              p: 3, 
              pb: 2,
              borderBottom: 1, 
              borderColor: 'divider',
              bgcolor: 'background.paper',
              display: 'flex',
              alignItems: 'center',
              backdropFilter: 'blur(8px)',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <IconButton 
                onClick={handleBackClick} 
                sx={{ 
                  mr: 2,
                  color: '#6366f1',
                  '&:hover': {
                    bgcolor: '#6366f115',
                    color: '#4f46e5'
                  }
                }}
              >
                <ArrowBackIcon />
              </IconButton>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {loading ? 'Loading...' : (agent?.name || 'New Agent')}
              </Typography>
            </Box>

            {/* Workflow Progress Indicator */}
            <Box sx={{ px: 3, pt: 2 }}>
              <WorkflowProgressIndicator 
                workflow={workflow}
                agentId={agentId}
                compact={true}
                onStageClick={handleWorkflowStageClick}
              />
            </Box>

            {/* Main Content */}
            <Box sx={{ 
              flex: 1,
              display: 'flex', 
              gap: 3, 
              p: 3,
              overflow: 'hidden',
              minHeight: 0
            }}>
              {/* Left Panel - Alchemist Conversation */}
              <Box sx={{ flex: 1, minHeight: 0 }}>
                <AgentConversationPanel
                  agentId={agentId}
                  messages={messages}
                  onMessagesUpdate={setMessages}
                  thoughtProcess={thoughtProcess}
                  onThoughtProcessUpdate={setThoughtProcess}
                  disabled={saving}
                />
              </Box>
              
              {/* Right Panel - Agent Configuration */}
              <Box sx={{ width: '400px', minHeight: 0 }}>
                <AgentConfigurationForm
                  agent={agent}
                  onAgentUpdate={handleAgentUpdate}
                  onSave={handleAgentSave}
                  saving={saving}
                  disabled={loading}
                />
              </Box>
            </Box>
          </Box>
        );

      case 'knowledge':
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ px: 3, pt: 2, flexShrink: 0 }}>
              <WorkflowProgressIndicator 
                workflow={workflow}
                agentId={agentId}
                compact={true}
                onStageClick={handleWorkflowStageClick}
              />
            </Box>
            <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
              <KnowledgeBaseManager
                agentId={agentId}
                onNotification={handleNotification}
                disabled={saving}
              />
            </Box>
          </Box>
        );

      case 'api':
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ px: 3, pt: 2, flexShrink: 0 }}>
              <WorkflowProgressIndicator 
                workflow={workflow}
                agentId={agentId}
                compact={true}
                onStageClick={handleWorkflowStageClick}
              />
            </Box>
            <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
              <ApiIntegrationManager
                onNotification={handleNotification}
                disabled={saving}
              />
            </Box>
          </Box>
        );

      case 'testing':
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ px: 3, pt: 2, flexShrink: 0 }}>
              <WorkflowProgressIndicator 
                workflow={workflow}
                agentId={agentId}
                compact={true}
                onStageClick={handleWorkflowStageClick}
              />
            </Box>
            <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
              <AgentTestingInterface
                agentId={agentId}
                onNotification={handleNotification}
                disabled={saving}
              />
            </Box>
          </Box>
        );

      case 'fine-tuning':
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ px: 3, pt: 2, flexShrink: 0 }}>
              <WorkflowProgressIndicator 
                workflow={workflow}
                agentId={agentId}
                compact={true}
                onStageClick={handleWorkflowStageClick}
              />
            </Box>
            <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
              <AgentFineTuningInterface
                agentId={agentId}
                onNotification={handleNotification}
                disabled={saving}
              />
            </Box>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <AgentEditorLayout error={error} loading={loading}>
      <AgentSidebarNavigation 
        activeSection={activeSection} 
        onSectionChange={handleSectionChange}
        disabled={saving}
        workflow={workflow}
      >
        {renderSectionContent()}
      </AgentSidebarNavigation>

      {/* Notification System */}
      <NotificationSystem
        notification={notification}
        onClose={handleCloseNotification}
      />
    </AgentEditorLayout>
  );
};

export default AgentEditor;