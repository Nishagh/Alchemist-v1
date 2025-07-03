import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { services } from '../config/services';

// Real metrics data from actual service monitoring

const statusColors = {
  healthy: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  unknown: '#6b7280',
};

function Dashboard() {
  const [serviceStatuses, setServiceStatuses] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [totalRequestsCount, setTotalRequestsCount] = useState(0);
  const [metricsHistory, setMetricsHistory] = useState([]);

  const fetchMetricsSummary = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch('https://alchemist-monitor-service-851487020021.us-central1.run.app/api/monitoring/summary?time_range=24h', {
        signal: controller.signal,
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timeout (>10s)');
      }
      throw error;
    }
  };

  const fetchServicesHealth = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch('https://alchemist-monitor-service-851487020021.us-central1.run.app/api/monitoring/services/health', {
        signal: controller.signal,
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timeout (>10s)');
      }
      throw error;
    }
  };

  const checkAllServices = async () => {
    setIsLoading(true);
    const statuses = {};
    const currentTime = new Date();

    try {
      // Fetch both summary metrics and health data
      const [summaryData, healthData] = await Promise.all([
        fetchMetricsSummary(),
        fetchServicesHealth()
      ]);
      
      // Update total requests from summary
      if (summaryData.success && summaryData.data?.summary) {
        setTotalRequestsCount(summaryData.data.summary.total_requests || 0);
      }
      
      // Process health data
      if (healthData.success && healthData.data?.services) {
        const apiServices = healthData.data?.services || healthData.services || [];
        
        services.forEach(service => {
          const apiService = apiServices.find(s => 
            s.service_name === service.name ||
            s.service_name === service.name.toLowerCase().replace(/ /g, '-') ||
            s.service_name.includes(service.name.toLowerCase().replace(/ /g, '-'))
          );
          
          if (apiService) {
            statuses[service.name] = {
              status: apiService.status,
              responseTime: Math.round(apiService.current_response_time),
              timestamp: new Date(apiService.last_updated),
              serviceName: service.name,
              cpuUsage: apiService.current_cpu,
              memoryUsage: apiService.current_memory
            };
          } else {
            statuses[service.name] = {
              status: 'unknown',
              responseTime: null,
              timestamp: currentTime,
              serviceName: service.name,
              error: 'Not reporting to metrics system'
            };
          }
        });
      }
      
      // Calculate metrics for history chart
      const healthyServicesCount = Object.values(statuses).filter(s => s.status === 'healthy').length;
      const responseTimesArray = Object.values(statuses)
        .filter(s => s.responseTime)
        .map(s => s.responseTime);
      const avgResponseTime = responseTimesArray.length > 0 
        ? Math.round(responseTimesArray.reduce((a, b) => a + b, 0) / responseTimesArray.length)
        : 0;
      
      // Add to metrics history (keep only last 24 data points for chart)
      setMetricsHistory(prev => {
        const newEntry = {
          time: currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          timestamp: currentTime,
          healthyServices: healthyServicesCount,
          totalServices: services.length,
          avgResponseTime,
          requests: summaryData.success ? summaryData.data?.summary?.total_requests || 0 : 0
        };
        
        const updated = [...prev, newEntry].slice(-24);
        return updated;
      });
      
    } catch (error) {
      console.error('Failed to fetch metrics data:', error);
      
      // Fallback: mark all services as error
      services.forEach(service => {
        statuses[service.name] = {
          status: 'error',
          responseTime: null,
          timestamp: currentTime,
          serviceName: service.name,
          error: `Metrics API error: ${error.message}`
        };
      });
    }
    
    setServiceStatuses(statuses);
    setLastUpdated(currentTime);
    setIsLoading(false);
  };

  useEffect(() => {
    checkAllServices();
    const interval = setInterval(checkAllServices, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon sx={{ color: statusColors.healthy }} />;
      case 'warning':
        return <WarningIcon sx={{ color: statusColors.warning }} />;
      case 'error':
        return <ErrorIcon sx={{ color: statusColors.error }} />;
      default:
        return <WarningIcon sx={{ color: statusColors.unknown }} />;
    }
  };

  const getStatusColor = (status) => {
    return statusColors[status] || statusColors.unknown;
  };

  const healthyServices = Object.values(serviceStatuses).filter(s => s.status === 'healthy').length;
  const totalServices = services.length;
  const systemHealth = totalServices > 0 ? (healthyServices / totalServices) * 100 : 0;

  const pieData = [
    { name: 'Healthy', value: healthyServices, color: statusColors.healthy },
    { name: 'Issues', value: totalServices - healthyServices, color: statusColors.error },
  ];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Alchemist Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time monitoring of all Alchemist services
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Refresh Status">
            <IconButton 
              onClick={checkAllServices} 
              disabled={isLoading}
              sx={{ color: 'primary.main' }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* System Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    System Health
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color={systemHealth > 80 ? 'success.main' : 'error.main'}>
                    {systemHealth.toFixed(0)}%
                  </Typography>
                </Box>
                <SpeedIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={systemHealth} 
                sx={{ mt: 2, height: 6, borderRadius: 3 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Active Services
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {healthyServices}/{totalServices}
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Avg Response Time
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {metricsHistory.length > 0 ? `${metricsHistory[metricsHistory.length - 1].avgResponseTime}ms` : '0ms'}
                  </Typography>
                </Box>
                <MemoryIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Requests
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {totalRequestsCount}
                  </Typography>
                </Box>
                <StorageIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Service Status Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Service Status
            </Typography>
            <Grid container spacing={2}>
              {services.map((service) => {
                const status = serviceStatuses[service.name];
                return (
                  <Grid item xs={12} sm={6} md={4} key={service.name}>
                    <Card 
                      sx={{ 
                        backgroundColor: 'background.default',
                        border: `2px solid ${getStatusColor(status?.status || 'unknown')}`,
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3,
                        }
                      }}
                    >
                      <CardContent sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="h6" sx={{ fontSize: '1.1rem' }}>
                            {service.icon} {service.name}
                          </Typography>
                          {getStatusIcon(status?.status)}
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {service.description}
                        </Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                          <Chip 
                            label={status?.status || 'Checking...'} 
                            size="small"
                            sx={{ 
                              backgroundColor: getStatusColor(status?.status || 'unknown'),
                              color: 'white',
                              fontWeight: 'bold',
                              textTransform: 'uppercase',
                            }}
                          />
                          {status?.responseTime && (
                            <Typography variant="caption" color="text.secondary">
                              ~{status.responseTime}ms
                            </Typography>
                          )}
                        </Box>
                        {(status?.cpuUsage || status?.memoryUsage) && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              CPU: {status.cpuUsage?.toFixed(1)}% | Memory: {status.memoryUsage?.toFixed(1)}%
                            </Typography>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, backgroundColor: 'background.paper', height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Service Distribution
            </Typography>
            <Box sx={{ height: 200, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </Box>
            <Box sx={{ mt: 2 }}>
              {pieData.map((entry) => (
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
                    {entry.name}: {entry.value}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Performance Metrics */}
      <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          System Performance (24h)
        </Typography>
        <Box sx={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metricsHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#cbd5e1" />
              <YAxis stroke="#cbd5e1" />
              <Line 
                type="monotone" 
                dataKey="healthyServices" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Healthy Services"
              />
              <Line 
                type="monotone" 
                dataKey="avgResponseTime" 
                stroke="#6366f1" 
                strokeWidth={2}
                name="Avg Response Time (ms)"
              />
              <Line 
                type="monotone" 
                dataKey="requests" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="Total Requests"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Box>
  );
}

export default Dashboard;