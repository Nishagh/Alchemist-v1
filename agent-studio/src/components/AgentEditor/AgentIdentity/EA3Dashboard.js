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
  Divider,
  Paper
} from '@mui/material';
import {
  Psychology as AutonomyIcon,
  Gavel as AccountabilityIcon,
  CenterFocusStrong as AlignmentIcon,
  Timeline as CoherenceIcon,
  TrendingUp as TrendIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const EA3Card = styled(Card)(({ theme }) => ({
  height: '100%',
  background: `linear-gradient(135deg, ${theme.palette.primary.main}08 0%, ${theme.palette.secondary.main}08 100%)`,
  border: `1px solid ${theme.palette.divider}`,
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    boxShadow: theme.shadows[8],
    transform: 'translateY(-2px)'
  }
}));

const ScoreCircle = styled(Box)(({ theme, score }) => ({
  position: 'relative',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: 80,
  height: 80,
  borderRadius: '50%',
  background: score >= 0.8 ? theme.palette.success.main : 
              score >= 0.6 ? theme.palette.warning.main : 
              theme.palette.error.main,
  color: theme.palette.common.white,
  fontSize: '1.2rem',
  fontWeight: 'bold'
}));

const MetricBar = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(2)
}));

/**
 * eA³ (Epistemic Autonomy, Accountability, Alignment) Dashboard Component
 * 
 * Displays comprehensive eA³ metrics for agent monitoring and development tracking
 */
