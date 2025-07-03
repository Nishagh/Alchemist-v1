import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Alert,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function Settings() {
  const [activeTab, setActiveTab] = useState(0);
  const [showPassword, setShowPassword] = useState({});
  const [saveStatus, setSaveStatus] = useState(null);
  const [apiKeyDialog, setApiKeyDialog] = useState(false);
  const [newApiKey, setNewApiKey] = useState({ name: '', key: '', description: '' });

  // General Settings
  const [generalSettings, setGeneralSettings] = useState({
    dashboardTitle: 'Alchemist Admin Dashboard',
    refreshInterval: 30,
    timezone: 'UTC',
    theme: 'dark',
    autoRefresh: true,
    showWelcome: true,
  });

  // Notification Settings
  const [notificationSettings, setNotificationSettings] = useState({
    emailEnabled: true,
    emailHost: 'smtp.gmail.com',
    emailPort: 587,
    emailUser: 'admin@alchemist.com',
    emailPassword: '',
    slackEnabled: false,
    slackWebhook: '',
    webhookEnabled: true,
    webhookUrl: 'https://hooks.alchemist.com/alerts',
    criticalAlerts: true,
    warningAlerts: true,
    infoAlerts: false,
  });

  // Security Settings
  const [securitySettings, setSecuritySettings] = useState({
    sessionTimeout: 60,
    requireMFA: false,
    allowedIPs: '0.0.0.0/0',
    apiRateLimit: 1000,
    logRetention: 30,
    auditLogging: true,
  });

  // API Keys
  const [apiKeys, setApiKeys] = useState([
    {
      id: 1,
      name: 'Production Monitor',
      key: 'alch_prod_***************************',
      description: 'Main production monitoring key',
      created: new Date('2024-01-15'),
      lastUsed: new Date(),
      permissions: ['read', 'write'],
    },
    {
      id: 2,
      name: 'Development Access',
      key: 'alch_dev_****************************',
      description: 'Development environment access',
      created: new Date('2024-02-01'),
      lastUsed: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3),
      permissions: ['read'],
    },
  ]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleSave = (section) => {
    setSaveStatus({ section, status: 'saving' });
    
    // Simulate API call
    setTimeout(() => {
      setSaveStatus({ section, status: 'success' });
      setTimeout(() => setSaveStatus(null), 3000);
    }, 1000);
  };

  const togglePasswordVisibility = (field) => {
    setShowPassword(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleAddApiKey = () => {
    const newKey = {
      id: apiKeys.length + 1,
      ...newApiKey,
      key: `alch_${newApiKey.name.toLowerCase().replace(/\s+/g, '_')}_${'*'.repeat(28)}`,
      created: new Date(),
      lastUsed: null,
      permissions: ['read'],
    };
    setApiKeys([...apiKeys, newKey]);
    setNewApiKey({ name: '', key: '', description: '' });
    setApiKeyDialog(false);
  };

  const handleDeleteApiKey = (id) => {
    setApiKeys(apiKeys.filter(key => key.id !== id));
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure dashboard settings, notifications, and security options
        </Typography>
      </Box>

      {/* Save Status */}
      {saveStatus && (
        <Alert 
          severity={saveStatus.status === 'success' ? 'success' : 'info'} 
          sx={{ mb: 3 }}
        >
          {saveStatus.status === 'success' 
            ? `${saveStatus.section} settings saved successfully!`
            : `Saving ${saveStatus.section} settings...`
          }
        </Alert>
      )}

      {/* Settings Tabs */}
      <Paper sx={{ backgroundColor: 'background.paper' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          sx={{ borderBottom: '1px solid #334155' }}
        >
          <Tab icon={<CodeIcon />} label="General" />
          <Tab icon={<NotificationsIcon />} label="Notifications" />
          <Tab icon={<SecurityIcon />} label="Security" />
          <Tab icon={<StorageIcon />} label="API Keys" />
        </Tabs>

        {/* General Settings */}
        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            General Settings
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Dashboard Title"
                value={generalSettings.dashboardTitle}
                onChange={(e) => setGeneralSettings({
                  ...generalSettings,
                  dashboardTitle: e.target.value
                })}
                fullWidth
                margin="normal"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Refresh Interval (seconds)</InputLabel>
                <Select
                  value={generalSettings.refreshInterval}
                  onChange={(e) => setGeneralSettings({
                    ...generalSettings,
                    refreshInterval: e.target.value
                  })}
                  label="Refresh Interval (seconds)"
                >
                  <MenuItem value={15}>15 seconds</MenuItem>
                  <MenuItem value={30}>30 seconds</MenuItem>
                  <MenuItem value={60}>1 minute</MenuItem>
                  <MenuItem value={300}>5 minutes</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth margin="normal">
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={generalSettings.timezone}
                  onChange={(e) => setGeneralSettings({
                    ...generalSettings,
                    timezone: e.target.value
                  })}
                  label="Timezone"
                >
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="America/New_York">Eastern Time</MenuItem>
                  <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                  <MenuItem value="Europe/London">London</MenuItem>
                  <MenuItem value="Asia/Tokyo">Tokyo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Display Options
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={generalSettings.autoRefresh}
                      onChange={(e) => setGeneralSettings({
                        ...generalSettings,
                        autoRefresh: e.target.checked
                      })}
                    />
                  }
                  label="Auto-refresh data"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={generalSettings.showWelcome}
                      onChange={(e) => setGeneralSettings({
                        ...generalSettings,
                        showWelcome: e.target.checked
                      })}
                    />
                  }
                  label="Show welcome message"
                />
                <FormControl fullWidth margin="normal">
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={generalSettings.theme}
                    onChange={(e) => setGeneralSettings({
                      ...generalSettings,
                      theme: e.target.value
                    })}
                    label="Theme"
                  >
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="auto">Auto</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={() => handleSave('General')}
              disabled={saveStatus?.section === 'General' && saveStatus?.status === 'saving'}
            >
              Save General Settings
            </Button>
          </Box>
        </TabPanel>

        {/* Notification Settings */}
        <TabPanel value={activeTab} index={1}>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Notification Settings
          </Typography>
          
          {/* Email Settings */}
          <Card sx={{ mb: 3, backgroundColor: 'background.default' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Email Notifications
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.emailEnabled}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      emailEnabled: e.target.checked
                    })}
                  />
                }
                label="Enable email notifications"
                sx={{ mb: 2 }}
              />
              {notificationSettings.emailEnabled && (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="SMTP Host"
                      value={notificationSettings.emailHost}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        emailHost: e.target.value
                      })}
                      fullWidth
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="SMTP Port"
                      type="number"
                      value={notificationSettings.emailPort}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        emailPort: parseInt(e.target.value)
                      })}
                      fullWidth
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Email Username"
                      value={notificationSettings.emailUser}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        emailUser: e.target.value
                      })}
                      fullWidth
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Email Password"
                      type={showPassword.email ? 'text' : 'password'}
                      value={notificationSettings.emailPassword}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        emailPassword: e.target.value
                      })}
                      fullWidth
                      InputProps={{
                        endAdornment: (
                          <IconButton onClick={() => togglePasswordVisibility('email')}>
                            {showPassword.email ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        ),
                      }}
                    />
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>

          {/* Webhook Settings */}
          <Card sx={{ mb: 3, backgroundColor: 'background.default' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Webhook Notifications
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.webhookEnabled}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      webhookEnabled: e.target.checked
                    })}
                  />
                }
                label="Enable webhook notifications"
                sx={{ mb: 2 }}
              />
              {notificationSettings.webhookEnabled && (
                <TextField
                  label="Webhook URL"
                  value={notificationSettings.webhookUrl}
                  onChange={(e) => setNotificationSettings({
                    ...notificationSettings,
                    webhookUrl: e.target.value
                  })}
                  fullWidth
                />
              )}
            </CardContent>
          </Card>

          {/* Alert Level Settings */}
          <Card sx={{ mb: 3, backgroundColor: 'background.default' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Alert Levels
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.criticalAlerts}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      criticalAlerts: e.target.checked
                    })}
                  />
                }
                label="Critical alerts"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.warningAlerts}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      warningAlerts: e.target.checked
                    })}
                  />
                }
                label="Warning alerts"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.infoAlerts}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      infoAlerts: e.target.checked
                    })}
                  />
                }
                label="Info alerts"
              />
            </CardContent>
          </Card>

          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={() => handleSave('Notification')}
            disabled={saveStatus?.section === 'Notification' && saveStatus?.status === 'saving'}
          >
            Save Notification Settings
          </Button>
        </TabPanel>

        {/* Security Settings */}
        <TabPanel value={activeTab} index={2}>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Security Settings
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Session Timeout (minutes)"
                type="number"
                value={securitySettings.sessionTimeout}
                onChange={(e) => setSecuritySettings({
                  ...securitySettings,
                  sessionTimeout: parseInt(e.target.value)
                })}
                fullWidth
                margin="normal"
              />
              <TextField
                label="Allowed IP Addresses"
                value={securitySettings.allowedIPs}
                onChange={(e) => setSecuritySettings({
                  ...securitySettings,
                  allowedIPs: e.target.value
                })}
                fullWidth
                margin="normal"
                helperText="Use CIDR notation (e.g., 192.168.1.0/24)"
              />
              <TextField
                label="API Rate Limit (requests/hour)"
                type="number"
                value={securitySettings.apiRateLimit}
                onChange={(e) => setSecuritySettings({
                  ...securitySettings,
                  apiRateLimit: parseInt(e.target.value)
                })}
                fullWidth
                margin="normal"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Security Options
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={securitySettings.requireMFA}
                      onChange={(e) => setSecuritySettings({
                        ...securitySettings,
                        requireMFA: e.target.checked
                      })}
                    />
                  }
                  label="Require Multi-Factor Authentication"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={securitySettings.auditLogging}
                      onChange={(e) => setSecuritySettings({
                        ...securitySettings,
                        auditLogging: e.target.checked
                      })}
                    />
                  }
                  label="Enable audit logging"
                />
                <TextField
                  label="Log Retention (days)"
                  type="number"
                  value={securitySettings.logRetention}
                  onChange={(e) => setSecuritySettings({
                    ...securitySettings,
                    logRetention: parseInt(e.target.value)
                  })}
                  fullWidth
                  margin="normal"
                />
              </Box>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={() => handleSave('Security')}
              disabled={saveStatus?.section === 'Security' && saveStatus?.status === 'saving'}
            >
              Save Security Settings
            </Button>
          </Box>
        </TabPanel>

        {/* API Keys */}
        <TabPanel value={activeTab} index={3}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" fontWeight="bold">
              API Keys
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setApiKeyDialog(true)}
            >
              Create API Key
            </Button>
          </Box>

          <List>
            {apiKeys.map((apiKey) => (
              <Card key={apiKey.id} sx={{ mb: 2, backgroundColor: 'background.default' }}>
                <CardContent>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={8}>
                      <Typography fontWeight="bold" gutterBottom>
                        {apiKey.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {apiKey.description}
                      </Typography>
                      <Typography variant="caption" sx={{ fontFamily: 'monospace', backgroundColor: 'background.paper', p: 1, borderRadius: 1 }}>
                        {apiKey.key}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {apiKey.permissions.map((permission) => (
                          <Chip
                            key={permission}
                            label={permission}
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        ))}
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Created: {apiKey.created.toLocaleDateString()}
                      </Typography>
                      <br />
                      <Typography variant="caption" color="text.secondary">
                        Last Used: {apiKey.lastUsed ? apiKey.lastUsed.toLocaleDateString() : 'Never'}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Tooltip title="Edit">
                          <IconButton size="small">
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton size="small" onClick={() => handleDeleteApiKey(apiKey.id)}>
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            ))}
          </List>
        </TabPanel>
      </Paper>

      {/* Create API Key Dialog */}
      <Dialog open={apiKeyDialog} onClose={() => setApiKeyDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New API Key</DialogTitle>
        <DialogContent>
          <TextField
            label="Key Name"
            value={newApiKey.name}
            onChange={(e) => setNewApiKey({ ...newApiKey, name: e.target.value })}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Description"
            value={newApiKey.description}
            onChange={(e) => setNewApiKey({ ...newApiKey, description: e.target.value })}
            fullWidth
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApiKeyDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddApiKey}>
            Create Key
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Settings;