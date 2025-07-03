import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Avatar,
  Typography,
  Chip,
  LinearProgress,
  Divider,
  Button,
  Tab,
  Tabs,
  Badge,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Person,
  WorkHistory,
  Psychology,
  TrendingUp,
  Star,
  Timeline,
  Assignment,
  Visibility,
  AttachMoney,
  Speed,
  Shield,
  AutoGraph,
  SmartToy,
  CheckCircle,
  Warning,
  Warning as WarningIcon,
  Error,
  Info,
  BusinessCenter,
  AccessTime,
  ThumbUp,
  Security,
  Assessment,
  History,
  TrendingDown,
  MonetizationOn,
  Savings,
  PieChart,
  BarChart,
  Analytics,
  AccountBalance,
  ArrowBack as ArrowBackIcon,
  Edit,
  Settings,
  Delete as DeleteIcon,
  Launch as LaunchIcon,
  MoreVert as MoreVertIcon,
  BugReport as BugReportIcon,
  Analytics as AnalyticsIcon,
  History as DeploymentHistoryIcon,
  CloudQueue as CloudIcon,
  Publish as PublishIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  PhotoCamera as PhotoCameraIcon,
  Refresh as RefreshIcon,
  Palette as PaletteIcon
} from '@mui/icons-material';
import { workforceService } from '../services/workforce/workforceService';
import { useAuth } from '../utils/AuthContext';
import { db } from '../utils/firebase';
import { doc, getDoc } from 'firebase/firestore';
import { lifecycleService } from '../services/lifecycle/lifecycleService';
import AgentTesting from './AgentTesting';
import AgentAnalytics from './AgentAnalytics';
import { collection, query, where, orderBy, onSnapshot } from 'firebase/firestore';
import deploymentService from '../services/deployment/deploymentService';
import { api } from '../services/config/apiConfig';
import { markAgentAsDeleted } from '../services/agents/agentService';

// Helper functions
const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'active': return 'success';
    case 'idle': return 'warning';
    case 'offline': return 'error';
    default: return 'default';
  }
};

const getPerformanceColor = (value, thresholds = [90, 70]) => {
  if (value >= thresholds[0]) return 'success.main';
  if (value >= thresholds[1]) return 'warning.main';
  return 'error.main';
};

