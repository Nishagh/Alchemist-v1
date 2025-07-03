import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  IconButton,
  Avatar,
  Chip,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Stack,
  Paper,
  CircularProgress
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Analytics as AnalyticsIcon,
  Stop as StopIcon,
  PlayArrow as PlayIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useAuth } from '../utils/AuthContext';
import { getAgent } from '../services/agents/agentService';
import { 
  getBillingInfo,
  saveBillingSession,
  sendStreamingMessageToDeployedAgent,
  createDeployedAgentConversation,
  getTestConversationTemplates,
  testAgentEndpoint
} from '../services/conversations/conversationService';
import deploymentService from '../services/deployment/deploymentService';

const AgentTesting = ({ agentId: propAgentId, embedded = false }) => {
  const { agentId: routeAgentId } = useParams();
  const agentId = propAgentId || routeAgentId;
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  // Core state
  const [agent, setAgent] = useState(null);
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  const [isDeployed, setIsDeployed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamingEnabled = true;
  const [conversationId, setConversationId] = useState(null);

  // Billing state
  const [billingInfo, setBillingInfo] = useState({
    totalMessages: 0,
    totalTokens: 0,
    estimatedCost: 0,
    sessionCost: 0,
    lastBillableAction: null
  });

  // Testing controls
  const [testingActive, setTestingActive] = useState(false);
  const [showBillingAlert, setShowBillingAlert] = useState(false);
  const [agentHealth, setAgentHealth] = useState(null);
  const [templateTests, setTemplateTests] = useState([]);

  // Load agent and deployment status
  useEffect(() => {
    const loadAgentData = async () => {
      if (!agentId || !currentUser) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        
        // Load agent details
        const agentData = await getAgent(agentId);
        if (!agentData) {
          setError('Agent not found');
          return;
        }
        
        // Check if user owns this agent
        if (agentData.userId !== currentUser.uid) {
          setError('You do not have permission to test this agent');
          return;
        }

        setAgent(agentData);

        // Check deployment status
        const deploymentsResult = await deploymentService.listDeployments({ 
          agentId: agentId,
          limit: 1 
        });
        
        const deployStatus = deploymentsResult.deployments && deploymentsResult.deployments.length > 0 
          ? deploymentsResult.deployments[0] 
          : null;
          
        setDeploymentStatus(deployStatus);
        setIsDeployed(deployStatus?.status === 'completed' || deployStatus?.status === 'deployed');

        // Load existing billing info
        const billing = await getBillingInfo(agentId);
        setBillingInfo(billing);

        // Load test templates
        const templates = getTestConversationTemplates();
        setTemplateTests(templates);

        // Test agent health if deployed
        if (deployStatus?.status === 'completed' || deployStatus?.status === 'deployed') {
          try {
            const health = await testAgentEndpoint(agentId);
            setAgentHealth(health);
          } catch (err) {
            console.warn('Health check failed:', err);
            setAgentHealth({ available: false, error: err.message });
          }
        }

        // Create conversation ID for testing
        const newConversationId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        setConversationId(newConversationId);

      } catch (err) {
        console.error('Error loading agent data:', err);
        setError('Failed to load agent data');
      } finally {
        setLoading(false);
      }
    };

    loadAgentData();
  }, [agentId, currentUser]);

  // Start testing session
  const startTesting = useCallback(async () => {
    if (!isDeployed) {
      setError('Agent must be deployed before testing');
      return;
    }

    try {
      setTestingActive(true);
      setShowBillingAlert(true);

      // Create a new conversation with the deployed agent
      const newConversationId = await createDeployedAgentConversation(agentId);
      setConversationId(newConversationId);

      // Initialize conversation with welcome message
      const welcomeMessage = {
        id: `msg-${Date.now()}`,
        type: 'ai',
        content: `🤖 Hello! I'm ${agent?.name || 'your AI agent'}. I'm ready to help you.`,
        timestamp: new Date().toISOString(),
        tokens: { prompt: 0, completion: 25, total: 25 },
        cost: 0.001
      };

      setMessages([welcomeMessage]);
      
      // Track billing for all interactions
      setBillingInfo(prev => ({
        ...prev,
        sessionCost: prev.sessionCost + 0.001,
        totalTokens: prev.totalTokens + 25,
        lastBillableAction: new Date().toISOString()
      }));

    } catch (err) {
      console.error('Error starting testing session:', err);
      setError(`Failed to start testing session: ${err.message}`);
      setTestingActive(false);
    }

  }, [isDeployed, agent, agentId]);

  // Stop testing session
  const stopTesting = useCallback(async () => {
    setTestingActive(false);
    setIsStreaming(false);
    
    // Save final billing information
    if (conversationId && billingInfo.sessionCost > 0) {
      try {
        await saveBillingSession({
          agentId,
          conversationId,
          messages: messages.length,
          totalTokens: billingInfo.totalTokens,
          totalCost: billingInfo.sessionCost,
          endedAt: new Date().toISOString()
        });
      } catch (err) {
        console.error('Error saving billing session:', err);
      }
    }

    // Reset session state
    setBillingInfo(prev => ({ ...prev, sessionCost: 0 }));
    setMessages([]);
    setCurrentMessage('');
  }, [agentId, conversationId, billingInfo, messages]);

  // Send message to agent
  const sendMessage = useCallback(async () => {
    if (!currentMessage.trim() || isSending || !testingActive) return;

    const userMessage = {
      id: `msg-${Date.now()}`,
      type: 'user',
      content: currentMessage.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsSending(true);

    try {
      let tokens = { prompt: 0, completion: 0, total: 0 };
      let cost = 0;

      // Always use streaming for deployed agents
      setIsStreaming(true);
      
      const streamingMessage = {
        id: `msg-${Date.now() + 1}`,
        type: 'ai',
        content: '',
        timestamp: new Date().toISOString(),
        streaming: true
      };

      setMessages(prev => [...prev, streamingMessage]);

      await sendStreamingMessageToDeployedAgent({
        agentId,
        conversationId,
        message: currentMessage.trim(),
        onChunk: (chunk) => {
          setMessages(prev => prev.map(msg => 
            msg.id === streamingMessage.id 
              ? { ...msg, content: msg.content + chunk }
              : msg
          ));
        },
        onComplete: (finalTokens, finalCost) => {
          tokens = finalTokens;
          cost = finalCost;
          setMessages(prev => prev.map(msg => 
            msg.id === streamingMessage.id 
              ? { ...msg, streaming: false, tokens, cost }
              : msg
          ));
          setIsStreaming(false);
        }
      });

      // Update billing info
      setBillingInfo(prev => ({
        ...prev,
        totalMessages: prev.totalMessages + 1,
        totalTokens: prev.totalTokens + tokens.total,
        sessionCost: prev.sessionCost + cost,
        estimatedCost: prev.estimatedCost + cost,
        lastBillableAction: new Date().toISOString()
      }));

    } catch (err) {
      console.error('Error sending message:', err);
      
      let errorContent = 'Unknown error occurred';
      
      if (err.message) {
        errorContent = err.message;
      } else if (err.response?.data?.detail) {
        errorContent = err.response.data.detail;
      } else if (err.response?.statusText) {
        errorContent = `HTTP Error ${err.response.status}: ${err.response.statusText}`;
      } else if (typeof err === 'string') {
        errorContent = err;
      }
      
      const errorMessage = {
        id: `msg-${Date.now() + 1}`,
        type: 'error',
        content: `❌ Error: ${errorContent}`,
        timestamp: new Date().toISOString(),
        isDebugError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
      setIsStreaming(false);
    }
  }, [currentMessage, isSending, testingActive, streamingEnabled, agentId, conversationId]);

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Loading state
  if (loading) {
    return (
      <Box sx={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button 
          variant="outlined" 
          onClick={() => navigate('/agents')}
          color="primary"
        >
          Back to Agents
        </Button>
      </Box>
    );
  }

  // Check for authentication
  if (!loading && !currentUser) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          Please log in to view agent testing
        </Alert>
        <Button 
          variant="outlined" 
          onClick={() => navigate('/login')}
          color="primary"
        >
          Go to Login
        </Button>
      </Box>
    );
  }

  // Check for agent after loading is complete
  if (!loading && !agent) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Agent not found
        </Alert>
        <Button 
          variant="outlined" 
          onClick={() => navigate('/agents')}
          color="primary"
        >
          Back to Agents
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header Section */}
      {!embedded && (
        <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Test Agent: {agent?.name}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {isDeployed 
              ? "Test your deployed agent. All interactions will be tracked and billed."
              : "Deploy your agent first to begin testing."
            }
          </Typography>
        </Box>
      )}

      {/* Status Bar */}
      <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
        <Grid container spacing={3}>
          {/* Deployment Status */}
          <Grid item xs={12} md={4}>
            <Card elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  {isDeployed ? (
                    <CheckIcon color="success" sx={{ mr: 1 }} />
                  ) : (
                    <ErrorIcon color="error" sx={{ mr: 1 }} />
                  )}
                  <Typography variant="h6">Deployment</Typography>
                </Box>
                <Chip 
                  label={isDeployed ? 'Deployed' : 'Not Deployed'} 
                  color={isDeployed ? 'success' : 'error'}
                  size="small"
                />
                {agentHealth && (
                  <Typography variant="caption" display="block" sx={{ mt: 1, color: agentHealth.available ? 'success.main' : 'error.main' }}>
                    {agentHealth.available ? '✓ Health check passed' : `⚠ ${agentHealth.error}`}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Billing Summary */}
          <Grid item xs={12} md={8}>
            <Card elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Billing Summary</Typography>
                <Grid container spacing={3}>
                  <Grid item xs={3}>
                    <Typography variant="body2" color="text.secondary">Session Cost</Typography>
                    <Typography variant="h6" color="primary">
                      ₹{billingInfo.sessionCost.toFixed(4)}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="body2" color="text.secondary">Total Cost</Typography>
                    <Typography variant="h6" color="warning.main">
                      ₹{billingInfo.estimatedCost.toFixed(4)}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="body2" color="text.secondary">Messages</Typography>
                    <Typography variant="h6">
                      {messages.filter(m => m.type !== 'error').length}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="body2" color="text.secondary">Tokens</Typography>
                    <Typography variant="h6">
                      {billingInfo.totalTokens.toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>
                <Button
                  size="small"
                  startIcon={<AnalyticsIcon />}
                  sx={{ mt: 2 }}
                  onClick={() => navigate(`/agent-analytics/${agentId}`)}
                >
                  View Analytics
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Quick Tests */}
      {isDeployed && templateTests.length > 0 && (
        <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6" gutterBottom>Quick Tests</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {templateTests.map((template) => (
              <Button
                key={template.id}
                variant="outlined"
                size="small"
                onClick={() => {
                  if (!testingActive) {
                    startTesting();
                  }
                  setCurrentMessage(template.messages[0]);
                }}
                disabled={!isDeployed}
              >
                {template.name}
              </Button>
            ))}
          </Box>
        </Box>
      )}

      {/* Chat Interface */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 3 }}>
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Chat Header */}
          <CardContent sx={{ pb: 1, borderBottom: 1, borderColor: 'divider' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">Test Conversation</Typography>
              <Box display="flex" gap={2} alignItems="center">
                <Typography variant="body2" color="text.secondary">
                  🚀 Streaming Response Mode
                </Typography>
                {testingActive ? (
                  <Button
                    variant="contained"
                    startIcon={<StopIcon />}
                    onClick={stopTesting}
                    color="error"
                  >
                    Stop Testing
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={startTesting}
                    disabled={!isDeployed}
                    color="success"
                  >
                    Start Testing
                  </Button>
                )}
              </Box>
            </Box>
          </CardContent>

          {/* Messages Container */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
            {!testingActive ? (
              <Box 
                display="flex" 
                justifyContent="center" 
                alignItems="center" 
                height="100%"
                flexDirection="column"
              >
                <BotIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Ready to Test Your Agent
                </Typography>
                <Typography variant="body2" color="text.secondary" textAlign="center">
                  Click "Start Testing" to begin a conversation session.
                </Typography>
              </Box>
            ) : (
              <Stack spacing={2}>
                {messages.map((message) => (
                  <Box
                    key={message.id}
                    sx={{
                      display: 'flex',
                      justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                      mb: 1
                    }}
                  >
                    <Paper
                      elevation={1}
                      sx={{
                        maxWidth: '70%',
                        p: 2,
                        backgroundColor: 
                          message.type === 'user' ? 'primary.main' : 
                          message.type === 'error' ? (message.isDebugError ? 'error.main' : 'error.light') : 'grey.100',
                        color: 
                          message.type === 'user' ? 'white' : 
                          message.type === 'error' ? 'white' : 'text.primary',
                        borderRadius: 2
                      }}
                    >
                      <Box display="flex" alignItems="center" mb={1}>
                        <Avatar
                          sx={{
                            width: 24,
                            height: 24,
                            mr: 1,
                            backgroundColor: message.type === 'user' ? 'white' : 'primary.main'
                          }}
                        >
                          {message.type === 'user' ? (
                            <PersonIcon sx={{ fontSize: 16, color: 'primary.main' }} />
                          ) : (
                            <BotIcon sx={{ fontSize: 16, color: 'white' }} />
                          )}
                        </Avatar>
                        <Typography variant="caption">
                          {message.type === 'user' ? 'You' : agent?.name}
                        </Typography>
                        {message.streaming && (
                          <CircularProgress size={12} sx={{ ml: 1 }} />
                        )}
                      </Box>
                      
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Typography>
                      
                      {message.isDebugError && (
                        <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8, fontStyle: 'italic' }}>
                          💡 Debug Error - Check console for more details
                        </Typography>
                      )}
                      
                      {message.tokens && (
                        <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                          <Typography variant="caption" sx={{ opacity: 0.7 }}>
                            Tokens: {message.tokens.total} • Cost: ₹{message.cost?.toFixed(4) || '0.0000'}
                          </Typography>
                        </Box>
                      )}
                      
                      <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.7 }}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </Typography>
                    </Paper>
                  </Box>
                ))}
                
                {isStreaming && (
                  <Box display="flex" justifyContent="flex-start">
                    <Box display="flex" alignItems="center" sx={{ ml: 2 }}>
                      <CircularProgress size={16} sx={{ mr: 1 }} />
                      <Typography variant="caption" color="text.secondary">
                        {agent?.name} is typing...
                      </Typography>
                    </Box>
                  </Box>
                )}
              </Stack>
            )}
          </Box>

          {/* Input Area */}
          {testingActive && (
            <Box sx={{ p: 3, borderTop: 1, borderColor: 'divider' }}>
              <Box display="flex" gap={1}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  placeholder="Type your message..."
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isSending || isStreaming}
                  size="small"
                />
                <IconButton
                  onClick={sendMessage}
                  disabled={!currentMessage.trim() || isSending || isStreaming}
                  color="primary"
                  sx={{ alignSelf: 'flex-end' }}
                >
                  {isSending || isStreaming ? (
                    <CircularProgress size={24} />
                  ) : (
                    <SendIcon />
                  )}
                </IconButton>
              </Box>
            </Box>
          )}
        </Card>
      </Box>

      {/* Billing Warning Dialog */}
      <Dialog open={showBillingAlert} onClose={() => setShowBillingAlert(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <WarningIcon color="warning" sx={{ mr: 1 }} />
            Start Testing Session
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            You are about to start a testing session. All interactions with your deployed agent will be charged according to your current pricing plan.
          </Typography>
          <Typography gutterBottom color="text.secondary">
            • Each message will incur token usage charges
            • Costs are calculated in real-time
            • All conversations are logged for billing purposes
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowBillingAlert(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={() => {
              setShowBillingAlert(false);
            }}
          >
            Start Testing
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Notifications */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentTesting;