/**
 * Agent Editor Layout
 * 
 * Simplified layout wrapper for the Agent Editor with sidebar navigation
 */
import React from 'react';
import {
  Box,
  Alert,
  Slide,
  useTheme
} from '@mui/material';

const AgentEditorLayout = ({ 
  error, 
  children, 
  loading = false 
}) => {
  const theme = useTheme();

  return (
    <Box 
      sx={{ 
        height: '100vh',
        bgcolor: 'background.default',
        overflow: 'hidden'
      }}
    >
      {/* Error Display */}
      {error && (
        <Slide direction="down" in={!!error} mountOnEnter unmountOnExit>
          <Alert 
            severity="error" 
            sx={{ 
              position: 'absolute',
              top: 16,
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: theme.zIndex.snackbar,
              minWidth: 400,
              borderRadius: 2,
              boxShadow: 3
            }}
          >
            {error}
          </Alert>
        </Slide>
      )}

      {/* Main Content - Now handled by AgentSidebarNavigation */}
      {children}
    </Box>
  );
};

export default AgentEditorLayout;