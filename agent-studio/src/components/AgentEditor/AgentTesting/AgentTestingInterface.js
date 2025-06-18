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
const user_agent_url = process.env.REACT_APP_USER_AGENT_URL || 'https://standalone-agent-851487020021.us-central1.run.app';

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
      const apiUrl = new URL('/api/agent/create_conversation', user_agent_url).toString();
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
      const apiUrl = new URL('/api/agent/process_message', user_agent_url).toString();
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
            elevation={1}
            sx={{
              p: 2,
              maxWidth: '80%',
              bgcolor: isUser 
                ? 'primary.main' 
                : isError 
                  ? 'error.light' 
                  : 'background.paper',
              color: isUser 
                ? 'primary.contrastText' 
                : isError 
                  ? 'error.contrastText' 
                  : 'text.primary',
              borderRadius: 2,
              border: isUser ? 'none' : '1px solid',
              borderColor: isUser ? 'transparent' : 'divider'
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
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
              <Typography
                variant="caption"
                sx={{
                  opacity: 0.7,
                  fontSize: '0.75rem'
                }}
              >
                {new Date(message.timestamp).toLocaleTimeString()}
              </Typography>
              
              {message.metadata && Object.keys(message.metadata).length > 0 && (
                <Chip 
                  label="Info" 
                  size="small" 
                  variant="outlined"
                  sx={{ ml: 1, opacity: 0.7 }}
                />
              )}
            </Box>
          </Paper>
        </Box>
      </Fade>
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Sticky Header */}
      <Box sx={{ 
        position: 'sticky',
        top: 0,
        zIndex: 100,
        p: 3,
        borderBottom: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        backdropFilter: 'blur(8px)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <BugReportIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
              Agent Testing
            </Typography>
            <Chip 
              label="Live Testing" 
              size="small" 
              color="primary" 
              variant="outlined" 
              sx={{ ml: 2 }}
            />
          </Box>
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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Test your agent with real-world scenarios using the standalone agent API
          </Typography>
          {testConversationId && (
            <Chip 
              label={`Session: ${testConversationId.substring(0, 8)}...`}
              size="small"
              variant="outlined"
              sx={{ 
                fontSize: '0.7rem',
                height: 20
              }}
            />
          )}
        </Box>
      </Box>

      {/* Scrollable Content */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
        {/* Main Testing Interface */}
        <Grid container spacing={3}>
        {/* Test Conversation */}
        <Grid item xs={12} md={8}>
          <Paper 
            elevation={0} 
            sx={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 2,
              overflow: 'hidden'
            }}
          >
            {/* Chat Header */}
            <Box sx={{ p: 3, bgcolor: 'background.default' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <PsychologyIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    Test Conversation
                  </Typography>
                  <Chip 
                    label="Testing Mode" 
                    size="small" 
                    color="warning" 
                    variant="outlined" 
                    sx={{ ml: 2 }}
                  />
                </Box>
                
                {testMessages.length > 0 && (
                  <Button
                    size="small"
                    onClick={handleClearConversation}
                    startIcon={<ClearIcon />}
                    disabled={disabled}
                  >
                    Clear
                  </Button>
                )}
              </Box>
            </Box>

            <Divider />

            {/* Messages Area */}
            <Box 
              sx={{ 
                flex: 1,
                p: 3,
                overflowY: 'auto',
                minHeight: 300,
                maxHeight: 500
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

            {/* Error Display */}
            {error && (
              <>
                <Divider />
                <Box sx={{ p: 2 }}>
                  <Alert severity="error" onClose={() => setError('')}>
                    {error}
                  </Alert>
                </Box>
              </>
            )}

            {/* Input Area */}
            <Divider />
            <Box sx={{ p: 3 }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter test message for your agent (using standalone agent API)..."
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
                    borderRadius: 2
                  }
                }}
              />
            </Box>
          </Paper>
        </Grid>

        {/* Test Controls and Info */}
        <Grid item xs={12} md={4}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 3,
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 2,
              height: 'fit-content'
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
              Testing Information
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              Testing uses the standalone agent API ({user_agent_url}). Test interactions are isolated and won't affect production data.
            </Alert>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 1 }}>
                  Test Statistics
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Messages sent: {testMessages.filter(m => m.role === 'user').length}
                </Typography>
                <br />
                <Typography variant="caption" color="text.secondary">
                  Responses received: {testMessages.filter(m => m.role === 'assistant' && !m.isError).length}
                </Typography>
              </Box>

              <Divider />

              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 1 }}>
                  Quick Test Actions
                </Typography>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => setTestInput('Hello! Can you help me with a task?')}
                  disabled={disabled || loading}
                  sx={{ mb: 1 }}
                >
                  Test Basic Response
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => setTestInput('What tools and capabilities do you have available?')}
                  disabled={disabled || loading}
                >
                  Test Capabilities
                </Button>
              </Box>
            </Box>
          </Paper>
        </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default AgentTestingInterface;