const AgentProfile = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [agent, setAgent] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [workforceData, setWorkforceData] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [costMetrics, setCostMetrics] = useState(null);
  const [lifecycleEvents, setLifecycleEvents] = useState([]);
  const [lifecycleStats, setLifecycleStats] = useState(null);
  const [actionMenuAnchor, setActionMenuAnchor] = useState(null);
  const [deploymentHistory, setDeploymentHistory] = useState([]);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentProgress, setDeploymentProgress] = useState(null);
  const [deploymentSubscription, setDeploymentSubscription] = useState(null);
  
  // Lazy loading states for different tabs
  const [loadedTabs, setLoadedTabs] = useState(new Set([0])); // Identity tab loaded by default
  const [tabLoading, setTabLoading] = useState({});
  const [isGeneratingProfilePicture, setIsGeneratingProfilePicture] = useState(false);
  const [profilePictureStyle, setProfilePictureStyle] = useState('professional');
  const [showStyleSelector, setShowStyleSelector] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Handle back navigation
  const handleBackClick = () => {
    navigate('/');
  };

  // Handle action menu
  const handleActionMenu = (event) => {
    setActionMenuAnchor(event.currentTarget);
  };

  const closeActionMenu = () => {
    setActionMenuAnchor(null);
  };

  // Handle agent actions
  const handleEditAgent = () => {
    navigate(`/agent-editor/${agentId}`);
    closeActionMenu();
  };

  const handleDeployAgent = async () => {
    try {
      setIsDeploying(true);
      setDeploymentProgress({ status: 'initiating', message: 'Starting deployment...' });
      closeActionMenu();
      
      // Deploy the agent
      const result = await deploymentService.deployAgent(agentId);
      
      // Start polling for deployment status
      await deploymentService.pollDeploymentStatus(
        result.deployment_id,
        (progress) => {
          setDeploymentProgress(progress);
        },
        { timeoutMs: 600000 } // 10 minutes
      );
      
      setDeploymentProgress({ status: 'completed', message: 'Deployment completed successfully!' });
      
      // Refresh agent profile to show updated status
      await fetchAgentProfile();
      
      setTimeout(() => {
        setIsDeploying(false);
        setDeploymentProgress(null);
      }, 3000);
      
    } catch (error) {
      console.error('Deployment failed:', error);
      setDeploymentProgress({ 
        status: 'failed', 
        message: error.message || 'Deployment failed' 
      });
      
      setTimeout(() => {
        setIsDeploying(false);
        setDeploymentProgress(null);
      }, 5000);
    }
  };

  const handleDeleteAgent = () => {
    setShowDeleteDialog(true);
    closeActionMenu();
  };

  const confirmDeleteAgent = async () => {
    try {
      setIsDeleting(true);
      
      // Mark agent as deleted (soft delete)
      await markAgentAsDeleted(agentId);
      
      console.log('Agent successfully marked as deleted:', agentId);
      
      // Close dialog
      setShowDeleteDialog(false);
      
      // Navigate back to agents list after a short delay
      setTimeout(() => {
        navigate('/');
      }, 1000);
      
    } catch (error) {
      console.error('Error deleting agent:', error);
      alert('Failed to delete agent: ' + error.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDeleteAgent = () => {
    setShowDeleteDialog(false);
  };

  const handleGenerateProfilePicture = async (style = 'professional') => {
    try {
      setIsGeneratingProfilePicture(true);
      setShowStyleSelector(false);
      
      console.log('Generating profile picture for agent:', agentId, 'with style:', style);
      
      // Generate profile picture via agent-engine
      const generateResponse = await api.post('/api/agents/generate-profile-picture', {
        agent_id: agentId,
        style: style,
        size: '1024x1024',
        quality: 'standard'
      });
      
      if (!generateResponse.data || generateResponse.data.status !== 'success') {
        throw new Error(generateResponse.data?.message || 'Failed to generate profile picture');
      }
      
      // Save the generated image to Firebase Storage
      const saveResponse = await api.post('/api/agents/save-profile-picture', {
        agent_id: agentId,
        image_url: generateResponse.data.image_url,
        style: style
      });
      
      if (!saveResponse.data || saveResponse.data.status !== 'success') {
        throw new Error(saveResponse.data?.message || 'Failed to save profile picture');
      }
      
      console.log('Profile picture generated and saved successfully');
      
      // Update the agent state with new profile picture
      setAgent(prev => ({
        ...prev,
        profile_picture_url: saveResponse.data.profile_picture_url
      }));
      
      // Refresh agent profile to get updated data
      await fetchAgentProfile();
      
    } catch (error) {
      console.error('Error generating profile picture:', error);
      // You could add a notification system here
      alert('Failed to generate profile picture: ' + error.message);
    } finally {
      setIsGeneratingProfilePicture(false);
    }
  };

  const getAvailableStyles = () => {
    return [
      { id: 'professional', name: 'Professional', description: 'Corporate headshot style' },
      { id: 'friendly', name: 'Friendly', description: 'Warm and approachable' },
      { id: 'creative', name: 'Creative', description: 'Artistic composition' },
      { id: 'futuristic', name: 'Futuristic', description: 'High-tech aesthetic' },
      { id: 'minimalist', name: 'Minimalist', description: 'Clean and simple' }
    ];
  };

  useEffect(() => {
    if (currentUser && agentId) {
      fetchBasicAgentData();
    } else {
      // Set loading to false when prerequisites aren't met
      setDataLoading(false);
    }
    
    // Cleanup subscription on unmount
    return () => {
      if (deploymentSubscription) {
        deploymentSubscription();
      }
    };
  }, [agentId, currentUser]);

  // Handle tab change with lazy loading
  const handleTabChange = async (event, newValue) => {
    setActiveTab(newValue);
    
    // Load tab data if not already loaded
    if (!loadedTabs.has(newValue)) {
      await loadTabData(newValue);
    }
  };

  const fetchBasicAgentData = async () => {
    try {
      setDataLoading(true);
      
      // First, get basic agent data from Firestore
      const agentDocRef = doc(db, 'agents', agentId);
      const agentDoc = await getDoc(agentDocRef);
      
      let basicAgentData = null;
      if (agentDoc.exists()) {
        basicAgentData = { id: agentDoc.id, ...agentDoc.data() };
      }
      
      // Set initial agent data with basic information only
      const initialAgent = {
        id: agentId,
        name: basicAgentData?.name || `Agent ${agentId.slice(-4)}`,
        role: 'AI Specialist',
        department: 'General',
        status: basicAgentData?.status || 'draft',
        experience: 0,
        totalTasks: 0,
        successRate: 0,
        avgResponseTime: 0,
        userSatisfaction: 0,
        reliability: 0,
        totalCosts: 0,
        monthlyCosts: 0,
        costPerTask: 0,
        efficiency: 0,
        roi: 0,
        skills: ['Problem Solving', 'Communication'],
        specializations: ['Customer Support', 'Data Analysis'],
        lastActive: new Date().toISOString(),
        joinDate: basicAgentData?.created_at || new Date().toISOString(),
        profile_picture_url: basicAgentData?.profile_picture_url,
        isDeployed: basicAgentData?.status === 'deployed' || basicAgentData?.status === 'active',
        hasConversations: false,
        showMetrics: false
      };
      
      setAgent(initialAgent);
      
    } catch (error) {
      console.error('Error fetching basic agent data:', error);
      setAgent({
        id: agentId,
        name: `Agent ${agentId.slice(-4)}`,
        status: 'Error loading data',
        isDeployed: false,
        hasConversations: false,
        showMetrics: false
      });
    } finally {
      setDataLoading(false);
    }
  };

  const loadTabData = async (tabIndex) => {
    try {
      setTabLoading(prev => ({ ...prev, [tabIndex]: true }));
      
      // Get tab name based on agent metrics availability and deletion status
      const getTabType = (index) => {
        const isDeleted = agent?.status === 'deleted';
        
        if (isDeleted) {
          // For deleted agents: Identity(0), Deployment(1), Life Journey(2)
          const tabMap = { 0: 'identity', 1: 'deployment', 2: 'lifecycle' };
          return tabMap[index];
        } else if (!agent?.showMetrics) {
          // For agents without metrics: Identity(0), Testing(1), Analytics(2), Deployment(3), Life Journey(4)
          const tabMap = { 0: 'identity', 1: 'testing', 2: 'analytics', 3: 'deployment', 4: 'lifecycle' };
          return tabMap[index];
        } else {
          // For agents with metrics: Identity(0), Performance(1), Cost(2), Accountability(3), Testing(4), Analytics(5), Deployment(6), Life Journey(7)
          const tabMap = { 0: 'identity', 1: 'performance', 2: 'cost', 3: 'accountability', 4: 'testing', 5: 'analytics', 6: 'deployment', 7: 'lifecycle' };
          return tabMap[index];
        }
      };
      
      const tabType = getTabType(tabIndex);
      
      switch (tabType) {
        case 'identity':
          // Identity tab - load workforce data if not already loaded
          if (!workforceData) {
            const agentData = await workforceService.getAgentWorkforceData(agentId, currentUser.uid);
            setWorkforceData(agentData);
            
            // Update agent with detailed information
            const isDeployed = agent.status === 'deployed' || agent.status === 'active';
            const hasConversations = agentData?.conversations?.length > 0;
            const showMetrics = isDeployed && hasConversations;
            
            setAgent(prev => ({
              ...prev,
              skills: agentData.identity?.dominant_personality_traits || prev.skills,
              specializations: agentData.identity?.primary_goals || prev.specializations,
              hasConversations,
              showMetrics
            }));
          }
          break;
          
        case 'performance':
        case 'cost':
        case 'accountability':
          // Load workforce data and calculate metrics if not already loaded
          if (!workforceData || !performanceMetrics) {
            const agentData = await workforceService.getAgentWorkforceData(agentId, currentUser.uid);
            setWorkforceData(agentData);
            
            const performance = workforceService.calculatePerformanceMetrics(agentData);
            const costs = workforceService.calculateUsageCosts(agentData, performance);
            const experience = workforceService.calculateExperience(agentData);
            const efficiency = workforceService.calculateCostEfficiency(agentData);
            
            setPerformanceMetrics(performance);
            setCostMetrics(costs);
            
            // Update agent with calculated metrics
            setAgent(prev => ({
              ...prev,
              experience: experience.years,
              totalTasks: performance.totalTasks,
              successRate: performance.successRate,
              avgResponseTime: performance.averageResponseTime,
              userSatisfaction: performance.userSatisfactionScore,
              reliability: performance.reliabilityScore,
              totalCosts: costs.totalCost,
              monthlyCosts: costs.monthlyAverage,
              costPerTask: costs.costPerTask,
              efficiency: efficiency.efficiency,
              roi: efficiency.roi
            }));
          }
          break;
          
        case 'deployment':
          // Load deployment history if not already loaded
          if (deploymentHistory.length === 0) {
            const deployments = await deploymentService.listDeployments({ agentId, limit: 20 });
            setDeploymentHistory(deployments.deployments || []);
            
            // Subscribe to deployment updates
            if (deploymentSubscription) {
              deploymentSubscription();
            }
            const unsubscribe = deploymentService.subscribeToDeploymentUpdates(
              agentId,
              (deployments) => {
                setDeploymentHistory(deployments);
              },
              (error) => {
                console.error('Deployment subscription error:', error);
              }
            );
            setDeploymentSubscription(() => unsubscribe);
          }
          break;
          
        case 'lifecycle':
          // Load lifecycle events if not already loaded
          if (lifecycleEvents.length === 0) {
            const events = await lifecycleService.getAgentLifecycleEvents(agentId);
            const formattedEvents = events.map(event => lifecycleService.formatEventForDisplay(event));
            const stats = lifecycleService.getLifecycleStats(events);
            
            setLifecycleEvents(formattedEvents);
            setLifecycleStats(stats);
          }
          break;
          
        // Analytics and Testing tabs manage their own data loading
        case 'analytics':
        case 'testing':
        default:
          break;
      }
      
      // Mark tab as loaded
      setLoadedTabs(prev => new Set([...prev, tabIndex]));
      
    } catch (error) {
      console.error(`Error loading tab ${tabIndex} data:`, error);
    } finally {
      setTabLoading(prev => ({ ...prev, [tabIndex]: false }));
    }
  };
  
  // Keep the original fetchAgentProfile for compatibility (used by deployment)
  const fetchAgentProfile = async () => {
    await fetchBasicAgentData();
    // Load identity tab data by default
    await loadTabData(0);
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );


  // Removed the blocking loading check - page shows immediately

  // Show loading state
  if (dataLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (!currentUser) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="warning">Please log in to view agent profile</Alert>
      </Container>
    );
  }

  if (!agent) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Agent not found</Alert>
      </Container>
    );
  }

  // Check if agent is deleted
  const isDeleted = agent.status === 'deleted';

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Back Navigation */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton onClick={handleBackClick} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5" fontWeight="bold">
            Agent Profile
          </Typography>
        </Box>
        
        {/* Agent Management Actions */}
        {isDeleted ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label="ARCHIVED" 
              color="error" 
              variant="filled"
              sx={{ fontWeight: 'bold' }}
            />
            <Typography variant="body2" color="text.secondary">
              This agent has been deleted and is no longer active
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Edit />}
              onClick={handleEditAgent}
            >
              Edit Agent
            </Button>
            <Button
              variant="contained"
              startIcon={isDeploying ? <CircularProgress size={16} /> : <LaunchIcon />}
              onClick={handleDeployAgent}
              color="primary"
              disabled={isDeploying}
            >
              {isDeploying ? 'Deploying...' : 'Deploy'}
            </Button>
            <IconButton onClick={handleActionMenu}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        )}
      </Box>

      {/* Agent Header Card */}
      <Card sx={{ 
        mb: 3,
        ...(isDeleted && {
          border: 2,
          borderColor: 'error.light',
          bgcolor: 'error.50',
          opacity: 0.8
        })
      }}>
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item>
              <Box sx={{ position: 'relative', display: 'inline-block' }}>
                <Avatar
                  src={agent.profile_picture_url}
                  sx={{
                    width: 100,
                    height: 100,
                    bgcolor: dataLoading ? 'grey.300' : 'primary.main',
                    fontSize: '2.5rem',
                    opacity: dataLoading ? 0.7 : 1
                  }}
                >
                  {!agent.profile_picture_url && <SmartToy sx={{ fontSize: '3rem' }} />}
                </Avatar>
                
                {/* Profile Picture Generation Button */}
                <Box sx={{ position: 'absolute', bottom: -8, right: -8 }}>
                  <IconButton
                    size="small"
                    onClick={() => setShowStyleSelector(true)}
                    disabled={isGeneratingProfilePicture}
                    sx={{
                      bgcolor: 'primary.main',
                      color: 'white',
                      '&:hover': { bgcolor: 'primary.dark' },
                      width: 32,
                      height: 32
                    }}
                  >
                    {isGeneratingProfilePicture ? (
                      <CircularProgress size={16} color="inherit" />
                    ) : (
                      <PhotoCameraIcon sx={{ fontSize: 16 }} />
                    )}
                  </IconButton>
                </Box>
              </Box>
            </Grid>
            
            <Grid item xs>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography 
                  variant="h4" 
                  fontWeight="bold" 
                  sx={{ 
                    opacity: dataLoading ? 0.7 : 1,
                    ...(isDeleted && {
                      textDecoration: 'line-through',
                      color: 'text.secondary'
                    })
                  }}
                >
                  {agent.name}
                  {dataLoading && <Typography component="span" sx={{ ml: 1, fontSize: '0.5em' }}>Loading...</Typography>}
                </Typography>
                <Chip 
                  label={isDeleted ? 'DELETED' : agent.status} 
                  color={isDeleted ? 'error' : getStatusColor(agent.status)}
                  sx={{ fontWeight: 'bold', opacity: dataLoading ? 0.7 : 1 }}
                />
              </Box>
              
              <Typography variant="h6" color="text.secondary" sx={{ mb: 2, opacity: dataLoading ? 0.7 : 1 }}>
                {agent.role} • {agent.department}
              </Typography>
              
              {agent && agent.showMetrics ? (
                <Grid container spacing={3}>
                  <Grid item>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" fontWeight="bold" sx={{ opacity: dataLoading ? 0.5 : 1 }}>
                        {dataLoading ? '—' : `${agent.experience}y`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Experience
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" fontWeight="bold" color={dataLoading ? 'text.disabled' : getPerformanceColor(agent.successRate)} sx={{ opacity: dataLoading ? 0.5 : 1 }}>
                        {dataLoading ? '—' : `${agent.successRate}%`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Success Rate
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" fontWeight="bold" sx={{ opacity: dataLoading ? 0.5 : 1 }}>
                        {dataLoading ? '—' : agent.totalTasks}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Tasks Completed
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" fontWeight="bold" color={dataLoading ? 'text.disabled' : 'warning.main'} sx={{ opacity: dataLoading ? 0.5 : 1 }}>
                        {dataLoading ? '—' : `₹${agent.totalCosts?.toLocaleString('en-IN') || '0'}`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Total Usage Cost
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
                    {isDeleted ? 'Agent has been deleted' : 
                     agent?.status === 'draft' ? 'Agent is in draft mode' : 'Agent not yet deployed'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {isDeleted ? 'No longer active and cannot be deployed' :
                     'Deploy this agent to see performance metrics and usage statistics'}
                  </Typography>
                </Box>
              )}
            </Grid>

            {agent && agent.showMetrics && (
              <Grid item>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.50', opacity: dataLoading ? 0.7 : 1 }}>
                  <Typography variant="h3" fontWeight="bold" color="primary">
                    {dataLoading ? '—' : agent.reliability}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Reliability Score
                  </Typography>
                </Paper>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      {/* Deletion Information for Deleted Agents */}
      {isDeleted && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body1" fontWeight="bold" gutterBottom>
            This agent has been deleted
          </Typography>
          {agent.deleted_at && (
            <Typography variant="body2">
              Deleted on: {new Date(agent.deleted_at).toLocaleDateString()} at {new Date(agent.deleted_at).toLocaleTimeString()}
            </Typography>
          )}
          <Typography variant="body2" sx={{ mt: 1 }}>
            This agent is archived and cannot be modified, deployed, or used for testing. 
            Only identity information and historical data are available for reference.
          </Typography>
        </Alert>
      )}

      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<Person />} label="Identity & Skills" />
          {agent && agent.showMetrics && !isDeleted && <Tab icon={<Assessment />} label="Performance" />}
          {agent && agent.showMetrics && !isDeleted && <Tab icon={<MonetizationOn />} label="Cost Analysis" />}
          {agent && agent.showMetrics && !isDeleted && <Tab icon={<Shield />} label="Accountability" />}
          {!isDeleted && <Tab icon={<BugReportIcon />} label="Testing" />}
          {!isDeleted && <Tab icon={<AnalyticsIcon />} label="Analytics" />}
          <Tab icon={<DeploymentHistoryIcon />} label="Deployment History" />
          <Tab icon={<History />} label="Life Journey" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={activeTab} index={0}>
        {tabLoading[0] ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <IdentityTab agent={agent} />
        )}
      </TabPanel>
      
      {agent && agent.showMetrics && (
        <>
          <TabPanel value={activeTab} index={1}>
            {tabLoading[1] ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <PerformanceTab agent={agent} />
            )}
          </TabPanel>
          
          <TabPanel value={activeTab} index={2}>
            {tabLoading[2] ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <CostAnalysisTab agent={agent} />
            )}
          </TabPanel>
          
          <TabPanel value={activeTab} index={3}>
            {tabLoading[3] ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <AccountabilityTab agent={agent} />
            )}
          </TabPanel>
        </>
      )}
      
      {/* Testing Tab - Not available for deleted agents */}
      {!isDeleted && (
        <TabPanel value={activeTab} index={agent && agent.showMetrics ? 4 : 1}>
          {tabLoading[agent && agent.showMetrics ? 4 : 1] ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <AgentTesting agentId={agentId} embedded={true} />
          )}
        </TabPanel>
      )}
      
      {/* Analytics Tab - Not available for deleted agents */}
      {!isDeleted && (
        <TabPanel value={activeTab} index={agent && agent.showMetrics ? 5 : 2}>
          {tabLoading[agent && agent.showMetrics ? 5 : 2] ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <AgentAnalytics agentId={agentId} embedded={true} />
          )}
        </TabPanel>
      )}
      
      {/* Deployment History Tab - Always available */}
      <TabPanel value={activeTab} index={isDeleted ? 1 : (agent && agent.showMetrics ? 6 : 3)}>
        {tabLoading[isDeleted ? 1 : (agent && agent.showMetrics ? 6 : 3)] ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <DeploymentHistoryTab 
            agent={agent} 
            deploymentHistory={deploymentHistory} 
            deploymentProgress={deploymentProgress}
            isDeploying={isDeploying}
          />
        )}
      </TabPanel>
      
      {/* Life Journey Tab - Always available */}
      <TabPanel value={activeTab} index={isDeleted ? 2 : (agent && agent.showMetrics ? 7 : 4)}>
        {tabLoading[isDeleted ? 2 : (agent && agent.showMetrics ? 7 : 4)] ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <LifeJourneyTab agent={agent} lifecycleEvents={lifecycleEvents} lifecycleStats={lifecycleStats} />
        )}
      </TabPanel>

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={closeActionMenu}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        {!isDeleted ? (
          <>
            <MenuItem onClick={handleEditAgent}>
              <Edit sx={{ mr: 1 }} />
              Edit Agent
            </MenuItem>
            <MenuItem onClick={handleDeployAgent} disabled={isDeploying}>
              {isDeploying ? <CircularProgress size={16} sx={{ mr: 1 }} /> : <LaunchIcon sx={{ mr: 1 }} />}
              {isDeploying ? 'Deploying...' : 'Deploy Agent'}
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleDeleteAgent} sx={{ color: 'error.main' }}>
              <DeleteIcon sx={{ mr: 1 }} />
              Delete Agent
            </MenuItem>
          </>
        ) : (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              Agent is archived - no actions available
            </Typography>
          </MenuItem>
        )}
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={showDeleteDialog}
        onClose={cancelDeleteAgent}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', color: 'error.main' }}>
          <WarningIcon sx={{ mr: 1 }} />
          Delete Agent
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Are you sure you want to delete "{agent?.name}"? This action will:
          </Typography>
          <Box component="ul" sx={{ mt: 2, pl: 2 }}>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              Mark the agent as deleted and remove it from your dashboard
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              End the agent's life journey and prevent further updates
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              Preserve conversation history and analytics data
            </Typography>
            <Typography component="li" variant="body2">
              Stop any active deployments
            </Typography>
          </Box>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone. The agent will no longer be accessible for testing or modification.
          </Alert>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button 
            onClick={cancelDeleteAgent}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button 
            onClick={confirmDeleteAgent}
            color="error"
            variant="contained"
            disabled={isDeleting}
            startIcon={isDeleting ? <CircularProgress size={16} color="inherit" /> : <DeleteIcon />}
          >
            {isDeleting ? 'Deleting...' : 'Delete Agent'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Style Selector Dialog */}
      <Menu
        anchorEl={showStyleSelector ? document.body : null}
        open={showStyleSelector}
        onClose={() => setShowStyleSelector(false)}
        anchorOrigin={{
          vertical: 'center',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'center',
          horizontal: 'center',
        }}
        sx={{
          '& .MuiPaper-root': {
            minWidth: 300,
            maxWidth: 400
          }
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <PaletteIcon sx={{ mr: 1 }} />
            Choose Profile Picture Style
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select a style for your agent's AI-generated profile picture
          </Typography>
          
          {getAvailableStyles().map((style) => (
            <MenuItem
              key={style.id}
              onClick={() => handleGenerateProfilePicture(style.id)}
              disabled={isGeneratingProfilePicture}
              sx={{ mb: 1, borderRadius: 1 }}
            >
              <Box>
                <Typography variant="subtitle2" fontWeight="medium">
                  {style.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {style.description}
                </Typography>
              </Box>
            </MenuItem>
          ))}
          
          <Box sx={{ mt: 2, pt: 1, borderTop: 1, borderColor: 'divider' }}>
            <MenuItem
              onClick={() => setShowStyleSelector(false)}
              sx={{ justifyContent: 'center' }}
            >
              <Typography variant="body2" color="text.secondary">
                Cancel
              </Typography>
            </MenuItem>
          </Box>
        </Box>
      </Menu>
    </Container>
  );
};

// Identity & Skills Tab
const IdentityTab = ({ agent }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={8}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <BusinessCenter sx={{ mr: 1, verticalAlign: 'middle' }} />
            Agent Profile
          </Typography>
          
          <Typography paragraph>
            {agent.showMetrics ? (
              `${agent.name} is an AI agent specializing in ${agent.department.toLowerCase()} with ${agent.experience} years of operational experience. 
              This agent has successfully completed ${agent.totalTasks} tasks with a ${agent.successRate}% success rate, 
              demonstrating reliable performance in their assigned role.`
            ) : (
              `${agent.name} is an AI agent currently in ${agent.status} status. 
              This agent is being configured and prepared for deployment. Once deployed, it will provide 
              specialized assistance and handle various tasks assigned to it.`
            )}
          </Typography>
          
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            Core Skills
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
            {agent.skills?.map((skill, index) => (
              <Chip key={index} label={skill} variant="outlined" color="primary" />
            ))}
          </Box>
          
          <Typography variant="h6" gutterBottom>
            Specializations
          </Typography>
          <List dense>
            {agent.specializations?.map((spec, index) => (
              <ListItem key={index}>
                <ListItemIcon><Star color="primary" /></ListItemIcon>
                <ListItemText primary={spec} />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    </Grid>

    <Grid item xs={12} md={4}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Agent Details</Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="textSecondary">Employee ID</Typography>
            <Typography variant="body1" fontWeight="medium">{agent.id}</Typography>
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="textSecondary">Department</Typography>
            <Typography variant="body1" fontWeight="medium">{agent.department}</Typography>
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="textSecondary">Join Date</Typography>
            <Typography variant="body1" fontWeight="medium">
              {new Date(agent.joinDate).toLocaleDateString()}
            </Typography>
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="textSecondary">Last Active</Typography>
            <Typography variant="body1" fontWeight="medium">
              {new Date(agent.lastActive).toLocaleString()}
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="body2" color="textSecondary">Current Status</Typography>
            <Chip 
              label={agent.status} 
              color={getStatusColor(agent.status)}
              size="small"
            />
          </Box>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

// Performance Tab
const PerformanceTab = ({ agent }) => {
  const performanceMetrics = [
    { label: 'Task Success Rate', value: agent.successRate, unit: '%', target: 90 },
    { label: 'Average Response Time', value: agent.avgResponseTime, unit: 's', target: 5 },
    { label: 'User Satisfaction', value: agent.userSatisfaction, unit: '/5', target: 4 },
    { label: 'Reliability Score', value: agent.reliability, unit: '', target: 80 }
  ];

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Assessment sx={{ mr: 1, verticalAlign: 'middle' }} />
              Performance Metrics
            </Typography>
            
            <Grid container spacing={3}>
              {performanceMetrics.map((metric, index) => (
                <Grid item xs={12} sm={6} md={3} key={index}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color={
                      metric.value >= metric.target ? 'success.main' : 
                      metric.value >= metric.target * 0.8 ? 'warning.main' : 'error.main'
                    }>
                      {metric.value}{metric.unit}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {metric.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Target: {metric.target}{metric.unit}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Performance Trends</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Last 30 days performance overview
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2">Task Completion Rate</Typography>
              <LinearProgress 
                variant="determinate" 
                value={agent.successRate} 
                sx={{ height: 8, borderRadius: 4, mt: 1 }}
                color={agent.successRate >= 90 ? 'success' : agent.successRate >= 70 ? 'warning' : 'error'}
              />
              <Typography variant="caption" color="text.secondary">
                {agent.successRate}% (Target: 90%)
              </Typography>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2">Response Time</Typography>
              <LinearProgress 
                variant="determinate" 
                value={Math.max(0, 100 - (agent.avgResponseTime / 10 * 100))} 
                sx={{ height: 8, borderRadius: 4, mt: 1 }}
                color="info"
              />
              <Typography variant="caption" color="text.secondary">
                {agent.avgResponseTime}s average
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2">Customer Satisfaction</Typography>
              <LinearProgress 
                variant="determinate" 
                value={(agent.userSatisfaction / 5) * 100} 
                sx={{ height: 8, borderRadius: 4, mt: 1 }}
                color="success"
              />
              <Typography variant="caption" color="text.secondary">
                {agent.userSatisfaction}/5 stars
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
          <Typography variant="h6" gutterBottom>Performance Badges</Typography>
          <List>
            {agent.successRate >= 95 && (
              <ListItem>
                <ListItemIcon><Star sx={{ color: 'gold' }} /></ListItemIcon>
                <ListItemText primary="Excellence Award" secondary="95%+ success rate" />
              </ListItem>
            )}
            {agent.avgResponseTime <= 3 && (
              <ListItem>
                <ListItemIcon><Speed color="primary" /></ListItemIcon>
                <ListItemText primary="Speed Champion" secondary="Ultra-fast responses" />
              </ListItem>
            )}
            {agent.userSatisfaction >= 4.5 && (
              <ListItem>
                <ListItemIcon><ThumbUp color="success" /></ListItemIcon>
                <ListItemText primary="Customer Favorite" secondary="High satisfaction rating" />
              </ListItem>
            )}
            {agent.reliability >= 90 && (
              <ListItem>
                <ListItemIcon><Security color="secondary" /></ListItemIcon>
                <ListItemText primary="Reliability Expert" secondary="Consistently dependable" />
              </ListItem>
            )}
          </List>
        </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

// Cost Analysis Tab
const CostAnalysisTab = ({ agent }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={8}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <PieChart sx={{ mr: 1, verticalAlign: 'middle' }} />
            Cost Breakdown
          </Typography>
          
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  ₹{agent.totalCosts?.toLocaleString('en-IN') || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Costs
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">
                  ₹{agent.monthlyCosts?.toLocaleString('en-IN') || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Monthly Average
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  ₹{agent.costPerTask?.toLocaleString('en-IN') || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Cost per Task
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {agent.efficiency}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Efficiency Score
                </Typography>
              </Box>
            </Grid>
          </Grid>
          
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            Cost Optimization Opportunities
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><TrendingDown color="success" /></ListItemIcon>
              <ListItemText 
                primary="Optimize response time" 
                secondary="Reduce compute costs by 15% with performance tuning"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Savings color="primary" /></ListItemIcon>
              <ListItemText 
                primary="Batch processing" 
                secondary="Group similar tasks to reduce API call overhead"
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Grid>
    
    <Grid item xs={12} md={4}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>ROI Analysis</Typography>
          
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary">Return on Investment</Typography>
            <Typography variant="h4" color={agent.roi > 0 ? 'success.main' : 'error.main'}>
              {agent.roi > 0 ? '+' : ''}{agent.roi}%
            </Typography>
          </Box>
          
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary">Value Generated</Typography>
            <Typography variant="h5">
              ₹{(agent.totalTasks * 5).toLocaleString('en-IN')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Estimated business value
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="body2" color="text.secondary">Cost Efficiency</Typography>
            <Typography variant="h5">
              {agent.efficiency}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Above average efficiency
            </Typography>
          </Box>
        </CardContent>
      </Card>
      
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Budget Impact</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Monthly cost trend and budget utilization
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2">Budget Usage</Typography>
            <LinearProgress 
              variant="determinate" 
              value={65} 
              sx={{ height: 8, borderRadius: 4, mt: 1 }}
              color="info"
            />
            <Typography variant="caption" color="text.secondary">
              65% of allocated budget
            </Typography>
          </Box>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            Operating within budget parameters. Projected monthly cost: ${agent.monthlyCosts}
          </Alert>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

// Accountability Tab
const AccountabilityTab = ({ agent }) => {
  const accountabilityScores = [
    { metric: 'Decision Transparency', score: 92, description: 'Clear reasoning for all actions' },
    { metric: 'Outcome Ownership', score: agent.successRate, description: 'Takes responsibility for results' },
    { metric: 'Ethical Compliance', score: 98, description: 'Adheres to ethical guidelines' },
    { metric: 'Error Reporting', score: 89, description: 'Promptly reports and learns from mistakes' }
  ];

  const recentDecisions = [
    {
      id: 1,
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      decision: 'Escalated complex customer inquiry to human agent',
      reasoning: 'Customer request involved sensitive financial information requiring human judgment',
      outcome: 'Successful resolution with customer satisfaction'
    },
    {
      id: 2,
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      decision: 'Applied discount to customer account',
      reasoning: 'Customer met criteria for loyalty discount based on purchase history',
      outcome: 'Customer satisfied, repeat purchase made'
    }
  ];

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
              Accountability Metrics
            </Typography>
            
            {accountabilityScores.map((item, index) => (
              <Box key={index} sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle1">{item.metric}</Typography>
                  <Typography variant="h6" color="primary">{item.score}%</Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={item.score}
                  sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  color={item.score >= 90 ? 'success' : item.score >= 70 ? 'warning' : 'error'}
                />
                <Typography variant="body2" color="text.secondary">
                  {item.description}
                </Typography>
              </Box>
            ))}
          </CardContent>
        </Card>
        
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Visibility sx={{ mr: 1, verticalAlign: 'middle' }} />
              Recent Decision Audit Trail
            </Typography>
            
            {recentDecisions.map((decision) => (
              <Paper key={decision.id} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle2" fontWeight="medium">
                    Decision #{decision.id}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(decision.timestamp).toLocaleString()}
                  </Typography>
                </Box>
                <Typography variant="body1" gutterBottom>
                  <strong>Action:</strong> {decision.decision}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Reasoning:</strong> {decision.reasoning}
                </Typography>
                <Typography variant="body2" color="success.main">
                  <strong>Outcome:</strong> {decision.outcome}
                </Typography>
              </Paper>
            ))}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Overall Accountability</Typography>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography variant="h2" color="primary">
                {Math.round(accountabilityScores.reduce((sum, item) => sum + item.score, 0) / accountabilityScores.length)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Accountability Score
              </Typography>
            </Box>
            
            <List dense>
              <ListItem>
                <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                <ListItemText primary="Compliance Status" secondary="Fully Compliant" />
              </ListItem>
              <ListItem>
                <ListItemIcon><Shield color="primary" /></ListItemIcon>
                <ListItemText primary="Audit Ready" secondary="All decisions logged" />
              </ListItem>
              <ListItem>
                <ListItemIcon><Security color="secondary" /></ListItemIcon>
                <ListItemText primary="Trust Level" secondary="High Confidence" />
              </ListItem>
            </List>
          </CardContent>
        </Card>
        
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Transparency Features</Typography>
            <List dense>
              <ListItem>
                <ListItemIcon><Visibility /></ListItemIcon>
                <ListItemText primary="Decision Logging" secondary="Every action recorded" />
              </ListItem>
              <ListItem>
                <ListItemIcon><Analytics /></ListItemIcon>
                <ListItemText primary="Performance Tracking" secondary="Real-time monitoring" />
              </ListItem>
              <ListItem>
                <ListItemIcon><Assessment /></ListItemIcon>
                <ListItemText primary="Regular Audits" secondary="Continuous compliance checks" />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

// Life Journey Tab
const LifeJourneyTab = ({ agent, lifecycleEvents, lifecycleStats }) => {
  
  const getEventIcon = (eventType) => {
    const iconMap = {
      'agent_created': <CheckCircle color="success" />,
      'agent_named': <Edit color="info" />,
      'agent_description_updated': <Edit color="info" />,
      'prompt_update': <Settings color="warning" />,
      'knowledge_base_file_added': <Assignment color="primary" />,
      'knowledge_base_file_removed': <Warning color="error" />,
      'external_api_attached': <CheckCircle color="primary" />,
      'external_api_detached': <Warning color="warning" />,
      'agent_deployed': <CheckCircle color="success" />,
      'agent_undeployed': <Warning color="warning" />,
      'agent_status_changed': <Info color="info" />,
      'configuration_updated': <Settings color="info" />,
      'training_started': <Info color="info" />,
      'training_completed': <CheckCircle color="success" />,
      'agent_deleted': <DeleteIcon color="error" />
    };
    
    return iconMap[eventType] || <Info color="default" />;
  };

  const formatEventTitle = (event) => {
    switch (event.event_type) {
      case 'agent_created':
        return 'Agent Born';
      case 'agent_named':
        return event.metadata?.old_name ? 'Renamed' : 'Named';
      case 'agent_description_updated':
        return 'Description Updated';
      case 'prompt_update':
        return 'Prompt Modified';
      case 'knowledge_base_file_added':
        return `Knowledge Added: ${event.metadata?.filename || 'File'}`;
      case 'knowledge_base_file_removed':
        return `Knowledge Removed: ${event.metadata?.filename || 'File'}`;
      case 'external_api_attached':
        return `API Connected: ${event.metadata?.api_name || 'External API'}`;
      case 'external_api_detached':
        return `API Disconnected: ${event.metadata?.api_name || 'External API'}`;
      case 'agent_deployed':
        return `Deployed to ${event.metadata?.platform || 'Platform'}`;
      case 'agent_undeployed':
        return `Undeployed from ${event.metadata?.platform || 'Platform'}`;
      case 'agent_status_changed':
        return `Status: ${event.metadata?.old_status} → ${event.metadata?.new_status}`;
      case 'configuration_updated':
        return `${event.metadata?.config_section || 'Configuration'} Updated`;
      case 'agent_deleted':
        return 'Agent Deleted';
      default:
        return event.title || 'Activity';
    }
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <History sx={{ mr: 1, verticalAlign: 'middle' }} />
              Life Journey
            </Typography>
            
            {lifecycleEvents.length > 0 ? (
              <List>
                {lifecycleEvents.map((event, index) => (
                  <ListItem key={event.id} sx={{ mb: 2, border: 1, borderColor: 'grey.200', borderRadius: 1 }}>
                    <ListItemIcon>
                      {getEventIcon(event.event_type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="subtitle1" fontWeight="medium">
                            {event.icon} {formatEventTitle(event)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {event.timeSince}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {event.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {event.formattedDate}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  No lifecycle events recorded yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Events will appear here as you work with your agent
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Journey Summary</Typography>
            
            {lifecycleStats && (
              <>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary">Total Events</Typography>
                  <Typography variant="h4" color="primary">{lifecycleStats.totalEvents}</Typography>
                </Box>
                
                {lifecycleStats.creationDate && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" color="text.secondary">Created</Typography>
                    <Typography variant="h6">{lifecycleStats.creationDate.toLocaleDateString()}</Typography>
                  </Box>
                )}
                
                {lifecycleStats.lastActivity && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" color="text.secondary">Last Activity</Typography>
                    <Typography variant="h6">{lifecycleStats.lastActivity.toLocaleDateString()}</Typography>
                  </Box>
                )}
                
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Deployments</Typography>
                  <Typography variant="h6">{lifecycleStats.deploymentCount}</Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Knowledge Updates</Typography>
                  <Typography variant="h6">{lifecycleStats.knowledgeUpdates}</Typography>
                </Box>
                
                <Box>
                  <Typography variant="body2" color="text.secondary">Configuration Updates</Typography>
                  <Typography variant="h6">{lifecycleStats.configurationUpdates}</Typography>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
        
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Journey Milestones</Typography>
            <List dense>
              {lifecycleEvents.some(e => e.event_type === 'agent_created') && (
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Agent Created" secondary="Born and initialized" />
                </ListItem>
              )}
              {lifecycleEvents.some(e => e.event_type === 'agent_named') && (
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Named" secondary="Given an identity" />
                </ListItem>
              )}
              {lifecycleEvents.some(e => e.event_type === 'knowledge_base_file_added') && (
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Knowledge Added" secondary="Learned new information" />
                </ListItem>
              )}
              {lifecycleEvents.some(e => e.event_type === 'agent_deployed') && (
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Deployed" secondary="Ready for action" />
                </ListItem>
              )}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

// Deployment History Tab
const DeploymentHistoryTab = ({ agent, deploymentHistory, deploymentProgress, isDeploying }) => {
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'deployed':
        return 'success';
      case 'pending':
      case 'deploying':
      case 'building':
        return 'warning';
      case 'failed':
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'deployed':
        return <CheckCircleIcon color="success" />;
      case 'pending':
      case 'deploying':
      case 'building':
        return <CircularProgress size={20} />;
      case 'failed':
        return <CancelIcon color="error" />;
      case 'cancelled':
        return <StopIcon color="error" />;
      default:
        return <CircularProgress size={20} />;
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return '-';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end - start;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    
    if (diffMin > 0) {
      return `${diffMin}m ${diffSec % 60}s`;
    }
    return `${diffSec}s`;
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                <CloudIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Deployment History
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {deploymentHistory.length} deployment{deploymentHistory.length !== 1 ? 's' : ''}
              </Typography>
            </Box>

            {/* Current Deployment Progress */}
            {isDeploying && deploymentProgress && (
              <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  <Typography variant="h6" color="primary">
                    Current Deployment
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  Status: {deploymentProgress.status}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {deploymentProgress.message}
                </Typography>
                {deploymentProgress.progress && (
                  <Box sx={{ mt: 2 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={deploymentProgress.progress} 
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {deploymentProgress.progress}% complete
                    </Typography>
                  </Box>
                )}
              </Paper>
            )}

            {/* Deployment History List */}
            {deploymentHistory.length > 0 ? (
              <List>
                {deploymentHistory.map((deployment, index) => (
                  <ListItem key={deployment.deployment_id} sx={{ 
                    mb: 2, 
                    border: 1, 
                    borderColor: 'grey.200', 
                    borderRadius: 2,
                    bgcolor: index === 0 ? 'success.50' : 'background.paper'
                  }}>
                    <ListItemIcon>
                      {getStatusIcon(deployment.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle1" fontWeight="medium">
                              Deployment #{deployment.deployment_id.slice(-8)}
                            </Typography>
                            <Chip 
                              label={deployment.status} 
                              color={getStatusColor(deployment.status)}
                              size="small"
                              sx={{ fontWeight: 'bold' }}
                            />
                            {index === 0 && deployment.status === 'completed' && (
                              <Chip 
                                label="Current" 
                                color="primary"
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(deployment.created_at).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Grid container spacing={2}>
                            <Grid item xs={12} sm={6} md={3}>
                              <Typography variant="body2" color="text.secondary">
                                <strong>Duration:</strong> {formatDuration(deployment.created_at, deployment.updated_at)}
                              </Typography>
                            </Grid>
                            {deployment.region && (
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="body2" color="text.secondary">
                                  <strong>Region:</strong> {deployment.region}
                                </Typography>
                              </Grid>
                            )}
                            {deployment.service_url && (
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="body2" color="text.secondary">
                                  <strong>Service URL:</strong> 
                                  <a href={deployment.service_url} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 4 }}>
                                    {deployment.service_url.replace('https://', '').slice(0, 30)}...
                                  </a>
                                </Typography>
                              </Grid>
                            )}
                            {deployment.error_message && (
                              <Grid item xs={12}>
                                <Alert severity="error" sx={{ mt: 1 }}>
                                  <Typography variant="body2">
                                    <strong>Error:</strong> {deployment.error_message}
                                  </Typography>
                                </Alert>
                              </Grid>
                            )}
                          </Grid>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <CloudIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No Deployments Yet
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Click the Deploy button to deploy this agent for the first time
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Deployment Statistics */}
      {deploymentHistory.length > 0 && (
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Deployment Statistics</Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">Total Deployments</Typography>
                <Typography variant="h4" color="primary">{deploymentHistory.length}</Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">Successful Deployments</Typography>
                <Typography variant="h4" color="success.main">
                  {deploymentHistory.filter(d => d.status === 'completed' || d.status === 'deployed').length}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">Failed Deployments</Typography>
                <Typography variant="h4" color="error.main">
                  {deploymentHistory.filter(d => d.status === 'failed').length}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="body2" color="text.secondary">Last Deployment</Typography>
                <Typography variant="body1">
                  {deploymentHistory.length > 0 ? 
                    new Date(deploymentHistory[0].created_at).toLocaleDateString() : 
                    'Never'
                  }
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );
};

export default AgentProfile;