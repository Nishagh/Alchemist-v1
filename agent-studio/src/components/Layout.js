import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Button, 
  Menu, 
  MenuItem,
  IconButton,
  Avatar,
  Divider,
  useTheme,
  alpha,
  Chip,
  Stack,
  Tooltip
} from '@mui/material';
import { 
  Add as AddIcon, 
  List as ListIcon, 
  AccountCircle as AccountCircleIcon,
  Menu as MenuIcon,
  RocketLaunch as RocketLaunchIcon,
  Dashboard as DashboardIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  CreditCard as CreditCardIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { useAuth } from '../utils/AuthContext';
import { useThemeMode } from '../App';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();
  const [anchorEl, setAnchorEl] = React.useState(null);
  const theme = useTheme();
  const { mode, toggleTheme } = useThemeMode();
  
  // Show the app bar on all pages except landing page for unauthenticated users
  const showFullAppBar = !(location.pathname === '/' && !currentUser);
  
  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };
  
  const handleLogout = async () => {
    try {
      await logout();
      handleClose();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed', error);
    }
  };
  
  return (
    <>
      {showFullAppBar && (
        <AppBar 
          position="static" 
          elevation={0}
          sx={{
            background: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
            borderBottom: `1px solid ${theme.palette.mode === 'dark' ? '#333333' : '#e5e7eb'}`,
            position: 'static',
            zIndex: 1100,
            boxShadow: 'none'
          }}
        >
        <Toolbar sx={{ py: 1 }}>
          <Typography 
            variant="h5" 
            component={Link} 
            to="/" 
            sx={{ 
              flexGrow: 1, 
              color: theme.palette.text.primary, 
              textDecoration: 'none',
              fontWeight: 900,
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24" style={{ marginRight: '0.5rem' }}>
              <path d="m19 9 1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25z"></path>
            </svg>
            Alchemist
          </Typography>
          
          {currentUser ? (
            <>
              <Stack direction="row" spacing={1} sx={{ display: { xs: 'none', md: 'flex' }, mr: 2 }}>
                <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
                  <IconButton
                    onClick={toggleTheme}
                    color="inherit"
                    sx={{
                      color: theme.palette.text.primary,
                      bgcolor: 'transparent',
                      border: `1px solid ${theme.palette.mode === 'dark' ? '#333333' : '#e5e7eb'}`,
                      '&:hover': {
                        bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                      }
                    }}
                  >
                    {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
                  </IconButton>
                </Tooltip>
                <Button
                  component={Link}
                  to="/dashboard"
                  startIcon={<DashboardIcon />}
                  color="inherit"
                  variant={location.pathname === '/dashboard' ? 'contained' : 'text'}
                  sx={{
                    borderRadius: 2,
                    fontWeight: 'bold',
                    bgcolor: location.pathname === '/dashboard' ? (theme.palette.mode === 'dark' ? '#ffffff' : '#000000') : 'transparent',
                    color: location.pathname === '/dashboard' ? (theme.palette.mode === 'dark' ? '#000000' : '#ffffff') : theme.palette.text.primary,
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                    }
                  }}
                >
                  Dashboard
                </Button>
                
                <Button
                  component={Link}
                  to="/agents"
                  startIcon={<ListIcon />}
                  color="inherit"
                  variant={location.pathname === '/agents' ? 'contained' : 'text'}
                  sx={{
                    borderRadius: 2,
                    fontWeight: 'bold',
                    bgcolor: location.pathname === '/agents' ? (theme.palette.mode === 'dark' ? '#ffffff' : '#000000') : 'transparent',
                    color: location.pathname === '/agents' ? (theme.palette.mode === 'dark' ? '#000000' : '#ffffff') : theme.palette.text.primary,
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                    }
                  }}
                >
                  My Agents
                </Button>
                
                <Button
                  component={Link}
                  to="/agent-editor"
                  startIcon={<RocketLaunchIcon />}
                  color="inherit"
                  variant={location.pathname === '/agent-editor' || location.pathname.startsWith('/agent-editor/') ? 'contained' : 'text'}
                  sx={{
                    borderRadius: 2,
                    fontWeight: 'bold',
                    bgcolor: (location.pathname === '/agent-editor' || location.pathname.startsWith('/agent-editor/')) ? (theme.palette.mode === 'dark' ? '#ffffff' : '#000000') : 'transparent',
                    color: (location.pathname === '/agent-editor' || location.pathname.startsWith('/agent-editor/')) ? (theme.palette.mode === 'dark' ? '#000000' : '#ffffff') : theme.palette.text.primary,
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                    }
                  }}
                >
                  Create Agent
                </Button>
              </Stack>
              
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                sx={{
                  color: theme.palette.text.primary,
                  bgcolor: 'transparent',
                  border: `1px solid ${theme.palette.mode === 'dark' ? '#333333' : '#e5e7eb'}`,
                  '&:hover': {
                    bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                  }
                }}
              >
                {currentUser.photoURL ? (
                  <Avatar 
                    src={currentUser.photoURL} 
                    alt={currentUser.email}
                    sx={{ width: 32, height: 32 }}
                  />
                ) : (
                  <AccountCircleIcon sx={{ fontSize: '2rem' }} />
                )}
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
                PaperProps={{
                  sx: {
                    borderRadius: 2,
                    mt: 1,
                    minWidth: 200,
                    boxShadow: '0 8px 30px rgba(0, 0, 0, 0.12)',
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
                  }
                }}
              >
                <Box sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                    {currentUser.displayName || 'User'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {currentUser.email}
                  </Typography>
                </Box>
                <Divider />
                <MenuItem 
                  onClick={() => {
                    handleClose();
                    navigate('/account');
                  }}
                  sx={{
                    py: 1.5,
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                    }
                  }}
                >
                  <PersonIcon sx={{ mr: 1 }} />
                  <Typography>My Account</Typography>
                </MenuItem>
                <MenuItem 
                  onClick={() => {
                    handleClose();
                    navigate('/credits');
                  }}
                  sx={{
                    py: 1.5,
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                    }
                  }}
                >
                  <CreditCardIcon sx={{ mr: 1 }} />
                  <Typography>Credits</Typography>
                </MenuItem>
                <Divider />
                <MenuItem 
                  onClick={handleLogout}
                  sx={{
                    py: 1.5,
                    '&:hover': {
                      bgcolor: alpha(theme.palette.error.main, 0.1)
                    }
                  }}
                >
                  <Typography color="error">Logout</Typography>
                </MenuItem>
              </Menu>
            </>
          ) : (
            <Stack direction="row" spacing={2} alignItems="center">
              <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
                <IconButton
                  onClick={toggleTheme}
                  color="inherit"
                  sx={{
                    color: theme.palette.text.primary,
                    bgcolor: 'transparent',
                    border: `1px solid ${theme.palette.mode === 'dark' ? '#333333' : '#e5e7eb'}`,
                    '&:hover': {
                      bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                    }
                  }}
                >
                  {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
              </Tooltip>
              <Button
                component={Link}
                to="/login"
                color="inherit"
                variant="text"
                sx={{ 
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  '&:hover': {
                    bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
                  }
                }}
              >
                Login
              </Button>
              <Button
                component={Link}
                to="/signup"
                variant="contained"
                sx={{ 
                  fontWeight: 'bold',
                  borderRadius: 2,
                  bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                  color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
                  '&:hover': {
                    bgcolor: theme.palette.mode === 'dark' ? '#e5e5e5' : '#333333'
                  }
                }}
              >
                Sign Up
              </Button>
            </Stack>
          )}
        </Toolbar>
        </AppBar>
      )}
      
      <Box 
        sx={{ 
          mt: showFullAppBar ? 3 : 0, 
          mb: 3, 
          px: showFullAppBar ? 3 : 0,
          width: '100%',
          maxWidth: '100%'
        }}
      >
        {children}
      </Box>
    </>
  );
};

export default Layout;
