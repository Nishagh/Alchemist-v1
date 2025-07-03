/**
 * WhatsApp Status Card
 * 
 * Component for displaying WhatsApp integration status and management options
 */
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  Box,
  Button,
  IconButton,
  Menu,
  MenuItem,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  WhatsApp as WhatsAppIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  CloudQueue as CloudQueueIcon,
  Phone as PhoneIcon,
  Webhook as WebhookIcon,
  Settings as SettingsIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Science as ScienceIcon,
  Launch as LaunchIcon,
  AccessTime as AccessTimeIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

import { 
  testWhatsAppIntegration, 
  deleteWhatsAppIntegration, 
  getWhatsAppStatus 
} from '../../../services/whatsapp/whatsappService';

const WhatsAppStatusCard = ({
  integration,
  deployment,
  onUpdate,
  onDelete,
  onError,
  disabled = false
}) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testPhoneNumber, setTestPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'success';
      case 'disconnected': return 'error';
      case 'setup_required': return 'warning';
      case 'pending': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected': return <CheckCircleIcon />;
      case 'disconnected': return <ErrorIcon />;
      case 'setup_required': return <WarningIcon />;
      case 'pending': return <CloudQueueIcon />;
      default: return <CloudQueueIcon />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'setup_required': return 'Setup Required';
      case 'pending': return 'Pending';
      default: return 'Unknown';
    }
  };

  const handleRefreshStatus = async () => {
    setStatusLoading(true);
    try {
      const status = await getWhatsAppStatus(integration.id);
      onUpdate(status);
    } catch (error) {
      console.error('Error refreshing status:', error);
      onError('Failed to refresh WhatsApp status');
    } finally {
      setStatusLoading(false);
    }
  };

  const handleTestIntegration = async () => {
    if (!testPhoneNumber.trim()) {
      onError('Please enter a phone number for testing');
      return;
    }

    if (!/^\+\d{10,15}$/.test(testPhoneNumber)) {
      onError('Please enter a valid phone number with country code (e.g., +1234567890)');
      return;
    }

    setLoading(true);
    try {
      await testWhatsAppIntegration(integration.id, testPhoneNumber);
      setTestDialogOpen(false);
      setTestPhoneNumber('');
      onUpdate({ ...integration, last_test: new Date().toISOString() });
      // Note: Success message should be handled by parent component
    } catch (error) {
      console.error('Error testing integration:', error);
      onError(`Test failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteIntegration = async () => {
    setLoading(true);
    try {
      await deleteWhatsAppIntegration(integration.id);
      setDeleteDialogOpen(false);
      onDelete(integration.id);
    } catch (error) {
      console.error('Error deleting integration:', error);
      onError(`Failed to delete integration: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    try {
      return format(new Date(timestamp), 'MMM dd, yyyy HH:mm');
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <>
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
                icon={getStatusIcon(integration.status)}
                label={getStatusText(integration.status)}
                color={getStatusColor(integration.status)}
                size="small"
              />
              <Tooltip title="Refresh status">
                <IconButton
                  size="small"
                  onClick={handleRefreshStatus}
                  disabled={disabled || statusLoading}
                >
                  {statusLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
                </IconButton>
              </Tooltip>
              <IconButton
                size="small"
                onClick={handleMenuOpen}
                disabled={disabled}
              >
                <MoreVertIcon />
              </IconButton>
            </Box>
          </Box>

          {integration.status === 'setup_required' && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Webhook configuration required in WhatsApp Business API dashboard
              </Typography>
            </Alert>
          )}

          <Divider sx={{ mb: 2 }} />

          <List dense>
            <ListItem disablePadding>
              <ListItemIcon>
                <PhoneIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="Phone Number"
                secondary={integration.phone_number || 'Not configured'}
              />
            </ListItem>

            <ListItem disablePadding>
              <ListItemIcon>
                <WebhookIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="Webhook URL"
                secondary={integration.webhook_url || 'Not configured'}
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
                secondary={formatTimestamp(integration.updated_at)}
              />
            </ListItem>

            {integration.last_test && (
              <ListItem disablePadding>
                <ListItemIcon>
                  <ScienceIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="Last Test"
                  secondary={formatTimestamp(integration.last_test)}
                />
              </ListItem>
            )}
          </List>
        </CardContent>

        <CardActions sx={{ pt: 0 }}>
          <Button
            size="small"
            startIcon={<ScienceIcon />}
            onClick={() => setTestDialogOpen(true)}
            disabled={disabled || integration.status !== 'connected'}
          >
            Test
          </Button>
          <Button
            size="small"
            startIcon={<SettingsIcon />}
            disabled={disabled}
          >
            Settings
          </Button>
          {deployment?.service_url && (
            <Button
              size="small"
              startIcon={<LaunchIcon />}
              href={deployment.service_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Service
            </Button>
          )}
        </CardActions>
      </Card>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => { handleMenuClose(); setTestDialogOpen(true); }} disabled={integration.status !== 'connected'}>
          <ScienceIcon sx={{ mr: 1 }} />
          Test Integration
        </MenuItem>
        <MenuItem onClick={handleMenuClose} disabled>
          <SettingsIcon sx={{ mr: 1 }} />
          Configuration
        </MenuItem>
        <Divider />
        <MenuItem 
          onClick={() => { handleMenuClose(); setDeleteDialogOpen(true); }}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} />
          Delete Integration
        </MenuItem>
      </Menu>

      {/* Test Integration Dialog */}
      <Dialog
        open={testDialogOpen}
        onClose={() => setTestDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Test WhatsApp Integration
        </DialogTitle>
        
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Send a test message to verify your WhatsApp integration is working correctly.
          </Typography>

          <TextField
            autoFocus
            fullWidth
            label="Test Phone Number"
            value={testPhoneNumber}
            onChange={(e) => setTestPhoneNumber(e.target.value)}
            placeholder="+1234567890"
            helperText="Include country code (e.g., +1234567890)"
            disabled={loading}
          />

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              A test message will be sent to this number: "Hello! This is a test message from your AI agent."
            </Typography>
          </Alert>
        </DialogContent>
        
        <DialogActions>
          <Button 
            onClick={() => setTestDialogOpen(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleTestIntegration}
            variant="contained"
            disabled={loading || !testPhoneNumber.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <ScienceIcon />}
            sx={{
              bgcolor: '#25D366',
              '&:hover': {
                bgcolor: '#1EA952'
              }
            }}
          >
            {loading ? 'Sending...' : 'Send Test Message'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Delete WhatsApp Integration
        </DialogTitle>
        
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Warning:</strong> This action cannot be undone.
            </Typography>
          </Alert>

          <Typography variant="body2">
            Are you sure you want to delete this WhatsApp integration? This will:
          </Typography>
          
          <List dense sx={{ mt: 1 }}>
            <ListItem>
              <ListItemText primary="• Remove webhook configuration" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• Stop processing WhatsApp messages" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• Delete all integration settings" />
            </ListItem>
          </List>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Phone number: <strong>{integration.phone_number}</strong>
          </Typography>
        </DialogContent>
        
        <DialogActions>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteIntegration}
            variant="contained"
            color="error"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {loading ? 'Deleting...' : 'Delete Integration'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default WhatsAppStatusCard;