/**
 * Agent Testing Interface
 * 
 * Component for testing agent functionality and tools
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Chip,
  Fade,
  InputAdornment,
  IconButton,
  Grid
} from '@mui/material';
import {
  Send as SendIcon,
  BugReport as BugReportIcon,
  Clear as ClearIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';
// Standalone agent URL for testing
const SANDBOX_CONSOLE_URL = process.env.REACT_APP_SANDBOX_CONSOLE_URL || 'https://standalone-agent-851487020021.us-central1.run.app';

const AgentTestingInterface = ({ 
  agentId, 
  onNotification,
  disabled = false 
}) => {
  const [testInput, setTestInput] = useState('');
  const [testMessages, setTestMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [testConversationId, setTestConversationId] = useState(null);
  const [creatingConversation, setCreatingConversation] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [testMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const createNewConversation = async () => {
    if (!agentId) {
      onNotification?.({
        message: 'Please save the agent first to create a conversation',
        severity: 'warning',
        timestamp: Date.now()
      });
      return;
    }
    
    setCreatingConversation(true);
    
    try {
      // Call the standalone agent API to create a new conversation
      const apiUrl = new URL('/api/agent/create_conversation', SANDBOX_CONSOLE_URL).toString();
      console.log('Making request to:', apiUrl);
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify({
          agent_id: agentId
        })
      });
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const data = await response.json();
      setTestConversationId(data.conversation_id);
      setTestMessages([]);
      
      onNotification?.({
        message: 'New conversation created successfully',
        severity: 'success',
        timestamp: Date.now()
      });
      
      return data.conversation_id;
    } catch (error) {
      console.error('Error creating conversation:', error);
      onNotification?.({
        message: `Failed to create conversation: ${error.message}`,
        severity: 'error',
        timestamp: Date.now()
      });
      return null;
    } finally {
      setCreatingConversation(false);
    }
  };

  const handleSendTestMessage = async () => {
    if (!testInput.trim() || loading) return;

    const message = testInput.trim();
    const originalInput = testInput;
    setTestInput('');
    setError('');

    // Add user message to the conversation
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date()
    };

    const updatedMessages = [...testMessages, userMessage];
    setTestMessages(updatedMessages);

    try {
      setLoading(true);

      // Create a new conversation if one doesn't exist yet
      let conversationId = testConversationId;
      if (!conversationId) {
        conversationId = await createNewConversation();
        if (!conversationId) {
          throw new Error('Unable to create conversation for testing');
        }
      }

      // Use the standalone agent API to process the message
      const apiUrl = new URL('/api/agent/process_message', SANDBOX_CONSOLE_URL).toString();
      console.log('Making request to:', apiUrl);
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify({
          conversation_id: conversationId,
          agent_id: agentId,
          message: message
        })
      });
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Test response:', result);
      
      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: result.response.content,
        timestamp: new Date(),
        metadata: result.metadata || {}
      };

      setTestMessages([...updatedMessages, assistantMessage]);

    } catch (err) {
      console.error('Error sending test message:', err);
      setError('Failed to send test message. Please try again.');
      
      // Restore the input on error
      setTestInput(originalInput);
      
      // Add error message to conversation
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your test request. Please check the agent deployment status and try again.',
        timestamp: new Date(),
        isError: true
      };

      setTestMessages([...updatedMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendTestMessage();
    }
  };

  const handleClearConversation = () => {
    setTestMessages([]);
    setTestConversationId(null);
    setError('');
  };

  const renderMessage = (message) => {
    const isUser = message.role === 'user';
    const isError = message.isError;

    return (
      <Fade in={true} key={message.id}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            mb: 2
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: 2,
              maxWidth: '80%',
              bgcolor: isUser 
                ? (theme) => theme.palette.mode === 'dark' ? '#000000' : '#ffffff'
                : isError 
                  ? (theme) => theme.palette.mode === 'dark' ? '#444444' : '#f0f0f0'
                  : (theme) => theme.palette.mode === 'dark' ? '#333333' : '#f8f9fa',
              color: isUser 
                ? (theme) => theme.palette.mode === 'dark' ? '#ffffff' : '#000000'
                : isError 
                  ? (theme) => theme.palette.mode === 'dark' ? '#ffffff' : '#000000'
                  : (theme) => theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
              borderRadius: 2,
              border: '1px solid',
              borderColor: isUser 
                ? (theme) => theme.palette.mode === 'dark' ? '#555555' : '#dddddd'
                : (theme) => theme.palette.mode === 'dark' ? '#555555' : '#dddddd'
            }}
          >
            <Typography
              variant="body1"
              sx={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                lineHeight: 1.5
              }}
            >
              {message.content}
            </Typography>
            
            <Typography
              variant="caption"
              sx={{
                mt: 1,
                display: 'block',
                opacity: 0.7,
                fontSize: '0.75rem'
              }}
            >
              {new Date(message.timestamp).toLocaleTimeString()}
            </Typography>
          </Paper>
        </Box>
      </Fade>
    );
  };

  return (
    <Box 
      sx={{ 
        height: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
        position: 'relative'
      }}
    >
      {/* Messages Area - Takes full height minus input */}
      <Box 
        sx={{ 
          flex: 1,
          overflowY: 'auto',
          px: 3,
          py: 2,
          pb: '120px', // Space for fixed input area
          minHeight: 0,
          width: '100%'
        }}
      >
        {testMessages.length === 0 ? (
          <Box 
            sx={{ 
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              color: 'text.secondary'
            }}
          >
            <BugReportIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
            <Typography variant="h6" sx={{ mb: 1 }}>
              Start testing your agent
            </Typography>
            <Typography variant="body2">
              Send test messages to see how your agent responds
            </Typography>
          </Box>
        ) : (
          <>
            {testMessages.map(renderMessage)}
            {loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    bgcolor: 'background.paper',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    <Typography variant="body2" color="text.secondary">
                      Agent is processing...
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </Box>

      {/* Error Display - Fixed above input */}
      {error && (
        <Box sx={{ 
          p: 2, 
          borderTop: 1, 
          borderColor: 'divider',
          position: 'fixed',
          bottom: '80px',
          left: { xs: 0, md: '420px' },
          right: 0,
          bgcolor: 'background.paper',
          zIndex: 999
        }}>
          <Alert severity="error" onClose={() => setError('')}>
            {error}
          </Alert>
        </Box>
      )}

      {/* Fixed Input Area at Bottom */}
      <Box sx={{ 
        p: 3,
        borderTop: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        position: 'fixed',
        bottom: 0,
        left: { xs: 0, md: '420px' }, // Account for sidebar width
        right: 0,
        zIndex: 1200, // Higher than sticky header (1100)
        boxSizing: 'border-box'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <BugReportIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
              Agent Testing
            </Typography>
            <Chip 
              label="Live Testing" 
              size="small" 
              color="primary" 
              variant="outlined" 
              sx={{ ml: 2 }}
            />
            {testConversationId && (
              <Chip 
                label={`Session: ${testConversationId.substring(0, 8)}...`}
                size="small"
                variant="outlined"
                sx={{ 
                  ml: 2,
                  fontSize: '0.7rem',
                  height: 20
                }}
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {testMessages.length > 0 && (
              <Button
                size="small"
                onClick={handleClearConversation}
                startIcon={<ClearIcon />}
                disabled={disabled}
                sx={{ textTransform: 'none' }}
              >
                Clear
              </Button>
            )}
            <Button
              variant="outlined"
              size="small"
              startIcon={creatingConversation ? <CircularProgress size={16} /> : <PsychologyIcon />}
              onClick={createNewConversation}
              disabled={disabled || creatingConversation || !agentId}
              sx={{ textTransform: 'none' }}
            >
              {creatingConversation ? 'Creating...' : 'New Session'}
            </Button>
          </Box>
        </Box>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={testInput}
          onChange={(e) => setTestInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Test your agent..."
          disabled={disabled || loading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={handleSendTestMessage}
                  disabled={disabled || loading || !testInput.trim()}
                  color="primary"
                  size="small"
                >
                  {loading ? <CircularProgress size={20} /> : <SendIcon />}
                </IconButton>
              </InputAdornment>
            )
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              bgcolor: 'background.default'
            }
          }}
        />
      </Box>
    </Box>
  );
};

export default AgentTestingInterface;