import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  LinearProgress,
  Chip,
  Button,
  Collapse,
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import {
  SmartToy as SmartToyIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  BugReport as BugReportIcon,
  RocketLaunch as RocketLaunchIcon,
  PlayArrow as PlayArrowIcon,
  IntegrationInstructions as IntegrationIcon,
  Analytics as AnalyticsIcon,
  CheckCircle as CheckIcon,
  Lock as LockIcon,
  Circle as CircleIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const STAGE_ICONS = {
  'Smart-Toy': SmartToyIcon,
  'Storage': StorageIcon,
  'Api': ApiIcon,
  'BugReport': BugReportIcon,
  'Rocket-Launch': RocketLaunchIcon,
  'PlayArrow': PlayArrowIcon,
  'Integration-Instructions': IntegrationIcon,
  'Analytics': AnalyticsIcon
};

const WorkflowProgressIndicator = ({ 
  workflow, 
  agentId, 
  compact = false, 
  onStageClick 
}) => {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(!compact);
  
  const {
    stages,
    phases,
    currentStage,
    completedStages,
    getStageStatus,
    canAccessStage,
    navigateToStage,
    getWorkflowSummary,
    getPhaseProgress
  } = workflow;

  const workflowSummary = getWorkflowSummary();

  const getStageIcon = (stage, status) => {
    const IconComponent = STAGE_ICONS[stage.icon] || CircleIcon;
    
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'available':
        return <IconComponent color="primary" />;
      case 'locked':
        return <LockIcon color="disabled" />;
      default:
        return <CircleIcon color="disabled" />;
    }
  };

  const getStageColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'available': return 'primary';
      case 'locked': return 'default';
      default: return 'default';
    }
  };

  const handleStageClick = (stage) => {
    const status = getStageStatus(stage.id);
    
    if (status === 'locked') {
      return; // Don't navigate to locked stages
    }

    if (onStageClick) {
      onStageClick(stage);
    } else {
      // Default navigation
      const route = stage.route.replace(':agentId', agentId);
      navigate(route);
      navigateToStage(stage.id);
    }
  };

  const getStageDescription = (stage) => {
    const status = getStageStatus(stage.id);
    const validation = workflow.stageValidation[stage.id];
    
    if (status === 'completed') {
      return '✓ Completed';
    }
    
    if (status === 'locked' && validation?.requirements?.length > 0) {
      return `Requires: ${validation.requirements.join(', ')}`;
    }
    
    return stage.description;
  };

  if (compact) {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ py: 2 }}>
          <Box display="flex" alignItems="center" justifyContent="between">
            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="subtitle2">
                Workflow Progress
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={workflowSummary.overallProgress} 
                sx={{ minWidth: 120, height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {workflowSummary.completedStages}/{workflowSummary.totalStages} stages
              </Typography>
            </Box>
            
            <IconButton 
              onClick={() => setExpanded(!expanded)}
              size="small"
            >
              {expanded ? <CollapseIcon /> : <ExpandIcon />}
            </IconButton>
          </Box>
          
          <Collapse in={expanded}>
            <Box sx={{ mt: 2 }}>
              {renderProgressContent()}
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  }

  function renderProgressContent() {
    return (
      <Box>
        {/* Overall Progress */}
        <Box sx={{ mb: 3 }}>
          <Box display="flex" justifyContent="between" alignItems="center" mb={1}>
            <Typography variant="h6">
              Agent Development Progress
            </Typography>
            <Chip 
              label={`${workflowSummary.overallProgress}% Complete`}
              color={workflowSummary.isComplete ? 'success' : 'primary'}
              variant={workflowSummary.isComplete ? 'filled' : 'outlined'}
            />
          </Box>
          
          <LinearProgress 
            variant="determinate" 
            value={workflowSummary.overallProgress} 
            sx={{ height: 8, borderRadius: 4, mb: 1 }}
          />
          
          <Typography variant="caption" color="text.secondary">
            {workflowSummary.completedStages} of {workflowSummary.totalStages} stages completed
            {workflowSummary.requiredCompleted < workflowSummary.requiredStages && (
              <> • {workflowSummary.requiredStages - workflowSummary.requiredCompleted} required stages remaining</>
            )}
          </Typography>
        </Box>

        {/* Phase Progress */}
        <Box sx={{ mb: 3 }}>
          {phases.map(phase => {
            const phaseProgress = getPhaseProgress(phase.id);
            const phaseStages = stages.filter(stage => stage.phase === phase.id);
            
            return (
              <Box key={phase.id} sx={{ mb: 2 }}>
                <Box display="flex" justifyContent="between" alignItems="center" mb={1}>
                  <Typography variant="subtitle2">
                    {phase.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {phaseProgress.completed}/{phaseProgress.total}
                  </Typography>
                </Box>
                
                <LinearProgress 
                  variant="determinate" 
                  value={phaseProgress.percentage} 
                  sx={{ height: 6, borderRadius: 3, mb: 1 }}
                />
                
                <Typography variant="caption" color="text.secondary" display="block">
                  {phase.description}
                </Typography>
              </Box>
            );
          })}
        </Box>

        {/* Stage Stepper */}
        <Stepper orientation="vertical" nonLinear>
          {stages.map((stage, index) => {
            const status = getStageStatus(stage.id);
            const isActive = currentStage === stage.id;
            const canAccess = canAccessStage(stage.id);
            
            return (
              <Step key={stage.id} completed={status === 'completed'} active={isActive}>
                <StepLabel
                  StepIconComponent={() => getStageIcon(stage, status)}
                  onClick={() => canAccess && handleStageClick(stage)}
                  sx={{ 
                    cursor: canAccess ? 'pointer' : 'default',
                    '& .MuiStepLabel-labelContainer': {
                      cursor: canAccess ? 'pointer' : 'default'
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography 
                      variant="subtitle2" 
                      color={status === 'locked' ? 'text.disabled' : 'text.primary'}
                    >
                      {stage.name}
                    </Typography>
                    
                    {stage.required && (
                      <Chip 
                        label="Required" 
                        size="small" 
                        color="warning" 
                        variant="outlined"
                      />
                    )}
                    
                    <Chip 
                      label={status === 'completed' ? 'Completed' : 
                             status === 'available' ? 'Available' : 'Locked'}
                      size="small"
                      color={getStageColor(status)}
                      variant={status === 'completed' ? 'filled' : 'outlined'}
                    />
                  </Box>
                </StepLabel>
                
                <StepContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {getStageDescription(stage)}
                  </Typography>
                  
                  {canAccess && status !== 'completed' && (
                    <Button 
                      variant="outlined" 
                      size="small"
                      onClick={() => handleStageClick(stage)}
                      sx={{ mt: 1 }}
                    >
                      {isActive ? 'Continue' : 'Start'} {stage.name}
                    </Button>
                  )}
                </StepContent>
              </Step>
            );
          })}
        </Stepper>

        {/* Ready to Deploy Alert */}
        {workflowSummary.canDeploy && !workflowSummary.isComplete && (
          <Alert severity="success" sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Ready for Deployment!
            </Typography>
            <Typography variant="body2">
              You've completed all required stages. You can now deploy your agent and continue with testing and integrations.
            </Typography>
          </Alert>
        )}

        {/* Completion Alert */}
        {workflowSummary.isComplete && (
          <Alert severity="success" sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              🎉 Workflow Complete!
            </Typography>
            <Typography variant="body2">
              Your agent is fully configured, deployed, and ready for production use.
            </Typography>
          </Alert>
        )}
      </Box>
    );
  }

  return (
    <Card>
      <CardContent>
        {renderProgressContent()}
      </CardContent>
    </Card>
  );
};

export default WorkflowProgressIndicator;