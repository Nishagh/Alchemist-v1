/**
 * WhatsApp Setup Wizard
 * 
 * Step-by-step wizard for setting up WhatsApp Business API integration
 */
import React, { useState } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  TextField,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  CircularProgress,
  Link,
  Divider
} from '@mui/material';
import {
  AccountCircle as AccountCircleIcon,
  Phone as PhoneIcon,
  Webhook as WebhookIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Launch as LaunchIcon
} from '@mui/icons-material';

import { validateCredentials, createWhatsAppIntegration } from '../../../services/whatsapp/whatsappService';

const WhatsAppSetupWizard = ({
  deployment,
  onComplete,
  onCancel,
  onError
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [validationResults, setValidationResults] = useState(null);
  const [formData, setFormData] = useState({
    businessAccountId: '',
    accessToken: '',
    phoneNumber: '',
    webhookVerifyToken: '',
    testPhoneNumber: ''
  });
  const [errors, setErrors] = useState({});

  const steps = [
    {
      label: 'WhatsApp Business Account',
      description: 'Enter your WhatsApp Business API credentials'
    },
    {
      label: 'Phone Number Configuration',
      description: 'Configure your WhatsApp Business phone number'
    },
    {
      label: 'Webhook Setup',
      description: 'Set up webhook for message handling'
    },
    {
      label: 'Test & Complete',
      description: 'Test the integration and complete setup'
    }
  ];

  const handleInputChange = (field) => (event) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateStep = (stepIndex) => {
    const newErrors = {};
    
    switch (stepIndex) {
      case 0:
        if (!formData.businessAccountId) {
          newErrors.businessAccountId = 'Business Account ID is required';
        }
        if (!formData.accessToken) {
          newErrors.accessToken = 'Access Token is required';
        }
        break;
      case 1:
        if (!formData.phoneNumber) {
          newErrors.phoneNumber = 'Phone Number is required';
        } else if (!/^\+\d{10,15}$/.test(formData.phoneNumber)) {
          newErrors.phoneNumber = 'Please enter a valid phone number with country code (e.g., +1234567890)';
        }
        break;
      case 2:
        if (!formData.webhookVerifyToken) {
          newErrors.webhookVerifyToken = 'Webhook Verify Token is required';
        } else if (formData.webhookVerifyToken.length < 8) {
          newErrors.webhookVerifyToken = 'Verify token must be at least 8 characters long';
        }
        break;
      case 3:
        if (!formData.testPhoneNumber) {
          newErrors.testPhoneNumber = 'Test phone number is required';
        } else if (!/^\+\d{10,15}$/.test(formData.testPhoneNumber)) {
          newErrors.testPhoneNumber = 'Please enter a valid phone number with country code';
        }
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = async () => {
    if (!validateStep(activeStep)) {
      return;
    }

    // Special validation for step 0 (credentials)
    if (activeStep === 0) {
      setLoading(true);
      try {
        const validation = await validateCredentials({
          businessAccountId: formData.businessAccountId,
          accessToken: formData.accessToken,
          phoneNumber: formData.phoneNumber
        });
        setValidationResults(validation);
      } catch (error) {
        setErrors({
          businessAccountId: 'Invalid credentials. Please check your Business Account ID and Access Token.'
        });
        setLoading(false);
        return;
      }
      setLoading(false);
    }

    setActiveStep(prevStep => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep(prevStep => prevStep - 1);
  };

  const handleComplete = async () => {
    if (!validateStep(activeStep)) {
      return;
    }

    setLoading(true);
    try {
      const integration = await createWhatsAppIntegration(deployment.deployment_id, {
        businessAccountId: formData.businessAccountId,
        accessToken: formData.accessToken,
        phoneNumber: formData.phoneNumber,
        webhookVerifyToken: formData.webhookVerifyToken,
        serviceUrl: deployment.service_url
      });

      onComplete(integration);
    } catch (error) {
      console.error('Error creating WhatsApp integration:', error);
      onError(error.message || 'Failed to create WhatsApp integration');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (stepIndex) => {
    switch (stepIndex) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                You need a WhatsApp Business API account to proceed. If you don't have one, 
                <Link href="https://business.whatsapp.com/api" target="_blank" sx={{ ml: 0.5 }}>
                  sign up here <LaunchIcon fontSize="small" sx={{ verticalAlign: 'middle' }} />
                </Link>
              </Typography>
            </Alert>

            <TextField
              fullWidth
              label="Business Account ID"
              value={formData.businessAccountId}
              onChange={handleInputChange('businessAccountId')}
              error={!!errors.businessAccountId}
              helperText={errors.businessAccountId || 'Your WhatsApp Business Account ID'}
              sx={{ mb: 2 }}
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Access Token"
              type="password"
              value={formData.accessToken}
              onChange={handleInputChange('accessToken')}
              error={!!errors.accessToken}
              helperText={errors.accessToken || 'Your WhatsApp Business API Access Token'}
              sx={{ mb: 2 }}
              disabled={loading}
            />

            {validationResults && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Credentials validated successfully!</strong>
                </Typography>
                <Typography variant="body2">
                  Business Name: {validationResults.business_name}
                </Typography>
              </Alert>
            )}
          </Box>
        );

      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                Configure the phone number that will be used for your WhatsApp Business integration.
              </Typography>
            </Alert>

            <TextField
              fullWidth
              label="WhatsApp Business Phone Number"
              value={formData.phoneNumber}
              onChange={handleInputChange('phoneNumber')}
              error={!!errors.phoneNumber}
              helperText={errors.phoneNumber || 'Include country code (e.g., +1234567890)'}
              placeholder="+1234567890"
              disabled={loading}
            />

            {validationResults && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Available phone numbers from your account:
                </Typography>
                <List dense>
                  {validationResults.phone_numbers?.map((phone, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <PhoneIcon />
                      </ListItemIcon>
                      <ListItemText primary={phone.number} secondary={phone.status} />
                      <Chip 
                        label={phone.verified ? 'Verified' : 'Unverified'} 
                        color={phone.verified ? 'success' : 'warning'}
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </Alert>
            )}
          </Box>
        );

      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                Set up webhook configuration to receive WhatsApp messages in your deployed agent.
              </Typography>
            </Alert>

            <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
              <Typography variant="subtitle2" gutterBottom>
                Webhook Configuration
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Webhook URL"
                    secondary={`${deployment.service_url}/webhook/whatsapp`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="HTTP Method"
                    secondary="POST"
                  />
                </ListItem>
              </List>
            </Paper>

            <TextField
              fullWidth
              label="Webhook Verify Token"
              value={formData.webhookVerifyToken}
              onChange={handleInputChange('webhookVerifyToken')}
              error={!!errors.webhookVerifyToken}
              helperText={errors.webhookVerifyToken || 'Enter a secure verify token (min 8 characters)'}
              placeholder="Enter a secure token"
              disabled={loading}
            />

            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Important:</strong> You'll need to configure this webhook URL and verify token 
                in your WhatsApp Business API dashboard.
              </Typography>
            </Alert>
          </Box>
        );

      case 3:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Ready to complete setup!</strong> Review your configuration and test the integration.
              </Typography>
            </Alert>

            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Configuration Summary
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                <ListItem>
                  <ListItemIcon><AccountCircleIcon /></ListItemIcon>
                  <ListItemText 
                    primary="Business Account"
                    secondary={formData.businessAccountId}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><PhoneIcon /></ListItemIcon>
                  <ListItemText 
                    primary="Phone Number"
                    secondary={formData.phoneNumber}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><WebhookIcon /></ListItemIcon>
                  <ListItemText 
                    primary="Webhook URL"
                    secondary={`${deployment.service_url}/webhook/whatsapp`}
                  />
                </ListItem>
              </List>
            </Paper>

            <TextField
              fullWidth
              label="Test Phone Number"
              value={formData.testPhoneNumber}
              onChange={handleInputChange('testPhoneNumber')}
              error={!!errors.testPhoneNumber}
              helperText={errors.testPhoneNumber || 'Phone number to send a test message to'}
              placeholder="+1234567890"
              sx={{ mb: 2 }}
              disabled={loading}
            />

            <Alert severity="info">
              <Typography variant="body2">
                After completing setup, we'll send a test message to verify the integration is working correctly.
              </Typography>
            </Alert>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto' }}>
      <Stepper activeStep={activeStep} orientation="vertical">
        {steps.map((step, index) => (
          <Step key={step.label}>
            <StepLabel>
              <Typography variant="h6">{step.label}</Typography>
              <Typography variant="body2" color="text.secondary">
                {step.description}
              </Typography>
            </StepLabel>
            <StepContent>
              {renderStepContent(index)}
              
              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  onClick={index === steps.length - 1 ? handleComplete : handleNext}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : null}
                  sx={{
                    mr: 1,
                    bgcolor: '#25D366',
                    '&:hover': {
                      bgcolor: '#1EA952'
                    }
                  }}
                >
                  {loading ? 'Processing...' : (index === steps.length - 1 ? 'Complete Setup' : 'Next')}
                </Button>
                
                <Button
                  disabled={index === 0 || loading}
                  onClick={handleBack}
                  sx={{ mr: 1 }}
                >
                  Back
                </Button>
                
                <Button
                  onClick={onCancel}
                  disabled={loading}
                  color="inherit"
                >
                  Cancel
                </Button>
              </Box>
            </StepContent>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
};

export default WhatsAppSetupWizard;