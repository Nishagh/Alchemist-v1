/**
 * Status Badge Component
 * 
 * Reusable component for displaying status indicators with consistent styling
 */
import React from 'react';
import { Chip } from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  InfoOutlined as InfoIcon
} from '@mui/icons-material';

const StatusBadge = ({ status, variant = 'outlined', size = 'small', ...props }) => {
  const getStatusConfig = (status) => {
    const normalizedStatus = status?.toLowerCase();
    
    switch (normalizedStatus) {
      case 'indexed':
      case 'completed':
      case 'success':
      case 'deployed':
      case 'running':
        return {
          label: 'Indexed',
          color: 'success',
          icon: <CheckCircleIcon sx={{ fontSize: 'inherit' }} />
        };
      
      case 'indexing':
      case 'processing':
      case 'deploying':
      case 'pending':
        return {
          label: 'Processing',
          color: 'warning',
          icon: <ScheduleIcon sx={{ fontSize: 'inherit' }} />
        };
      
      case 'failed':
      case 'error':
      case 'stopped':
        return {
          label: 'Failed',
          color: 'error',
          icon: <ErrorIcon sx={{ fontSize: 'inherit' }} />
        };
      
      case 'warning':
        return {
          label: 'Warning',
          color: 'warning',
          icon: <WarningIcon sx={{ fontSize: 'inherit' }} />
        };
      
      case 'not_indexed':
      case 'not_deployed':
      case 'inactive':
        return {
          label: 'Not Indexed',
          color: 'default',
          icon: <InfoIcon sx={{ fontSize: 'inherit' }} />
        };
      
      default:
        return {
          label: status || 'Unknown',
          color: 'default',
          icon: <InfoIcon sx={{ fontSize: 'inherit' }} />
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <Chip
      label={config.label}
      color={config.color}
      variant={variant}
      size={size}
      icon={config.icon}
      sx={{
        fontSize: '0.75rem',
        height: 'auto',
        '& .MuiChip-label': {
          px: 1
        },
        '& .MuiChip-icon': {
          fontSize: '1rem'
        }
      }}
      {...props}
    />
  );
};

export default StatusBadge;