import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
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
  LockOutlined as LockOutlinedIcon,
  Google as GoogleIcon,
  AutoAwesome as AutoAwesomeIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { login, signInWithGoogle, error: authError, currentUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  
  // Get the path to redirect to after login (if any)
  const from = location.state?.from || '/agents';
  const loginMessage = location.state?.message;
  
  // Check if user is already logged in
  useEffect(() => {
    console.log("Login page mounted, checking auth state");
    console.log("Current user:", currentUser);
    console.log("Redirect path:", from);
    
    if (currentUser) {
      console.log("User already logged in, redirecting to:", from);
      navigate(from, { replace: true });
    }
  }, [currentUser, navigate, from]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log("Attempting login with email:", email);
      await login(email, password);
      console.log("Login successful, waiting for auth state update");
      // Don't navigate here - let the useEffect handle redirection when currentUser updates
    } catch (error) {
      console.error("Login error:", error);
      setError(error.message || "Failed to sign in");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      console.log("Attempting Google sign in");
      await signInWithGoogle();
      console.log("Google sign in successful, waiting for auth state update");
      // Don't navigate here - let the useEffect handle redirection when currentUser updates
    } catch (error) {
      console.error("Google sign in error:", error);
      setError(error.userFriendlyMessage || error.message || "Failed to sign in with Google");
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
                  <AutoAwesomeIcon sx={{ mr: 1, fontSize: 'inherit' }} />
                  Welcome Back
                </Typography>
                <Typography 
                  variant="h5" 
                  color="text.secondary" 
                  sx={{ mb: 4, fontWeight: 400, lineHeight: 1.4 }}
                >
                  Sign in to continue building amazing AI agents with Alchemist
                </Typography>
                
                <Stack direction="row" spacing={2} sx={{ mb: 3, justifyContent: { xs: 'center', md: 'flex-start' } }}>
                  <Chip 
                    icon={<SecurityIcon />} 
                    label="Enterprise Security" 
                    variant="outlined" 
                    sx={{ fontWeight: 'bold' }}
                  />
                  <Chip 
                    icon={<SpeedIcon />} 
                    label="Lightning Fast" 
                    variant="outlined" 
                    sx={{ fontWeight: 'bold' }}
                  />
                </Stack>
                
                <Typography variant="body1" color="text.secondary" sx={{ maxWidth: '500px' }}>
                  Join thousands of users who are building the future of AI with our intuitive platform. 
                  Create, deploy, and manage intelligent agents in minutes.
                </Typography>
              </Box>
            </Grid>

            {/* Right Side - Login Form */}
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
                      <LockOutlinedIcon sx={{ fontSize: '2rem' }} />
                    </Box>
                    <Typography component="h2" variant="h4" sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                      Sign In
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', mt: 1 }}>
                      {loginMessage || 'Access your AI agent dashboard'}
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

                  <Box component="form" onSubmit={handleLogin} sx={{ width: '100%' }}>
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
                      label="Password"
                      type="password"
                      id="password"
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
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
                      endIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
                      sx={{ 
                        py: 1.5,
                        mb: 3,
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        borderRadius: 2
                      }}
                    >
                      {loading ? 'Signing in...' : 'Sign In'}
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

                    <Grid container spacing={2} justifyContent="space-between">
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
                      <Grid item>
                        <Link to="/forgot-password" style={{ textDecoration: 'none' }}>
                          <Typography 
                            variant="body2" 
                            color="primary"
                            sx={{ 
                              fontWeight: 'bold',
                              '&:hover': { textDecoration: 'underline' }
                            }}
                          >
                            Forgot Password?
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

export default Login;
