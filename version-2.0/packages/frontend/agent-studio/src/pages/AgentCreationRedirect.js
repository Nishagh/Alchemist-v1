import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import {
  Box,
  CircularProgress,
  Typography,
  Alert,
  Container,
  Paper,
  useTheme,
  alpha
} from '@mui/material';
import { interactWithAlchemist } from '../services';
import { useAuth } from '../utils/AuthContext';

const AgentCreationRedirect = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { currentUser } = useAuth();
  const [status, setStatus] = useState('loading'); // loading, creating, error, success
  const [error, setError] = useState('');

  useEffect(() => {
    const handleAgentCreation = async () => {
      // Check if user is authenticated
      if (!currentUser) {
        navigate('/login');
        return;
      }

      try {
        // Get pending agent creation data from sessionStorage
        const pendingDataStr = sessionStorage.getItem('pendingAgentCreation');
        
        if (!pendingDataStr) {
          // No pending agent creation, redirect to agents list
          navigate('/agents');
          return;
        }

        const pendingData = JSON.parse(pendingDataStr);
        
        // Check if the data is not too old (24 hours)
        const twentyFourHours = 24 * 60 * 60 * 1000;
        if (Date.now() - pendingData.timestamp > twentyFourHours) {
          sessionStorage.removeItem('pendingAgentCreation');
          setStatus('error');
          setError('Session expired. Please try creating your agent again.');
          return;
        }

        setStatus('creating');

        // Generate a new agent ID
        const newAgentId = uuidv4();

        // Send the user input to Alchemist
        await interactWithAlchemist(pendingData.input, newAgentId);

        // Clean up the pending data
        sessionStorage.removeItem('pendingAgentCreation');

        setStatus('success');

        // Navigate to the agent editor with the new agent ID
        setTimeout(() => {
          navigate(`/agent-editor/${newAgentId}`);
        }, 1500);

      } catch (error) {
        console.error('Error creating agent:', error);
        setStatus('error');
        setError('Failed to create agent. Please try again.');
        
        // Clean up the pending data on error
        sessionStorage.removeItem('pendingAgentCreation');
      }
    };

    handleAgentCreation();
  }, [currentUser, navigate]);

  const renderContent = () => {
    switch (status) {
      case 'loading':
        return (
          <>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h5" gutterBottom>
              Preparing to create your agent...
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Please wait while we set up everything for you.
            </Typography>
          </>
        );

      case 'creating':
        return (
          <>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h5" gutterBottom>
              Creating your AI agent...
            </Typography>
            <Typography variant="body1" color="text.secondary">
              This may take a few moments. We're building something amazing!
            </Typography>
          </>
        );

      case 'success':
        return (
          <>
            <Box
              sx={{
                width: 60,
                height: 60,
                borderRadius: '50%',
                bgcolor: theme.palette.success.main,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 3
              }}
            >
              <Typography variant="h4" sx={{ color: 'white' }}>
                ✓
              </Typography>
            </Box>
            <Typography variant="h5" gutterBottom>
              Agent created successfully!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Redirecting to your new agent...
            </Typography>
          </>
        );

      case 'error':
        return (
          <>
            <Alert severity="error" sx={{ mb: 3, width: '100%' }}>
              {error}
            </Alert>
            <Typography variant="h5" gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Don't worry, you can try creating your agent again from the home page.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <button
                onClick={() => navigate('/')}
                style={{
                  padding: '12px 24px',
                  backgroundColor: theme.palette.primary.main,
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Go to Home
              </button>
              <button
                onClick={() => navigate('/agents')}
                style={{
                  padding: '12px 24px',
                  backgroundColor: 'transparent',
                  color: theme.palette.primary.main,
                  border: `2px solid ${theme.palette.primary.main}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                View My Agents
              </button>
            </Box>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.grey[50], 1)} 0%, ${alpha(theme.palette.grey[100], 1)} 100%)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={0}
          sx={{
            p: 6,
            borderRadius: 3,
            textAlign: 'center',
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
            boxShadow: '0 8px 40px rgba(0, 0, 0, 0.08)',
            background: alpha(theme.palette.background.paper, 0.9),
            backdropFilter: 'blur(10px)'
          }}
        >
          {renderContent()}
        </Paper>
      </Container>
    </Box>
  );
};

export default AgentCreationRedirect;