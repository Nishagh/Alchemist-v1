/**
 * Agent Dashboard Page
 * 
 * Central hub for managing a specific agent - shows overview, progress, and access to all features
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Avatar,
  Chip,
  LinearProgress,
  IconButton,
  Container,
  Paper,
  Divider,
  Alert,
  CircularProgress,
  Link
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  RocketLaunch as RocketLaunchIcon,
  BugReport as TestingIcon,
  Hub as IntegrationIcon,
  Analytics as AnalyticsIcon,
  Storage as KnowledgeIcon,
  Api as ApiIcon,
  SmartToy as SmartToyIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  Launch as LaunchIcon,
  WhatsApp as WhatsAppIcon,
  Language as WebsiteIcon
} from '@mui/icons-material';

// Import components
import WorkflowProgressIndicator from '../components/AgentEditor/WorkflowProgress/WorkflowProgressIndicator';
import NotificationSystem, { createNotification } from '../components/shared/NotificationSystem';

// Import hooks and services
import useAgentState from '../hooks/useAgentState';
import { useAgentWorkflow } from '../hooks/useAgentWorkflow';
import { listDeployments } from '../services';

const AgentDashboard = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  
  // Core state management
  const { agent, loading, error } = useAgentState(agentId);
  
  // Workflow management
  const workflow = useAgentWorkflow(agentId);
  
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
    navigate('/agents');
  };

  // Handle workflow stage clicks from progress indicator
  const handleWorkflowStageClick = (stage) => {
    const route = stage.route.replace(':agentId', agentId);
    navigate(route);
  };

  // Check deployment status - Google Cloud Run style: deployed if any successful deployment exists
  const latestDeployment = deployments.length > 0 ? deployments[0] : null;
  console.log('Latest Deployment',latestDeployment)
  
  // Get successful deployments (either completed or deployed status)
  const successfulDeployments = deployments.filter(d => d.status === 'completed' || d.status === 'deployed');
  const hasSuccessfulDeployment = successfulDeployments.length > 0;
  
  // Agent is considered deployed if:
  // 1. Agent document has deployment_status set to completed/deployed, OR
  // 2. Any deployment has succeeded (Google Cloud Run behavior)
  const isDeployed = !!(agent?.deployment_status === 'completed' || 
                       agent?.deployment_status === 'deployed' || 
                       hasSuccessfulDeployment);
  
  // Get the active deployment (most recent successful one for service URL)
  const activeDeployment = successfulDeployments.length > 0 ? successfulDeployments[0] : null;
  
  // Current deployment status for UI indicators
  const isDeploying = latestDeployment?.status === 'deploying' || 
                     latestDeployment?.status === 'building_image' || 
                     latestDeployment?.status === 'generating_code' ||
                     latestDeployment?.status === 'queued' ||
                     latestDeployment?.status === 'initializing';

  // Feature cards configuration
  const featureCards = [
    {
      id: 'editor',
      title: 'Agent Editor',
      description: 'Configure behavior, knowledge, and capabilities',
      icon: EditIcon,
      color: '#1976d2',
      route: `/agent-editor/${agentId}`,
      stage: 'definition',
      features: ['Agent Definition', 'Knowledge Base', 'API Integration', 'Pre-testing', 'Fine-tuning']
    },
    {
      id: 'deployment',
      title: 'Deployment',
      description: 'Deploy agent to production with optimized performance',
      icon: RocketLaunchIcon,
      color: '#f57c00',
      route: `/agent-deployment/${agentId}`,
      stage: 'deployment',
      features: ['Optimized Builds', 'Cloud Run', 'Real-time Monitoring', 'Auto-scaling']
    },
    {
      id: 'testing',
      title: 'Testing',
      description: 'Test agent functionality before and after deployment',
      icon: TestingIcon,
      color: '#388e3c',
      route: `/agent-testing/${agentId}`,
      stage: 'pre-testing',
      features: ['Pre-deployment Testing', 'Production Testing', 'Billing Tracking', 'Debug Tools']
    },
    {
      id: 'integration',
      title: 'Integration',
      description: 'Connect to WhatsApp, websites, and other platforms',
      icon: IntegrationIcon,
      color: '#7b1fa2',
      route: `/agent-integration/${agentId}`,
      stage: 'integration',
      features: ['WhatsApp Business API', 'Website Widgets', 'Webhooks', 'API Endpoints'],
      requiresDeployment: true
    },
    {
      id: 'analytics',
      title: 'Analytics',
      description: 'Monitor usage, performance, and billing metrics',
      icon: AnalyticsIcon,
      color: '#0288d1',
      route: `/agent-analytics/${agentId}`,
      stage: 'analytics',
      features: ['Usage Statistics', 'Performance Metrics', 'Billing Reports', 'User Analytics'],
      requiresDeployment: true
    }
  ];

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
          <Button onClick={handleBackClick} sx={{ mt: 2 }}>
            Back to Agents
          </Button>
        </Box>
      </Container>
    );
  }

  const getStageStatus = (stageId) => {
    if (!workflow) return 'pending';
    
    // Override deployment status based on our Google Cloud Run-style logic
    if (stageId === 'deployment') {
      return isDeployed ? 'completed' : workflow.getStageStatus(stageId);
    }
    
    // For stages that depend on deployment, use our enhanced deployment status
    if (['post-testing', 'integration', 'analytics'].includes(stageId)) {
      if (!isDeployed) {
        return 'locked';
      }
      return workflow.getStageStatus(stageId);
    }
    
    return workflow.getStageStatus(stageId);
  };

  const canAccessFeature = (feature) => {
    if (feature.requiresDeployment && !isDeployed) {
      return false;
    }
    return true;
  };

  const getFeatureStatusIcon = (feature) => {
    const status = getStageStatus(feature.stage);
    
    if (!canAccessFeature(feature)) {
      return <WarningIcon sx={{ color: 'warning.main' }} />;
    }
    
    switch (status) {
      case 'completed':
        return <CheckCircleIcon sx={{ color: 'success.main' }} />;
      case 'available':
        return <ScheduleIcon sx={{ color: 'info.main' }} />;
      default:
        return <ScheduleIcon sx={{ color: 'text.disabled' }} />;
    }
  };

  const getFeatureStatusText = (feature) => {
    if (!canAccessFeature(feature)) {
      return 'Requires Deployment';
    }
    
    const status = getStageStatus(feature.stage);
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'available':
        return 'Available';
      default:
        return 'Pending';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={handleBackClick} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Avatar
            sx={{
              bgcolor: 'primary.main',
              width: 56,
              height: 56,
              mr: 3
            }}
          >
            <SmartToyIcon sx={{ fontSize: 28 }} />
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              {agent?.name || 'Untitled Agent'}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {agent?.description || 'AI Agent Dashboard - Manage all aspects of your agent'}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Chip
              label={agent?.model || 'gpt-4'}
              color="primary"
              variant="outlined"
            />
            {isDeployed && (
              <Chip
                icon={<CheckCircleIcon />}
                label={`Deployed (${successfulDeployments.length} revision${successfulDeployments.length !== 1 ? 's' : ''})`}
                color="success"
                variant="filled"
              />
            )}
            {isDeploying && (
              <Chip
                icon={<CircularProgress size={16} />}
                label="Deploying"
                color="warning"
                variant="filled"
              />
            )}
            {!isDeployed && !isDeploying && deployments.length > 0 && (
              <Chip
                label={`${deployments.length} deployment${deployments.length !== 1 ? 's' : ''} - None successful`}
                color="error"
                variant="outlined"
              />
            )}
          </Box>
        </Box>

        {/* Agent Status Alert */}
        {!isDeployed && !isDeploying && (
          <Alert 
            severity="info" 
            action={
              <Button 
                color="inherit" 
                size="small"
                onClick={() => navigate(`/agent-deployment/${agentId}`)}
              >
                Deploy Now
              </Button>
            }
          >
            {deployments.length === 0 
              ? "Agent is not deployed yet. Deploy to enable integrations and production testing."
              : `${deployments.length} deployment attempt${deployments.length !== 1 ? 's' : ''} made, but none succeeded. Deploy successfully to enable integrations.`
            }
          </Alert>
        )}

        {/* Active Deployment Info */}
        {isDeployed && activeDeployment && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Active Deployment:</strong> {activeDeployment.deployment_id?.slice(-8) || 'Unknown'}
              {activeDeployment.created_at && (
                <span> • Deployed {new Date(activeDeployment.created_at).toLocaleDateString()}</span>
              )}
              {activeDeployment.service_url && (
                <span> • <Link href={activeDeployment.service_url} target="_blank" rel="noopener noreferrer" sx={{ ml: 1 }}>Service URL</Link></span>
              )}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Quick Actions */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            startIcon={<WhatsAppIcon />}
            onClick={() => navigate(`/agent-integration/${agentId}?section=whatsapp`)}
            disabled={!isDeployed}
          >
            Setup WhatsApp
          </Button>
          <Button
            variant="outlined"
            startIcon={<WebsiteIcon />}
            onClick={() => navigate(`/agent-integration/${agentId}?section=website`)}
            disabled={!isDeployed}
          >
            Add to Website
          </Button>
          <Button
            variant="outlined"
            startIcon={<TestingIcon />}
            onClick={() => navigate(`/agent-testing/${agentId}`)}
          >
            Test Agent
          </Button>
          {(activeDeployment?.service_url || agent?.service_url) && (
            <Button
              variant="outlined"
              startIcon={<LaunchIcon />}
              href={activeDeployment?.service_url || agent?.service_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open Service
            </Button>
          )}
        </Box>
      </Paper>

      {/* Agent Management */}
      <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>
        Agent Management
      </Typography>
      
      <Grid container spacing={3}>
        {featureCards.map((feature) => {
          const Icon = feature.icon;
          const isAccessible = canAccessFeature(feature);
          const statusIcon = getFeatureStatusIcon(feature);
          const statusText = getFeatureStatusText(feature);

          return (
            <Grid item xs={12} md={6} lg={4} key={feature.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: isAccessible ? 'pointer' : 'default',
                  opacity: isAccessible ? 1 : 0.7,
                  transition: 'all 0.3s ease',
                  '&:hover': isAccessible ? {
                    transform: 'translateY(-4px)',
                    boxShadow: (theme) => theme.shadows[8],
                    borderColor: feature.color
                  } : {},
                  border: '2px solid transparent'
                }}
                onClick={() => isAccessible && navigate(feature.route)}
              >
                <CardContent sx={{ flex: 1, p: 3 }}>
                  {/* Header */}
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: `${feature.color}15`,
                        color: feature.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <Icon sx={{ fontSize: 28 }} />
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="h6" fontWeight="bold">
                          {feature.title}
                        </Typography>
                        {statusIcon}
                      </Box>
                      <Chip
                        label={statusText}
                        size="small"
                        color={isAccessible ? 'primary' : 'default'}
                        variant="outlined"
                      />
                    </Box>
                  </Box>

                  {/* Description */}
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ mb: 3, lineHeight: 1.6 }}
                  >
                    {feature.description}
                  </Typography>

                  {/* Features List */}
                  <Box>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      Features:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {feature.features.map((featureName, index) => (
                        <Chip
                          key={index}
                          label={featureName}
                          size="small"
                          variant="outlined"
                          sx={{ 
                            fontSize: '0.75rem',
                            height: 24
                          }}
                        />
                      ))}
                    </Box>
                  </Box>
                </CardContent>

                <CardActions sx={{ p: 3, pt: 0 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    disabled={!isAccessible}
                    startIcon={<LaunchIcon />}
                    sx={{
                      bgcolor: feature.color,
                      '&:hover': {
                        bgcolor: feature.color,
                        filter: 'brightness(0.9)'
                      }
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (isAccessible) navigate(feature.route);
                    }}
                  >
                    Open {feature.title}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Development Progress */}
      <Paper sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Development Progress
        </Typography>
        <WorkflowProgressIndicator 
          workflow={workflow}
          agentId={agentId}
          compact={false}
          onStageClick={handleWorkflowStageClick}
        />
      </Paper>

      {/* Notification System */}
      <NotificationSystem
        notification={notification}
        onClose={handleCloseNotification}
      />
    </Container>
  );
};

export default AgentDashboard;