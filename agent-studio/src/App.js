import React, { useState, useEffect, createContext, useContext } from 'react';
import { useRoutes, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { useAuth } from './utils/AuthContext';
import { debugAuthState } from './utils/AuthDebug';

// Import components
import Layout from './components/Layout';

// Import pages
import Dashboard from './pages/Dashboard';
import AgentEditor from './pages/AgentEditor';
import AgentsList from './pages/AgentsList';
import AgentTesting from './pages/AgentTesting';
import AgentAnalytics from './pages/AgentAnalytics';
import AgentDeployment from './pages/AgentDeployment';
import AgentIntegration from './pages/AgentIntegration';
import AgentDashboard from './pages/AgentDashboard';
import KnowledgeBase from './pages/KnowledgeBase';
import ApiIntegration from './pages/ApiIntegration';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import LandingPage from './pages/LandingPage';
import AgentCreationRedirect from './pages/AgentCreationRedirect';
import CreateAgent from './pages/CreateAgent';
import Credits from './pages/Credits';
import Account from './pages/Account';
import AgentProfile from './pages/AgentProfile';

// Theme Context
const ThemeContext = createContext();

export const useThemeMode = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeMode must be used within a ThemeProvider');
  }
  return context;
};

// Create comprehensive theme function
const createAppTheme = (mode) => {
  const isDark = mode === 'dark';
  
  return createTheme({
    palette: {
      mode,
      primary: {
        main: '#6366f1',
        light: '#818cf8',
        dark: '#4f46e5',
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#8b5cf6',
        light: '#a78bfa',
        dark: '#7c3aed',
        contrastText: '#ffffff',
      },
      background: {
        default: isDark ? '#000000' : '#ffffff',
        paper: isDark ? '#111111' : '#ffffff',
      },
      text: {
        primary: isDark ? '#ffffff' : '#000000',
        secondary: isDark ? '#a1a1aa' : '#666666',
        disabled: isDark ? '#71717a' : '#9ca3af',
      },
      divider: isDark ? '#333333' : '#e0e0e0',
      action: {
        active: isDark ? '#ffffff' : '#000000',
        hover: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
        selected: isDark ? 'rgba(255, 255, 255, 0.16)' : 'rgba(0, 0, 0, 0.08)',
        disabled: isDark ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.26)',
        disabledBackground: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.12)',
      },
      grey: {
        50: '#fafafa',
        100: '#f5f5f5',
        200: '#eeeeee',
        300: isDark ? '#333333' : '#e0e0e0',
        400: isDark ? '#555555' : '#bdbdbd',
        500: isDark ? '#777777' : '#9e9e9e',
        600: isDark ? '#999999' : '#757575',
        700: isDark ? '#bbbbbb' : '#616161',
        800: isDark ? '#dddddd' : '#424242',
        900: isDark ? '#ffffff' : '#212121',
      },
      success: {
        main: '#22c55e',
        light: '#4ade80',
        dark: '#16a34a',
        contrastText: '#ffffff',
      },
      warning: {
        main: '#f59e0b',
        light: '#fbbf24',
        dark: '#d97706',
        contrastText: '#ffffff',
      },
      error: {
        main: '#ef4444',
        light: '#f87171',
        dark: '#dc2626',
        contrastText: '#ffffff',
      },
      info: {
        main: '#3b82f6',
        light: '#60a5fa',
        dark: '#2563eb',
        contrastText: '#ffffff',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: { fontWeight: 700, color: isDark ? '#ffffff' : '#000000' },
      h2: { fontWeight: 600, color: isDark ? '#ffffff' : '#000000' },
      h3: { fontWeight: 600, color: isDark ? '#ffffff' : '#000000' },
      h4: { fontWeight: 600, color: isDark ? '#ffffff' : '#000000' },
      h5: { fontWeight: 600, color: isDark ? '#ffffff' : '#000000' },
      h6: { fontWeight: 600, color: isDark ? '#ffffff' : '#000000' },
      body1: { color: isDark ? '#ffffff' : '#000000' },
      body2: { color: isDark ? '#a1a1aa' : '#666666' },
      caption: { color: isDark ? '#a1a1aa' : '#666666' },
      overline: { color: isDark ? '#a1a1aa' : '#666666' },
    },
    components: {
      // Global component overrides
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: isDark ? '#000000' : '#ffffff',
            color: isDark ? '#ffffff' : '#000000',
            transition: 'background-color 0.3s ease, color 0.3s ease',
          },
        },
      },
      
      // Card Components
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            backgroundColor: isDark ? '#111111' : '#ffffff',
            border: `1px solid ${isDark ? '#333333' : '#e0e0e0'}`,
            boxShadow: isDark 
              ? '0 1px 3px rgba(255, 255, 255, 0.1)'
              : '0 1px 3px rgba(0, 0, 0, 0.1)',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: isDark 
                ? '0 4px 6px rgba(255, 255, 255, 0.15)'
                : '0 4px 6px rgba(0, 0, 0, 0.15)',
            },
          },
        },
      },
      
      // Paper Components
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            backgroundColor: isDark ? '#111111' : '#ffffff',
            color: isDark ? '#ffffff' : '#000000',
          },
        },
      },
      
      // AppBar
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? '#000000' : '#ffffff',
            color: isDark ? '#ffffff' : '#000000',
            borderBottom: `1px solid ${isDark ? '#333333' : '#e0e0e0'}`,
            boxShadow: 'none',
            backgroundImage: 'none',
          },
        },
      },
      
      // Button Components
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: 8,
          },
          containedPrimary: {
            backgroundColor: '#6366f1',
            color: '#ffffff',
            '&:hover': {
              backgroundColor: '#4f46e5',
            },
            '&:disabled': {
              backgroundColor: isDark ? '#374151' : '#d1d5db',
              color: isDark ? '#6b7280' : '#9ca3af',
            },
          },
          outlined: {
            borderColor: isDark ? '#374151' : '#d1d5db',
            color: isDark ? '#ffffff' : '#000000',
            '&:hover': {
              borderColor: isDark ? '#4b5563' : '#9ca3af',
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)',
            },
          },
        },
      },
      
      // Input Components
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              backgroundColor: isDark ? '#1f2937' : '#ffffff',
              '& fieldset': {
                borderColor: isDark ? '#374151' : '#d1d5db',
              },
              '&:hover fieldset': {
                borderColor: isDark ? '#4b5563' : '#9ca3af',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#6366f1',
              },
            },
            '& .MuiInputLabel-root': {
              color: isDark ? '#d1d5db' : '#374151',
            },
            '& .MuiOutlinedInput-input': {
              color: isDark ? '#ffffff' : '#000000',
            },
          },
        },
      },
      
      // List Components
      MuiListItem: {
        styleOverrides: {
          root: {
            '&:hover': {
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)',
            },
          },
        },
      },
      
      // Menu Components
      MuiMenu: {
        styleOverrides: {
          paper: {
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
          },
        },
      },
      
      MuiMenuItem: {
        styleOverrides: {
          root: {
            color: isDark ? '#ffffff' : '#000000',
            '&:hover': {
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
            },
            '&.Mui-selected': {
              backgroundColor: isDark ? 'rgba(99, 102, 241, 0.16)' : 'rgba(99, 102, 241, 0.08)',
              '&:hover': {
                backgroundColor: isDark ? 'rgba(99, 102, 241, 0.24)' : 'rgba(99, 102, 241, 0.12)',
              },
            },
          },
        },
      },
      
      // Chip Components
      MuiChip: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? '#374151' : '#f3f4f6',
            color: isDark ? '#ffffff' : '#000000',
          },
          filled: {
            '&.MuiChip-colorPrimary': {
              backgroundColor: '#6366f1',
              color: '#ffffff',
            },
            '&.MuiChip-colorSecondary': {
              backgroundColor: '#8b5cf6',
              color: '#ffffff',
            },
          },
        },
      },
      
      // Dialog Components
      MuiDialog: {
        styleOverrides: {
          paper: {
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            color: isDark ? '#ffffff' : '#000000',
          },
        },
      },
      
      // Divider
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: isDark ? '#374151' : '#e5e7eb',
          },
        },
      },
      
      // Tooltip
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: isDark ? '#374151' : '#1f2937',
            color: isDark ? '#ffffff' : '#ffffff',
          },
        },
      },
      
      // Tab Components
      MuiTab: {
        styleOverrides: {
          root: {
            color: isDark ? '#9ca3af' : '#6b7280',
            '&.Mui-selected': {
              color: '#6366f1',
            },
          },
        },
      },
      
      // Table Components
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderBottom: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
            color: isDark ? '#ffffff' : '#000000',
          },
          head: {
            backgroundColor: isDark ? '#111827' : '#f9fafb',
            color: isDark ? '#ffffff' : '#000000',
            fontWeight: 600,
          },
        },
      },
      
      // Switch Components
      MuiSwitch: {
        styleOverrides: {
          switchBase: {
            '&.Mui-checked': {
              color: '#6366f1',
              '& + .MuiSwitch-track': {
                backgroundColor: '#6366f1',
              },
            },
          },
          track: {
            backgroundColor: isDark ? '#374151' : '#d1d5db',
          },
        },
      },
      
      // Checkbox Components
      MuiCheckbox: {
        styleOverrides: {
          root: {
            color: isDark ? '#9ca3af' : '#6b7280',
            '&.Mui-checked': {
              color: '#6366f1',
            },
          },
        },
      },
      
      // Radio Components
      MuiRadio: {
        styleOverrides: {
          root: {
            color: isDark ? '#9ca3af' : '#6b7280',
            '&.Mui-checked': {
              color: '#6366f1',
            },
          },
        },
      },
    },
  });
};

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { currentUser, loading } = useAuth();
  const location = useLocation();
  
  // Debug protected route
  useEffect(() => {
    console.log(`ProtectedRoute check for path: ${location.pathname}`);
    console.log(`Auth state: ${currentUser ? 'Authenticated' : 'Not authenticated'}`);
    console.log(`Loading: ${loading}`);
    
    if (!loading && !currentUser) {
      console.log(`Redirecting to login from ${location.pathname}`);
    }
  }, [currentUser, loading, location.pathname]);
  
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }
  
  if (!currentUser) {
    // Pass the current location to the Login page so it can redirect back after authentication
    return <Navigate to="/login" state={{ from: location.pathname }} />;
  }
  
  return children;
};

