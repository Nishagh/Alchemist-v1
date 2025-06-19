import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Container,
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
  CircularProgress,
  FormControl,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Analytics as AnalyticsIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
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
  sendMessageToDeployedAgent,
  sendStreamingMessageToDeployedAgent
} from '../services/conversations/conversationService';
import deploymentService from '../services/deployment/deploymentService';

const AgentTesting = () => {
  const { agentId } = useParams();
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
  const [streamingEnabled, setStreamingEnabled] = useState(true);
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
  const [testMode, setTestMode] = useState('production'); // 'development' or 'production'

  // Load agent and deployment status
  useEffect(() => {
    const loadAgentData = async () => {
      if (!agentId || !currentUser) return;

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
        const deployStatus = await deploymentService.getDeploymentStatus(agentId);
        setDeploymentStatus(deployStatus);
        setIsDeployed(deployStatus?.status === 'deployed');

        // Load existing billing info
        const billing = await getBillingInfo(agentId);
        setBillingInfo(billing);

        // Create new conversation for testing
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

    setTestingActive(true);
    
    // Show billing warning for production mode
    if (testMode === 'production') {
      setShowBillingAlert(true);
    }

    // Initialize conversation
    const welcomeMessage = {
      id: `msg-${Date.now()}`,
      type: 'ai',
      content: `🤖 Hello! I'm ${agent?.name || 'your AI agent'}. I'm ready to help you. This is a production test session - billing will apply for all interactions.`,
      timestamp: new Date().toISOString(),
      tokens: { prompt: 0, completion: 25, total: 25 },
      cost: 0.001
    };

    setMessages([welcomeMessage]);
    
    // Track billing
    setBillingInfo(prev => ({
      ...prev,
      sessionCost: prev.sessionCost + 0.001,
      totalTokens: prev.totalTokens + 25,
      lastBillableAction: new Date().toISOString()
    }));

  }, [isDeployed, testMode, agent]);

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
          testMode,
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
  }, [agentId, conversationId, billingInfo, messages, testMode]);

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
      let response;
      let tokens = { prompt: 0, completion: 0, total: 0 };
      let cost = 0;

      if (streamingEnabled) {
        // Streaming response
        setIsStreaming(true);
        
        const streamingMessage = {
          id: `msg-${Date.now() + 1}`,
          type: 'ai',
          content: '',
          timestamp: new Date().toISOString(),
          streaming: true
        };

        setMessages(prev => [...prev, streamingMessage]);

        response = await sendStreamingMessageToDeployedAgent({
          agentId,
          conversationId,
          message: currentMessage.trim(),
          testMode,
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

      } else {
        // Regular response
        response = await sendMessageToDeployedAgent({
          agentId,
          conversationId,
          message: currentMessage.trim(),
          testMode
        });

        tokens = response.tokens || { prompt: 50, completion: 100, total: 150 };
        cost = response.cost || 0.005;

        const aiMessage = {
          id: `msg-${Date.now() + 1}`,
          type: 'ai',
          content: response.content || response.response,
          timestamp: new Date().toISOString(),
          tokens,
          cost
        };

        setMessages(prev => [...prev, aiMessage]);
      }

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
      const errorMessage = {
        id: `msg-${Date.now() + 1}`,
        type: 'error',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
      setIsStreaming(false);
    }
  }, [currentMessage, isSending, testingActive, streamingEnabled, agentId, conversationId, testMode]);

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
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="outlined" onClick={() => navigate('/agents')}>
          Back to Agents
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Test Agent: {agent?.name}
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Test your deployed agent and monitor usage costs in real-time
        </Typography>
        
        {/* Status Cards */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          {/* Deployment Status */}
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%' }}>
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
                {deploymentStatus?.url && (
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {deploymentStatus.url}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Test Mode */}
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Test Mode</Typography>
                <FormControl fullWidth size="small">
                  <Select
                    value={testMode}
                    onChange={(e) => setTestMode(e.target.value)}
                    disabled={testingActive}
                  >
                    <MenuItem value="development">Development (Free)</MenuItem>
                    <MenuItem value="production">Production (Billable)</MenuItem>
                  </Select>
                </FormControl>
                {testMode === 'production' && (
                  <Typography variant="caption" display="block" sx={{ mt: 1, color: 'warning.main' }}>
                    ⚠️ Billing applies
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Session Stats */}
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Session Stats</Typography>
                <Typography variant="body2">
                  Messages: {messages.filter(m => m.type !== 'error').length}
                </Typography>
                <Typography variant="body2">
                  Tokens: {billingInfo.totalTokens.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="primary">
                  Cost: ${billingInfo.sessionCost.toFixed(4)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Total Billing */}
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Total Billing</Typography>
                <Typography variant="body2">
                  Total Messages: {billingInfo.totalMessages}
                </Typography>
                <Typography variant="body2">
                  Total Cost: ${billingInfo.estimatedCost.toFixed(4)}
                </Typography>
                <Button
                  size="small"
                  startIcon={<AnalyticsIcon />}
                  sx={{ mt: 1 }}
                  onClick={() => navigate(`/agent-analytics/${agentId}`)}
                >
                  View Analytics
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Main Testing Interface */}
      <Grid container spacing={3}>
        {/* Chat Interface */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ pb: 1 }}>
              <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
                <Typography variant="h6">Test Conversation</Typography>
                <Box display="flex" gap={1}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={streamingEnabled}
                        onChange={(e) => setStreamingEnabled(e.target.checked)}
                        disabled={testingActive}
                      />
                    }
                    label="Streaming"
                    disabled={testingActive}
                  />
                  {testingActive ? (
                    <Button
                      variant="contained"
                      color="error"
                      startIcon={<StopIcon />}
                      onClick={stopTesting}
                    >
                      Stop Testing
                    </Button>
                  ) : (
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<PlayIcon />}
                      onClick={startTesting}
                      disabled={!isDeployed}
                    >
                      Start Testing
                    </Button>
                  )}
                </Box>
              </Box>
            </CardContent>

            {/* Messages Container */}
            <Box sx={{ flexGrow: 1, overflow: 'auto', px: 2, pb: 2 }}>
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
                    {testMode === 'production' && (
                      <Box component="span" sx={{ color: 'warning.main', display: 'block', mt: 1 }}>
                        ⚠️ Production mode: All interactions will be billed
                      </Box>
                    )}
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
                            message.type === 'error' ? 'error.light' : 'grey.100',
                          color: message.type === 'user' ? 'white' : 'text.primary',
                          borderRadius: 2,
                          position: 'relative'
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
                        
                        {message.tokens && testMode === 'production' && (
                          <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                            <Typography variant="caption" sx={{ opacity: 0.7 }}>
                              Tokens: {message.tokens.total} • Cost: ${message.cost?.toFixed(4) || '0.0000'}
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
              <Box sx={{ p: 2, borderTop: '1px solid rgba(0,0,0,0.12)' }}>
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
                    color="primary"
                    onClick={sendMessage}
                    disabled={!currentMessage.trim() || isSending || isStreaming}
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
        </Grid>

        {/* Side Panel */}
        <Grid item xs={12} lg={4}>
          <Stack spacing={3}>
            {/* Real-time Billing */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Real-time Billing
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Session Cost</Typography>
                    <Typography variant="h5" color="primary">
                      ${billingInfo.sessionCost.toFixed(4)}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">Session Tokens</Typography>
                    <Typography variant="h6">
                      {billingInfo.totalTokens.toLocaleString()}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">Messages Sent</Typography>
                    <Typography variant="h6">
                      {messages.filter(m => m.type !== 'error').length}
                    </Typography>
                  </Box>
                  
                  {billingInfo.lastBillableAction && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">Last Activity</Typography>
                      <Typography variant="body2">
                        {new Date(billingInfo.lastBillableAction).toLocaleTimeString()}
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>

            {/* Agent Info */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Agent Information</Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Stack spacing={1}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Model</Typography>
                    <Typography variant="body2">{agent?.model || 'gpt-4'}</Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">Version</Typography>
                    <Typography variant="body2">{deploymentStatus?.version || '1.0.0'}</Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">Last Deployed</Typography>
                    <Typography variant="body2">
                      {deploymentStatus?.deployedAt 
                        ? new Date(deploymentStatus.deployedAt).toLocaleDateString()
                        : 'Not deployed'
                      }
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">Status</Typography>
                    <Chip 
                      label={deploymentStatus?.status || 'unknown'}
                      color={deploymentStatus?.status === 'deployed' ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Quick Actions</Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Stack spacing={2}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<AnalyticsIcon />}
                    onClick={() => navigate(`/agent-analytics/${agentId}`)}
                  >
                    View Analytics
                  </Button>
                  
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={() => {
                      // Download conversation log
                      const data = messages.map(m => ({
                        timestamp: m.timestamp,
                        type: m.type,
                        content: m.content,
                        tokens: m.tokens,
                        cost: m.cost
                      }));
                      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `agent-test-${agentId}-${Date.now()}.json`;
                      a.click();
                    }}
                    disabled={messages.length === 0}
                  >
                    Export Conversation
                  </Button>
                  
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<SettingsIcon />}
                    onClick={() => navigate(`/agent-editor/${agentId}`)}
                  >
                    Edit Agent
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>

      {/* Billing Warning Dialog */}
      <Dialog open={showBillingAlert} onClose={() => setShowBillingAlert(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <WarningIcon color="warning" sx={{ mr: 1 }} />
            Production Testing - Billing Active
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            You are about to start a production test session. All interactions with your agent will be billed according to your current pricing plan.
          </Typography>
          <Typography gutterBottom color="text.secondary">
            • Each message will incur token usage charges
            • Costs are calculated in real-time
            • All conversations are logged for billing purposes
          </Typography>
          <Typography variant="body2" color="warning.main">
            Switch to Development mode for free testing without billing.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowBillingAlert(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            color="warning"
            onClick={() => {
              setShowBillingAlert(false);
              // Continue with testing
            }}
          >
            Continue with Billing
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
    </Container>
  );
};

export default AgentTesting;