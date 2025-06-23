import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  IconButton,
  Tooltip,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  useTheme,
  alpha,
  Avatar,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  CreditCard as CreditCardIcon,
  Receipt as ReceiptIcon,
  TrendingUp as TrendingUpIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  AttachMoney as AttachMoneyIcon,
  AccountBalance as AccountBalanceIcon,
  Security as SecurityIcon,
  AutorenewIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useAuth } from '../utils/AuthContext';
import { billingService } from '../services';

const Billing = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [billingData, setBillingData] = useState({
    currentUsage: {
      characters_used: 0,
      characters_limit: 1000000,
      cost: 0,
      cost_limit: 1000,
      usage_percentage: 0,
      cost_percentage: 0
    },
    subscription: {
      plan: 'Production',
      status: 'active',
      next_billing: null,
      rate_per_1k_characters: 1.0
    },
    paymentMethods: [],
    invoices: []
  });
  
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState(''); // 'payment', 'plan', 'limit'
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [autoRecharge, setAutoRecharge] = useState(false);
  const [spendingLimit, setSpendingLimit] = useState(100);

  useEffect(() => {
    const loadBillingData = async () => {
      if (!currentUser) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError('');

        // Load all billing data in parallel
        const [usageResult, paymentMethodsResult, invoicesResult, settingsResult] = await Promise.allSettled([
          billingService.getCurrentUsage(),
          billingService.getPaymentMethods(),
          billingService.getInvoices(),
          billingService.getBillingSettings()
        ]);

        // Handle usage data
        if (usageResult.status === 'fulfilled' && usageResult.value.success) {
          const usageData = usageResult.value.data;
          setBillingData(prev => ({
            ...prev,
            currentUsage: {
              characters_used: usageData.current_usage?.characters_used || 0,
              characters_limit: usageData.current_usage?.characters_limit || 1000000,
              cost: usageData.current_usage?.cost || 0,
              cost_limit: usageData.current_usage?.cost_limit || 1000,
              usage_percentage: usageData.current_usage?.usage_percentage || 0,
              cost_percentage: usageData.current_usage?.cost_percentage || 0
            },
            subscription: {
              plan: usageData.subscription?.plan || 'Production',
              status: usageData.subscription?.status || 'active',
              next_billing: usageData.subscription?.next_billing || null,
              rate_per_1k_characters: usageData.subscription?.rate_per_1k_characters || 1.0
            }
          }));
        }

        // Handle payment methods
        if (paymentMethodsResult.status === 'fulfilled' && paymentMethodsResult.value.success) {
          setBillingData(prev => ({
            ...prev,
            paymentMethods: paymentMethodsResult.value.data || []
          }));
        }

        // Handle invoices
        if (invoicesResult.status === 'fulfilled' && invoicesResult.value.success) {
          setBillingData(prev => ({
            ...prev,
            invoices: invoicesResult.value.data || []
          }));
        }

        // Handle settings
        if (settingsResult.status === 'fulfilled' && settingsResult.value.success) {
          const settings = settingsResult.value.data;
          setEmailNotifications(settings.notifications?.email_notifications ?? true);
          setAutoRecharge(settings.preferences?.auto_recharge ?? false);
          setSpendingLimit(settings.limits?.monthly_spending_limit ?? 1000);
        }

      } catch (error) {
        console.error('Error loading billing data:', error);
        setError('Failed to load billing data. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    loadBillingData();
  }, [currentUser]);

  const getCurrentUsagePercentage = () => {
    return billingData.currentUsage.usage_percentage || 0;
  };

  const getCurrentCostPercentage = () => {
    return billingData.currentUsage.cost_percentage || 0;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'paid': return 'success';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const handleOpenDialog = (type) => {
    setDialogType(type);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setDialogType('');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  const formatNumber = (number) => {
    return new Intl.NumberFormat().format(number);
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <LinearProgress sx={{ width: '200px' }} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Billing & Usage
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Manage your subscription, usage, and payment methods
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          onClose={() => setError('')}
        >
          {error}
        </Alert>
      )}

      {/* Current Usage Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ 
                  bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                  color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
                  mr: 2 
                }}>
                  <TrendingUpIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    Current Usage
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This billing cycle
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">
                    Characters Used
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {formatNumber(billingData.currentUsage.characters_used)} / {formatNumber(billingData.currentUsage.characters_limit)}
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={getCurrentUsagePercentage()}
                  sx={{ 
                    height: 8, 
                    borderRadius: 4,
                    backgroundColor: theme.palette.mode === 'dark' ? '#333333' : '#f0f0f0',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getCurrentUsagePercentage() > 80 ? theme.palette.error.main : 
                                     getCurrentUsagePercentage() > 60 ? theme.palette.warning.main :
                                     theme.palette.mode === 'dark' ? '#ffffff' : '#000000'
                    }
                  }}
                />
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" fontWeight="bold">
                  {formatCurrency(billingData.currentUsage.cost)}
                </Typography>
                <Chip 
                  label={`${getCurrentUsagePercentage().toFixed(1)}% used`}
                  size="small"
                  sx={{
                    bgcolor: theme.palette.mode === 'dark' ? '#333333' : '#f0f0f0',
                    color: theme.palette.text.primary
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ 
                  bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                  color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
                  mr: 2 
                }}>
                  <CreditCardIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    Current Plan
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {billingData.subscription.plan}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Next billing date
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {billingData.subscription.next_billing ? 
                    new Date(billingData.subscription.next_billing).toLocaleDateString() : 
                    'Not scheduled'
                  }
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Rate per 1K characters
                  </Typography>
                  <Typography variant="h6" fontWeight="bold">
                    ₹{billingData.subscription.rate_per_1k_characters.toFixed(2)}
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleOpenDialog('plan')}
                  sx={{
                    borderColor: theme.palette.text.primary,
                    color: theme.palette.text.primary,
                    '&:hover': {
                      borderColor: theme.palette.text.primary,
                      backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                    }
                  }}
                >
                  Change Plan
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Spending Limit Alert */}
      {getCurrentCostPercentage() > 80 && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => handleOpenDialog('limit')}
            >
              Adjust Limit
            </Button>
          }
        >
          You've used {getCurrentCostPercentage().toFixed(1)}% of your monthly spending limit.
        </Alert>
      )}

      {/* Settings & Payment Methods */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Payment Methods
              </Typography>
              
              {billingData.paymentMethods.length > 0 ? (
                <List>
                  {billingData.paymentMethods.map((method) => (
                    <ListItem key={method.id} sx={{ px: 0 }}>
                      <ListItemIcon>
                        <CreditCardIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body1">
                              **** **** **** {method.last4}
                            </Typography>
                            {method.isDefault && (
                              <Chip 
                                label="Default" 
                                size="small" 
                                sx={{
                                  bgcolor: theme.palette.mode === 'dark' ? '#333333' : '#f0f0f0',
                                  color: theme.palette.text.primary
                                }}
                              />
                            )}
                          </Box>
                        }
                        secondary={method.expiryMonth && method.expiryYear ? 
                          `Expires ${method.expiryMonth}/${method.expiryYear}` : 
                          `${method.type} ending in ${method.last4}`
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton edge="end">
                          <EditIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    No payment methods added yet
                  </Typography>
                </Box>
              )}
              
              <Button
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog('payment')}
                sx={{ mt: 2 }}
              >
                Add Payment Method
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Settings
              </Typography>
              
              <List>
                <ListItem sx={{ px: 0 }}>
                  <ListItemText
                    primary="Email Notifications"
                    secondary="Get notified about billing updates"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={emailNotifications}
                      onChange={(e) => setEmailNotifications(e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                
                <ListItem sx={{ px: 0 }}>
                  <ListItemText
                    primary="Auto Recharge"
                    secondary="Automatically add credits when low"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={autoRecharge}
                      onChange={(e) => setAutoRecharge(e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
              
              <Button
                variant="outlined"
                fullWidth
                startIcon={<SettingsIcon />}
                onClick={() => handleOpenDialog('limit')}
                sx={{
                  mt: 2,
                  borderColor: theme.palette.text.primary,
                  color: theme.palette.text.primary,
                  '&:hover': {
                    borderColor: theme.palette.text.primary,
                    backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                  }
                }}
              >
                Spending Limits
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Invoice History */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" fontWeight="bold">
              Invoice History
            </Typography>
            <Button
              startIcon={<DownloadIcon />}
              variant="outlined"
              size="small"
              sx={{
                borderColor: theme.palette.text.primary,
                color: theme.palette.text.primary,
                '&:hover': {
                  borderColor: theme.palette.text.primary,
                  backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                }
              }}
            >
              Export All
            </Button>
          </Box>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Invoice ID</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {billingData.invoices.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {invoice.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {new Date(invoice.date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{invoice.description}</TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold">
                        {formatCurrency(invoice.amount)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={invoice.status.toUpperCase()}
                        size="small"
                        color={getStatusColor(invoice.status)}
                        sx={{
                          bgcolor: invoice.status === 'paid' ? 
                            (theme.palette.mode === 'dark' ? '#333333' : '#f0f0f0') : 
                            undefined,
                          color: invoice.status === 'paid' ? 
                            theme.palette.text.primary : 
                            undefined
                        }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="Download Invoice">
                        <IconButton size="small">
                          <DownloadIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Dialogs */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'payment' && 'Add Payment Method'}
          {dialogType === 'plan' && 'Change Plan'}
          {dialogType === 'limit' && 'Spending Limits'}
        </DialogTitle>
        <DialogContent>
          {dialogType === 'payment' && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Add a new payment method to your account
              </Typography>
              <TextField
                fullWidth
                label="Card Number"
                placeholder="1234 5678 9012 3456"
                margin="normal"
              />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Expiry Date"
                    placeholder="MM/YY"
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="CVC"
                    placeholder="123"
                    margin="normal"
                  />
                </Grid>
              </Grid>
              <TextField
                fullWidth
                label="Cardholder Name"
                margin="normal"
              />
            </Box>
          )}
          
          {dialogType === 'plan' && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Choose your billing plan
              </Typography>
              <List>
                <ListItem sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, mb: 1 }}>
                  <ListItemText
                    primary="Development"
                    secondary="Free - Perfect for testing"
                  />
                  <Typography variant="h6" fontWeight="bold">₹0</Typography>
                </ListItem>
                <ListItem sx={{ 
                  border: '2px solid', 
                  borderColor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000', 
                  borderRadius: 2, 
                  mb: 1,
                  bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                }}>
                  <ListItemText
                    primary="Production"
                    secondary="₹1 per 1K characters - Current plan"
                  />
                  <Typography variant="h6" fontWeight="bold">₹1/1K</Typography>
                </ListItem>
                <ListItem sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
                  <ListItemText
                    primary="Enterprise"
                    secondary="Custom volume pricing"
                  />
                  <Typography variant="h6" fontWeight="bold">Custom</Typography>
                </ListItem>
              </List>
            </Box>
          )}
          
          {dialogType === 'limit' && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Set your monthly spending limit to control costs
              </Typography>
              <TextField
                fullWidth
                label="Monthly Spending Limit (INR)"
                type="number"
                value={spendingLimit}
                onChange={(e) => setSpendingLimit(e.target.value)}
                margin="normal"
                InputProps={{
                  startAdornment: '₹'
                }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={autoRecharge}
                    onChange={(e) => setAutoRecharge(e.target.checked)}
                  />
                }
                label="Enable auto-recharge when limit is reached"
                sx={{ mt: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            variant="contained"
            sx={{
              bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
              color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
              '&:hover': {
                bgcolor: theme.palette.mode === 'dark' ? '#e5e5e5' : '#333333'
              }
            }}
          >
            {dialogType === 'payment' && 'Add Payment Method'}
            {dialogType === 'plan' && 'Change Plan'}
            {dialogType === 'limit' && 'Update Limits'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Billing;