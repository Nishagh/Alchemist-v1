import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Alert,
  Divider,
  Tooltip,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Psychology as ThinkingIcon,
  Timeline as TimelineIcon,
  CompareArrows as CompareIcon,
  Visibility as UmweltIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Styled components
const TraceCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  '&:hover': {
    boxShadow: theme.shadows[4]
  }
}));

const StepChip = styled(Chip)(({ theme, stepType }) => {
  const stepColors = {
    thinking: { bg: '#e3f2fd', color: '#1976d2' },
    action: { bg: '#e8f5e8', color: '#388e3c' },
    observation: { bg: '#fff3e0', color: '#f57c00' },
    decision: { bg: '#f3e5f5', color: '#7b1fa2' }
  };
  
  const colors = stepColors[stepType] || stepColors.thinking;
  
  return {
    backgroundColor: colors.bg,
    color: colors.color,
    fontWeight: 'bold'
  };
});

const DiffContainer = styled(Box)(({ theme, diffType }) => {
  const diffColors = {
    added: { border: '#22c55e', bg: 'rgba(34, 197, 94, 0.05)' },
    removed: { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.05)' },
    modified: { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.05)' }
  };
  
  const colors = diffColors[diffType] || diffColors.modified;
  
  return {
    borderLeft: `3px solid ${colors.border}`,
    backgroundColor: colors.bg,
    padding: theme.spacing(1),
    borderRadius: theme.shape.borderRadius,
    marginBottom: theme.spacing(1)
  };
});

const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    month: 'short',
    day: 'numeric'
  });
};

const formatDuration = (startTime, endTime) => {
  const duration = new Date(endTime) - new Date(startTime);
  if (duration < 1000) return `${duration}ms`;
  if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
  return `${(duration / 60000).toFixed(1)}m`;
};

const getStepIcon = (stepType) => {
  const icons = {
    thinking: <ThinkingIcon fontSize="small" />,
    action: <TrendingUpIcon fontSize="small" />,
    observation: <UmweltIcon fontSize="small" />,
    decision: <TimelineIcon fontSize="small" />
  };
  
  return icons[stepType] || <InfoIcon fontSize="small" />;
};

const getDiffIcon = (diffType) => {
  const icons = {
    added: <CheckCircleIcon color="success" fontSize="small" />,
    removed: <ErrorIcon color="error" fontSize="small" />,
    modified: <WarningIcon color="warning" fontSize="small" />
  };
  
  return icons[diffType] || <InfoIcon fontSize="small" />;
};

const UmweltDiffViewer = ({ diff, timestamp }) => {
  if (!diff || Object.keys(diff).length === 0) {
    return (
      <Typography variant="body2" color="textSecondary" sx={{ fontStyle: 'italic' }}>
        No Umwelt changes in this step
      </Typography>
    );
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        <UmweltIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Umwelt Changes
      </Typography>
      
      {Object.entries(diff).map(([key, change], index) => (
        <DiffContainer key={index} diffType={change.type}>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            {getDiffIcon(change.type)}
            <Typography variant="body2" component="span" fontWeight="bold">
              {key}
            </Typography>
            <Chip 
              label={change.type} 
              size="small" 
              color={change.type === 'added' ? 'success' : 
                     change.type === 'removed' ? 'error' : 'warning'}
              variant="outlined"
            />
          </Box>
          
          {change.type === 'added' && (
            <Box>
              <Typography variant="caption" color="textSecondary">Added:</Typography>
              <Typography 
                variant="body2" 
                component="pre" 
                sx={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.8rem',
                  whiteSpace: 'pre-wrap',
                  mt: 0.5
                }}
              >
                {JSON.stringify(change.newValue, null, 2)}
              </Typography>
            </Box>
          )}
          
          {change.type === 'removed' && (
            <Box>
              <Typography variant="caption" color="textSecondary">Removed:</Typography>
              <Typography 
                variant="body2" 
                component="pre" 
                sx={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.8rem',
                  whiteSpace: 'pre-wrap',
                  mt: 0.5,
                  textDecoration: 'line-through'
                }}
              >
                {JSON.stringify(change.oldValue, null, 2)}
              </Typography>
            </Box>
          )}
          
          {change.type === 'modified' && (
            <Box>
              <Typography variant="caption" color="textSecondary">Before:</Typography>
              <Typography 
                variant="body2" 
                component="pre" 
                sx={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.8rem',
                  whiteSpace: 'pre-wrap',
                  mt: 0.5,
                  opacity: 0.7
                }}
              >
                {JSON.stringify(change.oldValue, null, 2)}
              </Typography>
              
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                After:
              </Typography>
              <Typography 
                variant="body2" 
                component="pre" 
                sx={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.8rem',
                  whiteSpace: 'pre-wrap',
                  mt: 0.5
                }}
              >
                {JSON.stringify(change.newValue, null, 2)}
              </Typography>
            </Box>
          )}
          
          {change.reason && (
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
              Reason: {change.reason}
            </Typography>
          )}
        </DiffContainer>
      ))}
    </Box>
  );
};

