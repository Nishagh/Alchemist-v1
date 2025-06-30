/**
 * Alchemist Dashboard - AI Workforce Management
 * 
 * Comprehensive dashboard for managing AI agents as workforce members
 * Displays agents with human-like employee profiles and metrics
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Paper,
  LinearProgress,
  Stack,
  useTheme,
  alpha,
  Fade,
  Grow,
  Container,
  Badge,
  Tabs,
  Tab,
  CardActions,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Tooltip,
  Skeleton
} from '@mui/material';
import {
  Archive as ArchiveIcon,
  AutoAwesome as AutoAwesomeIcon,
  SmartToy as SmartToyIcon,
  RocketLaunch as RocketLaunchIcon,
  WhatsApp as WhatsAppIcon,
  Analytics as AnalyticsIcon,
  Add as AddIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Message as MessageIcon,
  Phone as PhoneIcon,
  Hub as IntegrationIcon,
  ArrowForward as ArrowForwardIcon,
  Edit as EditIcon,
  Launch as LaunchIcon,
  MoreVert as MoreVertIcon,
  Notifications as NotificationsIcon,
  Psychology as PsychologyIcon,
  Work as WorkIcon,
  Group as GroupIcon,
  AttachMoney as AttachMoneyIcon,
  Star as StarIcon,
  Shield as ShieldIcon,
  Timeline as TimelineIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIconAlt,
  Business as BusinessIcon,
  Assignment as AssignmentIcon,
  Visibility as VisibilityIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Sort as SortIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
  MoreHoriz as MoreHorizIcon,
  AccountCircle as AccountCircleIcon,
  EmojiEvents as EmojiEventsIcon,
  School as SchoolIcon,
  BarChart as BarChartIcon
} from '@mui/icons-material';

import { useAuth } from '../utils/AuthContext';
import { db } from '../utils/firebase';
import { collection, query, where, onSnapshot, orderBy, limit } from 'firebase/firestore';
import { gnfApi } from '../services/config/apiConfig';
import { WorkforceGrid, WorkforceControls } from '../components/AgentWorkforce';
import { workforceService } from '../services/workforce/workforceService';

const Dashboard = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { currentUser } = useAuth();
  
  const [stats, setStats] = useState({
    totalAgents: 0,
    activeDeployments: 0,
    totalIntegrations: 0,
    messagesHandled: 0,
    totalCosts: 0,
    avgPerformance: 0
  });
  
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [sortBy, setSortBy] = useState('name');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);
  const [agentIdentities, setAgentIdentities] = useState({});
  const [agentCounts, setAgentCounts] = useState({});

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown time';
    
    const now = new Date();
    const time = timestamp.seconds ? new Date(timestamp.seconds * 1000) : new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  };
  
  // Helper functions for real data processing
  
  const generateJobTitle = (agentId) => {
    const agentData = workforceData[agentId];
    if (!agentData) return 'AI Specialist';
    return workforceService.generateJobTitle(agentData);
  };
  
  const generateProfilePicture = (identity) => {
    if (!identity) return '#757575';
    const stage = identity.development_stage;
    const colors = {
      nascent: '#4CAF50',
      developing: '#2196F3', 
      mature: '#9C27B0',
      expert: '#FF9800'
    };
    return colors[stage] || '#757575';
  };
  
  const calculateExperienceYears = (agentId) => {
    const agentData = workforceData[agentId];
    if (!agentData) return 0;
    const experience = workforceService.calculateExperience(agentData);
    return experience.years;
  };
  
  const calculateUsageCosts = (agentId) => {
    const agentData = workforceData[agentId];
    if (!agentData) return 0;
    const performance = workforceService.calculatePerformanceMetrics(agentData);
    const costs = workforceService.calculateUsageCosts(agentData, performance);
    return costs.totalCost;
  };
  
  const getPerformanceScore = (agentId) => {
    const agentData = workforceData[agentId];
    if (!agentData) return 0;
    const performance = workforceService.calculatePerformanceMetrics(agentData);
    return performance.successRate;
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'deployed': return 'info';
      case 'training': return 'warning';
      case 'draft': return 'default';
      default: return 'default';
    }
  };
  
  
  
  const [allAgents, setAllAgents] = useState([]);
  const [recentAgents, setRecentAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userAgentIds, setUserAgentIds] = useState(new Set());
  const [allDeployments, setAllDeployments] = useState([]);
  const [agentsLoading, setAgentsLoading] = useState(true);
  const [workforceData, setWorkforceData] = useState({});
  const [realTimeStats, setRealTimeStats] = useState({
    totalCosts: 0,
    avgPerformance: 0,
    totalTasks: 0,
    avgResponseTime: 0
  });

  useEffect(() => {
    if (currentUser) {
      loadDashboardData();
      loadRealWorkforceData();
    }
  }, [currentUser]);
  
  const loadRealWorkforceData = async () => {
    try {
      console.log('Loading real workforce data...');
      const { agents, workforceData: data } = await workforceService.getAllAgentWorkforceData(currentUser.uid);
      
      setWorkforceData(data);
      
      // Calculate real-time statistics
      let totalCosts = 0;
      let totalPerformance = 0;
      let totalTasks = 0;
      let totalResponseTime = 0;
      let validAgents = 0;
      
      const identities = {};
      
      agents.forEach(agent => {
        const agentData = data[agent.id];
        if (agentData) {
          // Store identity data
          identities[agent.id] = agentData.identity;
          
          // Calculate real metrics
          const performance = workforceService.calculatePerformanceMetrics(agentData);
          const costs = workforceService.calculateUsageCosts(agentData, performance);
          
          if (performance.totalTasks > 0) {
            totalCosts += costs.totalCost;
            totalPerformance += performance.successRate;
            totalTasks += performance.totalTasks;
            totalResponseTime += performance.averageResponseTime;
            validAgents++;
          }
        }
      });
      
      setAgentIdentities(identities);
      const newRealTimeStats = {
        totalCosts: totalCosts,
        avgPerformance: validAgents > 0 ? Math.round(totalPerformance / validAgents) : 0,
        totalTasks: totalTasks,
        avgResponseTime: validAgents > 0 ? Math.round((totalResponseTime / validAgents) * 10) / 10 : 0
      };
      
      setRealTimeStats(newRealTimeStats);
      
      // Update the main stats with real data
      setStats(prev => ({
        ...prev,
        totalCosts: totalCosts,
        avgPerformance: newRealTimeStats.avgPerformance,
        messagesHandled: totalTasks
      }));
      
      // Calculate agent counts by status
      const counts = {
        total: agents.length,
        draft: 0,
        deployed: 0
      };
      
      agents.forEach(agent => {
        const status = agent.status || 'draft';
        
        if (status === 'draft') counts.draft++;
        else if (status === 'deployed') counts.deployed++;
      });
      
      setAgentCounts(counts);
      
      console.log('Real workforce data loaded:', {
        agentCount: agents.length,
        validAgents,
        totalCosts,
        avgPerformance: validAgents > 0 ? Math.round(totalPerformance / validAgents) : 0,
        statusCounts: counts
      });
      
    } catch (error) {
      console.error('Error loading real workforce data:', error);
    }
  };
  
  // Reload workforce data when agents change
  useEffect(() => {
    if (allAgents.length > 0 && currentUser) {
      loadRealWorkforceData();
    }
  }, [allAgents, currentUser]);

  // Load deployments when user agent IDs are available
  useEffect(() => {
    let unsubscribeDeployments;
    
    if (userAgentIds.size > 0) {
      console.log('Loading deployments for agent IDs:', Array.from(userAgentIds));
      
      // Firestore 'in' queries have a limit of 10 items, so we need to batch if more agents
      const agentIdsArray = Array.from(userAgentIds);
      if (agentIdsArray.length > 10) {
        console.warn('More than 10 agents detected, using first 10 for deployment query');
        agentIdsArray.splice(10); // Keep only first 10
      }
      
      // Query deployments for user's agents
      const deploymentsRef = collection(db, 'agent_deployments');
      const deploymentsQuery = query(
        deploymentsRef,
        where('agent_id', 'in', agentIdsArray),
        orderBy('updated_at', 'desc')
      );
      
      unsubscribeDeployments = onSnapshot(deploymentsQuery, 
        (snapshot) => {
          console.log('Deployments snapshot received:', snapshot.size, 'deployments');
          const deployments = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
          
          // Group by agent_id and keep only the latest deployment per agent
          const latestDeployments = {};
          deployments.forEach(deployment => {
            const agentId = deployment.agent_id;
            if (!latestDeployments[agentId] || 
                (deployment.updated_at?.seconds || 0) > (latestDeployments[agentId].updated_at?.seconds || 0)) {
              latestDeployments[agentId] = deployment;
            }
          });
          
          const uniqueDeployments = Object.values(latestDeployments);
          setAllDeployments(uniqueDeployments);
          
          // Update stats
          const activeDeployments = uniqueDeployments.filter(d => d.status === 'completed' || d.status === 'deployed').length;
          setStats(prev => ({ ...prev, activeDeployments }));
          
          // Generate activity from deployments
          const deploymentActivity = uniqueDeployments
            .sort((a, b) => (b.updated_at?.seconds || 0) - (a.updated_at?.seconds || 0))
            .slice(0, 2)
            .map(deployment => ({
              id: `deployment-${deployment.id}`,
              type: 'deployment',
              title: `Deployment ${deployment.status === 'completed' || deployment.status === 'deployed' ? 'completed' : deployment.status}`,
              time: formatTimeAgo(deployment.updated_at),
              icon: <RocketLaunchIcon />,
              color: deployment.status === 'completed' || deployment.status === 'deployed' ? 'success' : 
                    deployment.status === 'failed' ? 'error' : 'info'
            }));
          
        },
        (error) => {
          console.error('Error in deployments snapshot listener:', error);
          // Set empty deployments on error
          setAllDeployments([]);
          setStats(prev => ({ ...prev, activeDeployments: 0 }));
        }
      );
    } else {
      // No agents, so no deployments
      console.log('No agent IDs available, skipping deployment query');
      setAllDeployments([]);
      setStats(prev => ({ ...prev, activeDeployments: 0 }));
    }
    
    return () => {
      if (unsubscribeDeployments) {
        unsubscribeDeployments();
      }
    };
  }, [userAgentIds]);

  const loadDashboardData = async () => {
    console.log('Loading dashboard data for user:', currentUser?.uid);
    console.log('Current user:', currentUser);
    
    try {
      let unsubscribeAgents;
      let unsubscribePhones;
      
      // Load recent agents from correct collection (exclude deleted)
      const agentsRef = collection(db, 'agents');
      const agentsQuery = query(
        agentsRef, 
        where('userId', '==', currentUser.uid),
        where('status', '!=', 'deleted'),
        orderBy('status'),
        orderBy('updated_at', 'desc'),
        limit(6)
      );
      
      // Load ALL active agents for the workforce view (exclude deleted)
      const allAgentsRef = collection(db, 'agents');
      const allAgentsQuery = query(
        allAgentsRef, 
        where('userId', '==', currentUser.uid),
        where('status', '!=', 'deleted'),
        orderBy('status'),
        orderBy('updated_at', 'desc')
      );
      
      unsubscribeAgents = onSnapshot(allAgentsQuery, 
        (snapshot) => {
          console.log('Agents snapshot received:', snapshot.size, 'agents');
          const agents = [];
          const agentIds = new Set();
          snapshot.forEach((doc) => {
            console.log('Agent doc:', doc.id, doc.data());
            const agentData = { id: doc.id, agent_id: doc.id, ...doc.data() };
            agents.push(agentData);
            agentIds.add(doc.id);
          });
          setAllAgents(agents);
          setRecentAgents(agents.slice(0, 6)); // Keep recent agents for activity
          setUserAgentIds(agentIds);
          setStats(prev => ({
            ...prev, 
            totalAgents: snapshot.size
          }));
          setAgentsLoading(false);
        },
        (error) => {
          console.error('Error in agents snapshot listener:', error);
          setAgentsLoading(false);
        }
      );

      // Note: Deployments will be loaded after agents are fetched
      // This is handled in the useEffect that watches userAgentIds

      // Load WhatsApp integrations
      const phonesRef = collection(db, 'whatsapp_user_phones');
      const phonesQuery = query(
        phonesRef,
        where('user_id', '==', currentUser.uid)
      );
      
      unsubscribePhones = onSnapshot(phonesQuery, 
        (snapshot) => {
          console.log('Phones snapshot received:', snapshot.size, 'phones');
          const phones = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
          const activePhones = phones.filter(p => p.status === 'active').length;
          setStats(prev => ({ ...prev, totalIntegrations: activePhones }));
          
          // Generate activity from phone integrations
          const phoneActivity = phones
            .filter(p => p.verified_at || p.status === 'active')
            .sort((a, b) => (b.verified_at?.seconds || b.updated_at?.seconds || 0) - (a.verified_at?.seconds || a.updated_at?.seconds || 0))
            .slice(0, 1)
            .map(phone => ({
              id: `phone-${phone.id}`,
              type: 'integration',
              title: `WhatsApp ${phone.number} ${phone.status === 'active' ? 'activated' : 'configured'}`,
              time: formatTimeAgo(phone.verified_at || phone.updated_at),
              icon: <WhatsAppIcon />,
              color: 'info'
            }));
          
        },
        (error) => {
          console.error('Error in phones snapshot listener:', error);
        }
      );

      // Load recent agent creation activity (exclude deleted)
      const recentAgentsRef = collection(db, 'agents');
      const recentAgentsQuery = query(
        recentAgentsRef,
        where('userId', '==', currentUser.uid),
        where('status', '!=', 'deleted'),
        orderBy('status'),
        orderBy('created_at', 'desc'),
        limit(3)
      );
      
      onSnapshot(recentAgentsQuery, 
        (snapshot) => {
          console.log('Recent agents snapshot received:', snapshot.size, 'agents');
          const agentActivity = snapshot.docs
            .slice(0, 2)
            .map(doc => {
              const agent = doc.data();
              return {
                id: `agent-${doc.id}`,
                type: 'agent_created',
                title: `Agent "${agent.name || 'Untitled'}" created`,
                time: formatTimeAgo(agent.created_at),
                icon: <SmartToyIcon />,
                color: 'primary'
              };
            });
          
        },
        (error) => {
          console.error('Error in recent agents snapshot listener:', error);
        }
      );

      // Real task data will be updated when workforce data loads

      setLoading(false);
      
      return () => {
        unsubscribeAgents && unsubscribeAgents();
        unsubscribePhones && unsubscribePhones();
      };
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'Create New Agent',
      description: 'Build a new AI assistant',
      icon: <PersonIcon />,
      color: '#6366f1',
      action: () => navigate('/create-agent')
    },
    {
      title: 'Team Directory',
      description: 'View all workforce members',
      icon: <GroupIcon />,
      color: '#8b5cf6',
      action: () => navigate('/agents')
    },
    {
      title: 'Performance Review',
      description: 'Analyze team metrics',
      icon: <BarChartIcon />,
      color: '#f59e0b',
      action: () => {
        if (allAgents.length > 0) {
          navigate(`/agent-profile/${allAgents[0].id}`);
        } else {
          navigate('/create-agent');
        }
      }
    },
    {
      title: 'Deploy Agents',
      description: 'Connect to platforms',
      icon: <RocketLaunchIcon />,
      color: '#10b981',
      action: () => {
        if (allAgents.length > 0) {
          navigate(`/agent-profile/${allAgents[0].id}`);
        } else {
          navigate('/create-agent');
        }
      }
    }
  ];
  

  const StatCard = ({ title, value, icon, trend, color = 'primary', prefix = '' }) => (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold">
              {prefix}{typeof value === 'number' ? value.toLocaleString() : value}
            </Typography>
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUpIcon fontSize="small" color="success" />
                <Typography variant="caption" color="success.main" sx={{ ml: 0.5 }}>
                  +{trend}% this month
                </Typography>
              </Box>
            )}
          </Box>
          <Avatar
            sx={{
              bgcolor: alpha(theme.palette[color].main, 0.1),
              color: theme.palette[color].main,
              width: 56,
              height: 56
            }}
          >
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  const QuickActionCard = ({ title, description, icon, color, action }) => (
    <Card 
      sx={{ 
        height: '100%',
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[8]
        }
      }}
      onClick={action}
    >
      <CardContent sx={{ textAlign: 'center', py: 3 }}>
        <Avatar
          sx={{
            bgcolor: alpha(color, 0.1),
            color: color,
            width: 64,
            height: 64,
            mx: 'auto',
            mb: 2
          }}
        >
          {icon}
        </Avatar>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </CardContent>
    </Card>
  );


  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <LinearProgress sx={{ width: '200px' }} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Welcome Section */}
      <Fade in={true} timeout={500}>
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              AI Workforce Dashboard 🤖
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Managing {stats.totalAgents} AI employees • Total costs: ₹{stats.totalCosts.toLocaleString('en-IN')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<ArchiveIcon />}
              onClick={() => navigate('/archives')}
              sx={{
                color: 'text.secondary',
                borderColor: 'divider',
                '&:hover': {
                  borderColor: 'text.secondary',
                  bgcolor: alpha(theme.palette.grey[500], 0.05)
                }
              }}
            >
              Archives
            </Button>
          </Box>
        </Box>
      </Fade>

      {/* Workforce Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Fade in={true} timeout={600}>
            <div>
              <StatCard
                title="Total Employees"
                value={stats.totalAgents}
                icon={<GroupIcon />}
                color="primary"
              />
            </div>
          </Fade>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Fade in={true} timeout={700}>
            <div>
              <StatCard
                title="Active Deployments"
                value={stats.activeDeployments}
                icon={<WorkIcon />}
                color="success"
              />
            </div>
          </Fade>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Fade in={true} timeout={800}>
            <div>
              <StatCard
                title="Total Costs"
                value={stats.totalCosts}
                icon={<AttachMoneyIcon />}
                color="warning"
                prefix="₹"
              />
            </div>
          </Fade>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Fade in={true} timeout={900}>
            <div>
              <StatCard
                title="Avg Performance"
                value={`${stats.avgPerformance}%`}
                icon={<StarIcon />}
                color="info"
              />
            </div>
          </Fade>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Fade in={true} timeout={1000}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            Workforce Management
          </Typography>
          <Grid container spacing={3}>
            {quickActions.map((action, index) => (
              <Grid item xs={12} sm={6} md={3} key={action.title}>
                <Grow in={true} timeout={1100 + index * 100}>
                  <div>
                    <QuickActionCard {...action} />
                  </div>
                </Grow>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Fade>

      {/* AI Workforce Directory */}
      <Fade in={true} timeout={1200}>
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h5" fontWeight="bold">
                🏢 AI Workforce Directory
              </Typography>
              
              <WorkforceControls
                searchTerm={searchTerm}
                setSearchTerm={setSearchTerm}
                sortBy={sortBy}
                setSortBy={setSortBy}
                viewMode={viewMode}
                setViewMode={setViewMode}
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
                agentCounts={agentCounts}
              />
            </Box>
            
            <WorkforceGrid
              agents={allAgents}
              loading={agentsLoading}
              viewMode={viewMode}
              searchTerm={searchTerm}
              sortBy={sortBy}
              statusFilter={statusFilter}
              showActions={true}
              workforceData={workforceData}
              agentIdentities={agentIdentities}
            />
            
            {allAgents.length === 0 && !agentsLoading && (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<PersonIcon />}
                  onClick={() => navigate('/create-agent')}
                >
                  Create First Agent
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      </Fade>
      
    </Container>
  );
};

export default Dashboard;