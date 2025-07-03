import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Launch as LaunchIcon,
  Settings as SettingsIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  RestartAlt as RestartIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { services } from '../config/services';

function ServiceStatus() {
  const [serviceStatuses, setServiceStatuses] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [selectedService, setSelectedService] = useState(null);
  const [serviceDialog, setServiceDialog] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [nextRefreshIn, setNextRefreshIn] = useState(0);

  const fetchServicesHealthFromAPI = async () => {
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
    setConnectionStatus('connecting');
    const statuses = {};

    try {
      const healthData = await fetchServicesHealthFromAPI();
      
      if (healthData.success && healthData.data?.services) {
        // Map API response to our services
        const apiServices = healthData.data?.services || healthData.services || [];
        
        services.forEach(service => {
          // Find matching service from API response
          const apiService = apiServices.find(s => 
            s.service_name === service.name ||
            s.service_name === service.name.toLowerCase().replace(/ /g, '-') ||
            s.service_name.includes(service.name.toLowerCase().replace(/ /g, '-'))
          );
          
          if (apiService) {
            statuses[service.name] = {
              status: apiService.status,
              responseTime: Math.round(apiService.current_response_time),
              data: {
                cpu_usage: apiService.current_cpu,
                memory_usage: apiService.current_memory,
                response_time: apiService.current_response_time
              },
              lastChecked: new Date(apiService.last_updated),
              error: apiService.status === 'error' ? 'Service reported error status' : null
            };
          } else {
            // Service not found in API response
            statuses[service.name] = {
              status: 'unknown',
              responseTime: null,
              data: null,
              lastChecked: new Date(),
              error: 'Service not reporting to metrics system'
            };
          }
        });
        
        setConnectionStatus('connected');
      } else {
        throw new Error(healthData.message || 'Invalid response format');
      }
    } catch (error) {
      console.error('Failed to fetch service health from API:', error);
      setConnectionStatus('error');
      
      // Fallback: mark all services as unknown with error
      services.forEach(service => {
        statuses[service.name] = {
          status: 'error',
          responseTime: null,
          data: null,
          lastChecked: new Date(),
          error: `Metrics API error: ${error.message}`
        };
      });
    }

    setServiceStatuses(statuses);
    setLastUpdated(new Date());
    setIsLoading(false);
    setNextRefreshIn(refreshInterval);
  };

  useEffect(() => {
    checkAllServices();
    
    let interval;
    let countdownInterval;
    
    if (autoRefresh) {
      // Set up auto-refresh
      interval = setInterval(checkAllServices, refreshInterval * 1000);
      
      // Set up countdown timer
      countdownInterval = setInterval(() => {
        setNextRefreshIn(prevCount => {
          if (prevCount <= 1) {
            return refreshInterval;
          }
          return prevCount - 1;
        });
      }, 1000);
      
      setNextRefreshIn(refreshInterval);
    }
    
    return () => {
      if (interval) clearInterval(interval);
      if (countdownInterval) clearInterval(countdownInterval);
    };
  }, [autoRefresh, refreshInterval]); // eslint-disable-line react-hooks/exhaustive-deps

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'unknown':
        return 'default';
      default:
        return 'default';
    }
  };

  const handleServiceClick = (service) => {
    setSelectedService(service);
    setServiceDialog(true);
  };

  const handleCloseDialog = () => {
    setServiceDialog(false);
    setSelectedService(null);
  };

  const getUptimePercent = () => {
    const healthyServices = Object.values(serviceStatuses).filter(s => s.status === 'healthy').length;
    return services.length > 0 ? ((healthyServices / services.length) * 100).toFixed(1) : 0;
  };

  const getAverageResponseTime = () => {
    const responseTimes = Object.values(serviceStatuses)
      .filter(s => s.responseTime)
      .map(s => s.responseTime);
    
    if (responseTimes.length === 0) return 0;
    return Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Service Status
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and manage all Alchemist microservices
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting' : 'Error'}
              color={connectionStatus === 'connected' ? 'success' : connectionStatus === 'connecting' ? 'info' : 'error'}
              size="small"
            />
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
            {autoRefresh && nextRefreshIn > 0 && (
              <Typography variant="caption" color="text.secondary">
                (next in {nextRefreshIn}s)
              </Typography>
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Button
              variant={autoRefresh ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? 'Auto' : 'Manual'}
            </Button>
            <Button 
              variant="contained" 
              startIcon={isLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={checkAllServices}
              disabled={isLoading}
            >
              {isLoading ? 'Checking...' : 'Refresh All'}
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                System Uptime
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {getUptimePercent()}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {Object.values(serviceStatuses).filter(s => s.status === 'healthy').length} of {services.length} services healthy
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Avg Response Time
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {getAverageResponseTime()}ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all healthy services
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Issues Detected
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="error">
                {Object.values(serviceStatuses).filter(s => s.status === 'error').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Services requiring attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Services Table */}
      <Paper sx={{ backgroundColor: 'background.paper' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><Typography fontWeight="bold">Service</Typography></TableCell>
                <TableCell><Typography fontWeight="bold">Status</Typography></TableCell>
                <TableCell><Typography fontWeight="bold">Type</Typography></TableCell>
                <TableCell><Typography fontWeight="bold">Response Time</Typography></TableCell>
                <TableCell><Typography fontWeight="bold">Last Checked</Typography></TableCell>
                <TableCell><Typography fontWeight="bold">Actions</Typography></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {services.map((service) => {
                const status = serviceStatuses[service.name];
                return (
                  <TableRow 
                    key={service.name} 
                    hover
                    sx={{ 
                      '&:hover': { 
                        backgroundColor: 'action.hover',
                        cursor: 'pointer'
                      } 
                    }}
                    onClick={() => handleServiceClick(service)}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography sx={{ mr: 1, fontSize: '1.2rem' }}>
                          {service.icon}
                        </Typography>
                        <Box>
                          <Typography fontWeight="bold">
                            {service.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            v{service.version}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={status?.status || 'Unknown'}
                        color={getStatusColor(status?.status)}
                        size="small"
                        sx={{ textTransform: 'capitalize' }}
                      />
                      {status?.error && (
                        <Typography variant="caption" color="error" sx={{ display: 'block', mt: 0.5 }}>
                          {status.error}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {service.type}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2">
                          {status?.responseTime ? `${status.responseTime}ms` : '-'}
                        </Typography>
                        {status?.data && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            CPU: {status.data.cpu_usage?.toFixed(1)}% | MEM: {status.data.memory_usage?.toFixed(1)}%
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {status?.lastChecked ? status.lastChecked.toLocaleTimeString() : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="Open Service">
                          <IconButton 
                            size="small" 
                            onClick={(e) => {
                              e.stopPropagation();
                              window.open(service.url, '_blank');
                            }}
                          >
                            <LaunchIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Service Details">
                          <IconButton 
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleServiceClick(service);
                            }}
                          >
                            <InfoIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Service Details Dialog */}
      <Dialog 
        open={serviceDialog} 
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography sx={{ mr: 1, fontSize: '1.5rem' }}>
              {selectedService?.icon}
            </Typography>
            {selectedService?.name} Details
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedService && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Service Name"
                  value={selectedService.name}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Description"
                  value={selectedService.description}
                  fullWidth
                  disabled
                  margin="normal"
                  multiline
                  rows={2}
                />
                <TextField
                  label="Service Type"
                  value={selectedService.type}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Version"
                  value={selectedService.version}
                  fullWidth
                  disabled
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="URL"
                  value={selectedService.url}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Port"
                  value={selectedService.port}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Health Endpoint"
                  value={selectedService.healthEndpoint}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Current Status"
                  value={serviceStatuses[selectedService.name]?.status || 'Unknown'}
                  fullWidth
                  disabled
                  margin="normal"
                />
              </Grid>
              {serviceStatuses[selectedService.name]?.data && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Service Response
                  </Typography>
                  <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                    <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(serviceStatuses[selectedService.name].data, null, 2)}
                    </pre>
                  </Paper>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>
            Close
          </Button>
          <Button 
            variant="contained" 
            onClick={() => window.open(selectedService?.url, '_blank')}
          >
            Open Service
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ServiceStatus;