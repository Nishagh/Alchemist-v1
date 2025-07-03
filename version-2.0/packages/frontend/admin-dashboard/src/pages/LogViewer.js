import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

const services = [
  'All Services',
  'Agent Engine',
  'Knowledge Vault',
  'Agent Bridge',
  'Agent Launcher',
  'Tool Forge',
  'Agent Studio',
];

const logLevels = ['ALL', 'ERROR', 'WARN', 'INFO', 'DEBUG'];

const mockLogs = [
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    level: 'INFO',
    service: 'Agent Engine',
    message: 'Successfully processed agent request for user_123',
    requestId: 'req_abc123',
    userId: 'user_123',
    details: { endpoint: '/api/agents/create', method: 'POST', statusCode: 200 }
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 3),
    level: 'ERROR',
    service: 'Knowledge Vault',
    message: 'Failed to process document: file_not_found.pdf',
    requestId: 'req_def456',
    error: 'FileNotFoundError: The specified file could not be located',
    details: { filePath: '/uploads/file_not_found.pdf', operation: 'vectorize' }
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 2),
    level: 'WARN',
    service: 'Agent Bridge',
    message: 'WhatsApp webhook response time exceeded threshold',
    requestId: 'req_ghi789',
    details: { responseTime: '2.5s', threshold: '2.0s', webhook: 'message_received' }
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 1),
    level: 'INFO',
    service: 'Tool Forge',
    message: 'MCP server deployment completed successfully',
    requestId: 'req_jkl012',
    details: { serverId: 'mcp_banking_api', deploymentTime: '45s', status: 'active' }
  },
  {
    timestamp: new Date(Date.now() - 1000 * 30),
    level: 'DEBUG',
    service: 'Agent Launcher',
    message: 'Docker container health check passed',
    requestId: 'req_mno345',
    details: { containerId: 'agent_container_xyz', healthStatus: 'healthy', memoryUsage: '256MB' }
  },
];

