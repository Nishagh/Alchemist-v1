/**
 * Agent Configuration Form
 * 
 * Form component for configuring agent settings (name, description, type, model, etc.)
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Paper,
  Divider,
  Button,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  Save as SaveIcon,
  AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';
import { getAgentTypes } from '../../../services';
import { validateAgentConfig } from '../../../utils/agentEditorHelpers';

const AgentConfigurationForm = ({ 
  agent, 
  onAgentUpdate, 
  onSave, 
  saving = false,
  disabled = false 
}) => {
  const [agentTypes, setAgentTypes] = useState([]);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: '',
    model: 'gpt-4',
    custom_instructions: '',
    ...agent
  });
  const [validationErrors, setValidationErrors] = useState([]);

  // Load agent types on mount
  useEffect(() => {
    const fetchAgentTypes = async () => {
      try {
        setLoadingTypes(true);
        const types = await getAgentTypes();
        setAgentTypes(types || []);
      } catch (error) {
        console.error('Error loading agent types:', error);
        // This should not happen since getAgentTypes now returns static data
        setAgentTypes([]);
      } finally {
        setLoadingTypes(false);
      }
    };

    fetchAgentTypes();
  }, []);

  // Update form data when agent prop changes
  useEffect(() => {
    if (agent) {
      setFormData({
        name: '',
        description: '',
        type: '',
        model: 'gpt-4',
        custom_instructions: '',
        ...agent
      });
    }
  }, [agent]);

  // Validate form data
  useEffect(() => {
    const validation = validateAgentConfig(formData);
    setValidationErrors(validation.errors);
  }, [formData]);

  const handleInputChange = (field) => (event) => {
    const value = event.target.value;
    const newFormData = { ...formData, [field]: value };
    setFormData(newFormData);
    
    if (onAgentUpdate) {
      onAgentUpdate(newFormData);
    }
  };

  const handleSave = () => {
    const validation = validateAgentConfig(formData);
    if (validation.isValid && onSave) {
      onSave(formData);
    }
  };

  const modelOptions = [
    { value: 'gpt-4', label: 'GPT-4 (Recommended)' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'claude-3-opus', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku', label: 'Claude 3 Haiku' }
  ];

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      <Box sx={{ p: 3, flex: 1, overflowY: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <AutoAwesomeIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
          Agent Configuration
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Basic Information */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold', color: 'text.secondary' }}>
            Basic Information
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Agent Name"
              value={formData.name}
              onChange={handleInputChange('name')}
              disabled={disabled}
              required
              error={validationErrors.some(e => e.includes('name'))}
              helperText={validationErrors.find(e => e.includes('name')) || 'Enter a descriptive name for your agent'}
              sx={{ width: '100%' }}
            />

            <TextField
              label="Description"
              value={formData.description}
              onChange={handleInputChange('description')}
              disabled={disabled}
              multiline
              rows={2}
              error={validationErrors.some(e => e.includes('description'))}
              helperText={validationErrors.find(e => e.includes('description')) || 'Brief description of what this agent does'}
              sx={{ width: '100%' }}
            />
          </Box>
        </Box>

        <Divider />

        {/* Agent Type */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold', color: 'text.secondary' }}>
            Agent Type
          </Typography>
          
          <FormControl fullWidth disabled={disabled || loadingTypes}>
            <InputLabel>Agent Type</InputLabel>
            <Select
              value={formData.type}
              onChange={handleInputChange('type')}
              label="Agent Type"
              required
            >
              {loadingTypes ? (
                <MenuItem disabled>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  Loading types...
                </MenuItem>
              ) : (
                agentTypes.map((type) => (
                  <MenuItem key={type.id} value={type.id}>
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {type.name}
                      </Typography>
                      {type.description && (
                        <Typography variant="caption" color="text.secondary">
                          {type.description}
                        </Typography>
                      )}
                    </Box>
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
        </Box>

        <Divider />

        {/* Model Configuration */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold', color: 'text.secondary' }}>
            Model Configuration
          </Typography>
          
          <FormControl fullWidth disabled={disabled}>
            <InputLabel>Language Model</InputLabel>
            <Select
              value={formData.model}
              onChange={handleInputChange('model')}
              label="Language Model"
            >
              {modelOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <Typography>{option.label}</Typography>
                    {option.value === 'gpt-4' && (
                      <Chip label="Recommended" size="small" color="primary" variant="outlined" />
                    )}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        <Divider />

        {/* Custom Instructions */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold', color: 'text.secondary' }}>
            Custom Instructions
          </Typography>
          
          <TextField
            label="Custom Instructions"
            value={formData.custom_instructions}
            onChange={handleInputChange('custom_instructions')}
            disabled={disabled}
            multiline
            rows={4}
            placeholder="Enter specific instructions for how this agent should behave..."
            helperText="Optional: Provide specific guidelines for how the agent should respond and behave"
            sx={{ width: '100%' }}
          />
        </Box>

        {/* Save Button */}
        <Box sx={{ pt: 2 }}>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={disabled || saving || validationErrors.length > 0}
            startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
            fullWidth
            sx={{
              py: 1.5,
              fontWeight: 'bold',
              fontSize: '1rem'
            }}
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
          
          {validationErrors.length > 0 && (
            <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
              Please fix the validation errors above
            </Typography>
          )}
        </Box>
      </Box>
      </Box>
    </Paper>
  );
};

export default AgentConfigurationForm;