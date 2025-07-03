import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Badge,
  Tooltip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  CheckCircle,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Webhook as WebhookIcon,
} from '@mui/icons-material';

const mockAlerts = [
  {
    id: 1,
    title: 'High CPU Usage on Agent Engine',
    description: 'CPU usage has exceeded 80% for the last 10 minutes',
    severity: 'error',
    service: 'Agent Engine',
    timestamp: new Date(Date.now() - 1000 * 60 * 15),
    status: 'active',
    metric: 'cpu_usage',
    threshold: 80,
    currentValue: 87.5,
    acknowledged: false,
  },
  {
    id: 2,
    title: 'Memory Usage Warning',
    description: 'Knowledge Vault memory usage approaching limit',
    severity: 'warning',
    service: 'Knowledge Vault',
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    status: 'active',
    metric: 'memory_usage',
    threshold: 85,
    currentValue: 82.3,
    acknowledged: false,
  },
  {
    id: 3,
    title: 'Response Time Degradation',
    description: 'Agent Bridge response time is slower than expected',
    severity: 'warning',
    service: 'Agent Bridge',
    timestamp: new Date(Date.now() - 1000 * 60 * 45),
    status: 'active',
    metric: 'response_time',
    threshold: 2000,
    currentValue: 2456,
    acknowledged: true,
  },
  {
    id: 4,
    title: 'Service Health Check Failed',
    description: 'Tool Forge health check endpoint is not responding',
    severity: 'error',
    service: 'Tool Forge',
    timestamp: new Date(Date.now() - 1000 * 60 * 60),
    status: 'resolved',
    metric: 'health_check',
    threshold: 1,
    currentValue: 0,
    acknowledged: true,
  },
  {
    id: 5,
    title: 'Disk Space Warning',
    description: 'Available disk space is running low',
    severity: 'info',
    service: 'All Services',
    timestamp: new Date(Date.now() - 1000 * 60 * 120),
    status: 'active',
    metric: 'disk_usage',
    threshold: 90,
    currentValue: 87.2,
    acknowledged: false,
  },
];

const alertRules = [
  {
    id: 1,
    name: 'High CPU Usage',
    service: 'All Services',
    metric: 'cpu_usage',
    operator: '>',
    threshold: 80,
    duration: '5m',
    severity: 'error',
    enabled: true,
    notifications: ['email', 'webhook'],
  },
  {
    id: 2,
    name: 'Memory Usage Warning',
    service: 'All Services',
    metric: 'memory_usage',
    operator: '>',
    threshold: 85,
    duration: '10m',
    severity: 'warning',
    enabled: true,
    notifications: ['email'],
  },
  {
    id: 3,
    name: 'Response Time Alert',
    service: 'All Services',
    metric: 'response_time',
    operator: '>',
    threshold: 2000,
    duration: '3m',
    severity: 'warning',
    enabled: true,
    notifications: ['webhook'],
  },
  {
    id: 4,
    name: 'Service Down',
    service: 'All Services',
    metric: 'health_check',
    operator: '==',
    threshold: 0,
    duration: '1m',
    severity: 'error',
    enabled: true,
    notifications: ['email', 'sms', 'webhook'],
  },
];

