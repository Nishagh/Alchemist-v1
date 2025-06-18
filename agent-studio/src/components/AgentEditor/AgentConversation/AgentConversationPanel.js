/**
 * Agent Conversation Panel
 * 
 * Interactive conversation interface with the Alchemist agent for agent configuration
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  CircularProgress,
  Alert,
  Divider,
  Chip,
  Fade,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  AutoAwesome as AutoAwesomeIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';
import { interactWithAlchemist, getAgentConversations } from '../../../services';
import { convertTimestamp } from '../../../utils/agentEditorHelpers';
import ThoughtProcessDisplay from './ThoughtProcessDisplay';
import FileUploadArea from './FileUploadArea';

const AgentConversationPanel = ({ 
  agentId,
  messages = [],
  onMessagesUpdate,
  thoughtProcess = [],
  onThoughtProcessUpdate,
  disabled = false 
}) => {
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [error, setError] = useState('');
  const [showFileUpload, setShowFileUpload] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load existing conversations when component mounts
  useEffect(() => {
    const loadConversations = async () => {
      if (!agentId) return;

      try {
        setLoadingConversations(true);
        console.log(`Loading conversations for agent ${agentId}`);
        
        const messagesData = await getAgentConversations(agentId);
        console.log('Loaded conversation data:', messagesData);
        
        if (messagesData && messagesData.length > 0) {
          // Sort messages by created_at to display in proper sequence
          const sortedMessages = [...messagesData].sort((a, b) => {
            const dateA = convertTimestamp(a.created_at);
            const dateB = convertTimestamp(b.created_at);
            if (!dateA || !dateB) return 0;
            return dateA - dateB;
          });
          
          // Format the messages for display
          const formattedMessages = sortedMessages.map(msg => ({
            id: msg.id || Date.now() + Math.random(),
            role: msg.role || 'user',
            content: msg.content || '',
            timestamp: convertTimestamp(msg.created_at) || new Date()
          }));
          
          onMessagesUpdate(formattedMessages);
          console.log('Loaded and formatted messages:', formattedMessages.length);
        } else {
          console.log('No existing messages found for this agent');
          onMessagesUpdate([]);
        }
      } catch (error) {
        console.error('Error loading conversations:', error);
        setError('Failed to load conversation history.');
      } finally {
        setLoadingConversations(false);
      }
    };

    loadConversations();
  }, [agentId, onMessagesUpdate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!userInput.trim() || loading) return;

    const message = userInput.trim();
    setUserInput('');
    setError('');

    // Add user message to the conversation
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date()
    };

    const updatedMessages = [...messages, userMessage];
    onMessagesUpdate(updatedMessages);

    try {
      setLoading(true);

      // Call Alchemist API
      const response = await interactWithAlchemist(message, agentId);
      
      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response || response.message || 'No response received',
        timestamp: new Date()
      };

      onMessagesUpdate([...updatedMessages, assistantMessage]);

      // Update thought process if available
      if (response.thought_process) {
        onThoughtProcessUpdate(response.thought_process);
      }

    } catch (err) {
      console.error('Error sending message to Alchemist:', err);
      setError('Failed to send message. Please try again.');
      
      // Add error message to conversation
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        isError: true
      };

      onMessagesUpdate([...updatedMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileUpload = (files) => {
    // Handle file uploads - for now just log them
    console.log('Files uploaded:', files);
    setShowFileUpload(false);
    
    // You can add logic here to send file info to the conversation
    if (files.length > 0) {
      const fileMessage = `📎 Uploaded ${files.length} file(s): ${files.map(f => f.name).join(', ')}`;
      setUserInput(prevInput => prevInput + (prevInput ? '\n\n' : '') + fileMessage);
    }
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
      {/* Header */}
      <Box sx={{ p: 3, bgcolor: 'background.default' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <AutoAwesomeIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
            Alchemist Assistant
          </Typography>
          <Chip 
            label="AI-Powered" 
            size="small" 
            color="primary" 
            variant="outlined" 
            sx={{ ml: 2 }}
          />
        </Box>
        <Typography variant="body2" color="text.secondary">
          Chat with Alchemist to configure your agent using natural language
        </Typography>
      </Box>

      <Divider />

      {/* Messages Area */}
      <Box 
        sx={{ 
          flex: 1,
          p: 3,
          overflowY: 'auto',
          minHeight: 0
        }}
      >
        {loadingConversations ? (
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
            <CircularProgress sx={{ mb: 2 }} />
            <Typography variant="h6" sx={{ mb: 1 }}>
              Loading conversation history...
            </Typography>
            <Typography variant="body2">
              Fetching your previous conversations with Alchemist
            </Typography>
          </Box>
        ) : messages.length === 0 ? (
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
            <PsychologyIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
            <Typography variant="h6" sx={{ mb: 1 }}>
              Start a conversation
            </Typography>
            <Typography variant="body2">
              Ask Alchemist to help you configure your agent
            </Typography>
          </Box>
        ) : (
          <>
            {messages.map(renderMessage)}
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
                      Alchemist is thinking...
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </Box>

      {/* Thought Process */}
      {thoughtProcess.length > 0 && (
        <>
          <Divider />
          <ThoughtProcessDisplay thoughtProcess={thoughtProcess} />
        </>
      )}

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

      {/* File Upload Area */}
      {showFileUpload && (
        <>
          <Divider />
          <Box sx={{ p: 3 }}>
            <FileUploadArea
              onFilesUploaded={handleFileUpload}
              onCancel={() => setShowFileUpload(false)}
              accept=".txt,.md,.json,.yaml,.yml"
              maxFiles={5}
            />
          </Box>
        </>
      )}

      {/* Input Area */}
      <Divider />
      <Box sx={{ p: 3 }}>
        <TextField
          ref={inputRef}
          fullWidth
          multiline
          maxRows={4}
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask Alchemist to help configure your agent..."
          disabled={disabled || loading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton
                    onClick={() => setShowFileUpload(!showFileUpload)}
                    disabled={disabled || loading}
                    size="small"
                    color={showFileUpload ? 'primary' : 'default'}
                  >
                    <AttachFileIcon />
                  </IconButton>
                  <IconButton
                    onClick={handleSendMessage}
                    disabled={disabled || loading || !userInput.trim()}
                    color="primary"
                    size="small"
                  >
                    {loading ? <CircularProgress size={20} /> : <SendIcon />}
                  </IconButton>
                </Box>
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
  );
};

export default AgentConversationPanel;