function LogViewer() {
  const [logs, setLogs] = useState(mockLogs);
  const [filteredLogs, setFilteredLogs] = useState(mockLogs);
  const [selectedService, setSelectedService] = useState('All Services');
  const [selectedLevel, setSelectedLevel] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const logContainerRef = useRef(null);

  const generateRandomLog = () => {
    const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG'];
    const serviceNames = services.slice(1); // Remove 'All Services'
    const messages = [
      'Request processed successfully',
      'Database connection established',
      'Cache miss for key: user_session',
      'Authentication token validated',
      'File upload completed',
      'Webhook payload received',
      'Configuration updated',
      'Health check performed',
      'Memory usage within normal limits',
      'API rate limit approaching threshold',
    ];

    const level = levels[Math.floor(Math.random() * levels.length)];
    const service = serviceNames[Math.floor(Math.random() * serviceNames.length)];
    const message = messages[Math.floor(Math.random() * messages.length)];

    return {
      timestamp: new Date(),
      level,
      service,
      message,
      requestId: `req_${Math.random().toString(36).substr(2, 9)}`,
      details: {
        endpoint: `/api/${Math.random().toString(36).substr(2, 6)}`,
        method: Math.random() > 0.5 ? 'GET' : 'POST',
        responseTime: `${Math.floor(Math.random() * 1000)}ms`,
      }
    };
  };

  const refreshLogs = () => {
    setIsLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      const newLogs = Array.from({ length: Math.floor(Math.random() * 5) + 1 }, generateRandomLog);
      setLogs(prev => [...newLogs, ...prev].slice(0, 1000)); // Keep last 1000 logs
      setLastUpdated(new Date());
      setIsLoading(false);
    }, 1000);
  };

  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => {
        const newLog = generateRandomLog();
        setLogs(prev => [newLog, ...prev].slice(0, 1000));
        setLastUpdated(new Date());
      }, 3000); // Add new log every 3 seconds
    }
    return () => clearInterval(interval);
  }, [autoRefresh]);

  useEffect(() => {
    let filtered = logs;

    // Filter by service
    if (selectedService !== 'All Services') {
      filtered = filtered.filter(log => log.service === selectedService);
    }

    // Filter by log level
    if (selectedLevel !== 'ALL') {
      filtered = filtered.filter(log => log.level === selectedLevel);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.requestId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (log.error && log.error.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    setFilteredLogs(filtered);
  }, [logs, selectedService, selectedLevel, searchQuery]);

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR':
        return 'error';
      case 'WARN':
        return 'warning';
      case 'INFO':
        return 'info';
      case 'DEBUG':
        return 'default';
      default:
        return 'default';
    }
  };

  const downloadLogs = () => {
    const logText = filteredLogs.map(log => {
      return `[${log.timestamp.toISOString()}] [${log.level}] [${log.service}] ${log.message}${log.error ? ` - Error: ${log.error}` : ''} (Request: ${log.requestId})`;
    }).join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alchemist-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearSearch = () => {
    setSearchQuery('');
  };

  const scrollToTop = () => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0;
    }
  };

  useEffect(() => {
    scrollToTop();
  }, [filteredLogs]);

  const getLogStats = () => {
    const stats = {
      total: filteredLogs.length,
      error: filteredLogs.filter(log => log.level === 'ERROR').length,
      warn: filteredLogs.filter(log => log.level === 'WARN').length,
      info: filteredLogs.filter(log => log.level === 'INFO').length,
      debug: filteredLogs.filter(log => log.level === 'DEBUG').length,
    };
    return stats;
  };

  const stats = getLogStats();

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Log Viewer
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time logs from all Alchemist services
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                color="primary"
              />
            }
            label="Auto Refresh"
          />
          <Button
            variant="contained"
            startIcon={isLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={refreshLogs}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {/* Log Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6" fontWeight="bold">
                {stats.total}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Logs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6" fontWeight="bold" color="error.main">
                {stats.error}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Errors
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6" fontWeight="bold" color="warning.main">
                {stats.warn}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Warnings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6" fontWeight="bold" color="info.main">
                {stats.info}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Info
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={2.4}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6" fontWeight="bold" color="text.secondary">
                {stats.debug}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Debug
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          <FilterIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Filters
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth>
              <InputLabel>Service</InputLabel>
              <Select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                label="Service"
              >
                {services.map(service => (
                  <MenuItem key={service} value={service}>
                    {service}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth>
              <InputLabel>Log Level</InputLabel>
              <Select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                label="Log Level"
              >
                {logLevels.map(level => (
                  <MenuItem key={level} value={level}>
                    {level}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by message, request ID, or error"
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                endAdornment: searchQuery && (
                  <IconButton size="small" onClick={clearSearch}>
                    <ClearIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={downloadLogs}
              fullWidth
              disabled={filteredLogs.length === 0}
            >
              Export
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Logs Display */}
      <Paper sx={{ backgroundColor: 'background.paper' }}>
        <Box sx={{ p: 2, borderBottom: '1px solid #334155' }}>
          <Typography variant="h6" fontWeight="bold">
            Live Logs ({filteredLogs.length} entries)
          </Typography>
        </Box>
        <Box
          ref={logContainerRef}
          sx={{
            height: '60vh',
            overflow: 'auto',
            backgroundColor: '#0f172a',
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            p: 1,
          }}
        >
          {filteredLogs.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No logs found matching the current filters.
              </Typography>
            </Box>
          ) : (
            filteredLogs.map((log, index) => (
              <Box
                key={`${log.requestId}-${index}`}
                sx={{
                  p: 1,
                  mb: 1,
                  borderLeft: `4px solid ${
                    log.level === 'ERROR' ? '#ef4444' :
                    log.level === 'WARN' ? '#f59e0b' :
                    log.level === 'INFO' ? '#06b6d4' : '#6b7280'
                  }`,
                  backgroundColor: 'rgba(30, 41, 59, 0.5)',
                  borderRadius: 1,
                  '&:hover': {
                    backgroundColor: 'rgba(30, 41, 59, 0.8)',
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                  <Typography
                    variant="caption"
                    sx={{
                      color: '#94a3b8',
                      fontFamily: 'monospace',
                      minWidth: '180px',
                    }}
                  >
                    {log.timestamp.toLocaleString()}
                  </Typography>
                  <Chip
                    label={log.level}
                    size="small"
                    color={getLevelColor(log.level)}
                    sx={{ mx: 1, fontFamily: 'monospace', minWidth: '60px' }}
                  />
                  <Chip
                    label={log.service}
                    size="small"
                    variant="outlined"
                    sx={{ mx: 1, fontFamily: 'monospace' }}
                  />
                  <Typography
                    variant="caption"
                    sx={{
                      color: '#64748b',
                      fontFamily: 'monospace',
                      ml: 'auto',
                    }}
                  >
                    {log.requestId}
                  </Typography>
                </Box>
                <Typography
                  sx={{
                    color: '#f8fafc',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    mb: log.error || Object.keys(log.details || {}).length > 0 ? 1 : 0,
                  }}
                >
                  {log.message}
                </Typography>
                {log.error && (
                  <Alert severity="error" sx={{ mt: 1, fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {log.error}
                  </Alert>
                )}
                {log.details && Object.keys(log.details).length > 0 && (
                  <Box
                    sx={{
                      mt: 1,
                      p: 1,
                      backgroundColor: 'rgba(15, 23, 42, 0.7)',
                      borderRadius: 1,
                      border: '1px solid #334155',
                    }}
                  >
                    <pre style={{
                      margin: 0,
                      fontSize: '0.75rem',
                      color: '#cbd5e1',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                    }}>
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  </Box>
                )}
              </Box>
            ))
          )}
        </Box>
      </Paper>
    </Box>
  );
}

export default LogViewer;