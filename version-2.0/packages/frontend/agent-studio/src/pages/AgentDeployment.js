/**
 * Agent Deployment Page
 * 
 * Standalone page for managing agent deployments
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  IconButton, 
  CircularProgress,
  Container 
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';

// Import components
import AgentDeploymentManager from '../components/AgentEditor/AgentDeployment/AgentDeploymentManager';
import NotificationSystem, { createNotification } from '../components/shared/NotificationSystem';

// Import hooks and services
import useAgentState from '../hooks/useAgentState';
import { listDeployments } from '../services';

const AgentDeployment = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  
  // Core state management
  const { agent, loading, error } = useAgentState(agentId);
  
  
  // UI state
  const [notification, setNotification] = useState(null);
  const [deployments, setDeployments] = useState([]);
  const [loadingDeployments, setLoadingDeployments] = useState(true);

  // Load deployments when agentId changes
  useEffect(() => {
    const loadDeployments = async () => {
      if (agentId) {
        try {
          setLoadingDeployments(true);
          const result = await listDeployments({ agentId });
          setDeployments(result.deployments || []);
        } catch (error) {
          console.error('Error loading deployments:', error);
          setNotification(createNotification(
            'Failed to load deployment history',
            'error'
          ));
        } finally {
          setLoadingDeployments(false);
        }
      }
    };

    loadDeployments();
  }, [agentId]);

  // Handle notifications
  const handleNotification = (newNotification) => {
    setNotification(newNotification);
  };

  const handleCloseNotification = () => {
    setNotification(null);
  };

  // Handle back navigation
  const handleBackClick = () => {
    navigate(`/agent-editor/${agentId}`);
  };


  // Show loading spinner while agent data is loading
  if (loading || loadingDeployments) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '50vh'
          }}
        >
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  // Show error if agent not found
  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h5" color="error" gutterBottom>
            Error Loading Agent
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {error}
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ 
        p: 3, 
        borderBottom: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        display: 'flex',
        alignItems: 'center',
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
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Deploy Agent: {agent?.name || 'Untitled Agent'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Deploy your agent to production with optimized performance
          </Typography>
        </Box>
      </Box>


      {/* Main Content */}
      <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
        <AgentDeploymentManager
          agentId={agentId}
          onNotification={handleNotification}
          disabled={false}
        />
      </Box>

      {/* Notification System */}
      <NotificationSystem
        notification={notification}
        onClose={handleCloseNotification}
      />
    </Box>
  );
};

export default AgentDeployment;