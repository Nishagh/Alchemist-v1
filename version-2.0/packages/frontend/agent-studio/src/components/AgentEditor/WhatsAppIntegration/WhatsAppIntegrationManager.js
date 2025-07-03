/**
 * WhatsApp Webhook Integration Manager
 * 
 * Simplified component for WhatsApp webhook integration with existing Business API users
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Grid,
  Chip,
  CircularProgress,
  Paper,
  IconButton
} from '@mui/material';
import {
  WhatsApp as WhatsAppIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Webhook as WebhookIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';

import WhatsAppWebhookSetup from './WhatsAppWebhookSetup';
import whatsappWebhookService from '../../../services/whatsapp/whatsappWebhookService';

const WhatsAppIntegrationManager = ({ 
  agentId,
  deployments = [], 
  onNotification, 
  disabled = false, 
  onBack 
}) => {
  const [loading, setLoading] = useState(true);
  const [webhookConfig, setWebhookConfig] = useState(null);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Get the latest completed deployment
  const completedDeployment = deployments.find(d => d.status === 'completed' || d.status === 'deployed');
  const isDeployed = completedDeployment?.service_url;

  useEffect(() => {
    if (agentId) {
      loadWebhookConfig();
    }
  }, [agentId]);

  const loadWebhookConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const config = await whatsappWebhookService.getWebhookConfig(agentId);
      setWebhookConfig(config);
      
    } catch (err) {
      console.error('Error loading WhatsApp webhook config:', err);
      setError('Failed to load WhatsApp configuration');
      if (onNotification) {
        onNotification({
          message: 'Failed to load WhatsApp configuration',
          severity: 'error',
          timestamp: Date.now()
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfigurationChange = (newConfig) => {
    setWebhookConfig(newConfig);
  };

  const handleDeleteConfig = async () => {
    if (!webhookConfig || !window.confirm('Are you sure you want to delete the WhatsApp webhook configuration?')) {
      return;
    }

    try {
      setDeleting(true);
      await whatsappWebhookService.deleteWebhookConfig(webhookConfig.id);
      setWebhookConfig(null);
      if (onNotification) {
        onNotification({
          message: 'WhatsApp configuration removed successfully',
          severity: 'success',
          timestamp: Date.now()
        });
      }
    } catch (err) {
      setError('Failed to delete WhatsApp configuration');
      if (onNotification) {
        onNotification({
          message: 'Failed to delete WhatsApp configuration',
          severity: 'error',
          timestamp: Date.now()
        });
      }
    } finally {
      setDeleting(false);
    }
  };

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
          <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
            <Box display="flex" alignItems="center">
              {onBack && (
                <IconButton onClick={onBack} sx={{ mr: 1 }}>
                  <ArrowBackIcon />
                </IconButton>
              )}
              <WhatsAppIcon sx={{ fontSize: 40, color: '#25D366', mr: 2 }} />
              <Box>
                <Typography variant="h5" fontWeight="bold">
                  WhatsApp Integration
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Connect your existing WhatsApp Business number via webhook
                </Typography>
              </Box>
            </Box>
            
            {webhookConfig && (
              <Button
                variant="outlined"
                color="error"
                startIcon={deleting ? <CircularProgress size={16} /> : <DeleteIcon />}
                onClick={handleDeleteConfig}
                disabled={deleting}
                size="small"
              >
                Remove Integration
              </Button>
            )}
          </Box>

          {/* Status */}
          {webhookConfig ? (
            <Box display="flex" gap={1}>
              <Chip 
                icon={<CheckIcon />}
                label="Webhook Configured" 
                color="success" 
                size="small"
              />
              <Chip 
                icon={<WebhookIcon />}
                label={`Phone: ${webhookConfig.phone_id}`} 
                variant="outlined" 
                size="small"
              />
            </Box>
          ) : (
            <Chip 
              icon={<WebhookIcon />}
              label="Not Configured" 
              color="default" 
              size="small"
            />
          )}
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Deployment Check */}
      {!isDeployed && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Agent Deployment Required:</strong> Deploy your agent first to get the webhook URL for WhatsApp configuration.
          </Typography>
        </Alert>
      )}

      {/* Existing Config Display */}
      {webhookConfig && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Configuration
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">
                  Phone Number ID
                </Typography>
                <Typography variant="body2" fontFamily="monospace">
                  {webhookConfig.phone_id}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">
                  Webhook URL
                </Typography>
                <Typography variant="body2" fontFamily="monospace" sx={{ wordBreak: 'break-all' }}>
                  {webhookConfig.webhook_url}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">
                  Verify Token
                </Typography>
                <Typography variant="body2" fontFamily="monospace">
                  {webhookConfig.verify_token || 'default_verify_token'}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">
                  Security
                </Typography>
                <Typography variant="body2">
                  {webhookConfig.app_secret ? 'Signature verification enabled' : 'Basic security (no app secret)'}
                </Typography>
              </Grid>
            </Grid>

            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>
              Last updated: {new Date(webhookConfig.updated_at).toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Setup Component */}
      <WhatsAppWebhookSetup
        agentId={agentId}
        deploymentUrl={completedDeployment?.service_url}
        onConfigurationChange={handleConfigurationChange}
        disabled={disabled}
      />
    </Box>
  );
};

export default WhatsAppIntegrationManager;