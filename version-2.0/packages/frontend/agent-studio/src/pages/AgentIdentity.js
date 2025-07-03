import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Breadcrumbs,
  Link,
  Alert,
  CircularProgress,
  Fab,
  Tooltip
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Psychology as IdentityIcon,
  NavigateNext as NextIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Import the enhanced identity panel
import AgentIdentityPanel from '../components/AgentEditor/AgentIdentity/AgentIdentityPanel';

// Import services
import { getAgentConfig } from '../services';

const IdentityContainer = styled(Container)(({ theme }) => ({
  paddingTop: theme.spacing(3),
  paddingBottom: theme.spacing(3),
  minHeight: '100vh',
  background: `linear-gradient(135deg, ${theme.palette.background.default} 0%, ${theme.palette.grey[50]} 100%)`
}));

const BackFab = styled(Fab)(({ theme }) => ({
  position: 'fixed',
  top: theme.spacing(10),
  left: theme.spacing(2),
  zIndex: theme.zIndex.fab
}));

const HeaderBox = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(4),
  padding: theme.spacing(3),
  background: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[2],
  border: `1px solid ${theme.palette.divider}`
}));

/**
 * Agent Identity Page
 * 
 * Dedicated page for comprehensive agent identity management and monitoring
 * with enhanced eA³ (Epistemic Autonomy, Accountability, Alignment) features
 */
const AgentIdentity = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const [agentData, setAgentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (agentId) {
      fetchAgentData();
    }
  }, [agentId]);

  const fetchAgentData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const agent = await getAgentConfig(agentId);
      setAgentData(agent);
    } catch (err) {
      console.error('Error fetching agent data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBackClick = () => {
    // Navigate back to agent dashboard or agents list
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/agents');
    }
  };

  if (loading) {
    return (
      <IdentityContainer>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
          <CircularProgress size={60} />
        </Box>
      </IdentityContainer>
    );
  }

  if (error) {
    return (
      <IdentityContainer>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load agent data: {error}
        </Alert>
      </IdentityContainer>
    );
  }

  return (
    <IdentityContainer maxWidth="xl">
      {/* Back Navigation */}
      <Tooltip title="Back to Dashboard">
        <BackFab
          color="primary"
          size="medium"
          onClick={handleBackClick}
        >
          <BackIcon />
        </BackFab>
      </Tooltip>

      {/* Header Section */}
      <HeaderBox>
        {/* Breadcrumbs */}
        <Breadcrumbs 
          separator={<NextIcon fontSize="small" />} 
          sx={{ mb: 2 }}
          aria-label="breadcrumb"
        >
          <Link
            color="inherit"
            href="/agents"
            onClick={(e) => {
              e.preventDefault();
              navigate('/agents');
            }}
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          >
            Agents
          </Link>
          <Link
            color="inherit"
            onClick={(e) => {
              e.preventDefault();
              navigate(`/agent-dashboard/${agentId}`);
            }}
            sx={{ cursor: 'pointer' }}
          >
            {agentData?.name || agentId}
          </Link>
          <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
            <IdentityIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Identity & eA³ Status
          </Typography>
        </Breadcrumbs>

        {/* Page Title */}
        <Typography variant="h3" component="h1" gutterBottom sx={{ 
          fontWeight: 600,
          background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Agent Identity Dashboard
        </Typography>

        <Typography variant="h6" color="text.secondary" paragraph>
          Comprehensive view of {agentData?.name || 'Agent'}'s narrative development, 
          eA³ metrics, and story coherence
        </Typography>

        {/* Agent Status Overview */}
        <Box display="flex" gap={2} flexWrap="wrap">
          <Typography variant="body2" sx={{ 
            px: 2, 
            py: 0.5, 
            backgroundColor: 'primary.main', 
            color: 'primary.contrastText',
            borderRadius: 1,
            fontWeight: 500
          }}>
            Status: {agentData?.status || 'Active'}
          </Typography>
          
          <Typography variant="body2" sx={{ 
            px: 2, 
            py: 0.5, 
            backgroundColor: 'success.main', 
            color: 'success.contrastText',
            borderRadius: 1,
            fontWeight: 500
          }}>
            eA³ Enabled
          </Typography>
          
          <Typography variant="body2" sx={{ 
            px: 2, 
            py: 0.5, 
            backgroundColor: 'info.main', 
            color: 'info.contrastText',
            borderRadius: 1,
            fontWeight: 500
          }}>
            Story Tracking: Active
          </Typography>
        </Box>
      </HeaderBox>

      {/* Main Identity Panel */}
      <Box sx={{ 
        background: 'white',
        borderRadius: 2,
        boxShadow: 2,
        border: '1px solid',
        borderColor: 'divider',
        overflow: 'hidden'
      }}>
        <AgentIdentityPanel 
          agentId={agentId}
          showPersonality={true}
          showNarrativeArc={true}
          showResponsibility={true}
          onError={(error) => setError(error)}
        />
      </Box>

      {/* Footer Information */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          This dashboard provides real-time monitoring of agent development through the 
          eA³ (Epistemic Autonomy, Accountability, Alignment) framework
        </Typography>
      </Box>
    </IdentityContainer>
  );
};

export default AgentIdentity;