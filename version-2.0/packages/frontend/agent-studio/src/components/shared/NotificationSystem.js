/**
 * Notification System
 * 
 * Enhanced notification/snackbar system for user feedback
 */
import React from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Slide,
  useTheme
} from '@mui/material';

const SlideTransition = (props) => {
  return <Slide {...props} direction="up" />;
};

const NotificationSystem = ({ 
  notification,
  onClose,
  autoHideDuration = 6000
}) => {
  const theme = useTheme();

  if (!notification) return null;

  const {
    open = false,
    message = '',
    severity = 'info',
    title = '',
    details = '',
    persist = false
  } = notification;

  const handleClose = (event, reason) => {
    if (reason === 'clickaway' && persist) {
      return;
    }
    
    if (onClose) {
      onClose();
    }
  };

  return (
    <Snackbar
      open={open}
      autoHideDuration={persist ? null : autoHideDuration}
      onClose={handleClose}
      TransitionComponent={SlideTransition}
      anchorOrigin={{ 
        vertical: 'bottom', 
        horizontal: 'right' 
      }}
      sx={{
        '& .MuiSnackbarContent-root': {
          padding: 0
        }
      }}
    >
      <Alert 
        onClose={persist ? undefined : handleClose}
        severity={severity}
        variant="filled"
        sx={{ 
          width: '100%',
          minWidth: 300,
          maxWidth: 500,
          borderRadius: 2,
          boxShadow: theme.shadows[8],
          '& .MuiAlert-message': {
            padding: title ? '8px 0' : '4px 0'
          },
          '& .MuiAlert-action': {
            alignItems: 'flex-start',
            paddingTop: '6px'
          }
        }}
      >
        {title && (
          <AlertTitle sx={{ 
            marginBottom: details || message ? 1 : 0,
            fontSize: '1rem',
            fontWeight: 600
          }}>
            {title}
          </AlertTitle>
        )}
        
        {message && (
          <div style={{ 
            fontSize: '0.875rem',
            lineHeight: 1.4,
            marginBottom: details ? 8 : 0
          }}>
            {message}
          </div>
        )}
        
        {details && (
          <div style={{ 
            fontSize: '0.8rem',
            opacity: 0.9,
            lineHeight: 1.3,
            fontFamily: 'monospace',
            backgroundColor: 'rgba(0,0,0,0.1)',
            padding: '8px',
            borderRadius: '4px',
            marginTop: 4,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}>
            {details}
          </div>
        )}
      </Alert>
    </Snackbar>
  );
};

// Helper functions for creating notifications
export const createNotification = (message, severity = 'info', options = {}) => ({
  open: true,
  message,
  severity,
  ...options
});

export const createSuccessNotification = (message, options = {}) =>
  createNotification(message, 'success', options);

export const createErrorNotification = (message, options = {}) =>
  createNotification(message, 'error', { persist: true, ...options });

export const createWarningNotification = (message, options = {}) =>
  createNotification(message, 'warning', options);

export const createInfoNotification = (message, options = {}) =>
  createNotification(message, 'info', options);

export default NotificationSystem;