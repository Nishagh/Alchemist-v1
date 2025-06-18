/**
 * Agent Deployment Manager
 * 
 * Component for managing optimized agent deployments with real-time progress tracking
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Grid,
  IconButton,
  Menu,
  MenuItem,
  LinearProgress,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Collapse,
  Skeleton,
  Tooltip
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  MoreVert as MoreVertIcon,
  CloudQueue as CloudQueueIcon,
  Refresh as RefreshIcon,
  Launch as LaunchIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Cancel as CancelIcon,
  Timeline as TimelineIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';

import { 
  deployAgent, 
  getDeploymentStatus, 
  listDeployments, 
  cancelDeployment,
  pollDeploymentStatus,
  subscribeToDeploymentUpdates
} from '../../../services';

const AgentDeploymentManager = ({ 
  agentId, 
  onNotification, 
  disabled = false 
}) => {
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedDeployment, setSelectedDeployment] = useState(null);
  const [currentDeployment, setCurrentDeployment] = useState(null);
  const [deploymentProgress, setDeploymentProgress] = useState(null);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [showLogsExpanded, setShowLogsExpanded] = useState(false);
  const pollingRef = useRef(null);
  const unsubscribeRef = useRef(null);

  // Set up real-time subscription for deployments
  useEffect(() => {
    if (!agentId) {
      setLoadingData(false);
      return;
    }

    setLoadingData(true);
    
    // Set up real-time subscription to deployment updates
    const unsubscribe = subscribeToDeploymentUpdates(
      agentId,
      (deployments) => {
        setDeployments(deployments);
        setLoadingData(false);
      },
      (error) => {
        console.error('Deployment subscription error:', error);
        onNotification({
          message: 'Failed to load deployment updates',
          severity: 'error',
          timestamp: Date.now()
        });
        setLoadingData(false);
      }
    );
    
    unsubscribeRef.current = unsubscribe;
    
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
      if (pollingRef.current) {
        pollingRef.current = null;
      }
    };
  }, [agentId]);

  const loadDeployments = async () => {
    try {
      setLoadingData(true);
      const result = await listDeployments({ 
        agentId: agentId,
        limit: 10 
      });
      
      setDeployments(result.deployments || []);
    } catch (error) {
      console.error('Error loading deployments:', error);
      onNotification({
        message: 'Failed to load deployment history',
        severity: 'error',
        timestamp: Date.now()
      });
    } finally {
      setLoadingData(false);
    }
  };

  const handleMenuOpen = (event, deployment) => {
    setAnchorEl(event.currentTarget);
    setSelectedDeployment(deployment);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDeployment(null);
  };

  const handleDeploy = async () => {
    if (!agentId) {
      onNotification({
        message: 'Agent ID is required for deployment',
        severity: 'error',
        timestamp: Date.now()
      });
      return;
    }

    setLoading(true);
    
    try {
      // Start deployment
      const deploymentResult = await deployAgent(agentId, {
        priority: 8  // High priority for manual deployments
      });

      setCurrentDeployment(deploymentResult);
      setDeploymentProgress({
        deployment_id: deploymentResult.deployment_id,
        status: 'queued',
        progress_percentage: 0,
        current_step: 'Queued for optimized deployment',
        logs: []
      });
      setShowProgressDialog(true);

      onNotification({
        message: 'Deployment started successfully. Tracking progress...',
        severity: 'success',
        timestamp: Date.now()
      });

      // Start polling for progress
      pollingRef.current = deploymentResult.deployment_id;
      
      try {
        const finalStatus = await pollDeploymentStatus(
          deploymentResult.deployment_id,
          (progressUpdate) => {
            // Only update if this is still the current deployment
            if (pollingRef.current === deploymentResult.deployment_id) {
              setDeploymentProgress(progressUpdate);
            }
          },
          {
            pollInterval: 3000,
            timeoutMs: 600000 // 10 minutes
          }
        );

        if (pollingRef.current === deploymentResult.deployment_id) {
          setDeploymentProgress(finalStatus);
          
          onNotification({
            message: `🚀 Agent deployed successfully! Service URL: ${finalStatus.service_url}`,
            severity: 'success',
            timestamp: Date.now()
          });
          
          // Real-time subscription will automatically update the list
        }

      } catch (pollError) {
        console.error('Deployment polling error:', pollError);
        
        if (pollingRef.current === deploymentResult.deployment_id) {
          onNotification({
            message: `Deployment failed: ${pollError.message}`,
            severity: 'error',
            timestamp: Date.now()
          });
        }
      }

    } catch (error) {
      console.error('Error starting deployment:', error);
      
      onNotification({
        message: `Failed to start deployment: ${error.message}`,
        severity: 'error',
        timestamp: Date.now()
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCancelDeployment = async () => {
    if (!currentDeployment) return;

    try {
      await cancelDeployment(currentDeployment.deployment_id);
      pollingRef.current = null;
      
      setDeploymentProgress(prev => ({
        ...prev,
        status: 'cancelled',
        current_step: 'Deployment cancelled'
      }));

      onNotification({
        message: 'Deployment cancelled successfully',
        severity: 'info',
        timestamp: Date.now()
      });

    } catch (error) {
      console.error('Error cancelling deployment:', error);
      onNotification({
        message: `Failed to cancel deployment: ${error.message}`,
        severity: 'error',
        timestamp: Date.now()
      });
    }
  };

  const handleCloseProgressDialog = () => {
    setShowProgressDialog(false);
    setDeploymentProgress(null);
    setCurrentDeployment(null);
    pollingRef.current = null;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      case 'deploying':
      case 'building_image':
      case 'generating_code': return 'warning';
      case 'queued': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'failed': return <ErrorIcon />;
      case 'cancelled': return <CancelIcon />;
      case 'deploying':
      case 'building_image':
      case 'generating_code': return <CloudUploadIcon />;
      case 'queued': return <CloudQueueIcon />;
      default: return <CloudQueueIcon />;
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} minutes ago`;
      if (diffHours < 24) return `${diffHours} hours ago`;
      if (diffDays < 7) return `${diffDays} days ago`;
      
      return date.toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  const getDeploymentSteps = () => {
    return [
      { key: 'queued', label: 'Queued', description: 'Deployment queued for processing' },
      { key: 'initializing', label: 'Initializing', description: 'Setting up deployment environment' },
      { key: 'fetching_config', label: 'Fetching Config', description: 'Loading agent configuration from Firestore' },
      { key: 'generating_code', label: 'Generating Code', description: 'Creating optimized agent-specific code' },
      { key: 'building_image', label: 'Building Image', description: 'Building optimized container image' },
      { key: 'deploying', label: 'Deploying', description: 'Deploying to Google Cloud Run' },
      { key: 'completed', label: 'Completed', description: 'Deployment completed successfully' }
    ];
  };

  const getCurrentStepIndex = () => {
    if (!deploymentProgress) return -1;
    
    const steps = getDeploymentSteps();
    return steps.findIndex(step => step.key === deploymentProgress.status);
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
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SpeedIcon color="primary" />
            Optimized Deployment
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Deploy your agent with 60-80% faster performance and pre-loaded configuration
          </Typography>
        </Box>
        <Box>
          <Button
            variant="contained"
            startIcon={<CloudUploadIcon />}
            onClick={handleDeploy}
            disabled={disabled || loading}
            sx={{ mr: 1 }}
          >
            Deploy Agent
          </Button>
          <IconButton 
            onClick={loadDeployments} 
            disabled={disabled || loadingData}
          >
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Scrollable Content */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>

        {/* Performance Benefits */}
        <Alert 
          severity="info" 
          sx={{ mb: 3, borderRadius: 2 }}
          icon={<SpeedIcon />}
        >
          <Typography variant="body2">
            <strong>Optimized Deployment Benefits:</strong> Configuration baked at build time • 
            Tools pre-initialized • Zero runtime Firestore reads • 60-80% faster response times
          </Typography>
        </Alert>

        {loading && (
          <Box sx={{ mb: 3 }}>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Starting optimized deployment...
            </Typography>
          </Box>
        )}

        {/* Deployment History */}
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon />
          Deployment History
        </Typography>

        {loadingData ? (
          <Grid container spacing={3}>
            {[1, 2].map((i) => (
              <Grid item xs={12} md={6} key={i}>
                <Card>
                  <CardContent>
                    <Skeleton variant="text" width="60%" height={32} />
                    <Skeleton variant="text" width="40%" height={24} sx={{ mb: 2 }} />
                    <Skeleton variant="text" width="80%" />
                    <Skeleton variant="text" width="70%" />
                    <Skeleton variant="text" width="60%" />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : deployments.length === 0 ? (
          <Card sx={{ textAlign: 'center', py: 6 }}>
            <CardContent>
              <CloudQueueIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No deployments yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Deploy your agent to get started with optimized performance
              </Typography>
              <Button
                variant="contained"
                startIcon={<CloudUploadIcon />}
                onClick={handleDeploy}
                disabled={disabled || loading}
              >
                Deploy Now
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Grid container spacing={3}>
            {deployments.map((deployment) => (
              <Grid item xs={12} md={6} key={deployment.deployment_id}>
                <Card 
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative'
                  }}
                >
                  <CardContent sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          Deployment
                        </Typography>
                        <Chip
                          icon={getStatusIcon(deployment.status)}
                          label={deployment.status.replace('_', ' ').toUpperCase()}
                          color={getStatusColor(deployment.status)}
                          size="small"
                          sx={{ mb: 1 }}
                        />
                      </Box>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, deployment)}
                        disabled={disabled}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Box sx={{ space: 1 }}>
                      {deployment.service_url && (
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Service URL:</strong> 
                          <Tooltip title="Open service">
                            <Button
                              size="small"
                              href={deployment.service_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ ml: 1, minWidth: 'auto', p: 0.5 }}
                            >
                              <LaunchIcon fontSize="small" />
                            </Button>
                          </Tooltip>
                        </Typography>
                      )}
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Type:</strong> Optimized (60-80% faster)
                      </Typography>
                      
                      {deployment.progress_percentage !== undefined && (
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Progress:</strong> {deployment.progress_percentage}%
                        </Typography>
                      )}
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Started:</strong> {formatTimestamp(deployment.created_at)}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">
                        <strong>Updated:</strong> {formatTimestamp(deployment.updated_at)}
                      </Typography>
                    </Box>
                  </CardContent>

                  <CardActions sx={{ pt: 0 }}>
                    {deployment.service_url && (
                      <Button 
                        size="small"
                        href={deployment.service_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        startIcon={<LaunchIcon />}
                      >
                        Open Service
                      </Button>
                    )}
                    <Button 
                      size="small" 
                      startIcon={<SettingsIcon />}
                      disabled={disabled}
                    >
                      Details
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Deployment Progress Dialog */}
        <Dialog
          open={showProgressDialog}
          onClose={() => {}}
          maxWidth="md"
          fullWidth
          disableEscapeKeyDown={deploymentProgress?.status !== 'completed' && deploymentProgress?.status !== 'failed'}
        >
          <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CloudUploadIcon />
            Optimized Deployment Progress
          </DialogTitle>
          
          <DialogContent>
            {deploymentProgress && (
              <Box>
                {/* Progress Bar */}
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">
                      {deploymentProgress.current_step}
                    </Typography>
                    <Typography variant="body2">
                      {deploymentProgress.progress_percentage}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={deploymentProgress.progress_percentage} 
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                {/* Deployment Steps */}
                <Stepper activeStep={getCurrentStepIndex()} orientation="vertical">
                  {getDeploymentSteps().map((step, index) => (
                    <Step key={step.key}>
                      <StepLabel>
                        {step.label}
                      </StepLabel>
                      <StepContent>
                        <Typography variant="body2" color="text.secondary">
                          {step.description}
                        </Typography>
                      </StepContent>
                    </Step>
                  ))}
                </Stepper>

                {/* Deployment Logs */}
                {deploymentProgress.logs && deploymentProgress.logs.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Button
                      onClick={() => setShowLogsExpanded(!showLogsExpanded)}
                      startIcon={showLogsExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      size="small"
                    >
                      Deployment Logs ({deploymentProgress.logs.length})
                    </Button>
                    
                    <Collapse in={showLogsExpanded}>
                      <List dense sx={{ bgcolor: 'grey.50', borderRadius: 1, mt: 1, maxHeight: 200, overflow: 'auto' }}>
                        {deploymentProgress.logs.map((log, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <CheckCircleIcon fontSize="small" color="success" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={log}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Collapse>
                  </Box>
                )}

                {/* Error Message */}
                {deploymentProgress.error_message && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {deploymentProgress.error_message}
                  </Alert>
                )}

                {/* Success Message */}
                {deploymentProgress.status === 'completed' && deploymentProgress.service_url && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      🚀 Agent deployed successfully! Your optimized agent is now running at:
                    </Typography>
                    <Button
                      href={deploymentProgress.service_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{ mt: 1 }}
                      variant="outlined"
                      size="small"
                    >
                      {deploymentProgress.service_url}
                    </Button>
                  </Alert>
                )}
              </Box>
            )}
          </DialogContent>
          
          <DialogActions>
            {deploymentProgress?.status === 'completed' || deploymentProgress?.status === 'failed' || deploymentProgress?.status === 'cancelled' ? (
              <Button onClick={handleCloseProgressDialog}>
                Close
              </Button>
            ) : (
              <>
                <Button onClick={handleCancelDeployment} color="error">
                  Cancel Deployment
                </Button>
                <Button disabled>
                  Deploying...
                </Button>
              </>
            )}
          </DialogActions>
        </Dialog>

        {/* Context Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleMenuClose}>
            <SettingsIcon sx={{ mr: 1 }} />
            View Details
          </MenuItem>
          {selectedDeployment?.service_url && (
            <MenuItem 
              onClick={() => {
                window.open(selectedDeployment.service_url, '_blank');
                handleMenuClose();
              }}
            >
              <LaunchIcon sx={{ mr: 1 }} />
              Open Service
            </MenuItem>
          )}
          <MenuItem onClick={handleMenuClose}>
            <RefreshIcon sx={{ mr: 1 }} />
            Redeploy
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );
};

export default AgentDeploymentManager;