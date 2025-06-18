/**
 * WhatsApp Integration Manager
 * 
 * Main component for managing WhatsApp Business API integration with deployed agents
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
  IconButton,
  Menu,
  MenuItem,
  CircularProgress,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tooltip
} from '@mui/material';
import {
  WhatsApp as WhatsAppIcon,
  CloudQueue as CloudQueueIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Launch as LaunchIcon,
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Phone as PhoneIcon,
  Webhook as WebhookIcon,
  Science as ScienceIcon,
  AccessTime as AccessTimeIcon
} from '@mui/icons-material';

import { useAgentState } from '../../../hooks/useAgentState';
import { createNotification } from '../../shared/NotificationSystem';
import whatsappService from '../../../services/whatsapp/whatsappBusinessService';
import SimpleWhatsAppSetup from './SimpleWhatsAppSetup';
import PhoneVerification from './PhoneVerification';

const WhatsAppIntegrationManager = ({
  deployments = [],
  onNotification,
  disabled = false
}) => {
  const { agent, agentId } = useAgentState();
  const [managedAccount, setManagedAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [verificationDialogOpen, setVerificationDialogOpen] = useState(false);
  const [selectedDeployment, setSelectedDeployment] = useState(null);
  const [pendingAccount, setPendingAccount] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);

  // Get completed deployments that can have WhatsApp integration
  const availableDeployments = deployments.filter(d => d.status === 'completed' && d.service_url);
  
  // Get the latest deployment (most recent)
  const latestDeployment = availableDeployments.length > 0 
    ? availableDeployments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
    : null;

  useEffect(() => {
    loadManagedAccount();
  }, [latestDeployment]);

  const loadManagedAccount = async () => {
    try {
      setLoading(true);
      if (latestDeployment) {
        const account = await whatsappService.getManagedAccountByDeployment(latestDeployment.deployment_id);
        setManagedAccount(account);
      } else {
        setManagedAccount(null);
      }
    } catch (error) {
      console.error('Error loading managed WhatsApp account:', error);
      setManagedAccount(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSetupWhatsApp = () => {
    setSelectedDeployment(latestDeployment);
    setSetupDialogOpen(true);
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleSetupComplete = (account) => {
    setManagedAccount(account);
    setSetupDialogOpen(false);
    onNotification?.(createNotification(
      'WhatsApp integration setup completed successfully!',
      'success'
    ));
  };

  const handleVerificationRequired = (account) => {
    setPendingAccount(account);
    setSetupDialogOpen(false);
    setVerificationDialogOpen(true);
  };

  const handleVerificationComplete = (verifiedAccount) => {
    setManagedAccount(verifiedAccount);
    setPendingAccount(null);
    setVerificationDialogOpen(false);
    onNotification?.(createNotification(
      'Phone verification completed! Your WhatsApp integration is now active.',
      'success'
    ));
  };

  const handleTestAccount = async (testPhoneNumber) => {
    if (!managedAccount) return;
    
    try {
      await whatsappService.testManagedAccount(managedAccount.id, testPhoneNumber);
      onNotification?.(createNotification(
        `Test message sent successfully to ${testPhoneNumber}`,
        'success'
      ));
    } catch (error) {
      onNotification?.(createNotification(
        `Test failed: ${error.message}`,
        'error'
      ));
    }
  };

  const handleDeleteAccount = async () => {
    if (!managedAccount) return;
    
    try {
      await whatsappService.deleteManagedAccount(managedAccount.id);
      setManagedAccount(null);
      onNotification?.(createNotification(
        'WhatsApp integration deleted successfully',
        'success'
      ));
    } catch (error) {
      onNotification?.(createNotification(
        `Failed to delete integration: ${error.message}`,
        'error'
      ));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'verification_pending': return 'warning';
      case 'verification_failed': return 'error';
      case 'initializing': return 'info';
      case 'inactive': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircleIcon />;
      case 'verification_pending': return <WarningIcon />;
      case 'verification_failed': return <ErrorIcon />;
      case 'initializing': return <CloudQueueIcon />;
      case 'inactive': return <ErrorIcon />;
      default: return <CloudQueueIcon />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active': return 'Connected';
      case 'verification_pending': return 'Verification Required';
      case 'verification_failed': return 'Verification Failed';
      case 'initializing': return 'Setting Up';
      case 'inactive': return 'Inactive';
      default: return 'Unknown';
    }
  };

  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 8 
        }}
      >
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          Loading WhatsApp integrations...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Sticky Header */}
      <Box sx={{ 
        position: 'sticky',
        top: 0,
        zIndex: 100,
        p: 3,
        borderBottom: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        backdropFilter: 'blur(8px)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <WhatsAppIcon sx={{ mr: 1, color: '#25D366' }} />
          <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
            WhatsApp Integration
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Connect your deployed agents to WhatsApp Business API to enable messaging capabilities
        </Typography>
      </Box>

      {/* Main Content */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
        {!latestDeployment ? (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>No deployments available:</strong> You need to deploy your agent first before setting up WhatsApp integration.
              Go to the "Agent Deployment" section to deploy your agent.
            </Typography>
          </Alert>
        ) : (
          <>
            {/* Latest Deployment */}
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CloudQueueIcon />
              Latest Deployment
            </Typography>

            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} md={6}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          Deployed Agent
                        </Typography>
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="DEPLOYED"
                          color="success"
                          size="small"
                          sx={{ mb: 1 }}
                        />
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Box sx={{ space: 1 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Service URL:</strong>
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2, wordBreak: 'break-all' }}>
                        {latestDeployment.service_url}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Deployed:</strong>
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {new Date(latestDeployment.created_at).toLocaleString()}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>WhatsApp Status:</strong>
                      </Typography>
                      <Chip
                        icon={managedAccount ? getStatusIcon(managedAccount.status) : <WarningIcon />}
                        label={managedAccount ? getStatusText(managedAccount.status) : "Not Connected"}
                        color={managedAccount ? getStatusColor(managedAccount.status) : "warning"}
                        size="small"
                      />
                    </Box>
                  </CardContent>

                  <Box sx={{ p: 2, pt: 0 }}>
                    {managedAccount ? (
                      managedAccount.status === 'verification_pending' ? (
                        <Button
                          variant="contained"
                          startIcon={<WarningIcon />}
                          fullWidth
                          onClick={() => {
                            setPendingAccount(managedAccount);
                            setVerificationDialogOpen(true);
                          }}
                          disabled={disabled}
                          sx={{
                            bgcolor: '#ff9800',
                            '&:hover': {
                              bgcolor: '#f57c00'
                            }
                          }}
                        >
                          Complete Verification
                        </Button>
                      ) : (
                        <Button
                          variant="outlined"
                          startIcon={<SettingsIcon />}
                          fullWidth
                          disabled={disabled}
                          onClick={handleMenuOpen}
                        >
                          Manage WhatsApp
                        </Button>
                      )
                    ) : (
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={handleSetupWhatsApp}
                        fullWidth
                        disabled={disabled}
                        sx={{
                          bgcolor: '#25D366',
                          '&:hover': {
                            bgcolor: '#1EA952'
                          }
                        }}
                      >
                        Connect WhatsApp
                      </Button>
                    )}
                  </Box>
                </Card>
              </Grid>

              {/* WhatsApp Integration Status */}
              {managedAccount && (
                <Grid item xs={12} md={6}>
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <CardContent sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <WhatsAppIcon sx={{ color: '#25D366' }} />
                          <Typography variant="h6">
                            WhatsApp Business
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            icon={getStatusIcon(managedAccount.status)}
                            label={getStatusText(managedAccount.status)}
                            color={getStatusColor(managedAccount.status)}
                            size="small"
                          />
                          <IconButton
                            size="small"
                            onClick={handleMenuOpen}
                            disabled={disabled}
                          >
                            <MoreVertIcon />
                          </IconButton>
                        </Box>
                      </Box>

                      {managedAccount.status === 'verification_pending' && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                          <Typography variant="body2">
                            Phone number verification required to complete setup
                          </Typography>
                        </Alert>
                      )}

                      {managedAccount.status === 'verification_failed' && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                          <Typography variant="body2">
                            Phone verification failed. Please try again.
                          </Typography>
                        </Alert>
                      )}

                      <Divider sx={{ my: 2 }} />

                      <List dense>
                        <ListItem disablePadding>
                          <ListItemIcon>
                            <PhoneIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Phone Number"
                            secondary={managedAccount.phone_number || 'Not configured'}
                          />
                        </ListItem>
                        <ListItem disablePadding>
                          <ListItemIcon>
                            <WebhookIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Webhook URL"
                            secondary={managedAccount.webhook_url || `${latestDeployment.service_url}/webhook/whatsapp`}
                            secondaryTypographyProps={{
                              sx: { 
                                wordBreak: 'break-all',
                                fontSize: '0.75rem'
                              }
                            }}
                          />
                        </ListItem>
                        <ListItem disablePadding>
                          <ListItemIcon>
                            <AccessTimeIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Last Updated"
                            secondary={new Date(managedAccount.updated_at).toLocaleString()}
                          />
                        </ListItem>
                        {managedAccount.verified_at && (
                          <ListItem disablePadding>
                            <ListItemIcon>
                              <CheckCircleIcon fontSize="small" color="success" />
                            </ListItemIcon>
                            <ListItemText 
                              primary="Verified"
                              secondary={new Date(managedAccount.verified_at).toLocaleString()}
                            />
                          </ListItem>
                        )}
                      </List>
                    </CardContent>

                    <Box sx={{ p: 2, pt: 0 }}>
                      <Button
                        size="small"
                        startIcon={<ScienceIcon />}
                        disabled={disabled || managedAccount.status !== 'active'}
                        sx={{ mr: 1 }}
                        onClick={() => {
                          // Could open test dialog here
                        }}
                      >
                        Test
                      </Button>
                      <Button
                        size="small"
                        startIcon={<LaunchIcon />}
                        href={latestDeployment.service_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Service
                      </Button>
                    </Box>
                  </Card>
                </Grid>
              )}
            </Grid>
          </>
        )}
      </Box>

      {/* WhatsApp Setup Dialog */}
      <Dialog
        open={setupDialogOpen}
        onClose={() => setSetupDialogOpen(false)}
        maxWidth="md"
        fullWidth
        disableEscapeKeyDown
      >
        <SimpleWhatsAppSetup
          deployment={selectedDeployment}
          onComplete={handleSetupComplete}
          onVerificationRequired={handleVerificationRequired}
          onCancel={() => setSetupDialogOpen(false)}
          onError={(error) => {
            onNotification?.(createNotification(
              error,
              'error'
            ));
          }}
        />
      </Dialog>

      {/* Phone Verification Dialog */}
      <Dialog
        open={verificationDialogOpen}
        onClose={() => setVerificationDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        disableEscapeKeyDown
      >
        <PhoneVerification
          managedAccount={pendingAccount}
          onVerificationComplete={handleVerificationComplete}
          onCancel={() => {
            setVerificationDialogOpen(false);
            setPendingAccount(null);
          }}
          onError={(error) => {
            onNotification?.(createNotification(
              error,
              'error'
            ));
          }}
        />
      </Dialog>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose} disabled>
          <SettingsIcon sx={{ mr: 1 }} />
          Settings
        </MenuItem>
        <MenuItem onClick={handleMenuClose} disabled={!managedAccount || managedAccount.status !== 'active'}>
          <ScienceIcon sx={{ mr: 1 }} />
          Test Integration
        </MenuItem>
        <MenuItem 
          onClick={() => {
            handleMenuClose();
            handleDeleteAccount();
          }} 
          sx={{ color: 'error.main' }}
          disabled={!managedAccount}
        >
          <ErrorIcon sx={{ mr: 1 }} />
          Delete Integration
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default WhatsAppIntegrationManager;