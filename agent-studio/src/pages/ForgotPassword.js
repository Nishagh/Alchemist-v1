import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  Container,
  Grid,
  useTheme,
  alpha,
  Fade,
  CircularProgress,
  Stack,
  Chip
} from '@mui/material';
import {
  Password as PasswordIcon,
  AutoAwesome as AutoAwesomeIcon,
  Email as EmailIcon,
  Security as SecurityIcon
} from '@mui/icons-material';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const { resetPassword } = useAuth();
  const theme = useTheme();

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      await resetPassword(email);
      setMessage('Check your email for password reset instructions');
      setEmail('');
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box 
      sx={{ 
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.grey[100], 1)} 0%, ${alpha(theme.palette.grey[50], 1)} 100%)`,
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.02) 100%)'
        }
      }}
    >
      <Container component="main" maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <Fade in={true} timeout={800}>
          <Grid container spacing={8} alignItems="center">
            {/* Left Side - Branding */}
            <Grid item xs={12} md={6}>
              <Box sx={{ textAlign: { xs: 'center', md: 'left' }, mb: { xs: 4, md: 0 } }}>
                <Typography 
                  variant="h2" 
                  component="h1" 
                  sx={{ 
                    fontWeight: 900,
                    fontSize: { xs: '2rem', md: '3rem' },
                    color: theme.palette.text.primary,
                    mb: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: { xs: 'center', md: 'flex-start' }
                  }}
                >
                  <EmailIcon sx={{ mr: 1, fontSize: 'inherit' }} />
                  Forgot Password?
                </Typography>
                <Typography 
                  variant="h5" 
                  color="text.secondary" 
                  sx={{ mb: 4, fontWeight: 400, lineHeight: 1.4 }}
                >
                  No worries! We'll send you a reset link to get you back into your Alchemist account
                </Typography>
                
                <Stack direction="row" spacing={2} sx={{ mb: 3, justifyContent: { xs: 'center', md: 'flex-start' } }}>
                  <Chip 
                    icon={<SecurityIcon />} 
                    label="Secure Process" 
                    variant="outlined" 
                    sx={{ fontWeight: 'bold' }}
                  />
                  <Chip 
                    icon={<AutoAwesomeIcon />} 
                    label="Quick Recovery" 
                    variant="outlined" 
                    sx={{ fontWeight: 'bold' }}
                  />
                </Stack>
                
                <Typography variant="body1" color="text.secondary" sx={{ maxWidth: '500px' }}>
                  Enter your email address below and we'll send you a secure link to reset your password. 
                  You'll be back to building AI agents in no time!
                </Typography>
              </Box>
            </Grid>

            {/* Right Side - Reset Form */}
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 6, 
                    borderRadius: 3,
                    maxWidth: '450px',
                    width: '100%',
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    boxShadow: '0 8px 40px rgba(0, 0, 0, 0.08)',
                    background: alpha(theme.palette.background.paper, 0.9),
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <Box 
                    sx={{
                      mb: 4,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                    }}
                  >
                    <Box 
                      sx={{ 
                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                        color: theme.palette.primary.main,
                        p: 2,
                        borderRadius: 3,
                        mb: 2
                      }}
                    >
                      <PasswordIcon sx={{ fontSize: '2rem' }} />
                    </Box>
                    <Typography component="h2" variant="h4" sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                      Reset Password
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', mt: 1 }}>
                      Enter your email to receive reset instructions
                    </Typography>
                  </Box>

                  {error && (
                    <Alert 
                      severity="error" 
                      sx={{ 
                        width: '100%', 
                        mb: 3,
                        borderRadius: 2,
                        '& .MuiAlert-message': {
                          fontSize: '0.9rem'
                        }
                      }}
                    >
                      {error}
                    </Alert>
                  )}

                  {message && (
                    <Alert 
                      severity="success" 
                      sx={{ 
                        width: '100%', 
                        mb: 3,
                        borderRadius: 2,
                        '& .MuiAlert-message': {
                          fontSize: '0.9rem'
                        }
                      }}
                    >
                      {message}
                    </Alert>
                  )}

                  <Box component="form" onSubmit={handleResetPassword} sx={{ width: '100%' }}>
                    <TextField
                      margin="normal"
                      required
                      fullWidth
                      id="email"
                      label="Email Address"
                      name="email"
                      autoComplete="email"
                      autoFocus
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      sx={{ 
                        mb: 3,
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 2
                        }
                      }}
                    />
                    
                    <Button
                      type="submit"
                      fullWidth
                      variant="contained"
                      size="large"
                      disabled={loading}
                      endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <EmailIcon />}
                      sx={{ 
                        py: 1.5,
                        mb: 4,
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        borderRadius: 2
                      }}
                    >
                      {loading ? 'Sending...' : 'Send Reset Link'}
                    </Button>

                    <Grid container spacing={2} justifyContent="space-between">
                      <Grid item>
                        <Link to="/login" style={{ textDecoration: 'none' }}>
                          <Typography 
                            variant="body2" 
                            color="primary"
                            sx={{ 
                              fontWeight: 'bold',
                              '&:hover': { textDecoration: 'underline' }
                            }}
                          >
                            Back to Sign In
                          </Typography>
                        </Link>
                      </Grid>
                      <Grid item>
                        <Link to="/signup" style={{ textDecoration: 'none' }}>
                          <Typography 
                            variant="body2" 
                            color="primary"
                            sx={{ 
                              fontWeight: 'bold',
                              '&:hover': { textDecoration: 'underline' }
                            }}
                          >
                            Create Account
                          </Typography>
                        </Link>
                      </Grid>
                    </Grid>
                  </Box>
                </Paper>
              </Box>
            </Grid>
          </Grid>
        </Fade>
      </Container>
    </Box>
  );
};

export default ForgotPassword; 