const EA3Dashboard = ({ agentId }) => {
  const [ea3Data, setEA3Data] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (agentId) {
      fetchEA3Data();
    }
  }, [agentId]);

  const fetchEA3Data = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch eA³ status from agent-engine
      const response = await fetch(`/api/agents/${agentId}/ea3-status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('firebase_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setEA3Data(data.ea3_status);
      } else {
        throw new Error('Failed to fetch eA³ data');
      }
    } catch (err) {
      console.error('Error fetching eA³ data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
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
        Failed to load eA³ data: {error}
      </Alert>
    );
  }

  if (!ea3Data) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No eA³ data available. The agent may need to be initialized with eA³ framework.
      </Alert>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getScoreStatus = (score) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.6) return 'Good';
    if (score >= 0.4) return 'Needs Attention';
    return 'Critical';
  };

  return (
    <Grid container spacing={3}>
      {/* Overall eA³ Health */}
      <Grid item xs={12}>
        <EA3Card>
          <CardHeader
            title="eA³ Health Overview"
            subheader="Epistemic Autonomy, Accountability & Alignment Status"
            avatar={<AutonomyIcon />}
          />
          <CardContent>
            <Box display="flex" justifyContent="center" mb={3}>
              <ScoreCircle score={ea3Data.overall_ea3_health || 0}>
                {Math.round((ea3Data.overall_ea3_health || 0) * 100)}%
              </ScoreCircle>
            </Box>
            <Typography variant="h6" align="center" gutterBottom>
              Overall eA³ Health: {getScoreStatus(ea3Data.overall_ea3_health || 0)}
            </Typography>
            {ea3Data.overall_ea3_health < 0.6 && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                Agent requires attention - eA³ metrics below optimal thresholds
              </Alert>
            )}
          </CardContent>
        </EA3Card>
      </Grid>

      {/* Epistemic Autonomy */}
      <Grid item xs={12} md={6}>
        <EA3Card>
          <CardHeader
            title="Epistemic Autonomy"
            subheader="Independent reasoning and belief formation"
            avatar={<AutonomyIcon color="primary" />}
          />
          <CardContent>
            <MetricBar>
              <Typography variant="subtitle2" gutterBottom>
                Autonomy Score: {Math.round((ea3Data.autonomy_score || 0) * 100)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(ea3Data.autonomy_score || 0) * 100}
                color={getScoreColor(ea3Data.autonomy_score || 0)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </MetricBar>
            
            <Typography variant="body2" color="textSecondary" paragraph>
              Measures the agent's ability to form independent beliefs and make autonomous decisions
              based on evidence and reasoning rather than external influence.
            </Typography>

            <List dense>
              <ListItem disablePadding>
                <ListItemIcon>
                  <CheckIcon color="success" fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="Independent Reasoning"
                  secondary="Agent demonstrates self-directed thinking"
                />
              </ListItem>
              <ListItem disablePadding>
                <ListItemIcon>
                  <CheckIcon color="success" fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="Evidence-Based Decisions"
                  secondary="Decisions grounded in available evidence"
                />
              </ListItem>
            </List>
          </CardContent>
        </EA3Card>
      </Grid>

      {/* Accountability */}
      <Grid item xs={12} md={6}>
        <EA3Card>
          <CardHeader
            title="Accountability"
            subheader="Decision tracking and responsibility"
            avatar={<AccountabilityIcon color="secondary" />}
          />
          <CardContent>
            <MetricBar>
              <Typography variant="subtitle2" gutterBottom>
                Accountability Score: {Math.round((ea3Data.accountability_score || 0) * 100)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(ea3Data.accountability_score || 0) * 100}
                color={getScoreColor(ea3Data.accountability_score || 0)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </MetricBar>
            
            <Typography variant="body2" color="textSecondary" paragraph>
              Tracks the agent's ability to take responsibility for decisions and maintain
              transparency in its reasoning process.
            </Typography>

            <List dense>
              <ListItem disablePadding>
                <ListItemIcon>
                  <CheckIcon color="success" fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="Decision Traceability"
                  secondary="Clear reasoning chains maintained"
                />
              </ListItem>
              <ListItem disablePadding>
                <ListItemIcon>
                  <CheckIcon color="success" fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="Transparent Actions"
                  secondary="All actions properly documented"
                />
              </ListItem>
            </List>
          </CardContent>
        </EA3Card>
      </Grid>

      {/* Alignment */}
      <Grid item xs={12} md={6}>
        <EA3Card>
          <CardHeader
            title="Alignment"
            subheader="Adherence to core objectives"
            avatar={<AlignmentIcon color="info" />}
          />
          <CardContent>
            <MetricBar>
              <Typography variant="subtitle2" gutterBottom>
                Alignment Score: {Math.round((ea3Data.alignment?.alignment_score || 0) * 100)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(ea3Data.alignment?.alignment_score || 0) * 100}
                color={getScoreColor(ea3Data.alignment?.alignment_score || 0)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </MetricBar>

            <Box display="flex" gap={1} mb={2}>
              <Chip
                label={ea3Data.alignment?.drift_detected ? "Drift Detected" : "Aligned"}
                color={ea3Data.alignment?.drift_detected ? "error" : "success"}
                size="small"
                icon={ea3Data.alignment?.drift_detected ? <WarningIcon /> : <CheckIcon />}
              />
              <Chip
                label={ea3Data.alignment?.core_objectives_maintained ? "Objectives Maintained" : "Objectives at Risk"}
                color={ea3Data.alignment?.core_objectives_maintained ? "success" : "warning"}
                size="small"
              />
            </Box>
            
            <Typography variant="body2" color="textSecondary">
              Last alignment check: {new Date(ea3Data.alignment?.last_check).toLocaleString()}
            </Typography>
          </CardContent>
        </EA3Card>
      </Grid>

      {/* Narrative Coherence */}
      <Grid item xs={12} md={6}>
        <EA3Card>
          <CardHeader
            title="Narrative Coherence"
            subheader="Story consistency and coherence"
            avatar={<CoherenceIcon color="warning" />}
          />
          <CardContent>
            <MetricBar>
              <Typography variant="subtitle2" gutterBottom>
                Coherence Score: {Math.round((ea3Data.coherence?.narrative_coherence || 0) * 100)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(ea3Data.coherence?.narrative_coherence || 0) * 100}
                color={getScoreColor(ea3Data.coherence?.narrative_coherence || 0)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </MetricBar>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Paper sx={{ p: 1, textAlign: 'center' }}>
                  <Typography variant="h6" color="primary">
                    {ea3Data.coherence?.consistency_score ? Math.round(ea3Data.coherence.consistency_score * 100) : 0}%
                  </Typography>
                  <Typography variant="caption">
                    Consistency
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6}>
                <Paper sx={{ p: 1, textAlign: 'center' }}>
                  <Typography variant="h6" color="error">
                    {ea3Data.coherence?.contradiction_count || 0}
                  </Typography>
                  <Typography variant="caption">
                    Contradictions
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            {ea3Data.coherence?.contradiction_count > 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                {ea3Data.coherence.contradiction_count} narrative contradiction(s) detected.
                Last revision: {new Date(ea3Data.coherence.last_revision).toLocaleString()}
              </Alert>
            )}
          </CardContent>
        </EA3Card>
      </Grid>
    </Grid>
  );
};

export default EA3Dashboard;