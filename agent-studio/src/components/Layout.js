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
  Stack
} from '@mui/material';
import { 
  Add as AddIcon, 
  List as ListIcon, 
  AccountCircle as AccountCircleIcon,
  Menu as MenuIcon,
  AutoAwesome as AutoAwesomeIcon,
  RocketLaunch as RocketLaunchIcon,
  Dashboard as DashboardIcon
} from '@mui/icons-material';
import { useAuth } from '../utils/AuthContext';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();
  const [anchorEl, setAnchorEl] = React.useState(null);
  const theme = useTheme();
  
  // Show the app bar on all pages except landing page when user is not logged in
  const showFullAppBar = location.pathname !== '/' || currentUser;
  
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
      <AppBar 
        position="static" 
        elevation={0}
        sx={{
          background: location.pathname === '/' && currentUser
            ? `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`
            : location.pathname !== '/'
            ? `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`
            : 'transparent',
          borderBottom: showFullAppBar ? 'none' : `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
          backdropFilter: 'blur(10px)',
          position: location.pathname === '/' && currentUser ? 'absolute' : 'static',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1100
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <Typography 
            variant="h5" 
            component={Link} 
            to="/" 
            sx={{ 
              flexGrow: 1, 
              color: (location.pathname === '/' && currentUser) || location.pathname !== '/' ? 'white' : theme.palette.primary.main, 
              textDecoration: 'none',
              fontWeight: 900,
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <AutoAwesomeIcon sx={{ mr: 1, fontSize: '1.5rem' }} />
            Alchemist
          </Typography>
          
          {currentUser ? (
            <>
              <Stack direction="row" spacing={1} sx={{ display: { xs: 'none', md: 'flex' }, mr: 2 }}>
                <Button
                  component={Link}
                  to="/agents"
                  startIcon={<DashboardIcon />}
                  color="inherit"
                  variant={location.pathname === '/agents' ? 'contained' : 'text'}
                  sx={{
                    borderRadius: 2,
                    fontWeight: 'bold',
                    bgcolor: location.pathname === '/agents' ? alpha('rgba(255,255,255,0.2)', 0.3) : 'transparent',
                    '&:hover': {
                      bgcolor: alpha('rgba(255,255,255,0.1)', 0.2)
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
                    bgcolor: (location.pathname === '/agent-editor' || location.pathname.startsWith('/agent-editor/')) ? alpha('rgba(255,255,255,0.2)', 0.3) : 'transparent',
                    '&:hover': {
                      bgcolor: alpha('rgba(255,255,255,0.1)', 0.2)
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
                  color: (location.pathname === '/' && currentUser) || location.pathname !== '/' ? 'white' : theme.palette.primary.main,
                  bgcolor: alpha('rgba(255,255,255,0.1)', 0.1),
                  '&:hover': {
                    bgcolor: alpha('rgba(255,255,255,0.2)', 0.2)
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
                <Box sx={{ p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                    {currentUser.displayName || 'User'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {currentUser.email}
                  </Typography>
                </Box>
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
            <Stack direction="row" spacing={2}>
              <Button
                component={Link}
                to="/login"
                color="inherit"
                variant="text"
                sx={{ 
                  fontWeight: 'bold',
                  color: (location.pathname === '/' && currentUser) || location.pathname !== '/' ? 'white' : theme.palette.primary.main,
                  '&:hover': {
                    bgcolor: alpha('rgba(255,255,255,0.1)', 0.1)
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
                  bgcolor: (location.pathname === '/' && currentUser) || location.pathname !== '/' 
                    ? alpha('rgba(255,255,255,0.2)', 0.3) 
                    : theme.palette.primary.main,
                  color: 'white',
                  '&:hover': {
                    bgcolor: (location.pathname === '/' && currentUser) || location.pathname !== '/' 
                      ? alpha('rgba(255,255,255,0.3)', 0.4) 
                      : theme.palette.primary.dark
                  }
                }}
              >
                Sign Up
              </Button>
            </Stack>
          )}
        </Toolbar>
      </AppBar>
      
      <Box 
        sx={{ 
          mt: showFullAppBar && location.pathname !== '/' ? 3 : 0, 
          pt: location.pathname === '/' && currentUser ? 8 : 0,
          mb: 3, 
          px: location.pathname === '/' ? 0 : 3,
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
