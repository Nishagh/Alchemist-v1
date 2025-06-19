import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  IconButton,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Chip,
  useTheme,
  alpha,
  Fade,
  Grow,
  Tooltip,
  Avatar,
  Slide,
  Zoom,
  Container
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon, 
  Edit as EditIcon,
  Psychology as PsychologyIcon,
  RocketLaunch as RocketLaunchIcon,
  Lock as LockIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
  Code as CodeIcon,
  MenuBook as MenuBookIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  PlayArrow as PlayArrowIcon
} from '@mui/icons-material';
import { deleteAgent } from '../services';
import { useAuth } from '../utils/AuthContext';
import { db } from '../utils/firebase';
import { collection, onSnapshot, query, where } from 'firebase/firestore';

const AgentsList = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  
  const navigate = useNavigate();
  const theme = useTheme();
  const { currentUser } = useAuth();

  useEffect(() => {
    if (currentUser) {
      const agentsCollectionRef = collection(db, 'alchemist_agents');
      const agentsQuery = query(agentsCollectionRef, where('userId', '==', currentUser.uid));
      const unsubscribe = onSnapshot(agentsQuery, (snapshot) => {
        const agents = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        setAgents(agents);
        setLoading(false);
      });
      
      // Return cleanup function
      return () => unsubscribe();
    } else {
      setLoading(false);
    }
  }, [currentUser]);

  const handleDeleteClick = (agent, event) => {
    event.stopPropagation();
    setAgentToDelete(agent);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!agentToDelete) return;
    
    try {
      await deleteAgent(agentToDelete.agent_id);
      setNotification({
        open: true,
        message: `Agent "${agentToDelete.name}" deleted successfully`,
        severity: 'success'
      });
    } catch (error) {
      console.error('Error deleting agent:', error);
      let errorMessage = 'Failed to delete agent';
      
      if (error.response && error.response.status === 401) {
        errorMessage = 'You must be logged in to delete agents';
      } else if (error.response && error.response.status === 403) {
        errorMessage = 'You do not have permission to delete this agent';
      } else if (error.message) {
        errorMessage = `Failed to delete agent: ${error.message}`;
      }
      
      setNotification({
        open: true,
        message: errorMessage,
        severity: 'error'
      });
    } finally {
      setDeleteDialogOpen(false);
      setAgentToDelete(null);
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  const handleCardClick = (agentId) => {
    if (agentId) {
      navigate(`/agent-editor/${agentId}`);
    }
  };

  const getRandomGradient = (index) => {
    const gradients = [
      `linear-gradient(135deg, ${theme.palette.grey[900]} 0%, ${theme.palette.grey[700]} 100%)`,
      `linear-gradient(135deg, ${theme.palette.grey[800]} 0%, ${theme.palette.grey[600]} 100%)`,
      `linear-gradient(135deg, ${theme.palette.grey[700]} 0%, ${theme.palette.grey[500]} 100%)`,
      `linear-gradient(135deg, ${theme.palette.grey[600]} 0%, ${theme.palette.grey[800]} 100%)`,
      `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.grey[800]} 100%)`,
      `linear-gradient(135deg, ${theme.palette.grey[800]} 0%, ${theme.palette.primary.main} 100%)`,
      `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.grey[700]} 100%)`,
      `linear-gradient(135deg, ${theme.palette.grey[700]} 0%, ${theme.palette.secondary.main} 100%)`,
      `linear-gradient(135deg, ${theme.palette.grey[900]} 0%, ${theme.palette.grey[600]} 100%)`,
      `linear-gradient(135deg, ${theme.palette.grey[600]} 0%, ${theme.palette.grey[900]} 100%)`
    ];
    return gradients[index % gradients.length];
  };

  const getAgentTypeIcon = (type) => {
    switch (type) {
      case 'customer_service': return <PersonIcon />;
      case 'data_analyst': return <TrendingUpIcon />;
      case 'developer': return <CodeIcon />;
      case 'researcher': return <MenuBookIcon />;
      default: return <SmartToyIcon />;
    }
  };


  // If not logged in, show enhanced login prompt
  if (!currentUser && !loading) {
    return (
      <Box 
        sx={{ 
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.03)} 100%)`,
          minHeight: '100vh',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {/* Decorative background elements */}
        <Box sx={{
          position: 'absolute',
          top: -100,
          right: -100,
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          filter: 'blur(40px)'
        }} />
        <Box sx={{
          position: 'absolute',
          bottom: -100,
          left: -100,
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${alpha(theme.palette.secondary.main, 0.1)} 0%, ${alpha(theme.palette.primary.main, 0.05)} 100%)`,
          filter: 'blur(40px)'
        }} />

        <Container maxWidth="md">
          <Zoom in={true} timeout={800}>
            <Card sx={{ 
              textAlign: 'center',
              p: 6,
              borderRadius: 4,
              background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.primary.light, 0.02)} 100%)`,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <Box sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 4,
                background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
              }} />
              
              <Avatar sx={{ 
                bgcolor: alpha(theme.palette.primary.main, 0.1), 
                mx: 'auto',
                mb: 3,
                width: 80,
                height: 80
              }}>
                <LockIcon sx={{ fontSize: 40, color: theme.palette.primary.main }} />
              </Avatar>
              
              <Typography variant="h3" gutterBottom fontWeight="bold" sx={{
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                textFillColor: 'transparent',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 2
              }}>
                My AI Agents
              </Typography>
              
              <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: '600px', mx: 'auto' }}>
                Access your personalized AI workforce. Please authenticate to view and manage your intelligent agents.
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate('/login', { state: { from: '/agents' } })}
                  sx={{ 
                    py: 1.5, 
                    px: 4,
                    borderRadius: 3,
                    textTransform: 'none',
                    fontWeight: 'bold',
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    boxShadow: '0 8px 25px rgba(0, 0, 0, 0.2)',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 12px 30px rgba(0, 0, 0, 0.3)'
                    },
                    transition: 'all 0.3s ease-in-out'
                  }}
                >
                  Sign In
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/signup')}
                  sx={{ 
                    py: 1.5, 
                    px: 4,
                    borderRadius: 3,
                    textTransform: 'none',
                    fontWeight: 'medium',
                    borderWidth: 2,
                    '&:hover': {
                      borderWidth: 2,
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 20px rgba(0, 0, 0, 0.1)'
                    },
                    transition: 'all 0.3s ease-in-out'
                  }}
                >
                  Create Account
                </Button>
              </Box>
            </Card>
          </Zoom>
        </Container>
      </Box>
    );
  }

  return (
    <Box 
      sx={{ 
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.03)} 0%, ${alpha(theme.palette.secondary.light, 0.02)} 100%)`,
        minHeight: '100vh',
        width: '100%',
        pb: 6
      }}
    >
      {/* Enhanced Header Section */}
      <Box sx={{ 
        background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.9)} 0%, ${alpha(theme.palette.primary.light, 0.05)} 100%)`,
        backdropFilter: 'blur(20px)',
        borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
        position: 'relative',
        overflow: 'hidden'
      }}>
        <Box sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
        }} />
        
        <Container maxWidth="xl">
          <Fade in={true} timeout={800}>
            <Box sx={{ 
              textAlign: 'center', 
              pt: 6, 
              pb: 4
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                <Avatar sx={{ 
                  bgcolor: theme.palette.primary.main, 
                  mr: 2,
                  width: 56,
                  height: 56
                }}>
                  <PsychologyIcon sx={{ fontSize: 30 }} />
                </Avatar>
                <Typography 
                  variant="h2" 
                  component="h1" 
                  sx={{ 
                    fontWeight: 'bold',
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    backgroundClip: 'text',
                    textFillColor: 'transparent',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}
                >
                  My AI Agents
                </Typography>
              </Box>
              
              <Typography variant="h6" color="text.secondary" sx={{ mb: 3, maxWidth: '800px', mx: 'auto' }}>
                Your intelligent workforce of specialized AI assistants, each crafted for specific tasks and expertise
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
                <Chip 
                  icon={<SmartToyIcon />}
                  label={`${agents.length} Active Agents`}
                  sx={{ 
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    color: theme.palette.primary.main,
                    fontWeight: 'medium',
                    px: 1
                  }} 
                />
                <Chip 
                  icon={<SpeedIcon />}
                  label="Always Available"
                  sx={{ 
                    bgcolor: alpha(theme.palette.success.main, 0.1),
                    color: theme.palette.success.main,
                    fontWeight: 'medium',
                    px: 1
                  }} 
                />
              </Box>
            </Box>
          </Fade>
        </Container>
      </Box>

      <Container maxWidth="xl" sx={{ mt: 4 }}>
        {/* Enhanced Error Display */}
        {error && (
          <Slide direction="down" in={!!error} mountOnEnter unmountOnExit>
            <Alert 
              severity="error" 
              sx={{ 
                mb: 4,
                borderRadius: 2,
                backgroundColor: alpha(theme.palette.error.main, 0.1),
                borderLeft: `4px solid ${theme.palette.error.main}`,
                '& .MuiAlert-icon': {
                  fontSize: '1.5rem'
                }
              }}
            >
              {error}
            </Alert>
          </Slide>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', my: 10 }}>
            <CircularProgress size={60} thickness={4} sx={{ mb: 3 }} />
            <Typography variant="h6" color="text.secondary" fontWeight="medium">
              Loading your AI agents...
            </Typography>
          </Box>
        ) : (
          <Fade in={true} timeout={1000}>
            <Box>
              {/* Enhanced Action Bar */}
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                mb: 4,
                p: 3,
                borderRadius: 3,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.primary.light, 0.03)} 100%)`,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                backdropFilter: 'blur(10px)'
              }}>
                <Box>
                  <Typography variant="h5" fontWeight="bold" color="primary">
                    Agent Dashboard
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {agents.length === 0 ? 'No agents created yet' : 
                     agents.length === 1 ? '1 agent in your fleet' : 
                     `${agents.length} agents in your fleet`}
                  </Typography>
                </Box>
                
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<AddIcon />}
                  onClick={() => navigate('/agent-editor')}
                  sx={{ 
                    py: 1.5, 
                    px: 4,
                    borderRadius: 3,
                    textTransform: 'none',
                    fontWeight: 'bold',
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    boxShadow: '0 8px 25px rgba(0, 0, 0, 0.2)',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 12px 30px rgba(0, 0, 0, 0.3)'
                    },
                    transition: 'all 0.3s ease-in-out'
                  }}
                >
                  Create New Agent
                </Button>
              </Box>

              {agents.length > 0 ? (
                <Grid container spacing={3}>
                  {agents.map((agent, index) => (
                    <Grid item xs={12} sm={6} lg={4} xl={3} key={agent?.agent_id || index}>
                      <Grow in={true} timeout={600 + (index * 100)}>
                        <Card 
                          elevation={0}
                          sx={{ 
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            cursor: 'pointer',
                            borderRadius: 4,
                            overflow: 'hidden',
                            border: `2px solid ${alpha(theme.palette.grey[300], 0.3)}`,
                            background: theme.palette.background.paper,
                            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                            position: 'relative',
                            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
                            '&:hover': {
                              transform: 'translateY(-12px)',
                              boxShadow: '0 25px 50px rgba(0, 0, 0, 0.25)',
                              border: `2px solid ${theme.palette.primary.main}`,
                              '& .agent-header': {
                                '&:after': {
                                  opacity: 1
                                }
                              },
                              '& .agent-avatar': {
                                transform: 'scale(1.1) rotate(5deg)',
                                boxShadow: '0 8px 25px rgba(0, 0, 0, 0.3)'
                              },
                              '& .agent-actions': {
                                transform: 'translateY(0)',
                                opacity: 1
                              }
                            },
                            '&:before': {
                              content: '""',
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              right: 0,
                              height: 6,
                              background: getRandomGradient(index),
                              transition: 'all 0.3s ease'
                            }
                          }}
                          onClick={() => handleCardClick(agent?.agent_id)}
                        >
                          {/* Modern Header with Clean Design */}
                          <Box 
                            className="agent-header"
                            sx={{ 
                              height: '140px',
                              background: `linear-gradient(135deg, ${alpha(theme.palette.grey[50], 1)} 0%, ${alpha(theme.palette.grey[100], 1)} 100%)`,
                              display: 'flex',
                              flexDirection: 'column',
                              justifyContent: 'center',
                              alignItems: 'center',
                              padding: 3,
                              position: 'relative',
                              transition: 'all 0.3s ease',
                              borderBottom: `1px solid ${alpha(theme.palette.grey[200], 0.5)}`,
                              '&:after': {
                                content: '""',
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                background: getRandomGradient(index),
                                opacity: 0,
                                transition: 'opacity 0.3s ease'
                              }
                            }}
                          >
                            {/* Agent Avatar */}
                            <Avatar 
                              className="agent-avatar"
                              sx={{ 
                                bgcolor: theme.palette.primary.main,
                                width: 64,
                                height: 64,
                                mb: 2,
                                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.15)',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                border: `3px solid ${theme.palette.background.paper}`,
                                zIndex: 2,
                                position: 'relative'
                              }}
                            >
                              {getAgentTypeIcon(agent?.type)}
                            </Avatar>
                            
                            {/* Agent Name */}
                            <Typography 
                              variant="h6" 
                              sx={{ 
                                fontWeight: 'bold', 
                                color: theme.palette.text.primary,
                                textAlign: 'center',
                                mb: 1,
                                zIndex: 2,
                                position: 'relative',
                                maxWidth: '100%',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {agent?.name || 'Unnamed Agent'}
                            </Typography>
                            
                            {/* Model Badge */}
                            <Chip 
                              size="small" 
                              label={agent?.model || 'gpt-4'} 
                              sx={{ 
                                bgcolor: alpha(theme.palette.primary.main, 0.1),
                                color: theme.palette.primary.main,
                                fontWeight: 'bold',
                                fontSize: '0.75rem',
                                zIndex: 2,
                                position: 'relative',
                                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                              }} 
                            />
                          </Box>
                          
                          {/* Enhanced Content Section */}
                          <CardContent sx={{ flexGrow: 1, p: 3, pb: 2 }}>
                            {/* Agent Type Badge */}
                            <Box sx={{ mb: 2 }}>
                              <Chip 
                                icon={getAgentTypeIcon(agent?.type)}
                                label={agent?.type?.charAt(0).toUpperCase() + agent?.type?.slice(1) || 'Generic'} 
                                size="small"
                                sx={{ 
                                  bgcolor: alpha(theme.palette.grey[100], 1),
                                  color: theme.palette.text.primary,
                                  fontWeight: 'bold',
                                  border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
                                  '& .MuiChip-icon': {
                                    color: theme.palette.primary.main
                                  }
                                }} 
                              />
                            </Box>
                            
                            {/* Description */}
                            <Typography 
                              variant="body2" 
                              color="text.secondary" 
                              sx={{ 
                                mb: 3,
                                display: '-webkit-box',
                                WebkitLineClamp: 3,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                height: '4.5em',
                                lineHeight: 1.5,
                                fontSize: '0.875rem'
                              }}
                            >
                              {agent?.description || 'This AI agent is ready to assist you with various tasks. Configure its capabilities and knowledge base to customize its behavior.'}
                            </Typography>
                            
                            {/* Status and Stats */}
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <MenuBookIcon sx={{ fontSize: 16, color: theme.palette.text.secondary }} />
                                <Typography variant="caption" color="text.secondary">
                                  {agent?.knowledge_base?.length || 0} KB items
                                </Typography>
                              </Box>
                              
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Box 
                                  sx={{ 
                                    width: 8, 
                                    height: 8, 
                                    borderRadius: '50%', 
                                    bgcolor: theme.palette.success.main 
                                  }} 
                                />
                                <Typography variant="caption" color="text.secondary">
                                  Active
                                </Typography>
                              </Box>
                              
                              {agent?.created_at && (
                                <Typography variant="caption" color="text.secondary">
                                  Created {new Date(agent?.created_at).toLocaleDateString()}
                                </Typography>
                              )}
                            </Box>
                          </CardContent>
                          
                          {/* Modern Action Bar */}
                          <Box 
                            className="agent-actions"
                            sx={{ 
                              p: 2.5,
                              background: `linear-gradient(135deg, ${alpha(theme.palette.grey[50], 1)} 0%, ${alpha(theme.palette.grey[100], 1)} 100%)`,
                              borderTop: `1px solid ${alpha(theme?.palette?.grey[200], 0.5)}`,
                              transform: 'translateY(10px)',
                              opacity: 0.7,
                              transition: 'all 0.3s ease'
                            }}
                          >
                            <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'space-between', alignItems: 'center' }}>
                              {/* Primary Actions */}
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button 
                                  size="small" 
                                  variant="contained"
                                  startIcon={<EditIcon />}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (agent?.agent_id) {
                                      navigate(`/agent-editor/${agent.agent_id}`);
                                    }
                                  }}
                                  sx={{
                                    borderRadius: 2,
                                    textTransform: 'none',
                                    fontWeight: 'bold',
                                    fontSize: '0.8rem',
                                    bgcolor: theme.palette.primary.main,
                                    color: 'white',
                                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
                                    '&:hover': {
                                      bgcolor: theme.palette.primary.dark,
                                      transform: 'translateY(-1px)',
                                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                                    }
                                  }}
                                >
                                  Edit
                                </Button>
                                
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<CodeIcon />}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (agent?.agent_id) {
                                      navigate(`/api-integration/${agent.agent_id}`);
                                    }
                                  }}
                                  sx={{
                                    borderRadius: 2,
                                    textTransform: 'none',
                                    fontWeight: 'medium',
                                    fontSize: '0.8rem',
                                    borderColor: alpha(theme.palette.grey[400], 0.8),
                                    color: theme.palette.text.primary,
                                    '&:hover': {
                                      borderColor: theme.palette.primary.main,
                                      backgroundColor: alpha(theme.palette.primary.main, 0.05),
                                      transform: 'translateY(-1px)'
                                    }
                                  }}
                                >
                                  API
                                </Button>
                                
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<MenuBookIcon />}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (agent?.agent_id) {
                                      navigate(`/knowledge-base/${agent.agent_id}`);
                                    }
                                  }}
                                  sx={{
                                    borderRadius: 2,
                                    textTransform: 'none',
                                    fontWeight: 'medium',
                                    fontSize: '0.8rem',
                                    borderColor: alpha(theme.palette.grey[400], 0.8),
                                    color: theme.palette.text.primary,
                                    '&:hover': {
                                      borderColor: theme.palette.secondary.main,
                                      backgroundColor: alpha(theme.palette.secondary.main, 0.05),
                                      transform: 'translateY(-1px)'
                                    }
                                  }}
                                >
                                  KB
                                </Button>
                                
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<PlayArrowIcon />}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (agent?.agent_id) {
                                      navigate(`/agent-testing/${agent.agent_id}`);
                                    }
                                  }}
                                  sx={{
                                    borderRadius: 2,
                                    textTransform: 'none',
                                    fontWeight: 'medium',
                                    fontSize: '0.8rem',
                                    borderColor: alpha(theme.palette.success.main, 0.8),
                                    color: theme.palette.success.main,
                                    '&:hover': {
                                      borderColor: theme.palette.success.main,
                                      backgroundColor: alpha(theme.palette.success.main, 0.1),
                                      transform: 'translateY(-1px)',
                                      boxShadow: '0 2px 8px rgba(76, 175, 80, 0.2)'
                                    }
                                  }}
                                >
                                  Test
                                </Button>
                                
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<TrendingUpIcon />}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (agent?.agent_id) {
                                      navigate(`/agent-analytics/${agent.agent_id}`);
                                    }
                                  }}
                                  sx={{
                                    borderRadius: 2,
                                    textTransform: 'none',
                                    fontWeight: 'medium',
                                    fontSize: '0.8rem',
                                    borderColor: alpha(theme.palette.info.main, 0.8),
                                    color: theme.palette.info.main,
                                    '&:hover': {
                                      borderColor: theme.palette.info.main,
                                      backgroundColor: alpha(theme.palette.info.main, 0.1),
                                      transform: 'translateY(-1px)',
                                      boxShadow: '0 2px 8px rgba(33, 150, 243, 0.2)'
                                    }
                                  }}
                                >
                                  Analytics
                                </Button>
                              </Box>
                              
                              {/* Delete Action */}
                              <Tooltip title={agent?.type === 'system' ? 'System agents cannot be deleted' : 'Delete Agent'} placement="top">
                                <span>
                                  <IconButton 
                                    size="small"
                                    disabled={agent?.type === 'system'}
                                    onClick={(e) => handleDeleteClick(agent, e)}
                                    sx={{
                                      color: theme.palette.text.secondary,
                                      bgcolor: alpha(theme.palette.grey[100], 1),
                                      border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
                                      '&:hover': {
                                        bgcolor: alpha(theme.palette.error.main, 0.1),
                                        color: theme.palette.error.main,
                                        borderColor: alpha(theme.palette.error.main, 0.3),
                                        transform: 'scale(1.05)'
                                      },
                                      '&:disabled': {
                                        bgcolor: alpha(theme.palette.action.disabled, 0.1),
                                        borderColor: alpha(theme.palette.action.disabled, 0.2)
                                      },
                                      transition: 'all 0.2s ease'
                                    }}
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            </Box>
                          </Box>
                        </Card>
                      </Grow>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Zoom in={true} timeout={800}>
                  <Card sx={{ 
                    textAlign: 'center',
                    p: 8,
                    borderRadius: 4,
                    background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.9)} 0%, ${alpha(theme.palette.primary.light, 0.05)} 100%)`,
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.05)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}>
                    <Box sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: 4,
                      background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                    }} />
                    
                    <Avatar sx={{ 
                      bgcolor: alpha(theme.palette.primary.main, 0.1), 
                      mx: 'auto',
                      mb: 3,
                      width: 80,
                      height: 80
                    }}>
                      <RocketLaunchIcon sx={{ fontSize: 40, color: theme.palette.primary.main }} />
                    </Avatar>
                    
                    <Typography variant="h4" gutterBottom fontWeight="bold" sx={{
                      background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                      backgroundClip: 'text',
                      textFillColor: 'transparent',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      mb: 2
                    }}>
                      Ready to Launch Your AI Journey?
                    </Typography>
                    
                    <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: '600px', mx: 'auto' }}>
                      Create your first AI agent to unlock the power of intelligent automation. Each agent can be customized for specific tasks and expertise.
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', mb: 4, flexWrap: 'wrap' }}>
                      <Chip icon={<SmartToyIcon />} label="Intelligent Responses" variant="outlined" />
                      <Chip icon={<MenuBookIcon />} label="Custom Knowledge" variant="outlined" />
                      <Chip icon={<CodeIcon />} label="API Integration" variant="outlined" />
                      <Chip icon={<SpeedIcon />} label="24/7 Available" variant="outlined" />
                    </Box>
                    
                    <Button
                      variant="contained"
                      size="large"
                      startIcon={<AddIcon />}
                      onClick={() => navigate('/agent-editor')}
                      sx={{ 
                        py: 2, 
                        px: 4,
                        borderRadius: 3,
                        textTransform: 'none',
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                        boxShadow: '0 8px 25px rgba(0, 0, 0, 0.2)',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: '0 12px 30px rgba(0, 0, 0, 0.3)'
                        },
                        transition: 'all 0.3s ease-in-out'
                      }}
                    >
                      Create Your First Agent
                    </Button>
                  </Card>
                </Zoom>
              )}
            </Box>
          </Fade>
        )}
      </Container>

      {/* Enhanced Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: { 
            borderRadius: 3,
            background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.error.light, 0.02)} 100%)`
          }
        }}
      >
        <DialogTitle sx={{ pb: 1, textAlign: 'center' }}>
          <Avatar sx={{ 
            bgcolor: alpha(theme.palette.error.main, 0.1), 
            mx: 'auto',
            mb: 2,
            width: 56,
            height: 56
          }}>
            <DeleteIcon sx={{ fontSize: 30, color: theme.palette.error.main }} />
          </Avatar>
          <Typography variant="h5" fontWeight="bold">
            Delete Agent
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ textAlign: 'center', pb: 2 }}>
          <Typography variant="body1" color="text.secondary">
            Are you sure you want to delete <strong>"{agentToDelete?.name}"</strong>? 
            This action cannot be undone and will permanently remove all associated data.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 3, gap: 1 }}>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
            variant="outlined"
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 'medium',
              px: 3
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error"
            variant="contained"
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 'bold',
              px: 3,
              background: `linear-gradient(45deg, ${theme.palette.error.main}, ${theme.palette.error.dark})`
            }}
          >
            Delete Agent
          </Button>
        </DialogActions>
      </Dialog>

      {/* Enhanced Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity}
          variant="filled"
          sx={{ 
            borderRadius: 2,
            fontWeight: 'medium',
            '& .MuiAlert-icon': {
              fontSize: '1.2rem'
            }
          }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentsList;
