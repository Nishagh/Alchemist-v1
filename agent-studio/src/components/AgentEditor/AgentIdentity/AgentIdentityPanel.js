import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  CircularProgress,
  Tab,
  Tabs
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  Timeline as TimelineIcon,
  AccountBalance as ResponsibilityIcon,
  TrendingUp as GrowthIcon,
  Star as StarIcon,
  Assignment as GoalIcon,
  Favorite as ValueIcon,
  EmojiEvents as AchievementIcon,
  AutoGraph as AnalyticsIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Import identity service
import { getAgentIdentity } from '../../../services';

// Styled components
const IdentityCard = styled(Card)(({ theme }) => ({
  height: '100%',
  transition: 'box-shadow 0.2s ease-in-out',
  '&:hover': {
    boxShadow: theme.shadows[8]
  }
}));

const StageChip = styled(Chip)(({ theme, stage }) => {
  const stageColors = {
    nascent: { bg: '#E3F2FD', color: '#1976D2' },
    developing: { bg: '#E8F5E8', color: '#388E3C' },
    established: { bg: '#FFF3E0', color: '#F57C00' },
    mature: { bg: '#F3E5F5', color: '#7B1FA2' },
    evolved: { bg: '#FCE4EC', color: '#C2185B' }
  };
  
  const colors = stageColors[stage] || stageColors.nascent;
  
  return {
    backgroundColor: colors.bg,
    color: colors.color,
    fontWeight: 'bold',
    textTransform: 'capitalize'
  };
});

const ScoreDisplay = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  marginBottom: theme.spacing(1)
}));

const IdentityTabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`identity-tabpanel-${index}`}
    aria-labelledby={`identity-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

/**
 * Agent Identity Panel Component
 * 
 * Displays comprehensive agent identity information from the Global Narrative Framework,
 * including personality traits, development stage, responsibility metrics, and narrative arc.
 */
const AgentIdentityPanel = ({ 
  agentId, 
  showPersonality = true, 
  showNarrativeArc = true, 
  showResponsibility = true,
  onError 
}) => {
  const [identityData, setIdentityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    if (agentId) {
      fetchIdentityData();
    }
  }, [agentId]);

  const fetchIdentityData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch agent identity data using the identity service
      const data = await getAgentIdentity(agentId);
      setIdentityData(data);
    } catch (err) {
      const errorMessage = err.message || 'Failed to load agent identity';
      setError(errorMessage);
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading agent identity...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!identityData) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No identity data available for this agent.
      </Alert>
    );
  }

  const renderPersonalityOverview = () => (
    <IdentityCard>
      <CardHeader
        title="Personality Overview"
        avatar={<PsychologyIcon color="primary" />}
        subheader={`Development Stage: ${identityData.development_stage || 'Unknown'}`}
        action={
          <StageChip 
            label={identityData.development_stage || 'nascent'} 
            stage={identityData.development_stage || 'nascent'}
            size="small"
          />
        }
      />
      <CardContent>
        <Grid container spacing={2}>
          {/* Dominant Traits */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              <StarIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Dominant Traits
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {(identityData.dominant_personality_traits || []).map((trait, index) => (
                <Chip 
                  key={index} 
                  label={trait}
                  variant="outlined"
                  size="small"
                  color="primary"
                />
              ))}
            </Box>
          </Grid>

          {/* Core Values */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              <ValueIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Core Values
            </Typography>
            <List dense>
              {(identityData.core_values || []).map((value, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemText primary={value} />
                </ListItem>
              ))}
            </List>
          </Grid>

          {/* Primary Goals */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              <GoalIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Primary Goals
            </Typography>
            <List dense>
              {(identityData.primary_goals || []).map((goal, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemText primary={goal} />
                </ListItem>
              ))}
            </List>
          </Grid>
        </Grid>
      </CardContent>
    </IdentityCard>
  );

  const renderDevelopmentMetrics = () => (
    <IdentityCard>
      <CardHeader
        title="Development Metrics"
        avatar={<GrowthIcon color="success" />}
        subheader="Growth and learning progress"
      />
      <CardContent>
        <Grid container spacing={3}>
          {/* Experience Points */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {identityData.experience_points || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Experience Points
              </Typography>
            </Paper>
          </Grid>

          {/* Total Interactions */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="secondary">
                {identityData.total_narrative_interactions || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Total Interactions
              </Typography>
            </Paper>
          </Grid>

          {/* Defining Moments */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">
                {identityData.defining_moments_count || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Defining Moments
              </Typography>
            </Paper>
          </Grid>

          {/* Narrative Coherence Score */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Narrative Coherence
            </Typography>
            <ScoreDisplay>
              <LinearProgress 
                variant="determinate" 
                value={(identityData.narrative_coherence_score || 0) * 100}
                sx={{ flexGrow: 1, height: 8, borderRadius: 1 }}
                color="primary"
              />
              <Typography variant="body2">
                {Math.round((identityData.narrative_coherence_score || 0) * 100)}%
              </Typography>
            </ScoreDisplay>
          </Grid>

          {/* Responsibility Score */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Responsibility Score
            </Typography>
            <ScoreDisplay>
              <LinearProgress 
                variant="determinate" 
                value={(identityData.responsibility_score || 0) * 100}
                sx={{ flexGrow: 1, height: 8, borderRadius: 1 }}
                color="success"
              />
              <Typography variant="body2">
                {Math.round((identityData.responsibility_score || 0) * 100)}%
              </Typography>
            </ScoreDisplay>
          </Grid>
        </Grid>
      </CardContent>
    </IdentityCard>
  );

  const renderNarrativeArc = () => (
    <IdentityCard>
      <CardHeader
        title="Narrative Arc"
        avatar={<TimelineIcon color="info" />}
        subheader="Current story progression"
      />
      <CardContent>
        {identityData.current_narrative_arc ? (
          <Box>
            <Typography variant="h6" gutterBottom>
              Current Arc: "{identityData.current_narrative_arc}"
            </Typography>
            <Typography variant="body1" color="textSecondary" paragraph>
              This agent is currently in the "{identityData.current_narrative_arc}" phase of their development,
              characterized by specific behavioral patterns and learning objectives.
            </Typography>
            
            {/* Arc progression indicator */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Arc Progression
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={getArcProgression(identityData.development_stage)}
                sx={{ height: 6, borderRadius: 1 }}
                color="info"
              />
            </Box>
          </Box>
        ) : (
          <Typography variant="body1" color="textSecondary">
            No active narrative arc. The agent is in the early stages of development.
          </Typography>
        )}
      </CardContent>
    </IdentityCard>
  );

  const renderResponsibilityTracking = () => (
    <IdentityCard>
      <CardHeader
        title="Responsibility Tracking"
        avatar={<ResponsibilityIcon color="warning" />}
        subheader="Accountability and decision-making metrics"
      />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              Responsibility Score
            </Typography>
            <ScoreDisplay>
              <CircularProgress 
                variant="determinate" 
                value={(identityData.responsibility_score || 0) * 100}
                size={60}
                thickness={4}
                color="warning"
              />
              <Box sx={{ ml: 2 }}>
                <Typography variant="h4">
                  {Math.round((identityData.responsibility_score || 0) * 100)}%
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Overall accountability
                </Typography>
              </Box>
            </ScoreDisplay>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              Recent Actions
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Total Actions: {identityData.total_actions || 0}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Success Rate: {identityData.success_rate ? Math.round(identityData.success_rate * 100) : 0}%
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Ethical Weight: {identityData.avg_ethical_weight ? Math.round(identityData.avg_ethical_weight * 100) : 0}%
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </IdentityCard>
  );

  const getArcProgression = (stage) => {
    const stageProgression = {
      nascent: 20,
      developing: 40,
      established: 60,
      mature: 80,
      evolved: 100
    };
    return stageProgression[stage] || 0;
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="agent identity tabs">
          <Tab label="Overview" icon={<PsychologyIcon />} iconPosition="start" />
          <Tab label="Development" icon={<GrowthIcon />} iconPosition="start" />
          <Tab label="Narrative" icon={<TimelineIcon />} iconPosition="start" />
          <Tab label="Responsibility" icon={<ResponsibilityIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      <IdentityTabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          {showPersonality && (
            <Grid item xs={12}>
              {renderPersonalityOverview()}
            </Grid>
          )}
        </Grid>
      </IdentityTabPanel>

      <IdentityTabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {renderDevelopmentMetrics()}
          </Grid>
        </Grid>
      </IdentityTabPanel>

      <IdentityTabPanel value={activeTab} index={2}>
        <Grid container spacing={3}>
          {showNarrativeArc && (
            <Grid item xs={12}>
              {renderNarrativeArc()}
            </Grid>
          )}
        </Grid>
      </IdentityTabPanel>

      <IdentityTabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          {showResponsibility && (
            <Grid item xs={12}>
              {renderResponsibilityTracking()}
            </Grid>
          )}
        </Grid>
      </IdentityTabPanel>
    </Box>
  );
};

export default AgentIdentityPanel;