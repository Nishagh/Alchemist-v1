/**
 * Phone Verification Component
 * 
 * Handles phone number verification for WhatsApp Business accounts
 * Supports SMS and voice verification methods
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  ButtonGroup,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  WhatsApp as WhatsAppIcon,
  Sms as SmsIcon,
  Phone as PhoneIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Timer as TimerIcon
} from '@mui/icons-material';

import whatsappService from '../../../services/whatsapp/whatsappBusinessService';

const PhoneVerification = ({
  managedAccount,
  onVerificationComplete,
  onError,
  onCancel
}) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [verificationMethod, setVerificationMethod] = useState('sms');
  const [loading, setLoading] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [attemptsRemaining, setAttemptsRemaining] = useState(3);
  const [error, setError] = useState('');

  // Start countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleVerificationMethodChange = (method) => {
    setVerificationMethod(method);
    setError('');
  };

  const handleRequestCode = async () => {
    setRequesting(true);
    setError('');
    
    try {
      const result = await whatsappService.requestVerificationCode(managedAccount.account_id, verificationMethod);
      setCountdown(result.expires_in || 300); // 5 minutes default
      setAttemptsRemaining(result.attempts_remaining || 3);
    } catch (err) {
      console.error('Error requesting verification code:', err);
      setError(err.message || 'Failed to request verification code');
    } finally {
      setRequesting(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!verificationCode.trim()) {
      setError('Please enter the verification code');
      return;
    }

    if (verificationCode.trim().length < 4) {
      setError('Verification code must be at least 4 digits');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await whatsappService.verifyPhoneNumber(
        managedAccount.account_id, 
        verificationCode.trim(), 
        verificationMethod
      );

      if (result.verified) {
        onVerificationComplete({
          ...managedAccount,
          status: 'active',
          verified_at: new Date().toISOString()
        });
      } else {
        setError(result.message || 'Verification failed. Please check your code and try again.');
        setAttemptsRemaining(prev => Math.max(0, prev - 1));
      }
    } catch (err) {
      console.error('Error verifying code:', err);
      setError(err.message || 'Verification failed. Please try again.');
      setAttemptsRemaining(prev => Math.max(0, prev - 1));
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (event) => {
    const value = event.target.value.replace(/\D/g, ''); // Only allow digits
    setVerificationCode(value);
    setError('');
  };

  const formatCountdown = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const canRequestCode = countdown === 0 && attemptsRemaining > 0;
  const canVerify = verificationCode.trim().length >= 4 && !loading;

  return (
    <Box sx={{ maxWidth: 500, mx: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <WhatsAppIcon sx={{ color: '#25D366' }} />
        <Typography variant="h6">
          Verify Phone Number
        </Typography>
        <Chip label="Almost Done!" color="warning" size="small" />
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Phone Verification Required:</strong> We need to verify ownership of{' '}
              <strong>{managedAccount.phone_number}</strong> to complete your WhatsApp Business setup.
            </Typography>
          </Alert>

          {/* Account Details */}
          <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon fontSize="small" />
              Account Details
            </Typography>
            <List dense>
              <ListItem disablePadding>
                <ListItemText 
                  primary="Phone Number"
                  secondary={managedAccount.phone_number}
                />
              </ListItem>
              <ListItem disablePadding>
                <ListItemText 
                  primary="Account ID"
                  secondary={managedAccount.account_id}
                />
              </ListItem>
              <ListItem disablePadding>
                <ListItemText 
                  primary="Status"
                  secondary="Waiting for verification"
                />
              </ListItem>
            </List>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Verification Method Selection */}
          <Typography variant="subtitle2" gutterBottom>
            Choose verification method:
          </Typography>
          
          <ButtonGroup 
            variant="outlined" 
            sx={{ mb: 3, width: '100%' }}
            disabled={loading || requesting}
          >
            <Button
              variant={verificationMethod === 'sms' ? 'contained' : 'outlined'}
              onClick={() => handleVerificationMethodChange('sms')}
              startIcon={<SmsIcon />}
              sx={{ 
                flex: 1,
                ...(verificationMethod === 'sms' && {
                  bgcolor: '#25D366',
                  '&:hover': { bgcolor: '#1EA952' }
                })
              }}
            >
              SMS Text
            </Button>
            <Button
              variant={verificationMethod === 'voice' ? 'contained' : 'outlined'}
              onClick={() => handleVerificationMethodChange('voice')}
              startIcon={<PhoneIcon />}
              sx={{ 
                flex: 1,
                ...(verificationMethod === 'voice' && {
                  bgcolor: '#25D366',
                  '&:hover': { bgcolor: '#1EA952' }
                })
              }}
            >
              Voice Call
            </Button>
          </ButtonGroup>

          {/* Request Code Button */}
          <Button
            fullWidth
            variant="outlined"
            onClick={handleRequestCode}
            disabled={!canRequestCode || requesting}
            startIcon={requesting ? <CircularProgress size={20} /> : <RefreshIcon />}
            sx={{ mb: 3 }}
          >
            {requesting ? 'Sending...' : 
             countdown > 0 ? `Resend in ${formatCountdown(countdown)}` : 
             `Send ${verificationMethod === 'sms' ? 'SMS' : 'Voice Call'}`}
          </Button>

          {/* Countdown Progress */}
          {countdown > 0 && (
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <TimerIcon fontSize="small" color="info" />
                <Typography variant="body2" color="info.main">
                  Code expires in {formatCountdown(countdown)}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={(countdown / 300) * 100} // Assuming 5 minute expiry
                sx={{ height: 6, borderRadius: 3 }}
              />
            </Box>
          )}

          {/* Verification Code Input */}
          <TextField
            fullWidth
            label="Verification Code"
            value={verificationCode}
            onChange={handleCodeChange}
            placeholder="Enter 4-6 digit code"
            disabled={loading}
            error={!!error}
            helperText={error || `Enter the ${verificationMethod === 'sms' ? 'SMS' : 'voice call'} verification code`}
            inputProps={{ 
              maxLength: 6,
              style: { 
                textAlign: 'center', 
                fontSize: '1.5rem', 
                letterSpacing: '0.5rem' 
              }
            }}
            sx={{ mb: 3 }}
          />

          {/* Attempts Remaining */}
          {attemptsRemaining < 3 && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              <Typography variant="body2">
                {attemptsRemaining > 0 
                  ? `${attemptsRemaining} verification attempts remaining`
                  : 'No verification attempts remaining. Please contact support.'}
              </Typography>
            </Alert>
          )}

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={handleVerifyCode}
              disabled={!canVerify || attemptsRemaining === 0}
              startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
              sx={{
                flex: 1,
                bgcolor: '#25D366',
                '&:hover': {
                  bgcolor: '#1EA952'
                }
              }}
            >
              {loading ? 'Verifying...' : 'Verify & Complete Setup'}
            </Button>
            
            <Button
              variant="outlined"
              onClick={onCancel}
              disabled={loading}
              sx={{ minWidth: 100 }}
            >
              Cancel
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Help Text */}
      <Alert severity="info">
        <Typography variant="body2">
          <strong>Not receiving codes?</strong> Make sure your phone can receive{' '}
          {verificationMethod === 'sms' ? 'SMS messages' : 'voice calls'} and check your spam folder.
          You can also try switching between SMS and voice verification methods.
        </Typography>
      </Alert>
    </Box>
  );
};

export default PhoneVerification;