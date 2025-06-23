import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Chip,
  CircularProgress,
  Grid,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import whatsappWebhookService from '../../../services/whatsapp/whatsappWebhookService';

const WhatsAppWebhookSetup = ({ agentId, deploymentUrl, onConfigurationChange, disabled = false }) => {
  const [config, setConfig] = useState({
    phone_id: '',
    access_token: '',
    verify_token: '',
    app_secret: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [existingConfig, setExistingConfig] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [webhookUrl, setWebhookUrl] = useState('');

  useEffect(() => {
    if (deploymentUrl) {
      const url = whatsappWebhookService.generateWebhookUrl(agentId, deploymentUrl);
      setWebhookUrl(url);
    }
    loadExistingConfig();
  }, [agentId, deploymentUrl]);

  const loadExistingConfig = async () => {
    try {
      setLoading(true);
      const existing = await whatsappWebhookService.getWebhookConfig(agentId);
      if (existing) {
        setExistingConfig(existing);
        setConfig({
          phone_id: existing.phone_id || '',
          access_token: existing.access_token || '',
          verify_token: existing.verify_token || '',
          app_secret: existing.app_secret || ''
        });
      }
    } catch (err) {
      console.error('Error loading webhook config:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      setError(null);
      
      // Validate required fields
      if (!config.phone_id || !config.access_token) {
        throw new Error('Phone ID and Access Token are required');
      }

      const configData = {
        ...config,
        webhook_url: webhookUrl,
        verify_token: config.verify_token || 'default_verify_token'
      };

      let result;
      if (existingConfig) {
        await whatsappWebhookService.updateWebhookConfig(existingConfig.id, configData);
        result = { ...existingConfig, ...configData };
      } else {
        result = await whatsappWebhookService.saveWebhookConfig(agentId, configData);
      }

      setExistingConfig(result);
      setSuccess('WhatsApp webhook configuration saved successfully!');
      
      if (onConfigurationChange) {
        onConfigurationChange(result);
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConfig = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      
      const result = await whatsappWebhookService.testWebhookConfig(agentId);
      setTestResult(result);
      
    } catch (err) {
      setTestResult({
        success: false,
        message: err.message
      });
    } finally {
      setTesting(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copied to clipboard!');
    setTimeout(() => setSuccess(null), 2000);
  };

  const setupInstructions = whatsappWebhookService.getSetupInstructions(webhookUrl);

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            WhatsApp Webhook Integration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Connect your existing WhatsApp Business number to this AI agent via webhook.
            No account creation needed - just configure your existing Business API.
          </Typography>
          
          {existingConfig && (
            <Chip 
              icon={<CheckIcon />}
              label="Webhook Configured" 
              color="success" 
              sx={{ mt: 2 }}
            />
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Setup Instructions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {setupInstructions.title}
              </Typography>
              
              <Stepper orientation="vertical">
                {setupInstructions.steps.map((step, index) => (
                  <Step key={index} active={true}>
                    <StepLabel>
                      <Typography variant="subtitle2">{step.title}</Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {step.description}
                      </Typography>
                      {step.details && (
                        <Box component="ul" sx={{ ml: 2, mt: 1 }}>
                          {step.details.map((detail, idx) => (
                            <Box component="li" key={idx} sx={{ mb: 0.5 }}>
                              <Typography variant="caption">{detail}</Typography>
                            </Box>
                          ))}
                        </Box>
                      )}
                    </StepContent>
                  </Step>
                ))}
              </Stepper>

              {/* Important Notes */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  <InfoIcon sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                  Important Notes:
                </Typography>
                {setupInstructions.notes.map((note, index) => (
                  <Typography key={index} variant="caption" display="block" sx={{ ml: 3, mb: 0.5 }}>
                    • {note}
                  </Typography>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Configuration Form */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Webhook Configuration
              </Typography>

              {/* Webhook URL */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Webhook URL
                </Typography>
                <Paper 
                  variant="outlined" 
                  sx={{ p: 2, backgroundColor: 'grey.50', display: 'flex', alignItems: 'center' }}
                >
                  <Typography 
                    variant="body2" 
                    sx={{ fontFamily: 'monospace', flex: 1, wordBreak: 'break-all' }}
                  >
                    {webhookUrl || 'Deploy agent first to get webhook URL'}
                  </Typography>
                  {webhookUrl && (
                    <Tooltip title="Copy URL">
                      <IconButton 
                        onClick={() => copyToClipboard(webhookUrl)} 
                        size="small"
                        disabled={disabled}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Paper>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Configuration Fields */}
              <Box sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  label="Phone Number ID"
                  value={config.phone_id}
                  onChange={(e) => setConfig({ ...config, phone_id: e.target.value })}
                  placeholder="Enter your WhatsApp Business Phone Number ID"
                  margin="normal"
                  required
                  disabled={disabled}
                  helperText="Found in your WhatsApp Business Platform dashboard"
                />

                <TextField
                  fullWidth
                  label="Access Token"
                  value={config.access_token}
                  onChange={(e) => setConfig({ ...config, access_token: e.target.value })}
                  placeholder="Enter your permanent access token"
                  margin="normal"
                  type="password"
                  required
                  disabled={disabled}
                  helperText="Permanent access token from your WhatsApp Business app"
                />

                <TextField
                  fullWidth
                  label="Verify Token"
                  value={config.verify_token}
                  onChange={(e) => setConfig({ ...config, verify_token: e.target.value })}
                  placeholder="Create a secure verify token"
                  margin="normal"
                  disabled={disabled}
                  helperText="Create a random string - must match what you set in WhatsApp platform"
                />

                <TextField
                  fullWidth
                  label="App Secret (Optional)"
                  value={config.app_secret}
                  onChange={(e) => setConfig({ ...config, app_secret: e.target.value })}
                  placeholder="Enter app secret for signature verification"
                  margin="normal"
                  type="password"
                  disabled={disabled}
                  helperText="Optional but recommended for production security"
                />
              </Box>

              {/* Actions */}
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleSaveConfig}
                  disabled={disabled || saving || !webhookUrl}
                  startIcon={saving ? <CircularProgress size={16} /> : null}
                >
                  {existingConfig ? 'Update' : 'Save'} Configuration
                </Button>

                {existingConfig && (
                  <Button
                    variant="outlined"
                    onClick={handleTestConfig}
                    disabled={disabled || testing}
                    startIcon={testing ? <CircularProgress size={16} /> : <RefreshIcon />}
                  >
                    Test Webhook
                  </Button>
                )}
              </Box>

              {/* Test Result */}
              {testResult && (
                <Alert 
                  severity={testResult.success ? 'success' : 'error'}
                  sx={{ mb: 2 }}
                >
                  {testResult.message}
                  {testResult.webhook_url && (
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      Webhook URL: {testResult.webhook_url}
                    </Typography>
                  )}
                </Alert>
              )}

              {/* Messages */}
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              {success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {success}
                </Alert>
              )}

              {!webhookUrl && (
                <Alert severity="warning">
                  Deploy your agent first to get the webhook URL for WhatsApp configuration.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default WhatsAppWebhookSetup;