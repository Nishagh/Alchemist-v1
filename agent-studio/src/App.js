import React, { useState, useEffect } from 'react';
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
import AgentEditor from './pages/AgentEditor';
import AgentsList from './pages/AgentsList';
import AgentTesting from './pages/AgentTesting';
import AgentAnalytics from './pages/AgentAnalytics';
import KnowledgeBase from './pages/KnowledgeBase';
import ApiIntegration from './pages/ApiIntegration';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import AgentCreationRedirect from './pages/AgentCreationRedirect';

// Black and White Material UI theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#000000',
      light: '#333333',
      dark: '#000000',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#666666',
      light: '#999999',
      dark: '#333333',
      contrastText: '#ffffff',
    },
    background: {
      default: '#ffffff',
      paper: '#ffffff',
    },
    text: {
      primary: '#000000',
      secondary: '#666666',
    },
    divider: '#e0e0e0',
    grey: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#eeeeee',
      300: '#e0e0e0',
      400: '#bdbdbd',
      500: '#9e9e9e',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
    success: {
      main: '#000000',
      light: '#333333',
      dark: '#000000',
    },
    warning: {
      main: '#666666',
      light: '#999999',
      dark: '#333333',
    },
    error: {
      main: '#000000',
      light: '#333333',
      dark: '#000000',
    },
    info: {
      main: '#666666',
      light: '#999999',
      dark: '#333333',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

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
  const location = useLocation();
  
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
      element: <LandingPage />
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
      path: '/agent-analytics/:agentId',
      element: <ProtectedRoute><AgentAnalytics /></ProtectedRoute>
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
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout>
        {routes}
      </Layout>
    </ThemeProvider>
  );
}

export default App;