const TraceStep = ({ step, index, totalSteps }) => {
  const [expanded, setExpanded] = useState(false);
  
  const duration = step.endTime ? formatDuration(step.startTime, step.endTime) : 'In progress...';
  const hasUmweltChanges = step.umweltDiff && Object.keys(step.umweltDiff).length > 0;
  const hasConflicts = step.conflicts && step.conflicts.length > 0;
  
  return (
    <Accordion 
      expanded={expanded} 
      onChange={() => setExpanded(!expanded)}
      sx={{ mb: 1 }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box display="flex" alignItems="center" gap={2} width="100%">
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
            {getStepIcon(step.type)}
          </Avatar>
          
          <Box flexGrow={1}>
            <Typography variant="subtitle1">
              {step.title || `Step ${index + 1}`}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <StepChip label={step.type} stepType={step.type} size="small" />
              <Typography variant="caption" color="textSecondary">
                {formatTimestamp(step.startTime)} • {duration}
              </Typography>
              {hasUmweltChanges && (
                <Badge color="info" variant="dot">
                  <UmweltIcon fontSize="small" />
                </Badge>
              )}
              {hasConflicts && (
                <Badge badgeContent={step.conflicts.length} color="error">
                  <WarningIcon fontSize="small" />
                </Badge>
              )}
            </Box>
          </Box>
          
          <Typography variant="body2" color="textSecondary">
            {index + 1} / {totalSteps}
          </Typography>
        </Box>
      </AccordionSummary>
      
      <AccordionDetails>
        <Box>
          {/* Step description */}
          {step.description && (
            <Typography variant="body2" paragraph>
              {step.description}
            </Typography>
          )}
          
          {/* Thinking process */}
          {step.reasoning && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>
                <ThinkingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Reasoning Process
              </Typography>
              <Typography variant="body2" sx={{ pl: 2 }}>
                {step.reasoning}
              </Typography>
            </Box>
          )}
          
          {/* Input/Output data */}
          {(step.input || step.output) && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>
                Data Flow
              </Typography>
              <Box display="flex" gap={2}>
                {step.input && (
                  <Paper sx={{ p: 1, flex: 1 }}>
                    <Typography variant="caption" color="textSecondary">Input:</Typography>
                    <Typography 
                      variant="body2" 
                      component="pre"
                      sx={{ 
                        fontFamily: 'monospace', 
                        fontSize: '0.8rem',
                        whiteSpace: 'pre-wrap',
                        maxHeight: 200,
                        overflow: 'auto'
                      }}
                    >
                      {typeof step.input === 'string' ? step.input : JSON.stringify(step.input, null, 2)}
                    </Typography>
                  </Paper>
                )}
                
                {step.output && (
                  <Paper sx={{ p: 1, flex: 1 }}>
                    <Typography variant="caption" color="textSecondary">Output:</Typography>
                    <Typography 
                      variant="body2" 
                      component="pre"
                      sx={{ 
                        fontFamily: 'monospace', 
                        fontSize: '0.8rem',
                        whiteSpace: 'pre-wrap',
                        maxHeight: 200,
                        overflow: 'auto'
                      }}
                    >
                      {typeof step.output === 'string' ? step.output : JSON.stringify(step.output, null, 2)}
                    </Typography>
                  </Paper>
                )}
              </Box>
            </Box>
          )}
          
          {/* Umwelt diff */}
          {hasUmweltChanges && (
            <Box mb={2}>
              <UmweltDiffViewer diff={step.umweltDiff} timestamp={step.startTime} />
            </Box>
          )}
          
          {/* Conflicts or issues */}
          {hasConflicts && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom color="error">
                <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Conflicts Detected
              </Typography>
              {step.conflicts.map((conflict, idx) => (
                <Alert key={idx} severity={conflict.severity || 'warning'} sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    <strong>{conflict.type}:</strong> {conflict.description}
                  </Typography>
                  {conflict.resolution && (
                    <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                      Resolution: {conflict.resolution}
                    </Typography>
                  )}
                </Alert>
              ))}
            </Box>
          )}
          
          {/* Performance metrics */}
          {step.metrics && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>
                Performance Metrics
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                {Object.entries(step.metrics).map(([key, value]) => (
                  <Chip 
                    key={key}
                    label={`${key}: ${value}`}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      </AccordionDetails>
    </Accordion>
  );
};

/**
 * Explain Your Work Trace Component
 * 
 * Displays a detailed trace of agent decision-making process including
 * Umwelt changes, conflicts, and reasoning steps.
 */
const ExplainYourWorkTrace = ({ 
  agentId, 
  conversationId, 
  traceId,
  onError,
  refreshInterval = 30000 
}) => {
  const [traceData, setTraceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    if (agentId && (conversationId || traceId)) {
      fetchTraceData();
      
      let interval;
      if (autoRefresh) {
        interval = setInterval(fetchTraceData, refreshInterval);
      }
      
      return () => {
        if (interval) clearInterval(interval);
      };
    }
  }, [agentId, conversationId, traceId, autoRefresh]);

  const fetchTraceData = async () => {
    try {
      setError(null);
      
      // Fetch trace data from the API
      const endpoint = traceId 
        ? `/api/traces/${traceId}`
        : `/api/agents/${agentId}/conversations/${conversationId}/trace`;
        
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Add auth header if available
          ...(localStorage.getItem('authToken') && {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          })
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          setError('Trace data not found for this conversation');
        } else if (response.status === 403) {
          setError('Not authorized to access trace data');
        } else {
          setError(`Failed to fetch trace data: ${response.status} ${response.statusText}`);
        }
        return;
      }

      const result = await response.json();

      if (result.success && result.data) {
        setTraceData(result.data);
      } else {
        setError(result.message || 'No trace data available');
      }
    } catch (err) {
      console.error('Error fetching trace data:', err);
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTrace = () => {
    if (!traceData) return;
    
    const dataStr = JSON.stringify(traceData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `trace_${traceData.id}_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <TraceCard>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="center" minHeight={200}>
            <Typography variant="body2">Loading trace data...</Typography>
          </Box>
        </CardContent>
      </TraceCard>
    );
  }

  if (error) {
    return (
      <TraceCard>
        <CardContent>
          <Alert severity="error">
            <Typography variant="body2">{error}</Typography>
          </Alert>
        </CardContent>
      </TraceCard>
    );
  }

  if (!traceData) {
    return (
      <TraceCard>
        <CardContent>
          <Typography variant="body2" color="textSecondary">
            No trace data available
          </Typography>
        </CardContent>
      </TraceCard>
    );
  }

  const duration = formatDuration(traceData.startTime, traceData.endTime);
  const totalUmweltChanges = traceData.steps.reduce((total, step) => {
    return total + (step.umweltDiff ? Object.keys(step.umweltDiff).length : 0);
  }, 0);
  const totalConflicts = traceData.steps.reduce((total, step) => {
    return total + (step.conflicts ? step.conflicts.length : 0);
  }, 0);

  return (
    <TraceCard>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <TimelineIcon color="primary" />
            <Typography variant="h6">
              Explain Your Work - Trace {traceData.id}
            </Typography>
          </Box>
        }
        subheader={
          <Box display="flex" alignItems="center" gap={2} mt={1}>
            <Typography variant="body2" color="textSecondary">
              Duration: {duration}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Steps: {traceData.totalSteps}
            </Typography>
            {totalUmweltChanges > 0 && (
              <Chip 
                label={`${totalUmweltChanges} Umwelt changes`} 
                size="small" 
                color="info"
                variant="outlined"
              />
            )}
            {totalConflicts > 0 && (
              <Chip 
                label={`${totalConflicts} conflicts`} 
                size="small" 
                color="warning"
                variant="outlined"
              />
            )}
          </Box>
        }
        action={
          <Box display="flex" gap={1}>
            <Tooltip title="Auto-refresh">
              <IconButton 
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? 'primary' : 'default'}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download trace">
              <IconButton onClick={handleDownloadTrace}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      
      <CardContent>
        {traceData.steps.map((step, index) => (
          <TraceStep 
            key={step.id} 
            step={step} 
            index={index} 
            totalSteps={traceData.totalSteps}
          />
        ))}
      </CardContent>
    </TraceCard>
  );
};

export default ExplainYourWorkTrace;