/**
 * Website Integration Manager
 * 
 * Component for managing website chat widget integration
 */
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Chip,
  Grid,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tab,
  Tabs
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Language as WebsiteIcon,
  Code as CodeIcon,
  Palette as PaletteIcon,
  Settings as SettingsIcon,
  Preview as PreviewIcon,
  CheckCircle as CheckCircleIcon,
  ContentCopy as ContentCopyIcon,
  Launch as LaunchIcon
} from '@mui/icons-material';

const WebsiteIntegrationManager = ({
  agentId,
  deployments = [],
  onNotification,
  disabled = false,
  onBack
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [config, setConfig] = useState({
    widgetEnabled: true,
    widgetPosition: 'bottom-right',
    primaryColor: '#1976d2',
    welcomeMessage: 'Hi! How can I help you today?',
    placeholder: 'Type your message...',
    agentName: 'AI Assistant',
    showAgentAvatar: true,
    allowFileUpload: true,
    showTypingIndicator: true
  });

  // Get the latest deployment
  const latestDeployment = deployments
    .filter(d => d.status === 'completed' || d.status === 'deployed')
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];

  const handleConfigChange = (field) => (event) => {
    setConfig(prev => ({
      ...prev,
      [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value
    }));
  };

  const generateEmbedCode = () => {
    if (!latestDeployment) return '';
    
    return `<!-- Alchemist AI Agent Widget -->
<script>
  window.AlchemistConfig = {
    agentId: "${latestDeployment.deployment_id}",
    apiUrl: "${latestDeployment.service_url}",
    position: "${config.widgetPosition}",
    primaryColor: "${config.primaryColor}",
    welcomeMessage: "${config.welcomeMessage}",
    placeholder: "${config.placeholder}",
    agentName: "${config.agentName}",
    showAgentAvatar: ${config.showAgentAvatar},
    allowFileUpload: ${config.allowFileUpload},
    showTypingIndicator: ${config.showTypingIndicator}
  };
</script>
<script src="https://cdn.alchemist.ai/widget/v1/widget.js" defer></script>`;
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generateEmbedCode());
    onNotification?.({
      id: Date.now(),
      type: 'success',
      message: 'Embed code copied to clipboard!'
    });
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`website-tabpanel-${index}`}
      aria-labelledby={`website-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={onBack} disabled={disabled}>
          <ArrowBackIcon />
        </IconButton>
        <WebsiteIcon sx={{ color: 'primary.main', fontSize: 32 }} />
        <Box>
          <Typography variant="h5" fontWeight="bold">
            Website Integration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Embed your AI agent as a chat widget on your website
          </Typography>
        </Box>
      </Box>

      {!latestDeployment && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>No Active Deployment:</strong> You need a completed deployment to set up website integration.
          </Typography>
        </Alert>
      )}

      {latestDeployment && (
        <Box>
          {/* Status Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={8}>
                  <Typography variant="h6" gutterBottom>
                    Integration Status
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircleIcon color="success" />
                    <Typography variant="body2">
                      Ready to integrate with <strong>{latestDeployment.agent_name}</strong>
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    Deployment ID: {latestDeployment.deployment_id}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
                  <Chip 
                    label="Active Deployment" 
                    color="success" 
                    icon={<CheckCircleIcon />}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Configuration Tabs */}
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
                <Tab icon={<SettingsIcon />} label="Configuration" />
                <Tab icon={<PaletteIcon />} label="Appearance" />
                <Tab icon={<CodeIcon />} label="Embed Code" />
                <Tab icon={<PreviewIcon />} label="Preview" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              {/* Configuration Tab */}
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Widget Settings
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Agent Name"
                    value={config.agentName}
                    onChange={handleConfigChange('agentName')}
                    helperText="Name displayed in the chat widget"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    select
                    label="Widget Position"
                    value={config.widgetPosition}
                    onChange={handleConfigChange('widgetPosition')}
                    SelectProps={{ native: true }}
                  >
                    <option value="bottom-right">Bottom Right</option>
                    <option value="bottom-left">Bottom Left</option>
                    <option value="top-right">Top Right</option>
                    <option value="top-left">Top Left</option>
                  </TextField>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Welcome Message"
                    value={config.welcomeMessage}
                    onChange={handleConfigChange('welcomeMessage')}
                    multiline
                    rows={2}
                    helperText="First message shown to users"
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Message Placeholder"
                    value={config.placeholder}
                    onChange={handleConfigChange('placeholder')}
                    helperText="Placeholder text in the message input"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Widget Features
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.showAgentAvatar}
                          onChange={handleConfigChange('showAgentAvatar')}
                        />
                      }
                      label="Show agent avatar"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.allowFileUpload}
                          onChange={handleConfigChange('allowFileUpload')}
                        />
                      }
                      label="Allow file uploads"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.showTypingIndicator}
                          onChange={handleConfigChange('showTypingIndicator')}
                        />
                      }
                      label="Show typing indicator"
                    />
                  </Box>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              {/* Appearance Tab */}
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Visual Customization
                  </Typography>
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="color"
                    label="Primary Color"
                    value={config.primaryColor}
                    onChange={handleConfigChange('primaryColor')}
                    helperText="Main color for the chat widget"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Alert severity="info">
                    <Typography variant="body2">
                      <strong>Pro Tip:</strong> The widget will automatically adapt to your website's theme. 
                      You can further customize the appearance with CSS if needed.
                    </Typography>
                  </Alert>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              {/* Embed Code Tab */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  Embed Code
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Copy and paste this code into your website's HTML, preferably before the closing &lt;/body&gt; tag.
                </Typography>

                <Paper 
                  sx={{ 
                    p: 2, 
                    bgcolor: 'grey.100', 
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    position: 'relative',
                    mb: 2
                  }}
                >
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {generateEmbedCode()}
                  </pre>
                  <IconButton
                    size="small"
                    onClick={copyToClipboard}
                    sx={{ position: 'absolute', top: 8, right: 8 }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Paper>

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<ContentCopyIcon />}
                    onClick={copyToClipboard}
                  >
                    Copy Code
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<LaunchIcon />}
                    href="https://docs.alchemist.ai/integrations/website"
                    target="_blank"
                  >
                    View Documentation
                  </Button>
                </Box>
              </Box>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              {/* Preview Tab */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  Widget Preview
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  This is how your chat widget will appear on your website.
                </Typography>

                <Alert severity="info" sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    <strong>Live Preview:</strong> The actual widget appearance may vary slightly 
                    based on your website's CSS and the user's browser.
                  </Typography>
                </Alert>

                {/* Mock Preview */}
                <Box
                  sx={{
                    position: 'relative',
                    height: 400,
                    bgcolor: 'grey.50',
                    borderRadius: 2,
                    border: '2px dashed',
                    borderColor: 'grey.300',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Typography variant="body1" color="text.secondary">
                    🖥️ Website Preview Area
                  </Typography>
                  
                  {/* Mock Widget */}
                  <Box
                    sx={{
                      position: 'absolute',
                      [config.widgetPosition.includes('bottom') ? 'bottom' : 'top']: 16,
                      [config.widgetPosition.includes('right') ? 'right' : 'left']: 16,
                      width: 300,
                      height: 400,
                      bgcolor: 'white',
                      borderRadius: 2,
                      boxShadow: 3,
                      border: `2px solid ${config.primaryColor}`,
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                  >
                    {/* Widget Header */}
                    <Box
                      sx={{
                        bgcolor: config.primaryColor,
                        color: 'white',
                        p: 2,
                        borderRadius: '8px 8px 0 0'
                      }}
                    >
                      <Typography variant="subtitle2" fontWeight="bold">
                        {config.agentName}
                      </Typography>
                    </Box>
                    
                    {/* Widget Content */}
                    <Box sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column' }}>
                      <Box
                        sx={{
                          bgcolor: 'grey.100',
                          p: 1.5,
                          borderRadius: 2,
                          mb: 2
                        }}
                      >
                        <Typography variant="body2">
                          {config.welcomeMessage}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ flex: 1 }} />
                      
                      <TextField
                        size="small"
                        placeholder={config.placeholder}
                        disabled
                        sx={{ mt: 1 }}
                      />
                    </Box>
                  </Box>
                </Box>
              </Box>
            </TabPanel>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default WebsiteIntegrationManager;