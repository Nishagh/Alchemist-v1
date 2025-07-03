import React from 'react';
import { Box, Typography, Button, Card, CardContent } from '@mui/material';
import { Error as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 3,
          backgroundColor: '#fafafa'
        }}>
          <Card sx={{ maxWidth: 600, textAlign: 'center' }}>
            <CardContent sx={{ p: 4 }}>
              <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
              
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                Oops! Something went wrong
              </Typography>
              
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                We're sorry, but there was an error loading this page.
              </Typography>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <Box sx={{ 
                  textAlign: 'left', 
                  backgroundColor: '#f5f5f5', 
                  p: 2, 
                  borderRadius: 1, 
                  mb: 3,
                  maxHeight: 200,
                  overflow: 'auto'
                }}>
                  <Typography variant="caption" display="block" gutterBottom>
                    Error: {this.state.error.toString()}
                  </Typography>
                  {this.state.errorInfo.componentStack && (
                    <Typography variant="caption" display="block" sx={{ whiteSpace: 'pre-wrap' }}>
                      {this.state.errorInfo.componentStack}
                    </Typography>
                  )}
                </Box>
              )}
              
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={() => window.location.reload()}
                sx={{ mr: 2 }}
              >
                Refresh Page
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => window.location.href = '/'}
              >
                Go Home
              </Button>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;