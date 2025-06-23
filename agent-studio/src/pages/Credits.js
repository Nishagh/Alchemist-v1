/**
 * Credits Page
 * 
 * Prepaid credits management interface
 */

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
  Badge,
  CircularProgress
} from '@mui/material';
import {
  AccountBalance as AccountBalanceIcon,
  Receipt as ReceiptIcon,
  TrendingUp as TrendingUpIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  AttachMoney as AttachMoneyIcon,
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ShoppingCart as ShoppingCartIcon,
  Add as AddIcon,
  Star as StarIcon,
  LocalOffer as LocalOfferIcon,
  History as HistoryIcon,
  CreditCard as CreditCardIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useAuth } from '../utils/AuthContext';
import { creditsService } from '../services';

const Credits = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [creditsData, setCreditsData] = useState({
    balance: {
      total_credits: 0,
      available_credits: 0,
      bonus_credits: 0
    },
    status: {
      is_low_balance: false,
      can_use_services: true
    },
    packages: [],
    transactions: [],
    orders: []
  });
  
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState(''); // 'purchase', 'custom', 'settings'
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [customAmount, setCustomAmount] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [settings, setSettings] = useState({
    low_balance_threshold: 50,
    auto_recharge_enabled: false,
    auto_recharge_amount: 500,
    balance_alerts: true
  });

  useEffect(() => {
    const loadCreditsData = async () => {
      if (!currentUser) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError('');

        // Load all credits data in parallel
        const [statusResult, packagesResult, transactionsResult, ordersResult] = await Promise.allSettled([
          creditsService.getStatus(),
          creditsService.getPackages(),
          creditsService.getTransactions(10),
          creditsService.getOrders(5)
        ]);

        // Handle status data
        if (statusResult.status === 'fulfilled' && statusResult.value.success) {
          const statusData = statusResult.value.data;
          setCreditsData(prev => ({
            ...prev,
            balance: statusData.balance || prev.balance,
            status: statusData.alerts || prev.status,
            settings: statusData.settings || prev.settings
          }));
          
          setSettings(statusData.settings || settings);
        }

        // Handle packages
        if (packagesResult.status === 'fulfilled' && packagesResult.value.success) {
          setCreditsData(prev => ({
            ...prev,
            packages: packagesResult.value.data || []
          }));
        }

        // Handle transactions
        if (transactionsResult.status === 'fulfilled' && transactionsResult.value.success) {
          setCreditsData(prev => ({
            ...prev,
            transactions: transactionsResult.value.data || []
          }));
        }

        // Handle orders
        if (ordersResult.status === 'fulfilled' && ordersResult.value.success) {
          setCreditsData(prev => ({
            ...prev,
            orders: ordersResult.value.data || []
          }));
        }

      } catch (error) {
        console.error('Error loading credits data:', error);
        setError('Failed to load credits data. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    loadCreditsData();
  }, [currentUser]);

  const handlePurchaseClick = (pkg) => {
    setSelectedPackage(pkg);
    if (pkg.id === 'custom_amount') {
      setDialogType('custom');
    } else {
      setDialogType('purchase');
    }
    setDialogOpen(true);
  };

  const handlePurchaseConfirm = async () => {
    try {
      setLoading(true);
      
      let order;
      if (dialogType === 'custom' && customAmount) {
        order = await creditsService.purchaseCredits('custom_amount', 1, parseFloat(customAmount));
      } else if (selectedPackage) {
        order = await creditsService.purchaseCredits(selectedPackage.id, quantity);
      }
      
      if (order.success) {
        // Open Razorpay checkout
        await creditsService.openPaymentCheckout(
          order.data.order,
          (result) => {
            // Payment successful
            setDialogOpen(false);
            setError('');
            // Reload data to show updated balance
            window.location.reload();
          },
          (error) => {
            // Payment failed
            setError(error.message || 'Payment failed. Please try again.');
          }
        );
      }
    } catch (error) {
      console.error('Error initiating purchase:', error);
      setError(error.message || 'Failed to initiate purchase');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setDialogType('');
    setSelectedPackage(null);
    setCustomAmount('');
    setQuantity(1);
  };

  const getBalanceColor = () => {
    const balance = creditsData.balance.total_credits;
    if (balance <= 0) return 'error';
    if (balance <= settings.low_balance_threshold) return 'warning';
    return 'success';
  };

  const formatCredits = (credits) => {
    return creditsService.formatCredits(credits);
  };

  const formatNumber = (number) => {
    return creditsService.formatNumber(number);
  };

  if (loading && creditsData.balance.total_credits === 0) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', my: 10 }}>
          <CircularProgress size={60} thickness={4} sx={{ mb: 3 }} />
          <Typography variant="h6" color="text.secondary" fontWeight="medium">
            Loading your credits account...
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Credits & Usage
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Manage your prepaid credits and monitor API usage
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

      {/* Low Balance Alert */}
      {creditsData.status.is_low_balance && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => handlePurchaseClick(creditsData.packages[0])}
            >
              Add Credits
            </Button>
          }
        >
          Your credit balance is low. Add credits to continue using AI services.
        </Alert>
      )}

      {/* Credit Balance Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ 
                  bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                  color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
                  mr: 2 
                }}>
                  <AccountBalanceIcon />
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" fontWeight="bold">
                    Credit Balance
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Prepaid credits for AI services
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => window.location.reload()}
                  sx={{
                    borderColor: theme.palette.text.primary,
                    color: theme.palette.text.primary,
                    '&:hover': {
                      borderColor: theme.palette.text.primary,
                      backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                    }
                  }}
                >
                  Refresh
                </Button>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="h3" fontWeight="bold" color={getBalanceColor()}>
                  {formatCredits(creditsData.balance.total_credits)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  ≈ {formatNumber(creditsService.creditsToCharacters(creditsData.balance.total_credits))} characters
                </Typography>
              </Box>
              
              {/* Credit Breakdown */}
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
                    <Typography variant="h6" fontWeight="bold">
                      {formatCredits(creditsData.balance.available_credits)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Purchased Credits
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
                    <Typography variant="h6" fontWeight="bold">
                      {formatCredits(creditsData.balance.bonus_credits)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Bonus Credits
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Quick Actions
              </Typography>
              
              <Stack spacing={2}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setDialogType('custom');
                    setDialogOpen(true);
                  }}
                  sx={{
                    bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#e5e5e5' : '#333333'
                    }
                  }}
                >
                  Add Credits
                </Button>
                
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<HistoryIcon />}
                  onClick={() => setDialogType('history') || setDialogOpen(true)}
                  sx={{
                    borderColor: theme.palette.text.primary,
                    color: theme.palette.text.primary,
                    '&:hover': {
                      borderColor: theme.palette.text.primary,
                      backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                    }
                  }}
                >
                  View History
                </Button>
                
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<SettingsIcon />}
                  onClick={() => setDialogType('settings') || setDialogOpen(true)}
                  sx={{
                    borderColor: theme.palette.text.primary,
                    color: theme.palette.text.primary,
                    '&:hover': {
                      borderColor: theme.palette.text.primary,
                      backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                    }
                  }}
                >
                  Settings
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Credit Packages */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Credit Packages
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Choose a package that fits your usage. All credits are valid for 1 year.
          </Typography>
          
          <Grid container spacing={3}>
            {(creditsData.packages || []).map((pkg) => (
              <Grid item xs={12} sm={6} md={3} key={pkg.id}>
                <Card 
                  sx={{ 
                    height: '100%',
                    border: pkg.popular ? `2px solid ${theme.palette.primary.main}` : 
                           pkg.best_value ? `2px solid ${theme.palette.success.main}` : 
                           `1px solid ${theme.palette.divider}`,
                    position: 'relative',
                    '&:hover': {
                      boxShadow: '0 8px 25px rgba(0, 0, 0, 0.15)'
                    }
                  }}
                >
                  {pkg.popular && (
                    <Chip 
                      label="Most Popular" 
                      color="primary" 
                      size="small"
                      sx={{ position: 'absolute', top: 10, right: 10 }}
                    />
                  )}
                  {pkg.best_value && (
                    <Chip 
                      label="Best Value" 
                      color="success" 
                      size="small"
                      sx={{ position: 'absolute', top: 10, right: 10 }}
                    />
                  )}
                  
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      {pkg.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {pkg.description}
                    </Typography>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="h4" fontWeight="bold">
                        {pkg.id === 'custom_amount' ? 'Custom' : formatCredits(pkg.price)}
                      </Typography>
                      {pkg.bonus_credits > 0 && (
                        <Chip 
                          label={`+${formatCredits(pkg.bonus_credits)} bonus`}
                          size="small"
                          color="success"
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Box>
                    
                    <List dense>
                      {pkg.features.map((feature, index) => (
                        <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 30 }}>
                            <CheckCircleIcon fontSize="small" color="success" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={feature}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                    
                    <Button
                      fullWidth
                      variant={pkg.popular ? 'contained' : 'outlined'}
                      onClick={() => handlePurchaseClick(pkg)}
                      sx={{ mt: 2 }}
                    >
                      {pkg.id === 'custom_amount' ? 'Add Custom Amount' : 'Purchase'}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Recent Transactions */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" fontWeight="bold">
              Recent Transactions
            </Typography>
            <Button
              startIcon={<HistoryIcon />}
              variant="outlined"
              size="small"
              onClick={() => setDialogType('history') || setDialogOpen(true)}
            >
              View All
            </Button>
          </Box>
          
          {(creditsData.transactions || []).length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Balance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(creditsData.transactions || []).slice(0, 5).map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell>
                        {new Date(transaction.timestamp).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={transaction.type}
                          size="small"
                          color={transaction.type === 'purchase' ? 'success' : 
                                transaction.type === 'usage' ? 'default' : 'info'}
                        />
                      </TableCell>
                      <TableCell>{transaction.description}</TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          color={transaction.amount > 0 ? 'success.main' : 'error.main'}
                          fontWeight="bold"
                        >
                          {transaction.amount > 0 ? '+' : ''}{formatCredits(transaction.amount)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatCredits(transaction.balance_after)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary">
                No transactions yet. Purchase credits to get started!
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Purchase Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'purchase' && `Purchase ${selectedPackage?.name}`}
          {dialogType === 'custom' && 'Add Credits'}
          {dialogType === 'settings' && 'Credit Settings'}
          {dialogType === 'history' && 'Transaction History'}
        </DialogTitle>
        <DialogContent>
          {dialogType === 'purchase' && selectedPackage && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body1" gutterBottom>
                You're about to purchase <strong>{selectedPackage.name}</strong>
              </Typography>
              
              {/* Quantity Selector */}
              <Box sx={{ my: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Quantity
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    disabled={quantity <= 1}
                    sx={{ minWidth: '40px', height: '40px' }}
                  >
                    -
                  </Button>
                  <TextField
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                    inputProps={{ 
                      min: 1, 
                      max: 10, 
                      style: { textAlign: 'center' } 
                    }}
                    sx={{ width: '80px' }}
                    type="number"
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setQuantity(Math.min(10, quantity + 1))}
                    disabled={quantity >= 10}
                    sx={{ minWidth: '40px', height: '40px' }}
                  >
                    +
                  </Button>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Maximum 10 packages per purchase
                </Typography>
              </Box>

              {/* Credits Breakdown */}
              <Box sx={{ my: 2, p: 2, bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb', borderRadius: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Per package: {formatCredits(selectedPackage.total_credits)} credits
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  ({formatCredits(selectedPackage.base_credits)} base + {formatCredits(selectedPackage.bonus_credits)} bonus)
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="h6" fontWeight="bold">
                  Total Credits: {formatCredits(selectedPackage.total_credits * quantity)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {formatCredits(selectedPackage.base_credits * quantity)} base + {formatCredits(selectedPackage.bonus_credits * quantity)} bonus
                </Typography>
              </Box>

              <Typography variant="h5" fontWeight="bold" sx={{ 
                p: 2, 
                bgcolor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0', 
                borderRadius: 2,
                textAlign: 'center'
              }}>
                Total: ₹{selectedPackage.price * quantity}
              </Typography>
            </Box>
          )}
          
          {dialogType === 'custom' && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body1" gutterBottom>
                <strong>Add Credits to Your Account</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
                Enter any amount of ₹1000 or more. There's no upper limit!
              </Typography>
              
              <TextField
                fullWidth
                label="Amount (INR)"
                type="number"
                value={customAmount}
                onChange={(e) => setCustomAmount(e.target.value)}
                margin="normal"
                inputProps={{ min: 1000 }}
                helperText="Minimum ₹1000 • 1 credit = ₹1 = ~1000 characters"
                error={customAmount && parseFloat(customAmount) < 1000}
                sx={{ mb: 3 }}
              />
              
              {customAmount && parseFloat(customAmount) >= 1000 && (
                <Box sx={{ 
                  p: 3, 
                  bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb', 
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.divider}`
                }}>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Purchase Summary
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Amount:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      ₹{parseFloat(customAmount).toLocaleString('en-IN')}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Credits you'll receive:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {parseFloat(customAmount).toLocaleString('en-IN')} credits
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Estimated characters:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      ~{(parseFloat(customAmount) * 1000).toLocaleString('en-IN')}
                    </Typography>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" fontWeight="bold">
                      Total:
                    </Typography>
                    <Typography variant="h5" fontWeight="bold" color="primary.main">
                      ₹{parseFloat(customAmount).toLocaleString('en-IN')}
                    </Typography>
                  </Box>
                </Box>
              )}
              
              {customAmount && parseFloat(customAmount) < 1000 && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Minimum purchase amount is ₹1000
                </Alert>
              )}
            </Box>
          )}
          
          {dialogType === 'settings' && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Configure your credit account settings
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.balance_alerts}
                    onChange={(e) => setSettings({...settings, balance_alerts: e.target.checked})}
                  />
                }
                label="Low balance alerts"
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Low Balance Threshold (INR)"
                type="number"
                value={settings.low_balance_threshold}
                onChange={(e) => setSettings({...settings, low_balance_threshold: parseInt(e.target.value)})}
                margin="normal"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          {(dialogType === 'purchase' || dialogType === 'custom') && (
            <Button 
              variant="contained"
              onClick={handlePurchaseConfirm}
              disabled={dialogType === 'custom' && (!customAmount || parseFloat(customAmount) < 1000)}
              sx={{
                bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
                '&:hover': {
                  bgcolor: theme.palette.mode === 'dark' ? '#e5e5e5' : '#333333'
                }
              }}
            >
              {dialogType === 'custom' && customAmount ? 
                `Purchase ₹${parseFloat(customAmount).toLocaleString('en-IN')}` : 
                'Purchase Credits'
              }
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Credits;