function App() {
  const { loading: authLoading, currentUser } = useAuth();
  const [appLoading, setAppLoading] = useState(true);
  const [themeMode, setThemeMode] = useState(() => {
    // Get theme from localStorage or default to dark
    const savedTheme = localStorage.getItem('themeMode');
    return savedTheme || 'dark';
  });
  const location = useLocation();
  
  const theme = createAppTheme(themeMode);
  
  const toggleTheme = () => {
    const newMode = themeMode === 'dark' ? 'light' : 'dark';
    setThemeMode(newMode);
    localStorage.setItem('themeMode', newMode);
    document.body.setAttribute('data-theme', newMode);
  };
  
  // Set initial theme attribute on body
  useEffect(() => {
    document.body.setAttribute('data-theme', themeMode);
  }, [themeMode]);
  
  const themeContextValue = {
    mode: themeMode,
    toggleTheme,
  };
  
  // Run auth debugging on mount and when auth state changes
  useEffect(() => {
    const runDebug = async () => {
      await debugAuthState();
    };
    
    runDebug();
  }, [currentUser]);
  
  // Log navigation
  useEffect(() => {
    console.log(`Navigation to: ${location.pathname}`);
  }, [location.pathname]);
  
  useEffect(() => {
    if (!authLoading) {
      console.log(`Auth loading complete. User authenticated: ${!!currentUser}`);
      setAppLoading(false);
    }
  }, [authLoading, currentUser]);

  // Define routes using useRoutes hook - must be at the same level as other hooks
  const routes = useRoutes([
    {
      path: '/',
      element: currentUser ? <ProtectedRoute><Dashboard /></ProtectedRoute> : <LandingPage />
    },
    {
      path: '/dashboard',
      element: <ProtectedRoute><Dashboard /></ProtectedRoute>
    },
    {
      path: '/login',
      element: <Login />
    },
    {
      path: '/signup',
      element: <Signup />
    },
    {
      path: '/forgot-password',
      element: <ForgotPassword />
    },
    {
      path: '/agent-creation-redirect',
      element: <ProtectedRoute><AgentCreationRedirect /></ProtectedRoute>
    },
    {
      path: '/agents',
      element: <ProtectedRoute><AgentsList /></ProtectedRoute>
    },
    {
      path: '/agent/:agentId',
      element: <ProtectedRoute><AgentDashboard /></ProtectedRoute>
    },
    {
      path: '/create-agent',
      element: <ProtectedRoute><CreateAgent /></ProtectedRoute>
    },
    {
      path: '/agent-editor',
      element: <ProtectedRoute><AgentEditor /></ProtectedRoute>
    },
    {
      path: '/agent-editor/:agentId',
      element: <ProtectedRoute><AgentEditor /></ProtectedRoute>
    },
    {
      path: '/knowledge-base/:agentId',
      element: <ProtectedRoute><KnowledgeBase /></ProtectedRoute>
    },
    {
      path: '/api-integration/:agentId',
      element: <ProtectedRoute><ApiIntegration /></ProtectedRoute>
    },
    {
      path: '/agent-testing/:agentId',
      element: <ProtectedRoute><AgentTesting /></ProtectedRoute>
    },
    {
      path: '/agent-fine-tuning/:agentId',
      element: <ProtectedRoute><AgentEditor /></ProtectedRoute>
    },
    {
      path: '/agent-deployment/:agentId',
      element: <ProtectedRoute><AgentDeployment /></ProtectedRoute>
    },
    {
      path: '/agent-integration/:agentId',
      element: <ProtectedRoute><AgentIntegration /></ProtectedRoute>
    },
    {
      path: '/agent-analytics/:agentId',
      element: <ProtectedRoute><AgentAnalytics /></ProtectedRoute>
    },
    {
      path: '/billing',
      element: <ProtectedRoute><Credits /></ProtectedRoute>
    },
    {
      path: '/credits',
      element: <ProtectedRoute><Credits /></ProtectedRoute>
    },
    {
      path: '/account',
      element: <ProtectedRoute><Account /></ProtectedRoute>
    },
    {
      path: '/agent-profile/:agentId',
      element: <ProtectedRoute><AgentProfile /></ProtectedRoute>
    },
  ]);

  // Show loading spinner while initializing
  if (appLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <ThemeContext.Provider value={themeContextValue}>
      <ThemeProvider theme={theme}>
        <CssBaseline enableColorScheme />
        <Layout>
          {routes}
        </Layout>
      </ThemeProvider>
    </ThemeContext.Provider>
  );
}

export default App;
