import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
  Divider,
  useTheme,
  alpha,
  Fade,
  CircularProgress,
  Stack,
  Chip
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Google as GoogleIcon,
  AutoAwesome as AutoAwesomeIcon,
  RocketLaunch as RocketLaunchIcon,
  People as PeopleIcon
} from '@mui/icons-material';

const Signup = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { signup, signInWithGoogle, error: authError } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();

  const handleSignup = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (password !== confirmPassword) {
      return setError('Passwords do not match');
    }
    
    if (password.length < 6) {
      return setError('Password must be at least 6 characters');
    }

    setError('');
    setLoading(true);

    try {
      await signup(email, password);
      navigate('/agents'); // Redirect to agents page after signup
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      await signInWithGoogle();
      navigate('/agents'); // Redirect to agents page after signup
    } catch (error) {
      setError(error.message);
    } finally {
      setGoogleLoading(false);
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
                  <RocketLaunchIcon sx={{ mr: 1, fontSize: 'inherit' }} />
                  Start Building Today
                </Typography>
                <Typography 
                  variant="h5" 
                  color="text.secondary" 
                  sx={{ mb: 4, fontWeight: 400, lineHeight: 1.4 }}
                >
                  Join the AI revolution and create intelligent agents that transform your workflow
                </Typography>
                
                <Stack direction="row" spacing={2} sx={{ mb: 3, justifyContent: { xs: 'center', md: 'flex-start' } }}>
                  <Chip 
                    icon={<PeopleIcon />} 
                    label="500+ Users" 
                    variant="outlined" 
                    sx={{ fontWeight: 'bold' }}
                  />
                  <Chip 
                    icon={<AutoAwesomeIcon />} 
                    label="10K+ Agents" 
                    variant="outlined" 
                    sx={{ fontWeight: 'bold' }}
                  />
                </Stack>
                
                <Typography variant="body1" color="text.secondary" sx={{ maxWidth: '500px' }}>
                  Create your first AI agent in under 2 minutes. No coding required, just describe 
                  what you want and watch your ideas come to life with enterprise-grade security.
                </Typography>
              </Box>
            </Grid>

            {/* Right Side - Signup Form */}
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
                      <PersonAddIcon sx={{ fontSize: '2rem' }} />
                    </Box>
                    <Typography component="h2" variant="h4" sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                      Create Account
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', mt: 1 }}>
                      Start building AI agents today
                    </Typography>
                  </Box>

                  {(error || authError) && (
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
                      {error || authError}
                    </Alert>
                  )}

                  <Box component="form" onSubmit={handleSignup} sx={{ width: '100%' }}>
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
                        mb: 2,
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 2
                        }
                      }}
                    />
                    <TextField
                      margin="normal"
                      required
                      fullWidth
                      name="password"
                      label="Password (min. 6 characters)"
                      type="password"
                      id="password"
                      autoComplete="new-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      sx={{ 
                        mb: 2,
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 2
                        }
                      }}
                    />
                    <TextField
                      margin="normal"
                      required
                      fullWidth
                      name="confirmPassword"
                      label="Confirm Password"
                      type="password"
                      id="confirmPassword"
                      autoComplete="new-password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
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
                      disabled={loading || googleLoading}
                      endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <RocketLaunchIcon />}
                      sx={{ 
                        py: 1.5,
                        mb: 3,
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        borderRadius: 2
                      }}
                    >
                      {loading ? 'Creating Account...' : 'Create My Account'}
                    </Button>

                    <Divider sx={{ my: 3 }}>
                      <Typography variant="body2" color="text.secondary">
                        OR
                      </Typography>
                    </Divider>

                    <Button
                      fullWidth
                      variant="outlined"
                      size="large"
                      startIcon={<GoogleIcon />}
                      onClick={handleGoogleSignIn}
                      disabled={loading || googleLoading}
                      endIcon={googleLoading ? <CircularProgress size={20} color="inherit" /> : null}
                      sx={{ 
                        py: 1.5,
                        mb: 4,
                        fontWeight: 'bold',
                        borderRadius: 2,
                        borderColor: alpha(theme.palette.primary.main, 0.3),
                        '&:hover': {
                          borderColor: theme.palette.primary.main,
                          bgcolor: alpha(theme.palette.primary.main, 0.05)
                        }
                      }}
                    >
                      {googleLoading ? 'Connecting...' : 'Continue with Google'}
                    </Button>

                    <Grid container justifyContent="center">
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
                            Already have an account? Sign in
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

export default Signup; 