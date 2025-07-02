/**
 * MCP Deployment Status
 * 
 * Component for displaying and managing MCP server deployment status
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Fade
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Api as ApiIcon,
  Build as BuildIcon,
  Link as LinkIcon,
  Functions as FunctionsIcon,
  OpenInNew as OpenInNewIcon,
  Timeline as TimelineIcon,
  Pending as PendingIcon
} from '@mui/icons-material';
import { formatDeploymentStatus, convertTimestamp } from '../../../utils/agentEditorHelpers';
import StatusBadge from '../../shared/StatusBadge';
import { subscribeToDeploymentStatus } from '../../../services/mcpServer/mcpServerService';

const McpDeploymentStatus = ({ 
  agentId,
  deploymentStatus,
  integrationSummary,
  deploymentHistory = [],
  onDeploy,
  onStop,
  deploying = false,
  disabled = false,
  currentDeploymentId = null // New prop for tracking current deployment
}) => {
  const [expandedAccordion, setExpandedAccordion] = useState(false);
  const [realtimeDeploymentStatus, setRealtimeDeploymentStatus] = useState(null);
  const [deploymentError, setDeploymentError] = useState(null);

  // Set up real-time listener for deployment status
  useEffect(() => {
    let unsubscribe = null;
    
    if (currentDeploymentId) {
      console.log('Setting up real-time listener for deployment:', currentDeploymentId);
      
      try {
        unsubscribe = subscribeToDeploymentStatus(
          currentDeploymentId,
          (deploymentData, error) => {
            if (error) {
              console.error('Real-time deployment listener error:', error);
              setDeploymentError(error.message);
              return;
            }
            
            if (deploymentData) {
              console.log('Real-time deployment update:', deploymentData);
              setRealtimeDeploymentStatus(deploymentData);
              setDeploymentError(null);
            } else {
              console.log('Deployment document not found');
              setRealtimeDeploymentStatus(null);
            }
          }
        );
      } catch (error) {
        console.error('Error setting up deployment listener:', error);
        setDeploymentError(error.message);
      }
    }
    
    return () => {
      if (unsubscribe) {
        console.log('Cleaning up real-time deployment listener');
        unsubscribe();
      }
    };
  }, [currentDeploymentId]);

  const getDeploymentSteps = () => {
    // Use real-time status if available, otherwise fall back to prop
    const currentStatus = realtimeDeploymentStatus || deploymentStatus;
    const progressSteps = realtimeDeploymentStatus?.progress_steps || [];
    
    // If we have progress steps from real-time data, use them
    if (progressSteps.length > 0) {
      return progressSteps.map(step => {
        // Normalize step names to be more user-friendly
        const stepNames = {
          'queued': 'Queued',
          'validating': 'Validating Specifications',
          'building': 'Building MCP Server',
          'deploying': 'Deploying to Cloud',
          'testing': 'Testing Integration'
        };
        
        return {
          label: stepNames[step.step] || step.step.charAt(0).toUpperCase() + step.step.slice(1),
          description: step.message || `${stepNames[step.step] || step.step} in progress`,
          status: step.status
        };
      });
    }
    
    // Fallback to static steps based on status
    const steps = [
      {
        label: 'Preparing Deployment',
        description: 'Validating API specifications and preparing deployment environment',
        status: 'completed'
      },
      {
        label: 'Building MCP Server',
        description: 'Creating containerized MCP server with your API integrations',
        status: currentStatus?.status === 'pending' ? 'active' : 
                currentStatus?.status === 'deploying' ? 'completed' : 'pending'
      },
      {
        label: 'Deploying to Cloud',
        description: 'Deploying server to cloud infrastructure and configuring endpoints',
        status: currentStatus?.status === 'deploying' ? 'active' :
                currentStatus?.status === 'deployed' ? 'completed' : 'pending'
      },
      {
        label: 'Testing Integration',
        description: 'Verifying server health and testing API connectivity',
        status: currentStatus?.status === 'deployed' ? 'completed' : 'pending'
      }
    ];

    return steps;
  };

  const getActiveStep = () => {
    const currentStatus = realtimeDeploymentStatus || deploymentStatus;
    if (!currentStatus) return -1;
    
    // If we have progress steps, find the active one
    const progressSteps = realtimeDeploymentStatus?.progress_steps || [];
    if (progressSteps.length > 0) {
      // Find the last completed step and the first active/in_progress step
      let lastCompletedIndex = -1;
      let activeStepIndex = -1;
      
      progressSteps.forEach((step, index) => {
        if (step.status === 'completed') {
          lastCompletedIndex = index;
        } else if ((step.status === 'active' || step.status === 'in_progress') && activeStepIndex === -1) {
          activeStepIndex = index;
        }
      });
      
      // If there's an active step, return its index
      if (activeStepIndex >= 0) {
        return activeStepIndex;
      }
      
      // If there are completed steps but no active step, return the next step after the last completed
      if (lastCompletedIndex >= 0) {
        return Math.min(lastCompletedIndex + 1, progressSteps.length - 1);
      }
      
      // If no steps are completed, return 0
      return 0;
    }
    
    // Fallback to status-based logic
    switch (currentStatus.status) {
      case 'queued':
        return 0;
      case 'validating':
      case 'pending':
        return 1;
      case 'building':
        return 2;
      case 'deploying':
        return 3;
      case 'deployed':
        return 4;
      case 'failed':
        return 1; // Show where it failed
      default:
        return 0;
    }
  };

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpandedAccordion(isExpanded ? panel : false);
  };

  const NoDeploymentState = () => (
    <Box 
      sx={{ 
        textAlign: 'center', 
        py: 6,
        color: 'text.secondary'
      }}
    >
      <ApiIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
      <Typography variant="h6" sx={{ mb: 1 }}>
        No MCP Server Deployed
      </Typography>
      <Typography variant="body2" sx={{ mb: 3 }}>
        Deploy an MCP server to make your API integrations available to the agent
      </Typography>
      <Button
        variant="contained"
        onClick={onDeploy}
        startIcon={deploying ? null : <PlayArrowIcon />}
        disabled={disabled || deploying}
      >
        {deploying ? 'Deploying...' : 'Deploy MCP Server'}
      </Button>
    </Box>
  );

  const renderDeploymentProgress = () => {
    const currentStatus = realtimeDeploymentStatus || deploymentStatus;
    if (!currentStatus) return null;

    const activeStep = getActiveStep();
    const steps = getDeploymentSteps();

    // Debug logging
    console.log('Rendering deployment progress:', {
      activeStep,
      steps: steps.map((s, i) => ({ index: i, label: s.label, status: s.status })),
      progressSteps: realtimeDeploymentStatus?.progress_steps,
      currentStatus: currentStatus.status
    });

    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
          Deployment Progress
        </Typography>
        
        {/* Real-time progress information */}
        {realtimeDeploymentStatus && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Current Step: {realtimeDeploymentStatus.current_step}
            </Typography>
            {realtimeDeploymentStatus.progress !== undefined && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={realtimeDeploymentStatus.progress} 
                  sx={{ flex: 1 }}
                />
                <Typography variant="body2" color="text.secondary">
                  {realtimeDeploymentStatus.progress}%
                </Typography>
              </Box>
            )}
          </Box>
        )}
        
        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((step, index) => (
            <Step key={step.label} completed={step.status === 'completed'}>
              <StepLabel
                StepIconComponent={({ active, completed, error }) => {
                  // Check for error state first
                  if (currentStatus.status === 'failed' && index === activeStep) {
                    return <ErrorIcon color="error" />;
                  }
                  
                  // Use step status for icon rendering
                  if (step.status === 'completed') {
                    return <CheckCircleIcon color="success" />;
                  }
                  
                  if (step.status === 'active' || step.status === 'in_progress') {
                    return <PendingIcon color="primary" sx={{ animation: 'pulse 2s infinite' }} />;
                  }
                  
                  // Default pending state
                  return <ScheduleIcon color="disabled" />;
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                  {step.label}
                </Typography>
              </StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
                {(step.status === 'active' || step.status === 'in_progress') && (
                  <Box sx={{ mt: 1 }}>
                    <LinearProgress size="small" />
                  </Box>
                )}
              </StepContent>
            </Step>
          ))}
        </Stepper>
        
        {/* Error display */}
        {(currentStatus.error_message || deploymentError) && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 1 }}>
              Deployment Error:
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {currentStatus.error_message || deploymentError}
            </Typography>
          </Alert>
        )}
      </Box>
    );
  };

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        height: '100%',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
              Deployment Status
            </Typography>
            <Typography variant="body2" color="text.secondary">
              MCP server deployment and management
            </Typography>
          </Box>
          
          {deploymentStatus && (
            <StatusBadge 
              status={deploymentStatus.status} 
              variant="outlined"
            />
          )}
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, p: 3, overflowY: 'auto', minHeight: 0 }}>
        {!deploymentStatus && !integrationSummary ? (
          <NoDeploymentState />
        ) : (
          <Box>
            {/* Current Status */}
            {deploymentStatus && (
              <Fade in={true}>
                <Box sx={{ mb: 3 }}>
                  <Alert 
                    severity={
                      (integrationSummary?.status === 'active' || deploymentStatus?.status === 'deployed') ? 'success' :
                      deploymentStatus?.status === 'failed' ? 'error' : 'info'
                    }
                  >
                    <Typography variant="body2">
                      {integrationSummary?.status ? (
                        <>MCP Server Status: {integrationSummary.status === 'active' ? 'Active' : integrationSummary.status}</>
                      ) : (
                        <>Deployment Status: {formatDeploymentStatus(deploymentStatus?.status || 'pending')}</>
                      )}
                      {(integrationSummary?.service_url || deploymentStatus?.url) && (
                        <> • Server URL: {integrationSummary?.service_url || deploymentStatus?.url}</>
                      )}
                    </Typography>
                  </Alert>
                </Box>
              </Fade>
            )}

            {/* Deployment Progress */}
            {deploymentStatus && renderDeploymentProgress()}

            {/* Integration Summary */}
            {integrationSummary && (
              <>
                {/* Server Info */}
                <Accordion 
                  expanded={expandedAccordion === 'serverInfo'} 
                  onChange={handleAccordionChange('serverInfo')}
                  sx={{ mt: 3 }}
                >
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <BuildIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        Server Information
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {integrationSummary.server_info?.name && (
                        <ListItem>
                          <ListItemText
                            primary="Server Name"
                            secondary={integrationSummary.server_info.name}
                          />
                        </ListItem>
                      )}
                      {integrationSummary.server_info?.description && (
                        <ListItem>
                          <ListItemText
                            primary="Description"
                            secondary={integrationSummary.server_info.description}
                          />
                        </ListItem>
                      )}
                      {integrationSummary.server_info?.version && (
                        <ListItem>
                          <ListItemText
                            primary="Version"
                            secondary={integrationSummary.server_info.version}
                          />
                        </ListItem>
                      )}
                      {integrationSummary.deployment_id && (
                        <ListItem>
                          <ListItemText
                            primary="Deployment ID"
                            secondary={integrationSummary.deployment_id}
                          />
                        </ListItem>
                      )}
                      {integrationSummary.deployed_at && (
                        <ListItem>
                          <ListItemText
                            primary="Deployed At"
                            secondary={convertTimestamp(integrationSummary.deployed_at)?.toLocaleString() || 'Unknown'}
                          />
                        </ListItem>
                      )}
                    </List>
                  </AccordionDetails>
                </Accordion>

                {/* Endpoints */}
                {integrationSummary.endpoints && Object.keys(integrationSummary.endpoints).length > 0 && (
                  <Accordion 
                    expanded={expandedAccordion === 'endpoints'} 
                    onChange={handleAccordionChange('endpoints')}
                    sx={{ mt: 1 }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <LinkIcon sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                          Available Endpoints ({Object.keys(integrationSummary.endpoints).length})
                        </Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List dense>
                        {Object.entries(integrationSummary.endpoints).map(([key, url]) => (
                          <ListItem key={key}>
                            <ListItemText
                              primary={key.charAt(0).toUpperCase() + key.slice(1)}
                              secondary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="caption" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                                    {url}
                                  </Typography>
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    startIcon={<OpenInNewIcon />}
                                    href={url}
                                    target="_blank"
                                    sx={{ minWidth: 'auto', px: 1 }}
                                  >
                                    Test
                                  </Button>
                                </Box>
                              }
                            />
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* MCP Tools */}
                {integrationSummary.tools && integrationSummary.tools.length > 0 && (
                  <Accordion 
                    expanded={expandedAccordion === 'tools'} 
                    onChange={handleAccordionChange('tools')}
                    sx={{ mt: 1 }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <FunctionsIcon sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                          MCP Tools ({integrationSummary.tools.length})
                        </Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List dense>
                        {integrationSummary.tools.map((tool, index) => (
                          <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                    {tool.name}
                                  </Typography>
                                  <Chip 
                                    label={tool.method}
                                    size="small"
                                    color={tool.method === 'GET' ? 'primary' : tool.method === 'POST' ? 'secondary' : 'default'}
                                    sx={{ fontSize: '0.7rem', height: 20 }}
                                  />
                                  {tool.args_count > 0 && (
                                    <Chip 
                                      label={`${tool.args_count} args`}
                                      size="small"
                                      variant="outlined"
                                      sx={{ fontSize: '0.7rem', height: 20 }}
                                    />
                                  )}
                                </Box>
                              }
                              secondary={
                                <Box sx={{ mt: 0.5 }}>
                                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                    {tool.description}
                                  </Typography>
                                  <Typography variant="caption" sx={{ fontFamily: 'monospace', wordBreak: 'break-all', color: 'text.secondary' }}>
                                    {tool.url_template}
                                  </Typography>
                                </Box>
                              }
                            />
                            {index < integrationSummary.tools.length - 1 && (
                              <Box sx={{ width: '100%', mt: 1, mb: 1, borderBottom: '1px solid', borderColor: 'divider' }} />
                            )}
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                )}
              </>
            )}

            {/* Deployment History */}
            {deploymentHistory.length > 0 && (
              <Accordion 
                expanded={expandedAccordion === 'deploymentHistory'} 
                onChange={handleAccordionChange('deploymentHistory')}
                sx={{ mt: 1 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TimelineIcon sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                      Deployment History ({deploymentHistory.length})
                    </Typography>
                    {deploymentHistory.some(d => d.status === 'failed') && (
                      <Chip 
                        label="Issues Found" 
                        size="small" 
                        color="error" 
                        variant="outlined"
                        sx={{ ml: 2, fontSize: '0.7rem' }}
                      />
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ maxHeight: 250, overflow: 'auto' }}>
                    {deploymentHistory.map((deployment, index) => (
                      <Box 
                        key={deployment.id} 
                        sx={{ 
                          mb: index < deploymentHistory.length - 1 ? 1 : 0,
                          p: 1.5,
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                          bgcolor: deployment.status === 'completed' 
                            ? 'success.50'
                            : deployment.status === 'failed'
                            ? 'error.50'
                            : 'info.50'
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {deployment.status === 'completed' ? (
                              <CheckCircleIcon color="success" sx={{ mr: 1, fontSize: 16 }} />
                            ) : deployment.status === 'failed' ? (
                              <ErrorIcon color="error" sx={{ mr: 1, fontSize: 16 }} />
                            ) : deployment.status === 'in_progress' ? (
                              <PendingIcon color="info" sx={{ mr: 1, fontSize: 16 }} />
                            ) : (
                              <ScheduleIcon color="warning" sx={{ mr: 1, fontSize: 16 }} />
                            )}
                            <Typography variant="caption" fontWeight="medium" sx={{ fontSize: '0.8rem' }}>
                              {deployment.deployment_id ? `Deployment ${deployment.deployment_id.slice(-8)}` : `Deployment ${deployment.id.slice(-8)}`}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip
                              label={deployment.status || 'pending'}
                              size="small"
                              color={
                                deployment.status === 'completed' ? 'success' :
                                deployment.status === 'failed' ? 'error' :
                                deployment.status === 'in_progress' ? 'info' : 'default'
                              }
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                        
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                          {deployment.created_at ? (
                            `Started: ${convertTimestamp(deployment.created_at)?.toLocaleString() || 'Unknown'}`
                          ) : deployment.started_at ? (
                            `Started: ${convertTimestamp(deployment.started_at)?.toLocaleString() || 'Unknown'}`
                          ) : (
                            'Start time not available'
                          )}
                        </Typography>
                        
                        {deployment.completed_at && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                            {deployment.status === 'failed' ? 'Failed' : 'Completed'}: {convertTimestamp(deployment.completed_at)?.toLocaleString() || 'Unknown'}
                          </Typography>
                        )}
                        
                        {deployment.last_updated && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                            Last updated: {convertTimestamp(deployment.last_updated)?.toLocaleString() || 'Unknown'}
                          </Typography>
                        )}
                        
                        {deployment.current_step && (
                          <Typography variant="caption" color="info.main" sx={{ display: 'block', mb: 1 }}>
                            Step: {deployment.current_step}
                          </Typography>
                        )}
                        
                        {deployment.progress !== undefined && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                            Progress: {deployment.progress}%
                          </Typography>
                        )}
                        
                        {deployment.error_message && (
                          <Box sx={{ mt: 1, p: 1, bgcolor: 'error.50', borderRadius: 1 }}>
                            <Typography variant="caption" color="error.main" sx={{ display: 'block', fontWeight: 'medium', mb: 1 }}>
                              Error Details:
                            </Typography>
                            <Typography variant="caption" color="error.main" sx={{ display: 'block', whiteSpace: 'pre-wrap', maxHeight: 150, overflow: 'auto' }}>
                              {deployment.error_message}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Action Buttons */}
            <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {!integrationSummary || integrationSummary.status !== 'active' ? (
                <Button
                  variant="contained"
                  onClick={onDeploy}
                  startIcon={deploying ? null : <PlayArrowIcon />}
                  disabled={disabled || deploying}
                >
                  {deploying ? 'Deploying...' : 'Deploy MCP Server'}
                </Button>
              ) : (
                <>
                  <Button
                    variant="outlined"
                    onClick={onDeploy}
                    startIcon={<RefreshIcon />}
                    disabled={disabled || deploying}
                  >
                    Redeploy
                  </Button>
                  {integrationSummary.service_url && (
                    <Button
                      variant="outlined"
                      startIcon={<OpenInNewIcon />}
                      href={integrationSummary.service_url}
                      target="_blank"
                    >
                      Open Server
                    </Button>
                  )}
                  {integrationSummary.mcp_config_url && (
                    <Button
                      variant="outlined"
                      startIcon={<OpenInNewIcon />}
                      href={integrationSummary.mcp_config_url}
                      target="_blank"
                    >
                      View Config
                    </Button>
                  )}
                  {onStop && (
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={onStop}
                      startIcon={<StopIcon />}
                      disabled={disabled}
                    >
                      Stop Server
                    </Button>
                  )}
                </>
              )}
            </Box>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default McpDeploymentStatus;