/**
 * Agent Editor (Refactored with Sidebar Navigation)
 * 
 * Main agent editor page using the new sidebar navigation architecture
 */
import React, { useState, useEffect } from 'react';
import { CircularProgress, Box, Typography, IconButton } from '@mui/material';
import { useNavigate } from 'react-router-dom';
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
import AgentDeploymentManager from '../components/AgentEditor/AgentDeployment/AgentDeploymentManager';
import AgentAnalyticsManager from '../components/AgentEditor/AgentAnalytics/AgentAnalyticsManager';
import AgentIntegrationManager from '../components/AgentEditor/AgentIntegration/AgentIntegrationManager';

// Import hooks and services
import useAgentState from '../hooks/useAgentState';
import { updateAgent, listDeployments } from '../services';

const AgentEditor = () => {
  const navigate = useNavigate();
  
  // Core state management
  const { 
    agent, 
    agentId, 
    loading, 
    error, 
    saving, 
    updateAgentLocal, 
    setSaving, 
    setError, 
    clearError 
  } = useAgentState();

  // UI state
  const [activeSection, setActiveSection] = useState('definition');
  const [notification, setNotification] = useState(null);

  // Agent conversation state
  const [messages, setMessages] = useState([]);
  const [thoughtProcess, setThoughtProcess] = useState([]);

  // Deployments state
  const [deployments, setDeployments] = useState([]);

  // Load deployments when agentId changes
  useEffect(() => {
    const loadDeployments = async () => {
      if (agentId) {
        try {
          const result = await listDeployments({ agentId });
          setDeployments(result.deployments || []);
        } catch (error) {
          console.error('Error loading deployments:', error);
        }
      }
    };

    loadDeployments();
  }, [agentId]);

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
              <IconButton onClick={handleBackClick} sx={{ mr: 2 }}>
                <ArrowBackIcon />
              </IconButton>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {loading ? 'Loading...' : (agent?.name || 'New Agent')}
              </Typography>
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

      case 'deployment':
        return (
          <AgentDeploymentManager
            agentId={agentId}
            onNotification={handleNotification}
            disabled={saving}
          />
        );

      case 'integration':
      case 'whatsapp':
      case 'website':
        return (
          <AgentIntegrationManager
            deployments={deployments}
            onNotification={handleNotification}
            disabled={saving}
            activeSection={activeSection}
          />
        );

      case 'analytics':
        return (
          <AgentAnalyticsManager
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
        deployments={deployments}
        disabled={saving}
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