import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Timeline as CoherenceIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  Psychology as ReflectionIcon,
  AutoFixHigh as RevisionIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, ResponsiveContainer } from 'recharts';

const CoherenceCard = styled(Card)(({ theme }) => ({
  height: '100%',
  border: `1px solid ${theme.palette.divider}`,
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    boxShadow: theme.shadows[6]
  }
}));

const MetricPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  textAlign: 'center',
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.grey[50]} 100%)`
}));

const ConflictItem = styled(ListItem)(({ theme, severity }) => ({
  border: `1px solid ${
    severity === 'high' ? theme.palette.error.main :
    severity === 'medium' ? theme.palette.warning.main :
    theme.palette.info.main
  }`,
  borderRadius: theme.shape.borderRadius,
  marginBottom: theme.spacing(1),
  backgroundColor: `${
    severity === 'high' ? theme.palette.error.main :
    severity === 'medium' ? theme.palette.warning.main :
    theme.palette.info.main
  }08`
}));

/**
 * Coherence Monitor Component
 * 
 * Real-time monitoring of narrative coherence with conflict detection
 * and revision tracking for agent story consistency
 */
const CoherenceMonitor = ({ agentId }) => {
  const [coherenceData, setCoherenceData] = useState(null);
  const [trends, setTrends] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [triggerDialogOpen, setTriggerDialogOpen] = useState(false);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    if (agentId) {
      fetchCoherenceData();
      // Set up real-time monitoring
      const interval = setInterval(fetchCoherenceData, 30000); // Every 30 seconds
      return () => clearInterval(interval);
    }
  }, [agentId]);

  const fetchCoherenceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch coherence status from agent-engine
      const response = await fetch(`/api/agents/${agentId}/ea3-status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('firebase_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCoherenceData(data.ea3_status?.coherence);
        if (data.ea3_status?.coherence) {
          await generateTrendsData();
          await generateConflictsData();
        }
      } else {
        throw new Error('Failed to fetch coherence data');
      }
    } catch (err) {
      console.error('Error fetching coherence data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateTrendsData = async () => {
    try {
      // Fetch historical coherence trends from agent-engine
      const response = await fetch(`/api/agents/${agentId}/coherence-trends`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('firebase_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTrends(data.trends || []);
      } else {
        setTrends([]);
      }
    } catch (err) {
      console.error('Error fetching trend data:', err);
      setTrends([]);
    }
  };

  const generateConflictsData = async () => {
    try {
      // Fetch active conflicts from agent-engine
      const response = await fetch(`/api/agents/${agentId}/conflicts`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('firebase_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConflicts(data.conflicts || []);
      } else {
        setConflicts([]);
      }
    } catch (err) {
      console.error('Error fetching conflicts data:', err);
      setConflicts([]);
    }
  };

  const triggerReflection = async () => {
    try {
      setTriggering(true);
      const response = await fetch(`/api/agents/${agentId}/trigger-reflection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('firebase_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setTriggerDialogOpen(false);
        // Refresh data after triggering reflection
        setTimeout(() => fetchCoherenceData(), 2000);
      } else {
        throw new Error('Failed to trigger reflection');
      }
    } catch (err) {
      console.error('Error triggering reflection:', err);
    } finally {
      setTriggering(false);
    }
  };

  const getCoherenceStatus = (score) => {
    if (score >= 0.9) return { label: 'Excellent', color: 'success' };
    if (score >= 0.8) return { label: 'Good', color: 'info' };
    if (score >= 0.7) return { label: 'Fair', color: 'warning' };
    return { label: 'Needs Attention', color: 'error' };
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'improving': return <TrendingUpIcon color="success" />;
      case 'declining': return <TrendingDownIcon color="error" />;
      default: return <CoherenceIcon color="primary" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load coherence data: {error}
      </Alert>
    );
  }

  if (!coherenceData) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No coherence data available. The agent may need to initialize narrative tracking.
      </Alert>
    );
  }

  const coherenceStatus = getCoherenceStatus(coherenceData?.narrative_coherence || 0);

  return (
    <Grid container spacing={3}>
      {/* Main Coherence Status */}
      <Grid item xs={12} md={8}>
        <CoherenceCard>
          <CardHeader
            title="Narrative Coherence Status"
            subheader="Real-time story consistency monitoring"
            avatar={<CoherenceIcon color="primary" />}
            action={
              <Tooltip title="Refresh Data">
                <IconButton onClick={fetchCoherenceData} size="small">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            }
          />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={6}>
                <MetricPaper>
                  <Typography variant="h4" color={coherenceStatus.color === 'error' ? 'error' : 'primary'}>
                    {Math.round((coherenceData?.narrative_coherence || 0) * 100)}%
                  </Typography>
                  <Typography variant="subtitle1" gutterBottom>
                    Narrative Coherence
                  </Typography>
                  <Chip 
                    label={coherenceStatus.label}
                    color={coherenceStatus.color}
                    size="small"
                  />
                </MetricPaper>
              </Grid>
              <Grid item xs={6}>
                <MetricPaper>
                  <Typography variant="h4" color="primary">
                    {Math.round((coherenceData?.consistency_score || 0) * 100)}%
                  </Typography>
                  <Typography variant="subtitle1" gutterBottom>
                    Consistency Score
                  </Typography>
                  <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                    {getTrendIcon(coherenceData?.stability_trend)}
                    <Typography variant="caption" color="textSecondary">
                      {coherenceData?.stability_trend || 'stable'}
                    </Typography>
                  </Box>
                </MetricPaper>
              </Grid>
            </Grid>

            {/* 24-Hour Coherence Trend */}
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                24-Hour Coherence Trend
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 1]} />
                  <ChartTooltip 
                    formatter={(value, name) => [
                      `${Math.round(value * 100)}%`, 
                      name === 'coherence' ? 'Coherence' : 'Consistency'
                    ]}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="coherence" 
                    stroke="#2196f3" 
                    strokeWidth={2}
                    name="coherence"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="consistency" 
                    stroke="#4caf50" 
                    strokeWidth={2}
                    name="consistency"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </CoherenceCard>
      </Grid>

      {/* Actions and Metrics */}
      <Grid item xs={12} md={4}>
        <Grid container spacing={2}>
          {/* Quick Actions */}
          <Grid item xs={12}>
            <CoherenceCard>
              <CardHeader
                title="Actions"
                subheader="Coherence management"
              />
              <CardContent>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Button
                    variant="outlined"
                    startIcon={<ReflectionIcon />}
                    onClick={() => setTriggerDialogOpen(true)}
                    disabled={triggering}
                    fullWidth
                  >
                    Trigger Reflection
                  </Button>
                  
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Last Revision
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {coherenceData?.last_revision ? 
                        new Date(coherenceData.last_revision).toLocaleString() :
                        'No revisions yet'
                      }
                    </Typography>
                  </Paper>

                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Contradiction Count
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="h6" color={
                        (coherenceData?.contradiction_count || 0) > 0 ? 'error' : 'success'
                      }>
                        {coherenceData?.contradiction_count || 0}
                      </Typography>
                      {(coherenceData?.contradiction_count || 0) > 0 ? 
                        <WarningIcon color="error" fontSize="small" /> :
                        <CheckIcon color="success" fontSize="small" />
                      }
                    </Box>
                  </Paper>
                </Box>
              </CardContent>
            </CoherenceCard>
          </Grid>

          {/* Current Conflicts */}
          <Grid item xs={12}>
            <CoherenceCard>
              <CardHeader
                title="Active Conflicts"
                subheader={`${conflicts.filter(c => c.status === 'pending').length} pending`}
              />
              <CardContent>
                {conflicts.length === 0 ? (
                  <Box display="flex" alignItems="center" justifyContent="center" py={2}>
                    <CheckIcon color="success" sx={{ mr: 1 }} />
                    <Typography variant="body2" color="textSecondary">
                      No conflicts detected
                    </Typography>
                  </Box>
                ) : (
                  <List dense>
                    {conflicts.slice(0, 3).map((conflict) => (
                      <ConflictItem key={conflict.id} severity={conflict.severity}>
                        <ListItemIcon>
                          {conflict.severity === 'high' ? <ErrorIcon color="error" /> :
                           conflict.severity === 'medium' ? <WarningIcon color="warning" /> :
                           <InfoIcon color="info" />}
                        </ListItemIcon>
                        <ListItemText
                          primary={conflict.description}
                          secondary={
                            <Box>
                              <Chip 
                                label={conflict.status}
                                size="small"
                                color={conflict.status === 'resolved' ? 'success' : 'warning'}
                                sx={{ mr: 1 }}
                              />
                              <Typography variant="caption" color="textSecondary">
                                {new Date(conflict.timestamp).toLocaleString()}
                              </Typography>
                            </Box>
                          }
                        />
                      </ConflictItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </CoherenceCard>
          </Grid>
        </Grid>
      </Grid>

      {/* Trigger Reflection Dialog */}
      <Dialog open={triggerDialogOpen} onClose={() => setTriggerDialogOpen(false)}>
        <DialogTitle>Trigger Autonomous Reflection</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            This will manually trigger the agent's recursive belief revision (RbR) process 
            to resolve any narrative conflicts and improve coherence.
          </Typography>
          <Alert severity="info">
            The reflection process may take a few minutes to complete and will update 
            the agent's internal narrative structure.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTriggerDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={triggerReflection}
            variant="contained"
            disabled={triggering}
            startIcon={triggering ? <CircularProgress size={16} /> : <RevisionIcon />}
          >
            {triggering ? 'Processing...' : 'Trigger Reflection'}
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
};

export default CoherenceMonitor;