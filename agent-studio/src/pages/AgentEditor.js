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

// Import feature components
import AgentConversationPanel from '../components/AgentEditor/AgentConversation/AgentConversationPanel';
import AgentConfigurationForm from '../components/AgentEditor/AgentConfiguration/AgentConfigurationForm';
import KnowledgeBaseManager from '../components/AgentEditor/KnowledgeBase/KnowledgeBaseManager';
import ApiIntegrationManager from '../components/AgentEditor/ApiIntegration/ApiIntegrationManager';
import AgentTestingInterface from '../components/AgentEditor/AgentTesting/AgentTestingInterface';
import AgentFineTuningInterface from '../components/AgentEditor/AgentFineTuning/AgentFineTuningInterface';

// Import hooks and services
import useAgentState from '../hooks/useAgentState';
import { updateAgent } from '../services';

const AgentEditor = () => {
  const navigate = useNavigate();
  const { agentId } = useParams();
  const location = useLocation();
  
  // Redirect to create agent if no agentId
  React.useEffect(() => {
    if (!agentId) {
      navigate('/create-agent');
    }
  }, [agentId, navigate]);
  
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

  // Handle section changes
  const handleSectionChange = (newSection) => {
    setActiveSection(newSection);
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
            {/* Full Height Conversation - No headers */}
            <Box sx={{ 
              flex: 1,
              display: 'flex',
              overflow: 'hidden',
              minHeight: 0,
              width: '100%'
            }}>
              <AgentConversationPanel
                agentId={agentId}
                messages={messages}
                onMessagesUpdate={setMessages}
                thoughtProcess={thoughtProcess}
                onThoughtProcessUpdate={setThoughtProcess}
                disabled={saving}
                fullHeight={true}
              />
            </Box>
          </Box>
        );

      case 'knowledge':
        return (
          <KnowledgeBaseManager
            agentId={agentId}
            onNotification={handleNotification}
            disabled={saving}
          />
        );

      case 'api':
        return (
          <ApiIntegrationManager
            onNotification={handleNotification}
            disabled={saving}
          />
        );

      case 'testing':
        return (
          <AgentTestingInterface
            agentId={agentId}
            onNotification={handleNotification}
            disabled={saving}
          />
        );

      case 'fine-tuning':
        return (
          <AgentFineTuningInterface
            agentId={agentId}
            onNotification={handleNotification}
            disabled={saving}
          />
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
        onBackClick={handleBackClick}
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