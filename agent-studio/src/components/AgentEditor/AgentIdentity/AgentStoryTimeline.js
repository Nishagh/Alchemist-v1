import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  Chat as ConversationIcon,
  Psychology as ReflectionIcon,
  Psychology as PsychologyIcon,
  School as LearningIcon,
  TrendingUp as GrowthIcon,
  Warning as ConflictIcon,
  AutoFixHigh as RevisionIcon,
  ExpandMore as ExpandIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const StoryCard = styled(Card)(({ theme }) => ({
  height: '100%',
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.grey[50]} 100%)`,
  border: `1px solid ${theme.palette.divider}`
}));

const EventAvatar = styled(Avatar)(({ theme, eventType }) => {
  const colors = {
    conversation: theme.palette.primary.main,
    learning: theme.palette.success.main,
    reflection: theme.palette.warning.main,
    conflict: theme.palette.error.main,
    revision: theme.palette.info.main,
    growth: theme.palette.secondary.main
  };
  
  return {
    backgroundColor: colors[eventType] || theme.palette.grey[400],
    color: theme.palette.common.white,
    width: 40,
    height: 40
  };
});

const EventCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(1),
  border: `1px solid ${theme.palette.divider}`,
  '&:hover': {
    boxShadow: theme.shadows[4]
  }
}));

/**
 * Agent Story Timeline Component
 * 
 * Visualizes the agent's narrative development over time with key events,
 * learning moments, and story coherence changes
 */
const AgentStoryTimeline = ({ agentId }) => {
  const [storyEvents, setStoryEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedEvent, setExpandedEvent] = useState(null);

  useEffect(() => {
    if (agentId) {
      fetchStoryTimeline();
    }
  }, [agentId]);

  const fetchStoryTimeline = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch agent life-story from agent-engine
      const response = await fetch(`/api/agents/${agentId}/life-story`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('firebase_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStoryEvents(data.life_story?.events || []);
      } else {
        throw new Error('Failed to fetch story timeline');
      }
    } catch (err) {
      console.error('Error fetching story timeline:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (eventType) => {
    const icons = {
      conversation: <ConversationIcon />,
      learning: <LearningIcon />,
      reflection: <ReflectionIcon />,
      conflict: <ConflictIcon />,
      revision: <RevisionIcon />,
      growth: <GrowthIcon />,
      creation: <PsychologyIcon />
    };
    return icons[eventType] || <TimelineIcon />;
  };

  const getImpactColor = (impactLevel) => {
    switch (impactLevel) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getCoherenceColor = (score) => {
    if (score >= 0.9) return 'success';
    if (score >= 0.7) return 'warning';
    return 'error';
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const eventTime = new Date(timestamp);
    const diffHours = Math.floor((now - eventTime) / (1000 * 60 * 60));
    
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    const diffWeeks = Math.floor(diffDays / 7);
    return `${diffWeeks}w ago`;
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
        Failed to load story timeline: {error}
      </Alert>
    );
  }

  return (
    <StoryCard>
      <CardHeader
        title="Agent Story Timeline"
        subheader="Narrative development and key events"
        avatar={<TimelineIcon color="primary" />}
        action={
          <Tooltip title="Refresh Timeline">
            <IconButton onClick={fetchStoryTimeline} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent>
        {storyEvents.length === 0 ? (
          <Alert severity="info">
            No story events recorded yet. Events will appear as the agent interacts and develops.
          </Alert>
        ) : (
          <List>
            {storyEvents.map((event, index) => (
              <ListItem key={event.id} sx={{ mb: 2, flexDirection: 'column', alignItems: 'stretch' }}>
                <EventCard elevation={1}>
                  <Box display="flex" alignItems="flex-start" gap={2} mb={2}>
                    <EventAvatar eventType={event.event_type}>
                      {getEventIcon(event.event_type)}
                    </EventAvatar>
                    
                    <Box flexGrow={1}>
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                        <Typography variant="h6" component="span">
                          {event.title}
                        </Typography>
                        <Box display="flex" gap={1}>
                          <Chip 
                            label={event.impact_level}
                            size="small"
                            color={getImpactColor(event.impact_level)}
                          />
                          <Chip 
                            label={`Coherence: ${Math.round((event.coherence_score || 0) * 100)}%`}
                            size="small"
                            color={getCoherenceColor(event.coherence_score || 0)}
                          />
                        </Box>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {formatTimeAgo(event.timestamp)}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {event.description}
                      </Typography>
                      
                      {event.details && (
                        <Accordion 
                          expanded={expandedEvent === event.id}
                          onChange={() => setExpandedEvent(expandedEvent === event.id ? null : event.id)}
                        >
                          <AccordionSummary expandIcon={<ExpandIcon />}>
                            <Typography variant="caption">View Details</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Box component="pre" sx={{ 
                              fontFamily: 'monospace', 
                              fontSize: '0.75rem',
                              whiteSpace: 'pre-wrap',
                              backgroundColor: 'grey.100',
                              p: 1,
                              borderRadius: 1,
                              overflow: 'auto'
                            }}>
                              {JSON.stringify(event.details, null, 2)}
                            </Box>
                          </AccordionDetails>
                        </Accordion>
                      )}
                    </Box>
                  </Box>
                </EventCard>
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </StoryCard>
  );
};

export default AgentStoryTimeline;