function Alerts() {
  const [alerts, setAlerts] = useState(mockAlerts);
  const [rules, setRules] = useState(alertRules);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [alertDialog, setAlertDialog] = useState(false);
  const [ruleDialog, setRuleDialog] = useState(false);
  const [selectedRule, setSelectedRule] = useState(null);
  const [globalNotifications, setGlobalNotifications] = useState(true);

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'error':
        return <ErrorIcon sx={{ color: '#ef4444' }} />;
      case 'warning':
        return <WarningIcon sx={{ color: '#f59e0b' }} />;
      case 'info':
        return <InfoIcon sx={{ color: '#06b6d4' }} />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'error';
      case 'resolved':
        return 'success';
      case 'acknowledged':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleAcknowledgeAlert = (alertId) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId 
        ? { ...alert, acknowledged: true }
        : alert
    ));
  };

  const handleResolveAlert = (alertId) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId 
        ? { ...alert, status: 'resolved' }
        : alert
    ));
  };

  const handleDeleteAlert = (alertId) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const handleToggleRule = (ruleId) => {
    setRules(prev => prev.map(rule => 
      rule.id === ruleId 
        ? { ...rule, enabled: !rule.enabled }
        : rule
    ));
  };

  const getAlertStats = () => {
    const activeAlerts = alerts.filter(alert => alert.status === 'active');
    return {
      total: alerts.length,
      active: activeAlerts.length,
      error: activeAlerts.filter(alert => alert.severity === 'error').length,
      warning: activeAlerts.filter(alert => alert.severity === 'warning').length,
      info: activeAlerts.filter(alert => alert.severity === 'info').length,
      unacknowledged: activeAlerts.filter(alert => !alert.acknowledged).length,
    };
  };

  const stats = getAlertStats();

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Alerts & Monitoring
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage alerts, notifications, and monitoring rules
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={globalNotifications}
                onChange={(e) => setGlobalNotifications(e.target.checked)}
                color="primary"
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {globalNotifications ? <NotificationsIcon /> : <NotificationsOffIcon />}
                <Typography sx={{ ml: 1 }}>Notifications</Typography>
              </Box>
            }
          />
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setSelectedRule(null);
              setRuleDialog(true);
            }}
          >
            Add Rule
          </Button>
        </Box>
      </Box>

      {/* Alert Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {stats.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Alerts
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="warning.main">
                {stats.active}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="error.main">
                {stats.error}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Critical
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="warning.main">
                {stats.warning}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Warnings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="info.main">
                {stats.info}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Info
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ backgroundColor: 'background.paper' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Badge badgeContent={stats.unacknowledged} color="error">
                <Typography variant="h4" fontWeight="bold" color="text.primary">
                  {stats.unacknowledged}
                </Typography>
              </Badge>
              <Typography variant="body2" color="text.secondary">
                Unacked
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Active Alerts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Paper sx={{ backgroundColor: 'background.paper' }}>
            <Box sx={{ p: 2, borderBottom: '1px solid #334155' }}>
              <Typography variant="h6" fontWeight="bold">
                Active Alerts ({stats.active})
              </Typography>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Alert</TableCell>
                    <TableCell>Service</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Time</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alerts.filter(alert => alert.status === 'active').map((alert) => (
                    <TableRow key={alert.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {getSeverityIcon(alert.severity)}
                          <Box sx={{ ml: 2 }}>
                            <Typography fontWeight="bold">
                              {alert.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {alert.description}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={alert.service} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={alert.severity.toUpperCase()} 
                          color={getSeverityColor(alert.severity)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={alert.acknowledged ? 'Acknowledged' : 'Active'} 
                          color={alert.acknowledged ? 'warning' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {alert.timestamp.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {!alert.acknowledged && (
                            <Tooltip title="Acknowledge">
                              <IconButton 
                                size="small" 
                                onClick={() => handleAcknowledgeAlert(alert.id)}
                              >
                                <CheckCircle fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Resolve">
                            <IconButton 
                              size="small" 
                              onClick={() => handleResolveAlert(alert.id)}
                            >
                              <SuccessIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Details">
                            <IconButton 
                              size="small"
                              onClick={() => {
                                setSelectedAlert(alert);
                                setAlertDialog(true);
                              }}
                            >
                              <InfoIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {stats.active === 0 && (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <SuccessIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No active alerts
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  All systems are running normally
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Alert Rules */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ backgroundColor: 'background.paper', height: 'fit-content' }}>
            <Box sx={{ p: 2, borderBottom: '1px solid #334155' }}>
              <Typography variant="h6" fontWeight="bold">
                Alert Rules ({rules.length})
              </Typography>
            </Box>
            <Box sx={{ p: 2 }}>
              {rules.map((rule) => (
                <Card key={rule.id} sx={{ mb: 2, backgroundColor: 'background.default' }}>
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography fontWeight="bold">
                        {rule.name}
                      </Typography>
                      <Switch
                        checked={rule.enabled}
                        onChange={() => handleToggleRule(rule.id)}
                        size="small"
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                      {rule.service} • {rule.metric} {rule.operator} {rule.threshold}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Chip 
                        label={rule.severity} 
                        color={getSeverityColor(rule.severity)}
                        size="small"
                      />
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {rule.notifications.includes('email') && <EmailIcon fontSize="small" />}
                        {rule.notifications.includes('sms') && <SmsIcon fontSize="small" />}
                        {rule.notifications.includes('webhook') && <WebhookIcon fontSize="small" />}
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Paper sx={{ backgroundColor: 'background.paper' }}>
        <Box sx={{ p: 2, borderBottom: '1px solid #334155' }}>
          <Typography variant="h6" fontWeight="bold">
            Recent Alert Activity
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Alert</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Time</TableCell>
                <TableCell>Current Value</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alerts.slice(0, 10).map((alert) => (
                <TableRow key={alert.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {getSeverityIcon(alert.severity)}
                      <Typography sx={{ ml: 2 }} fontWeight="bold">
                        {alert.title}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip label={alert.service} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={alert.severity.toUpperCase()} 
                      color={getSeverityColor(alert.severity)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={alert.status.toUpperCase()} 
                      color={getStatusColor(alert.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {alert.timestamp.toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {alert.currentValue}
                      {alert.metric.includes('usage') && '%'}
                      {alert.metric.includes('time') && 'ms'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Alert Details Dialog */}
      <Dialog 
        open={alertDialog} 
        onClose={() => setAlertDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Alert Details</DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Alert severity={getSeverityColor(selectedAlert.severity)} sx={{ mb: 2 }}>
                  <Typography fontWeight="bold">{selectedAlert.title}</Typography>
                  <Typography>{selectedAlert.description}</Typography>
                </Alert>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Service"
                  value={selectedAlert.service}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Metric"
                  value={selectedAlert.metric}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Threshold"
                  value={selectedAlert.threshold}
                  fullWidth
                  disabled
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Current Value"
                  value={selectedAlert.currentValue}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Status"
                  value={selectedAlert.status}
                  fullWidth
                  disabled
                  margin="normal"
                />
                <TextField
                  label="Acknowledged"
                  value={selectedAlert.acknowledged ? 'Yes' : 'No'}
                  fullWidth
                  disabled
                  margin="normal"
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlertDialog(false)}>Close</Button>
          {selectedAlert && !selectedAlert.acknowledged && (
            <Button 
              variant="contained" 
              onClick={() => {
                handleAcknowledgeAlert(selectedAlert.id);
                setAlertDialog(false);
              }}
            >
              Acknowledge
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Alerts;