/**
 * Conversational Fine-tuning Interface
 * 
 * Chat-like interface where AI generates queries and user provides responses
 * Automatic training is triggered based on conversation data
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Paper,
  Avatar,
  Divider,
  CircularProgress,
  Tooltip,
  Badge,
  Stack,
  Chip,
  Alert,
  LinearProgress,
  IconButton,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  AutoAwesome as AutoIcon,
  TrendingUp as ProgressIcon,
  CheckCircle as CompleteIcon
} from '@mui/icons-material';

// Import services
import {
  generateQueries,
  analyzeAgentContext,
  getQueryCategories,
  getQueryDifficulties,
  startConversationTraining,
  generateAndRespond,
  addTrainingPair,
  getConversationSession
} from '../../../services';

const ConversationalFineTuning = ({ 
  agentId, 
  onNotification, 
  disabled = false 
}) => {
  const messagesEndRef = useRef(null);
  const responseInputRef = useRef(null);
  
  // Conversation state
  const [sessionId, setSessionId] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [isActive, setIsActive] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(null);
  const [userResponse, setUserResponse] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  
  // Training state
  const [trainingPairs, setTrainingPairs] = useState([]);
  const [autoTrainingEnabled, setAutoTrainingEnabled] = useState(true);
  const [minPairsForTraining, setMinPairsForTraining] = useState(10);
  const [trainingTriggered, setTrainingTriggered] = useState(false);
  
  // Settings
  const [difficulty, setDifficulty] = useState('mixed');
  const [categories, setCategories] = useState([]);
  const [availableCategories, setAvailableCategories] = useState([]);
  const [availableDifficulties, setAvailableDifficulties] = useState([]);
  
  // UI state
  const [settingsMenuAnchor, setSettingsMenuAnchor] = useState(null);
  const [showStats, setShowStats] = useState(false);
  
  // Agent context
  const [agentContext, setAgentContext] = useState({
    agent_id: agentId,
    domain: "customer support",
    business_type: "software company",
    target_audience: "business users",
    tone: "professional"
  });

  // Initialize data
  useEffect(() => {
    loadAvailableOptions();
    if (agentId) {
      analyzeAgent();
    }
  }, [agentId]);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  // Focus response input when query is generated
  useEffect(() => {
    if (currentQuery && responseInputRef.current) {
      responseInputRef.current.focus();
    }
  }, [currentQuery]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadAvailableOptions = async () => {
    try {
      const [cats, diffs] = await Promise.all([
        getQueryCategories(),
        getQueryDifficulties()
      ]);
      setAvailableCategories(cats);
      setAvailableDifficulties(diffs);
    } catch (error) {
      console.error('Failed to load options:', error);
    }
  };

  const analyzeAgent = async () => {
    try {
      const analysis = await analyzeAgentContext(agentId);
      if (analysis && analysis.context) {
        setAgentContext(prev => ({
          ...prev,
          domain: analysis.context.domain || prev.domain,
          business_type: analysis.context.business_type || prev.business_type,
          target_audience: analysis.context.target_audience || prev.target_audience,
          tone: analysis.context.tone || prev.tone
        }));
      }
    } catch (error) {
      console.error('Failed to analyze agent:', error);
    }
  };

  const startConversation = async () => {
    try {
      setIsActive(true);
      setConversation([]);
      setTrainingPairs([]);
      setTrainingTriggered(false);
      
      // Create conversation session via backend
      const autoConfig = {
        agent_id: agentId,
        min_pairs_for_training: minPairsForTraining,
        auto_trigger_enabled: autoTrainingEnabled,
        training_frequency: 'on_threshold'
      };
      
      const session = await startConversationTraining(agentId, autoConfig);
      setSessionId(session.session_id);
      
      // Add welcome message
      addMessage('system', 'Welcome to conversational fine-tuning! I\'ll generate realistic user queries for your agent. Please provide the ideal responses you want your agent to give.', {
        timestamp: new Date(),
        type: 'welcome'
      });
      
      // Add loading message
      setTimeout(() => {
        if (isActive) {
          addMessage('system', '🤖 Generating your first user query...', {
            timestamp: new Date(),
            type: 'loading'
          });
        }
      }, 1000);
      
      // Generate first query
      setTimeout(generateNextQuery, 2000);
      
      onNotification?.({
        type: 'success',
        message: 'Conversational training session started!'
      });
      
    } catch (error) {
      console.error('Failed to start conversation:', error);
      onNotification?.({
        type: 'error',
        message: 'Failed to start training session'
      });
    }
  };

  const stopConversation = () => {
    setIsActive(false);
    setCurrentQuery(null);
    setUserResponse('');
    
    addMessage('system', `Training session completed! Generated ${trainingPairs.length} training pairs.${trainingTriggered ? ' Automatic training has been triggered.' : ''}`, {
      timestamp: new Date(),
      type: 'completion',
      stats: {
        pairs: trainingPairs.length,
        autoTraining: trainingTriggered
      }
    });
    
    onNotification?.({
      type: 'info',
      message: `Session completed with ${trainingPairs.length} training pairs`
    });
  };

  const generateNextQuery = async () => {
    if (!isActive || !sessionId) return;
    
    setIsGenerating(true);
    setCurrentQuery(null);
    
    // Add thinking message
    addMessage('assistant', 'Thinking of a realistic user scenario...', {
      timestamp: new Date(),
      type: 'thinking'
    });
    
    try {
      const queryRequest = {
        agent_context: agentContext,
        query_settings: {
          difficulty: difficulty,
          count: 1,
          categories: categories.length > 0 ? categories : [],
          avoid_repetition: true,
          include_context: true
        }
      };
      
      const response = await generateAndRespond(sessionId, queryRequest);
      
      if (response && response.generated_query) {
        const query = response.generated_query;
        
        // Remove thinking and loading messages
        setConversation(prev => prev.filter(msg => 
          msg.metadata?.type !== 'thinking' && 
          msg.metadata?.type !== 'loading'
        ));
        
        // Add generated query
        addMessage('user', query.query, {
          timestamp: new Date(),
          type: 'generated_query',
          difficulty: query.difficulty,
          category: query.category,
          context: query.context,
          metadata: query.metadata
        });
        
        setCurrentQuery(query);
        
      } else {
        throw new Error('No query generated');
      }
      
    } catch (error) {
      console.error('Query generation failed:', error);
      
      // Remove thinking and loading messages
      setConversation(prev => prev.filter(msg => 
        msg.metadata?.type !== 'thinking' && 
        msg.metadata?.type !== 'loading'
      ));
      
      // Show detailed error message to user
      const errorMessage = error.message.includes('Failed to fetch') 
        ? '🌐 Network issue: Unable to connect to training service. Using fallback question.'
        : error.message.includes('401') || error.message.includes('403')
        ? '🔒 Authentication issue: Please check your login status. Using fallback question.'
        : `⚠️ Unable to generate query: ${error.message}. Using fallback question.`;
      
      addMessage('system', errorMessage, {
        timestamp: new Date(),
        type: 'warning'
      });
      
      // Use fallback
      const fallbackQueries = [
        "Hi! I'm new to your service. Can you help me understand what you do?",
        "I'm having trouble with my account. Can you help?",
        "What are your pricing options?",
        "How does your platform work?",
        "I need help with a technical issue."
      ];
      
      const fallbackQuery = fallbackQueries[Math.floor(Math.random() * fallbackQueries.length)];
      
      addMessage('user', fallbackQuery, {
        timestamp: new Date(),
        type: 'generated_query',
        difficulty: 'mixed',
        category: 'general',
        context: 'fallback template',
        fallback: true
      });
      
      setCurrentQuery({
        query: fallbackQuery,
        difficulty: 'mixed',
        category: 'general',
        context: 'fallback template'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const submitResponse = async () => {
    if (!userResponse.trim() || !currentQuery || !sessionId) return;
    
    setIsSending(true);
    
    try {
      // Add user's response to conversation
      addMessage('assistant', userResponse, {
        timestamp: new Date(),
        type: 'user_response',
        responding_to: currentQuery.query
      });
      
      // Save training pair via backend
      const queryMetadata = {
        difficulty: currentQuery.difficulty,
        category: currentQuery.category,
        context: currentQuery.context
      };
      
      const savedPair = await addTrainingPair(sessionId, currentQuery.query, userResponse, queryMetadata);
      
      // Update local state
      const newPair = {
        query: currentQuery.query,
        response: userResponse,
        timestamp: new Date(),
        metadata: {
          difficulty: currentQuery.difficulty,
          category: currentQuery.category,
          context: currentQuery.context,
          session_id: sessionId
        }
      };
      
      const updatedPairs = [...trainingPairs, newPair];
      setTrainingPairs(updatedPairs);
      
      // Check if we should trigger automatic training
      if (autoTrainingEnabled && updatedPairs.length >= minPairsForTraining && !trainingTriggered) {
        setTrainingTriggered(true);
        addMessage('system', `🚀 Great! You've created ${updatedPairs.length} training pairs. Automatic training will be triggered to improve your agent.`, {
          timestamp: new Date(),
          type: 'auto_training_triggered'
        });
      }
      
      // Reset for next query
      setUserResponse('');
      setCurrentQuery(null);
      
      // Generate next query after a brief pause
      if (isActive && updatedPairs.length < 50) { // Reasonable limit
        setTimeout(generateNextQuery, 2000);
      } else if (updatedPairs.length >= 50) {
        addMessage('system', 'You\'ve reached the session limit of 50 training pairs. Great work!', {
          timestamp: new Date(),
          type: 'session_limit'
        });
        stopConversation();
      }
      
    } catch (error) {
      console.error('Failed to submit response:', error);
      onNotification?.({
        type: 'error',
        message: 'Failed to save training pair'
      });
    } finally {
      setIsSending(false);
    }
  };

  const addMessage = (role, content, metadata = {}) => {
    const message = {
      id: Date.now() + Math.random(),
      role, // 'user', 'assistant', 'system'
      content,
      metadata: {
        ...metadata,
        timestamp: metadata.timestamp || new Date()
      }
    };
    
    setConversation(prev => [...prev, message]);
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submitResponse();
    }
  };

  const skipQuery = () => {
    if (!currentQuery) return;
    
    addMessage('system', `Query skipped: "${currentQuery.query}"`, {
      timestamp: new Date(),
      type: 'skipped'
    });
    
    setCurrentQuery(null);
    setUserResponse('');
    
    // Generate next query
    if (isActive) {
      setTimeout(generateNextQuery, 1000);
    }
  };

  const formatMessageTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getMessageAvatar = (role, metadata) => {
    if (role === 'system') {
      return <AutoIcon sx={{ color: '#666' }} />;
    } else if (role === 'user') {
      return <PersonIcon sx={{ color: '#1976d2' }} />;
    } else {
      return <BotIcon sx={{ color: '#2e7d32' }} />;
    }
  };

  const getMessageColor = (role, metadata) => {
    if (role === 'system') return '#f5f5f5';
    if (role === 'user') return '#e3f2fd';
    return '#e8f5e8';
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ pb: 2 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AutoIcon color="primary" />
                Conversational Fine-tuning
                {isActive && <Badge color="success" variant="dot" />}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Train your agent through natural conversation
              </Typography>
            </Box>
            
            <Stack direction="row" spacing={1}>
              {/* Training Stats */}
              {trainingPairs.length > 0 && (
                <Tooltip title="Training pairs collected">
                  <Chip 
                    icon={<ProgressIcon />}
                    label={`${trainingPairs.length} pairs`}
                    color={trainingTriggered ? "success" : "primary"}
                    variant={trainingTriggered ? "filled" : "outlined"}
                  />
                </Tooltip>
              )}
              
              {/* Auto-training indicator */}
              {autoTrainingEnabled && (
                <Tooltip title={`Auto-training at ${minPairsForTraining} pairs`}>
                  <Chip 
                    icon={<AutoIcon />}
                    label="Auto-train"
                    color="secondary"
                    size="small"
                  />
                </Tooltip>
              )}
              
              {/* Settings */}
              <IconButton 
                onClick={(e) => setSettingsMenuAnchor(e.currentTarget)}
                size="small"
              >
                <SettingsIcon />
              </IconButton>
              
              {/* Start/Stop button */}
              {!isActive ? (
                <Button
                  variant="contained"
                  startIcon={<StartIcon />}
                  onClick={startConversation}
                  disabled={disabled}
                  sx={{ bgcolor: '#10b981', '&:hover': { bgcolor: '#059669' } }}
                >
                  Start Training
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  startIcon={<StopIcon />}
                  onClick={stopConversation}
                  color="error"
                >
                  Stop Training
                </Button>
              )}
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {/* Conversation Area */}
      <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
          {/* Messages */}
          <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
            {conversation.length === 0 ? (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center',
                height: '100%',
                color: 'text.secondary'
              }}>
                <AutoIcon sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
                <Typography variant="h6" gutterBottom>
                  Ready to Start Training
                </Typography>
                <Typography variant="body2" textAlign="center">
                  Click "Start Training" to begin a conversation where I'll generate realistic user queries
                  and you'll provide the ideal responses for training your agent.
                </Typography>
              </Box>
            ) : (
              <Stack spacing={2}>
                {conversation.map((message) => (
                  <Box key={message.id}>
                    <Stack direction="row" spacing={2} alignItems="flex-start">
                      <Avatar sx={{ 
                        bgcolor: getMessageColor(message.role, message.metadata),
                        width: 36, 
                        height: 36 
                      }}>
                        {getMessageAvatar(message.role, message.metadata)}
                      </Avatar>
                      
                      <Box sx={{ flex: 1 }}>
                        <Paper sx={{ 
                          p: 2, 
                          bgcolor: getMessageColor(message.role, message.metadata),
                          border: message.role === 'system' ? '1px dashed #ccc' : 'none'
                        }}>
                          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                            {message.content}
                          </Typography>
                          
                          {/* Query metadata */}
                          {message.metadata?.type === 'generated_query' && (
                            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                              <Chip 
                                label={message.metadata.difficulty} 
                                size="small" 
                                color="primary" 
                                variant="outlined"
                              />
                              <Chip 
                                label={message.metadata.category} 
                                size="small" 
                                color="secondary" 
                                variant="outlined"
                              />
                              {message.metadata.fallback && (
                                <Chip 
                                  label="fallback" 
                                  size="small" 
                                  color="warning" 
                                  variant="outlined"
                                />
                              )}
                            </Stack>
                          )}
                        </Paper>
                        
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 1, mt: 0.5 }}>
                          {formatMessageTime(message.metadata.timestamp)}
                        </Typography>
                      </Box>
                    </Stack>
                  </Box>
                ))}
                <div ref={messagesEndRef} />
              </Stack>
            )}
          </Box>

          {/* Response Input */}
          {isActive && currentQuery && (
            <Box sx={{ borderTop: 1, borderColor: 'divider', p: 2 }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                💬 Provide your ideal response to the user query above:
              </Typography>
              
              <Stack direction="row" spacing={2} alignItems="flex-end">
                <TextField
                  ref={responseInputRef}
                  fullWidth
                  multiline
                  maxRows={4}
                  value={userResponse}
                  onChange={(e) => setUserResponse(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type the ideal response your agent should give..."
                  variant="outlined"
                  disabled={isSending}
                />
                
                <Stack spacing={1}>
                  <Button
                    variant="contained"
                    endIcon={isSending ? <CircularProgress size={16} /> : <SendIcon />}
                    onClick={submitResponse}
                    disabled={!userResponse.trim() || isSending}
                    sx={{ minWidth: 100 }}
                  >
                    {isSending ? 'Saving...' : 'Send'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={skipQuery}
                    disabled={isSending}
                  >
                    Skip
                  </Button>
                </Stack>
              </Stack>
            </Box>
          )}

          {/* Loading state */}
          {isActive && isGenerating && (
            <Box sx={{ borderTop: 1, borderColor: 'divider', p: 2 }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <CircularProgress size={20} />
                <Typography variant="body2" color="text.secondary">
                  Generating next query...
                </Typography>
              </Stack>
            </Box>
          )}
          
          {/* Waiting state - when active but no current query and not generating */}
          {isActive && !currentQuery && !isGenerating && conversation.length > 0 && (
            <Box sx={{ borderTop: 1, borderColor: 'divider', p: 2 }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <CircularProgress size={20} />
                <Typography variant="body2" color="text.secondary">
                  Preparing your next query...
                </Typography>
              </Stack>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Settings Menu */}
      <Menu
        anchorEl={settingsMenuAnchor}
        open={Boolean(settingsMenuAnchor)}
        onClose={() => setSettingsMenuAnchor(null)}
      >
        <MenuItem onClick={() => setSettingsMenuAnchor(null)}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Difficulty</InputLabel>
            <Select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              label="Difficulty"
            >
              {availableDifficulties.map(diff => (
                <MenuItem key={diff} value={diff}>{diff}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ConversationalFineTuning;