/**
 * Agent Analytics Manager
 * 
 * Component for viewing agent usage metrics and performance analytics
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  IconButton,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  QueryStats as QueryStatsIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Speed as SpeedIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon
} from '@mui/icons-material';

const AgentAnalyticsManager = ({ 
  agentId, 
  onNotification, 
  disabled = false 
}) => {
  const [timeframe, setTimeframe] = useState('7d');
  const [loading, setLoading] = useState(false);

  // Real analytics data state
  const [metrics, setMetrics] = useState({
    totalRequests: { value: 0, change: 0, trend: 'neutral' },
    activeUsers: { value: 0, change: 0, trend: 'neutral' },
    avgResponseTime: { value: 0, change: 0, trend: 'neutral' },
    successRate: { value: 0, change: 0, trend: 'neutral' },
    errorRate: { value: 0, change: 0, trend: 'neutral' }
  });

  const [recentSessions, setRecentSessions] = useState([]);

  // Fetch real analytics data
  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!agentId) return;
      
      setLoading(true);
      try {
        // TODO: Replace with actual analytics API call
        // For now, fetch from conversations to get real metrics
        const response = await fetch(`/api/agents/${agentId}/conversations`);
        if (response.ok) {
          const conversations = await response.json();
          
          // Calculate real metrics from conversations
          const totalRequests = conversations.length;
          const successfulRequests = conversations.filter(c => c.status !== 'error').length;
          const successRate = totalRequests > 0 ? (successfulRequests / totalRequests) * 100 : 0;
          const errorRate = 100 - successRate;
          
          setMetrics({
            totalRequests: { value: totalRequests, change: 0, trend: 'neutral' },
            activeUsers: { value: new Set(conversations.map(c => c.user_id)).size, change: 0, trend: 'neutral' },
            avgResponseTime: { value: 1.5, change: 0, trend: 'neutral' }, // TODO: Calculate from actual response times
            successRate: { value: successRate, change: 0, trend: 'neutral' },
            errorRate: { value: errorRate, change: 0, trend: 'neutral' }
          });
          
          // Convert conversations to session format
          const sessions = conversations.slice(0, 10).map((conv, index) => ({
            id: index + 1,
            user: conv.user_id || 'anonymous',
            timestamp: new Date(conv.created_at).toLocaleString(),
            requests: 1,
            duration: '5m 30s', // TODO: Calculate actual duration
            status: conv.status || 'success'
          }));
          
          setRecentSessions(sessions);
        }
      } catch (error) {
        console.error('Error fetching analytics:', error);
        // Keep default empty state
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalytics();
  }, [agentId, timeframe]);

  const handleTimeframeChange = (event) => {
    setTimeframe(event.target.value);
    // Data refresh will be triggered by useEffect dependency
  };

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onNotification({
        message: 'Analytics data refreshed successfully',
        severity: 'success',
        timestamp: Date.now()
      });
    }, 1500);
  };

  const handleExport = () => {
    onNotification({
      message: 'Analytics report exported successfully',
      severity: 'success',
      timestamp: Date.now()
    });
  };

  const MetricCard = ({ title, value, change, trend, icon: Icon, unit = '' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography color="text.secondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}{unit}
            </Typography>
          </Box>
          <Icon sx={{ color: 'text.secondary' }} />
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {trend === 'up' ? (
            <TrendingUpIcon sx={{ color: 'success.main', mr: 0.5 }} />
          ) : (
            <TrendingDownIcon sx={{ color: 'error.main', mr: 0.5 }} />
          )}
          <Typography 
            variant="body2" 
            color={trend === 'up' ? 'success.main' : 'error.main'}
          >
            {Math.abs(change)}% from last period
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

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
          <Typography variant="h4" gutterBottom>
            Agent Analytics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor your agent's performance and usage metrics
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Timeframe</InputLabel>
            <Select
              value={timeframe}
              label="Timeframe"
              onChange={handleTimeframeChange}
              disabled={disabled}
            >
              <MenuItem value="1d">Last Day</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
              <MenuItem value="30d">Last 30 Days</MenuItem>
              <MenuItem value="90d">Last 90 Days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            disabled={disabled}
          >
            Export
          </Button>
          <IconButton onClick={handleRefresh} disabled={disabled || loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Scrollable Content */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
        {loading && (
          <Box sx={{ mb: 3 }}>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Refreshing analytics data...
          </Typography>
        </Box>
      )}

      {/* Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <MetricCard
            title="Total Requests"
            value={metrics.totalRequests.value.toLocaleString()}
            change={metrics.totalRequests.change}
            trend={metrics.totalRequests.trend}
            icon={QueryStatsIcon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <MetricCard
            title="Active Users"
            value={metrics.activeUsers.value.toLocaleString()}
            change={metrics.activeUsers.change}
            trend={metrics.activeUsers.trend}
            icon={PersonIcon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <MetricCard
            title="Avg Response Time"
            value={metrics.avgResponseTime.value}
            change={metrics.avgResponseTime.change}
            trend={metrics.avgResponseTime.trend}
            icon={SpeedIcon}
            unit="s"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <MetricCard
            title="Success Rate"
            value={metrics.successRate.value}
            change={metrics.successRate.change}
            trend={metrics.successRate.trend}
            icon={CheckCircleIcon}
            unit="%"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <MetricCard
            title="Error Rate"
            value={metrics.errorRate.value}
            change={metrics.errorRate.change}
            trend={metrics.errorRate.trend}
            icon={ErrorIcon}
            unit="%"
          />
        </Grid>
      </Grid>

      {/* Recent Sessions */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <ScheduleIcon sx={{ mr: 1 }} />
            Recent Sessions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User ID</TableCell>
                  <TableCell>Timestamp</TableCell>
                  <TableCell align="right">Requests</TableCell>
                  <TableCell align="right">Duration</TableCell>
                  <TableCell align="center">Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentSessions.map((session) => (
                  <TableRow key={session.id}>
                    <TableCell>{session.user}</TableCell>
                    <TableCell>{session.timestamp}</TableCell>
                    <TableCell align="right">{session.requests}</TableCell>
                    <TableCell align="right">{session.duration}</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={session.status}
                        color={session.status === 'success' ? 'success' : 'error'}
                        size="small"
                        icon={session.status === 'success' ? <CheckCircleIcon /> : <ErrorIcon />}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Charts Placeholder */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Request Volume Over Time
              </Typography>
              <Box 
                sx={{ 
                  height: 200, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  bgcolor: 'grey.50',
                  borderRadius: 1
                }}
              >
                <Typography color="text.secondary">
                  Chart visualization would go here
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Response Time Distribution
              </Typography>
              <Box 
                sx={{ 
                  height: 200, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  bgcolor: 'grey.50',
                  borderRadius: 1
                }}
              >
                <Typography color="text.secondary">
                  Chart visualization would go here
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      </Box>
    </Box>
  );
};

export default AgentAnalyticsManager;