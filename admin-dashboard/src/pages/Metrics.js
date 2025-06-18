import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  CloudQueue as CloudIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { services } from '../config/services';

const timeRanges = ['1h', '6h', '24h', '7d', '30d'];

// Get Agent Engine service URL for metrics API
const getAgentEngineUrl = () => {
  const agentEngine = services.find(service => service.name === 'Agent Engine');
  return agentEngine?.url || 'https://alchemist-agent-engine-851487020021.us-central1.run.app';
};

// API functions
const fetchDashboardMetrics = async (timeRange = '24h') => {
  try {
    const response = await fetch(`${getAgentEngineUrl()}/api/metrics/dashboard?time_range=${timeRange}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result.success ? result.data : null;
  } catch (error) {
    console.error('Failed to fetch dashboard metrics:', error);
    return null;
  }
};

const fetchHealthStatus = async () => {
  try {
    const response = await fetch(`${getAgentEngineUrl()}/api/metrics/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result.success ? result.data : null;
  } catch (error) {
    console.error('Failed to fetch health status:', error);
    return null;
  }
};


const serviceColors = {
  'agent-engine': '#6366f1',
  'knowledge-vault': '#10b981',
  'agent-bridge': '#f59e0b',
  'agent-launcher': '#ef4444',
  'tool-forge': '#8b5cf6',
};

function Metrics() {
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedService, setSelectedService] = useState('All Services');
  const [metricsData, setMetricsData] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch dashboard metrics
      const dashboardData = await fetchDashboardMetrics(timeRange);
      
      // Fetch health status
      const healthStatus = await fetchHealthStatus();
      
      if (dashboardData) {
        setMetricsData(dashboardData);
        setError(null);
      } else {
        throw new Error('No metrics data received from API');
      }
      
      if (healthStatus) {
        setHealthData(healthStatus);
      }
      
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error refreshing metrics data:', err);
      setError('Failed to load metrics data from API');
      setMetricsData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [timeRange]);

  const getCurrentMetrics = () => {
    if (!metricsData) {
      return {
        totalCPU: 0,
        totalMemory: 0,
        avgResponseTime: 0,
        totalRequests: 0,
        errorRate: 0,
      };
    }

    // Calculate averages from current metrics
    const cpuValues = Object.values(metricsData.current_cpu || {});
    const memoryValues = Object.values(metricsData.current_memory || {});
    const responseTimeValues = Object.values(metricsData.current_response_time || {});

    return {
      totalCPU: cpuValues.length > 0 ? cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length : 0,
      totalMemory: memoryValues.length > 0 ? memoryValues.reduce((a, b) => a + b, 0) / memoryValues.length : 0,
      avgResponseTime: responseTimeValues.length > 0 ? responseTimeValues.reduce((a, b) => a + b, 0) / responseTimeValues.length : 0,
      totalRequests: metricsData.total_requests || 0,
      errorRate: metricsData.overall_error_rate || 0,
    };
  };

  const metrics = getCurrentMetrics();

  // Show loading spinner while fetching data
  if (loading && !metricsData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Show error message if no data and not loading
  if (!loading && !metricsData) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load metrics data. Please check that the metrics services are running and try again.
        </Alert>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
          <Button variant="contained" onClick={refreshData} startIcon={<RefreshIcon />}>
            Retry Loading Metrics
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      {/* Error Alert */}
      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Performance Metrics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor system performance and resource usage across all services
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              {timeRanges.map(range => (
                <MenuItem key={range} value={range}>{range}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <RefreshIcon />}
            onClick={refreshData}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} lg={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Avg CPU Usage
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="primary">
                    {metrics.totalCPU.toFixed(1)}%
                  </Typography>
                </Box>
                <SpeedIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
              </Box>
              <Box sx={{ mt: 1 }}>
                <Chip 
                  label={metrics.totalCPU > 70 ? "High" : metrics.totalCPU > 50 ? "Medium" : "Low"}
                  color={metrics.totalCPU > 70 ? "error" : metrics.totalCPU > 50 ? "warning" : "success"}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Memory Usage
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="success.main">
                    {metrics.totalMemory.toFixed(1)}%
                  </Typography>
                </Box>
                <MemoryIcon sx={{ fontSize: 40, color: 'success.main', opacity: 0.7 }} />
              </Box>
              <Box sx={{ mt: 1 }}>
                <Chip 
                  label={metrics.totalMemory > 80 ? "High" : metrics.totalMemory > 60 ? "Medium" : "Low"}
                  color={metrics.totalMemory > 80 ? "error" : metrics.totalMemory > 60 ? "warning" : "success"}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Response Time
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="warning.main">
                    {metrics.avgResponseTime.toFixed(0)}ms
                  </Typography>
                </Box>
                <TimelineIcon sx={{ fontSize: 40, color: 'warning.main', opacity: 0.7 }} />
              </Box>
              <Box sx={{ mt: 1 }}>
                <Chip 
                  label={metrics.avgResponseTime > 200 ? "Slow" : metrics.avgResponseTime > 100 ? "Average" : "Fast"}
                  color={metrics.avgResponseTime > 200 ? "error" : metrics.avgResponseTime > 100 ? "warning" : "success"}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Requests
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="info.main">
                    {metrics.totalRequests.toLocaleString()}
                  </Typography>
                </Box>
                <CloudIcon sx={{ fontSize: 40, color: 'info.main', opacity: 0.7 }} />
              </Box>
              <Box sx={{ mt: 1 }}>
                <Chip 
                  label="24h"
                  color="info"
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Error Rate
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="error.main">
                    {metrics.errorRate.toFixed(2)}%
                  </Typography>
                </Box>
                <ErrorIcon sx={{ fontSize: 40, color: 'error.main', opacity: 0.7 }} />
              </Box>
              <Box sx={{ mt: 1 }}>
                <Chip 
                  label={metrics.errorRate > 5 ? "High" : metrics.errorRate > 2 ? "Medium" : "Low"}
                  color={metrics.errorRate > 5 ? "error" : metrics.errorRate > 2 ? "warning" : "success"}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* CPU Usage Chart */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              CPU Usage Over Time
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metricsData?.cpu_time_series || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#cbd5e1" />
                  <YAxis stroke="#cbd5e1" />
                  <RechartsTooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc'
                    }} 
                  />
                  <Legend />
                  {metricsData?.services?.map(service => (
                    <Line
                      key={service}
                      type="monotone"
                      dataKey={service}
                      stroke={serviceColors[service] || '#6366f1'}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper', height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Request Distribution
            </Typography>
            <Box sx={{ height: 250 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={metricsData?.request_distribution || []}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="requests"
                    label={({ service, percent }) => `${service} ${(percent * 100).toFixed(0)}%`}
                  >
                    {(metricsData?.request_distribution || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={serviceColors[entry.service] || Object.values(serviceColors)[index % Object.values(serviceColors).length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc'
                    }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Memory Usage and Response Time */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Memory Usage
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metricsData?.memory_time_series || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#cbd5e1" />
                  <YAxis stroke="#cbd5e1" />
                  <RechartsTooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc'
                    }} 
                  />
                  <Legend />
                  {metricsData?.services?.map(service => (
                    <Area
                      key={service}
                      type="monotone"
                      dataKey={service}
                      stackId="1"
                      stroke={serviceColors[service] || '#6366f1'}
                      fill={serviceColors[service] || '#6366f1'}
                      fillOpacity={0.3}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Response Time Trends
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metricsData?.response_time_series || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#cbd5e1" />
                  <YAxis stroke="#cbd5e1" />
                  <RechartsTooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc'
                    }} 
                  />
                  <Legend />
                  {metricsData?.services?.map(service => (
                    <Line
                      key={service}
                      type="monotone"
                      dataKey={service}
                      stroke={serviceColors[service] || '#6366f1'}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Requests and Error Analysis */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Requests per Service
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metricsData?.request_distribution || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="service" stroke="#cbd5e1" />
                  <YAxis stroke="#cbd5e1" />
                  <RechartsTooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc'
                    }} 
                  />
                  <Bar dataKey="requests" fill="#6366f1" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper', height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Success vs Errors
            </Typography>
            <Box sx={{ height: 250 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={metricsData?.error_statistics || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {(metricsData?.error_statistics || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc'
                    }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            </Box>
            <Box sx={{ mt: 2 }}>
              {(metricsData?.error_statistics || []).map((entry) => (
                <Box key={entry.name} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box 
                    sx={{ 
                      width: 12, 
                      height: 12, 
                      backgroundColor: entry.color, 
                      borderRadius: '50%', 
                      mr: 1 
                    }} 
                  />
                  <Typography variant="body2">
                    {entry.name}: {entry.value.toLocaleString()}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Metrics;