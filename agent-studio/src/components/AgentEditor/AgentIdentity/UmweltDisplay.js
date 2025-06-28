import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  CircularProgress,
  Collapse,
  IconButton,
  Tooltip,
  Badge,
  Avatar
} from '@mui/material';
import {
  Visibility as UmweltIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Circle as CircleIcon,
  TrendingUp as TrendingUpIcon,
  Storage as DatabaseIcon,
  Api as ApiIcon,
  Event as EventIcon,
  Sensors as SensorIcon,
  AccessTime as TimeIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Styled components
const UmweltCard = styled(Card)(({ theme }) => ({
  height: '100%',
  transition: 'box-shadow 0.2s ease-in-out',
  '&:hover': {
    boxShadow: theme.shadows[4]
  }
}));

const UmweltKeyItem = styled(ListItem)(({ theme, priority }) => {
  const priorityColors = {
    critical: { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.05)' },
    high: { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.05)' },
    medium: { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.05)' },
    low: { border: '#6b7280', bg: 'rgba(107, 114, 128, 0.05)' }
  };
  
  const colors = priorityColors[priority] || priorityColors.medium;
  
  return {
    borderLeft: `3px solid ${colors.border}`,
    backgroundColor: colors.bg,
    marginBottom: theme.spacing(0.5),
    borderRadius: theme.shape.borderRadius,
    '&:hover': {
      backgroundColor: colors.bg
    }
  };
});

const PriorityChip = styled(Chip)(({ theme, priority }) => {
  const priorityColors = {
    critical: { bg: '#fee2e2', color: '#991b1b' },
    high: { bg: '#fef3c7', color: '#92400e' },
    medium: { bg: '#dbeafe', color: '#1e40af' },
    low: { bg: '#f3f4f6', color: '#374151' }
  };
  
  const colors = priorityColors[priority] || priorityColors.medium;
  
  return {
    backgroundColor: colors.bg,
    color: colors.color,
    fontSize: '0.75rem',
    height: '20px'
  };
});

const getSignalTypeIcon = (signalType) => {
  const icons = {
    api: <ApiIcon fontSize="small" />,
    database: <DatabaseIcon fontSize="small" />,
    sensor: <SensorIcon fontSize="small" />,
    event: <EventIcon fontSize="small" />,
    message: <InfoIcon fontSize="small" />
  };
  
  return icons[signalType] || <CircleIcon fontSize="small" />;
};

const getSignalTypeColor = (signalType) => {
  const colors = {
    api: 'primary',
    database: 'secondary',
    sensor: 'success',
    event: 'warning',
    message: 'info'
  };
  
  return colors[signalType] || 'default';
};

const formatValue = (value) => {
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
};

const truncateValue = (value, maxLength = 100) => {
  const stringValue = formatValue(value);
  if (stringValue.length <= maxLength) return stringValue;
  return stringValue.substring(0, maxLength) + '...';
};

const getTimeSinceUpdate = (timestamp) => {
  const now = new Date();
  const updated = new Date(timestamp);
  const diffMs = now - updated;
  
  const minutes = Math.floor(diffMs / 60000);
  const hours = Math.floor(diffMs / 3600000);
  const days = Math.floor(diffMs / 86400000);
  
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'Just now';
};

/**
 * Umwelt Display Component
 * 
 * Shows the agent's current world snapshot (Umwelt) with real-time updates
 * and filtering based on the Core Objective Function.
 */
const UmweltDisplay = ({ agentId, onError }) => {
  const [umweltData, setUmweltData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [conflictKeys, setConflictKeys] = useState([]);
  const intervalRef = useRef(null);

  const refreshInterval = 30000; // 30 seconds
  const maxDisplayItems = expanded ? 50 : 10;

  useEffect(() => {
    if (agentId) {
      fetchUmweltData();
      
      // Set up automatic refresh
      intervalRef.current = setInterval(fetchUmweltData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [agentId]);

  const fetchUmweltData = async () => {
    if (!agentId) return;

    try {
      setError(null);

      // Fetch Umwelt data from the service
      const response = await fetch(`/api/agents/${agentId}/umwelt`, {
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
          setError('Umwelt service not available for this agent');
        } else if (response.status === 403) {
          setError('Not authorized to access agent Umwelt data');
        } else {
          setError(`Failed to fetch Umwelt data: ${response.status} ${response.statusText}`);
        }
        return;
      }

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        setError('Invalid response format from Umwelt service');
        return;
      }

      const result = await response.json();

      if (result.success) {
        const umweltData = result.data?.umwelt || {};
        setUmweltData(umweltData);
        setLastUpdated(new Date());
        
        // Check for any conflict indicators in metadata
        const conflicts = Object.keys(umweltData).filter(key => {
          const entry = umweltData[key];
          return entry?.metadata?.has_conflict === true;
        });
        setConflictKeys(conflicts);
      } else {
        setError(result.message || 'Failed to fetch Umwelt data');
      }
    } catch (err) {
      console.error('Error fetching Umwelt data:', err);
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    fetchUmweltData();
  };

  const parseUmweltKey = (key) => {
    // Parse keys like "api_weather_temperature" or "database_conversations_count"
    const parts = key.split('_');
    if (parts.length >= 3) {
      return {
        signalType: parts[0],
        source: parts[1],
        property: parts.slice(2).join('_')
      };
    }
    return {
      signalType: 'unknown',
      source: 'unknown',
      property: key
    };
  };

  const getUmweltEntries = () => {
    const entries = Object.entries(umweltData).map(([key, value]) => {
      const parsed = parseUmweltKey(key);
      const priority = getPriority(key, value);
      const hasConflict = conflictKeys.includes(key);
      
      return {
        key,
        value,
        parsed,
        priority,
        hasConflict,
        timestamp: value.timestamp || new Date().toISOString(),
        metadata: value.metadata || {}
      };
    });

    // Sort by priority (critical first) then by timestamp (newest first)
    return entries.sort((a, b) => {
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      const aPriority = priorityOrder[a.priority] || 2;
      const bPriority = priorityOrder[b.priority] || 2;
      
      if (aPriority !== bPriority) {
        return aPriority - bPriority;
      }
      
      return new Date(b.timestamp) - new Date(a.timestamp);
    });
  };

  const getPriority = (key, value) => {
    // Determine priority based on key patterns and value types
    if (key.includes('error') || key.includes('failure')) return 'critical';
    if (key.includes('warning') || key.includes('alert')) return 'high';
    if (key.includes('status') || key.includes('health')) return 'medium';
    if (typeof value === 'object') return 'medium';
    return 'low';
  };

  const renderUmweltEntry = (entry) => {
    const { key, value, parsed, priority, hasConflict, timestamp, metadata } = entry;
    
    return (
      <UmweltKeyItem key={key} priority={priority}>
        <ListItemIcon>
          <Badge
            color="error"
            variant="dot"
            invisible={!hasConflict}
            overlap="circular"
          >
            <Avatar 
              sx={{ width: 24, height: 24, bgcolor: getSignalTypeColor(parsed.signalType) + '.main' }}
            >
              {getSignalTypeIcon(parsed.signalType)}
            </Avatar>
          </Badge>
        </ListItemIcon>
        
        <ListItemText
          primary={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="subtitle2" component="span">
                {parsed.property}
              </Typography>
              <PriorityChip 
                label={priority} 
                priority={priority}
                size="small"
              />
              {hasConflict && (
                <Tooltip title="Conflict detected with GNF facts">
                  <WarningIcon color="error" fontSize="small" />
                </Tooltip>
              )}
            </Box>
          }
          secondary={
            <Box>
              <Typography 
                variant="body2" 
                component="div"
                sx={{ 
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                  mt: 0.5,
                  p: 1,
                  bgcolor: 'grey.50',
                  borderRadius: 1,
                  wordBreak: 'break-all'
                }}
              >
                {truncateValue(value)}
              </Typography>
              <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                <Chip
                  label={parsed.source}
                  size="small"
                  variant="outlined"
                  color={getSignalTypeColor(parsed.signalType)}
                />
                <Typography variant="caption" color="textSecondary">
                  <TimeIcon fontSize="small" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                  {getTimeSinceUpdate(timestamp)}
                </Typography>
              </Box>
            </Box>
          }
        />
      </UmweltKeyItem>
    );
  };

  const umweltEntries = getUmweltEntries();
  const displayedEntries = umweltEntries.slice(0, maxDisplayItems);
  const hasMore = umweltEntries.length > maxDisplayItems;
  const conflictCount = conflictKeys.length;
  const totalKeys = umweltEntries.length;

  if (loading && !lastUpdated) {
    return (
      <UmweltCard>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="center" minHeight={200}>
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 2 }}>
              Loading Umwelt data...
            </Typography>
          </Box>
        </CardContent>
      </UmweltCard>
    );
  }

  return (
    <UmweltCard>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <UmweltIcon color="primary" />
            <Typography variant="h6">
              Umwelt (World Snapshot)
            </Typography>
            {conflictCount > 0 && (
              <Badge badgeContent={conflictCount} color="error">
                <WarningIcon color="error" fontSize="small" />
              </Badge>
            )}
          </Box>
        }
        subheader={
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="body2" color="textSecondary">
              {totalKeys} active signals
            </Typography>
            {lastUpdated && (
              <Typography variant="caption" color="textSecondary">
                Updated: {lastUpdated.toLocaleTimeString()}
              </Typography>
            )}
          </Box>
        }
        action={
          <Tooltip title="Refresh Umwelt data">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      
      <CardContent>
        {error && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">{error}</Typography>
          </Alert>
        )}

        {conflictCount > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2">
              {conflictCount} signal{conflictCount > 1 ? 's' : ''} conflict with established beliefs
            </Typography>
          </Alert>
        )}

        {totalKeys === 0 ? (
          <Box display="flex" alignItems="center" justifyContent="center" minHeight={100}>
            <Typography variant="body2" color="textSecondary">
              No Umwelt data available
            </Typography>
          </Box>
        ) : (
          <>
            <List dense>
              {displayedEntries.map(renderUmweltEntry)}
            </List>

            {hasMore && (
              <Box textAlign="center" mt={2}>
                <IconButton
                  onClick={() => setExpanded(!expanded)}
                  size="small"
                  color="primary"
                >
                  {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  <Typography variant="caption" sx={{ ml: 1 }}>
                    {expanded ? 'Show Less' : `Show ${umweltEntries.length - maxDisplayItems} More`}
                  </Typography>
                </IconButton>
              </Box>
            )}

            <Divider sx={{ my: 2 }} />

            {/* Summary Statistics */}
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 1, textAlign: 'center' }}>
                  <Typography variant="h6" color="primary">
                    {totalKeys}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Total Keys
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 1, textAlign: 'center' }}>
                  <Typography variant="h6" color="success.main">
                    {umweltEntries.filter(e => e.priority === 'high').length}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    High Priority
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 1, textAlign: 'center' }}>
                  <Typography variant="h6" color="warning.main">
                    {conflictCount}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Conflicts
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 1, textAlign: 'center' }}>
                  <Typography variant="h6" color="info.main">
                    {new Set(umweltEntries.map(e => e.parsed.source)).size}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Sources
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </>
        )}
      </CardContent>
    </UmweltCard>
  );
};

export default UmweltDisplay;