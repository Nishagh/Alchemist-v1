/**
 * Simple WhatsApp Setup
 * 
 * Simplified one-step WhatsApp integration requiring only a phone number
 * Handles automated Business account creation through BSP
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  WhatsApp as WhatsAppIcon,
  Phone as PhoneIcon,
  Business as BusinessIcon,
  CheckCircle as CheckCircleIcon,
  Autorenew as AutorenewIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Support as SupportIcon
} from '@mui/icons-material';

import whatsappService from '../../../services/whatsapp/whatsappBusinessService';

const SimpleWhatsAppSetup = ({
  deployment,
  onComplete,
  onCancel,
  onError,
  onVerificationRequired
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    phoneNumber: '',
    businessName: '',
    industry: 'technology',
    description: ''
  });
  const [errors, setErrors] = useState({});

  const steps = [
    {
      label: 'Phone Number',
      description: 'Enter your WhatsApp Business phone number'
    },
    {
      label: 'Business Details',
      description: 'Optional business information for better setup'
    },
    {
      label: 'Setup Complete',
      description: 'Automatic account creation and configuration'
    }
  ];

  const industries = [
    { value: 'technology', label: 'Technology' },
    { value: 'ecommerce', label: 'E-commerce' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'education', label: 'Education' },
    { value: 'finance', label: 'Finance' },
    { value: 'retail', label: 'Retail' },
    { value: 'hospitality', label: 'Hospitality' },
    { value: 'consulting', label: 'Consulting' },
    { value: 'other', label: 'Other' }
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

  const validatePhoneNumber = () => {
    const newErrors = {};
    
    if (!formData.phoneNumber) {
      newErrors.phoneNumber = 'Phone number is required';
    } else if (!/^\+\d{10,15}$/.test(formData.phoneNumber)) {
      newErrors.phoneNumber = 'Please enter a valid phone number with country code (e.g., +1234567890)';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (activeStep === 0 && !validatePhoneNumber()) {
      return;
    }
    setActiveStep(prevStep => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep(prevStep => prevStep - 1);
  };

  const handleSetupComplete = async () => {
    if (!validatePhoneNumber()) {
      setActiveStep(0);
      return;
    }

    setLoading(true);
    try {
      const managedAccount = await whatsappService.createManagedWhatsAppAccount(
        deployment.deployment_id,
        formData.phoneNumber,
        {
          businessName: formData.businessName || 'AI Agent Business',
          industry: formData.industry,
          description: formData.description || 'AI-powered customer service',
          serviceUrl: deployment.service_url
        }
      );

      if (managedAccount.verification_required) {
        // Phone verification needed
        onVerificationRequired(managedAccount);
      } else {
        // Account is ready to use
        onComplete(managedAccount);
      }
    } catch (error) {
      console.error('Error setting up WhatsApp:', error);
      onError(error.message || 'Failed to setup WhatsApp integration');
      setActiveStep(0); // Go back to first step
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
                <strong>Direct WhatsApp Business API:</strong> Just enter your phone number and we'll handle everything else automatically through Meta's official API!
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
              InputProps={{
                startAdornment: <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />

            <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SpeedIcon fontSize="small" />
                What we'll do automatically:
              </Typography>
              <List dense>
                <ListItem disablePadding>
                  <ListItemIcon>
                    <CheckCircleIcon fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="Create WhatsApp Business account via Meta API" />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemIcon>
                    <CheckCircleIcon fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="Configure webhooks and API integration" />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemIcon>
                    <CheckCircleIcon fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="Set up message handling for your AI agent" />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemIcon>
                    <CheckCircleIcon fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="Verify phone number ownership" />
                </ListItem>
              </List>
            </Box>
          </Box>
        );

      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Optional:</strong> Provide business details for a better WhatsApp profile setup.
                You can skip this step if you prefer.
              </Typography>
            </Alert>

            <TextField
              fullWidth
              label="Business Name"
              value={formData.businessName}
              onChange={handleInputChange('businessName')}
              helperText="Display name for your WhatsApp Business profile"
              sx={{ mb: 2 }}
              disabled={loading}
              InputProps={{
                startAdornment: <BusinessIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Industry</InputLabel>
              <Select
                value={formData.industry}
                onChange={handleInputChange('industry')}
                label="Industry"
                disabled={loading}
              >
                {industries.map((industry) => (
                  <MenuItem key={industry.value} value={industry.value}>
                    {industry.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Business Description"
              value={formData.description}
              onChange={handleInputChange('description')}
              multiline
              rows={2}
              helperText="Brief description of your business (optional)"
              disabled={loading}
            />
          </Box>
        );

      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Ready to setup!</strong> We'll create your WhatsApp Business account automatically.
              </Typography>
            </Alert>

            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Setup Summary
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <List dense>
                  <ListItem>
                    <ListItemIcon><PhoneIcon /></ListItemIcon>
                    <ListItemText 
                      primary="Phone Number"
                      secondary={formData.phoneNumber}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><BusinessIcon /></ListItemIcon>
                    <ListItemText 
                      primary="Business Name"
                      secondary={formData.businessName || 'AI Agent Business'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><AutorenewIcon /></ListItemIcon>
                    <ListItemText 
                      primary="Service URL"
                      secondary={deployment.service_url}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Box sx={{ flex: 1, textAlign: 'center', p: 2, bgcolor: 'success.50', borderRadius: 1 }}>
                <SecurityIcon color="success" sx={{ mb: 1 }} />
                <Typography variant="caption" display="block">
                  Secure & Verified
                </Typography>
              </Box>
              <Box sx={{ flex: 1, textAlign: 'center', p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
                <SpeedIcon color="info" sx={{ mb: 1 }} />
                <Typography variant="caption" display="block">
                  Quick Setup
                </Typography>
              </Box>
              <Box sx={{ flex: 1, textAlign: 'center', p: 2, bgcolor: 'warning.50', borderRadius: 1 }}>
                <SupportIcon color="warning" sx={{ mb: 1 }} />
                <Typography variant="caption" display="block">
                  Managed Service
                </Typography>
              </Box>
            </Box>

            <Alert severity="info">
              <Typography variant="body2">
                The setup process takes about 30-60 seconds. You may need to verify phone ownership via SMS.
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
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <WhatsAppIcon sx={{ color: '#25D366' }} />
        <Typography variant="h6">
          Simple WhatsApp Setup
        </Typography>
        <Chip label="Managed Service" color="primary" size="small" />
      </Box>

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
                  onClick={index === steps.length - 1 ? handleSetupComplete : handleNext}
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
                  {loading ? 'Setting up...' : (index === steps.length - 1 ? 'Setup WhatsApp' : 'Next')}
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

export default SimpleWhatsAppSetup;