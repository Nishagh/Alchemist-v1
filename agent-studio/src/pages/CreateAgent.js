/**
 * Create Agent Page
 * 
 * First step in agent creation - collects agent name and creates agent with unique ID
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Container,
  Alert,
  CircularProgress,
  Fade,
  InputAdornment
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  ArrowForward as ArrowForwardIcon,
  SmartToy as SmartToyIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { createAgent } from '../services/agents/agentService';

const CreateAgent = () => {
  const navigate = useNavigate();
  const [agentName, setAgentName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreateAgent = async () => {
    if (!agentName.trim()) {
      setError('Please enter a name for your agent');
      return;
    }

    if (agentName.trim().length < 2) {
      setError('Agent name must be at least 2 characters long');
      return;
    }

    if (agentName.trim().length > 50) {
      setError('Agent name must be less than 50 characters');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Create agent with minimal data
      const agentData = {
        name: agentName.trim(),
        description: '',
        instructions: '',
        personality: '',
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      console.log('Creating agent with data:', agentData);
      const createdAgent = await createAgent(agentData);
      console.log('Agent created successfully:', createdAgent);

      // Navigate to agent editor with the new agent ID
      const agentId = createdAgent.id || createdAgent.agent_id;
      if (agentId) {
        navigate(`/agent-editor/${agentId}`);
      } else {
        throw new Error('No agent ID returned from server');
      }
    } catch (err) {
      console.error('Error creating agent:', err);
      setError(err.message || 'Failed to create agent. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !loading) {
      handleCreateAgent();
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8, mb: 4 }}>
      <Fade in={true}>
        <Paper 
          elevation={0}
          sx={{ 
            p: 6,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            textAlign: 'center',
            bgcolor: 'background.paper'
          }}
        >
          {/* Header */}
          <Box sx={{ mb: 4 }}>
            <Box 
              sx={{ 
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                mb: 3
              }}
            >
              <AutoAwesomeIcon sx={{ fontSize: 32 }} />
            </Box>
            
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 600,
                mb: 2,
                color: 'text.primary'
              }}
            >
              Create New Agent
            </Typography>
            
            <Typography 
              variant="body1" 
              color="text.secondary"
              sx={{ mb: 4, lineHeight: 1.6 }}
            >
              Give your AI agent a name to get started. You'll be able to configure 
              its personality, knowledge, and capabilities in the next step.
            </Typography>
          </Box>

          {/* Agent Name Input */}
          <Box sx={{ mb: 4 }}>
            <TextField
              fullWidth
              label="Agent Name"
              placeholder="e.g., Customer Support Assistant, Code Helper, Research Bot..."
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              autoFocus
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SmartToyIcon color="primary" />
                  </InputAdornment>
                )
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2
                }
              }}
            />
          </Box>

          {/* Error Display */}
          {error && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 3,
                borderRadius: 2,
                textAlign: 'left'
              }}
            >
              {error}
            </Alert>
          )}

          {/* Create Button */}
          <Button
            variant="contained"
            size="large"
            onClick={handleCreateAgent}
            disabled={loading || !agentName.trim()}
            endIcon={loading ? <CircularProgress size={20} /> : <ArrowForwardIcon />}
            sx={{
              borderRadius: 2,
              py: 1.5,
              px: 4,
              fontWeight: 600,
              minWidth: 200
            }}
          >
            {loading ? 'Creating Agent...' : 'Create Agent'}
          </Button>

          {/* Helper Text */}
          <Typography 
            variant="body2" 
            color="text.secondary" 
            sx={{ mt: 3 }}
          >
            Don't worry, you can always change the name later
          </Typography>
        </Paper>
      </Fade>
    </Container>
  );
};

export default CreateAgent;