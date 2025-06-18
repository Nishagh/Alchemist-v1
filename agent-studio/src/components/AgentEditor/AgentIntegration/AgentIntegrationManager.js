/**
 * Agent Integration Manager
 * 
 * Main component for managing various agent integrations (WhatsApp, Website, etc.)
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  WhatsApp as WhatsAppIcon,
  Language as WebsiteIcon,
  Hub as IntegrationIcon,
  Add as AddIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon,
  Launch as LaunchIcon,
  Settings as SettingsIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';

import WhatsAppIntegrationManager from '../WhatsAppIntegration/WhatsAppIntegrationManager';
import WebsiteIntegrationManager from './WebsiteIntegrationManager';

const AgentIntegrationManager = ({
  deployments = [],
  onNotification,
  disabled = false,
  activeSection = 'integration'
}) => {
  const [selectedIntegration, setSelectedIntegration] = useState(null);

  // Set selected integration based on activeSection
  useEffect(() => {
    if (activeSection === 'whatsapp' || activeSection === 'website') {
      setSelectedIntegration(activeSection);
    } else {
      setSelectedIntegration(null);
    }
  }, [activeSection]);

  // Check if there are completed deployments
  const hasCompletedDeployments = deployments.some(d => d.status === 'completed');

  const integrationOptions = [
    {
      id: 'whatsapp',
      title: 'WhatsApp Integration',
      description: 'Connect your AI agent to WhatsApp Business API for messaging',
      icon: WhatsAppIcon,
      color: '#25D366',
      features: [
        'Direct WhatsApp Business API integration',
        'Auto phone number verification',
        'Real-time message handling',
        'Media message support',
        'Business profile setup'
      ],
      status: 'available'
    },
    {
      id: 'website',
      title: 'Website Integration',
      description: 'Embed your AI agent as a chat widget on your website',
      icon: WebsiteIcon,
      color: '#1976d2',
      features: [
        'Customizable chat widget',
        'Multiple website embedding',
        'Responsive design',
        'Custom branding',
        'Analytics integration'
      ],
      status: 'available'
    }
  ];

  const handleSelectIntegration = (integrationId) => {
    setSelectedIntegration(integrationId);
  };

  const handleBackToOverview = () => {
    setSelectedIntegration(null);
  };

  const renderIntegrationOverview = () => (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <IntegrationIcon sx={{ color: 'primary.main', fontSize: 32 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Agent Integration
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Connect your deployed agent to various platforms and services
            </Typography>
          </Box>
        </Box>

        {!hasCompletedDeployments && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Deployment Required:</strong> You need to deploy your agent before setting up integrations.
              Please complete the deployment process first.
            </Typography>
          </Alert>
        )}
      </Box>

      {/* Integration Options */}
      <Grid container spacing={3}>
        {integrationOptions.map((integration) => {
          const Icon = integration.icon;
          
          return (
            <Grid item xs={12} md={6} key={integration.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  cursor: hasCompletedDeployments ? 'pointer' : 'default',
                  opacity: hasCompletedDeployments ? 1 : 0.6,
                  transition: 'all 0.3s ease',
                  '&:hover': hasCompletedDeployments ? {
                    transform: 'translateY(-4px)',
                    boxShadow: (theme) => theme.shadows[8]
                  } : {},
                  border: (theme) => `2px solid transparent`,
                  '&:hover': hasCompletedDeployments ? {
                    borderColor: integration.color
                  } : {}
                }}
                onClick={() => hasCompletedDeployments && handleSelectIntegration(integration.id)}
              >
                <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  {/* Header */}
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: `${integration.color}15`,
                        color: integration.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <Icon sx={{ fontSize: 28 }} />
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" fontWeight="bold" gutterBottom>
                        {integration.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {integration.description}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Features */}
                  <Box sx={{ flex: 1, mb: 3 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      Key Features:
                    </Typography>
                    <List dense>
                      {integration.features.map((feature, index) => (
                        <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 20 }}>
                            <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
                          </ListItemIcon>
                          <ListItemText 
                            primary={feature}
                            primaryTypographyProps={{ fontSize: '0.875rem' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>

                  {/* Action Button */}
                  <Button
                    variant="contained"
                    fullWidth
                    disabled={!hasCompletedDeployments || disabled}
                    startIcon={<AddIcon />}
                    sx={{
                      bgcolor: integration.color,
                      '&:hover': {
                        bgcolor: integration.color,
                        filter: 'brightness(0.9)'
                      }
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectIntegration(integration.id);
                    }}
                  >
                    Setup {integration.title.split(' ')[0]}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Coming Soon Section */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Coming Soon
        </Typography>
        <Grid container spacing={2}>
          {[
            { name: 'Slack Integration', icon: '💬', color: '#4A154B' },
            { name: 'Discord Integration', icon: '🎮', color: '#5865F2' },
            { name: 'Telegram Integration', icon: '✈️', color: '#0088CC' },
            { name: 'Microsoft Teams', icon: '👥', color: '#6264A7' }
          ].map((item, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card sx={{ opacity: 0.6 }}>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" sx={{ mb: 1 }}>
                    {item.icon}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {item.name}
                  </Typography>
                  <Chip label="Coming Soon" size="small" sx={{ mt: 1 }} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );

  const renderSelectedIntegration = () => {
    switch (selectedIntegration) {
      case 'whatsapp':
        return (
          <WhatsAppIntegrationManager
            deployments={deployments}
            onNotification={onNotification}
            disabled={disabled}
            onBack={handleBackToOverview}
          />
        );
      case 'website':
        return (
          <WebsiteIntegrationManager
            deployments={deployments}
            onNotification={onNotification}
            disabled={disabled}
            onBack={handleBackToOverview}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {selectedIntegration ? renderSelectedIntegration() : renderIntegrationOverview()}
    </Box>
  );
};

export default AgentIntegrationManager;