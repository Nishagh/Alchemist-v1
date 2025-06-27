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
import { 
  DEPLOYMENT_STATUS, 
  WORKFLOW_STAGE_STATUS,
  getStatusMetadata,
  getStatusVariant 
} from '../../constants/workflowStates';

const StatusBadge = ({ status, variant = 'outlined', size = 'small', ...props }) => {
  const getStatusConfig = (status) => {
    try {
      const metadata = getStatusMetadata(status);
      const statusVariant = getStatusVariant(status);
      
      // Icon mapping
      const iconMap = {
        'CheckCircle': <CheckCircleIcon sx={{ fontSize: 'inherit' }} />,
        'Schedule': <ScheduleIcon sx={{ fontSize: 'inherit' }} />,
        'Error': <ErrorIcon sx={{ fontSize: 'inherit' }} />,
        'Warning': <WarningIcon sx={{ fontSize: 'inherit' }} />,
        'Help': <InfoIcon sx={{ fontSize: 'inherit' }} />,
        'CircleOutlined': <InfoIcon sx={{ fontSize: 'inherit' }} />,
        'PlayArrow': <ScheduleIcon sx={{ fontSize: 'inherit' }} />,
        'Lock': <InfoIcon sx={{ fontSize: 'inherit' }} />,
        'Queue': <ScheduleIcon sx={{ fontSize: 'inherit' }} />,
        'Refresh': <ScheduleIcon sx={{ fontSize: 'inherit' }} />,
        'Code': <ScheduleIcon sx={{ fontSize: 'inherit' }} />,
        'Build': <ScheduleIcon sx={{ fontSize: 'inherit' }} />,
        'RocketLaunch': <ScheduleIcon sx={{ fontSize: 'inherit' }} />,
        'Cancel': <InfoIcon sx={{ fontSize: 'inherit' }} />,
        'AccessTime': <WarningIcon sx={{ fontSize: 'inherit' }} />,
        'Block': <InfoIcon sx={{ fontSize: 'inherit' }} />
      };
      
      return {
        label: metadata.label,
        color: statusVariant,
        icon: iconMap[metadata.icon] || <InfoIcon sx={{ fontSize: 'inherit' }} />
      };
    } catch (error) {
      // Fallback for unknown statuses
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