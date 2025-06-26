/**
 * Alchemist Dashboard - Central Hub
 * 
 * Modern dashboard serving as the main entry point for authenticated users
 * Provides overview, quick actions, and navigation to all features
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
  Container
} from '@mui/material';
import {
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
  Psychology as PsychologyIcon
} from '@mui/icons-material';

import { useAuth } from '../utils/AuthContext';
import { db } from '../utils/firebase';
import { collection, query, where, onSnapshot, orderBy, limit } from 'firebase/firestore';

const Dashboard = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { currentUser } = useAuth();
  
  const [stats, setStats] = useState({
    totalAgents: 0,
    activeDeployments: 0,
    totalIntegrations: 0,
    messagesHandled: 0
  });

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
  
  const [recentAgents, setRecentAgents] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userAgentIds, setUserAgentIds] = useState(new Set());
  const [allDeployments, setAllDeployments] = useState([]);

  useEffect(() => {
    if (currentUser) {
      loadDashboardData();
    }
  }, [currentUser]);

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
          
          setRecentActivity(prev => [...prev.filter(a => !a.id.startsWith('deployment-')), ...deploymentActivity]);
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
      
      // Load agents from correct collection
      const agentsRef = collection(db, 'agents');
      const agentsQuery = query(
        agentsRef, 
        where('userId', '==', currentUser.uid),
        orderBy('updated_at', 'desc'),
        limit(6)
      );
      
      unsubscribeAgents = onSnapshot(agentsQuery, 
        (snapshot) => {
          console.log('Agents snapshot received:', snapshot.size, 'agents');
          const agents = [];
          const agentIds = new Set();
          snapshot.forEach((doc) => {
            console.log('Agent doc:', doc.id, doc.data());
            agents.push({ id: doc.id, agent_id: doc.id, ...doc.data() });
            agentIds.add(doc.id);
          });
          setRecentAgents(agents);
          setUserAgentIds(agentIds);
          setStats(prev => ({ ...prev, totalAgents: snapshot.size }));
        },
        (error) => {
          console.error('Error in agents snapshot listener:', error);
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
          
          setRecentActivity(prev => [...prev.filter(a => !a.id.startsWith('phone-')), ...phoneActivity]);
        },
        (error) => {
          console.error('Error in phones snapshot listener:', error);
        }
      );

      // Load recent agent creation activity
      const recentAgentsRef = collection(db, 'agents');
      const recentAgentsQuery = query(
        recentAgentsRef,
        where('userId', '==', currentUser.uid),
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
          
          setRecentActivity(prev => [...prev.filter(a => !a.id.startsWith('agent-')), ...agentActivity]);
        },
        (error) => {
          console.error('Error in recent agents snapshot listener:', error);
        }
      );

      // Set mock messages handled (would need actual message tracking)
      setStats(prev => ({ ...prev, messagesHandled: 0 })); // Real implementation would track this

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
      title: 'Create Agent',
      description: 'Build a new AI agent',
      icon: <SmartToyIcon />,
      color: '#6366f1',
      action: () => navigate('/create-agent')
    },
    {
      title: 'My Agents',
      description: 'Manage existing agents',
      icon: <IntegrationIcon />,
      color: '#8b5cf6',
      action: () => navigate('/agents')
    },
    {
      title: 'WhatsApp Integration',
      description: 'Connect agents to WhatsApp',
      icon: <WhatsAppIcon />,
      color: '#25D366',
      action: () => {
        // Navigate to agent management
        // If user has agents, go to first agent's dashboard
        if (recentAgents.length > 0) {
          navigate(`/agent/${recentAgents[0].id}`);
        } else {
          // If no agents, suggest creating one first
          navigate('/create-agent');
        }
      }
    },
    {
      title: 'API Documentation',
      description: 'Integration guides',
      icon: <AnalyticsIcon />,
      color: '#f59e0b',
      action: () => window.open('https://docs.example.com', '_blank')
    }
  ];

  const StatCard = ({ title, value, icon, trend, color = 'primary' }) => (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold">
              {value.toLocaleString()}
            </Typography>
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUpIcon fontSize="small" color="success" />
                <Typography variant="caption" color="success.main" sx={{ ml: 0.5 }}>
                  +{trend}% this week
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

  const AgentCard = ({ agent, index }) => (
    <Grow in={true} timeout={300 + index * 100}>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                <PsychologyIcon />
              </Avatar>
              <Box>
                <Typography variant="h6" fontWeight="bold">
                  {agent.name || 'Untitled Agent'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {agent.description || 'No description'}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Chip 
                    label={agent.status || 'Draft'} 
                    size="small" 
                    color={agent.status === 'active' ? 'success' : 'default'}
                  />
                  <Chip 
                    label={`Updated ${new Date(agent.updated_at?.seconds * 1000 || Date.now()).toLocaleDateString()}`}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Box>
            </Box>
            <Box>
              <IconButton onClick={() => navigate(`/agent/${agent.id}`)}>
                <EditIcon />
              </IconButton>
              <IconButton>
                <MoreVertIcon />
              </IconButton>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Grow>
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
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Welcome back, {currentUser?.displayName || currentUser?.email?.split('@')[0] || 'there'}! 👋
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Here's what's happening with your AI agents today.
          </Typography>
        </Box>
      </Fade>

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Fade in={true} timeout={600}>
            <div>
              <StatCard
                title="Total Agents"
                value={stats.totalAgents}
                icon={<SmartToyIcon />}
                trend={12}
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
                icon={<RocketLaunchIcon />}
                trend={8}
                color="success"
              />
            </div>
          </Fade>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Fade in={true} timeout={800}>
            <div>
              <StatCard
                title="Integrations"
                value={stats.totalIntegrations}
                icon={<IntegrationIcon />}
                trend={25}
                color="info"
              />
            </div>
          </Fade>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Fade in={true} timeout={900}>
            <div>
              <StatCard
                title="Messages Handled"
                value={stats.messagesHandled}
                icon={<MessageIcon />}
                trend={156}
                color="secondary"
              />
            </div>
          </Fade>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Fade in={true} timeout={1000}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            Quick Actions
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

      <Grid container spacing={4}>
        {/* Recent Agents */}
        <Grid item xs={12} lg={8}>
          <Fade in={true} timeout={1200}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6" fontWeight="bold">
                    Recent Agents
                  </Typography>
                  <Button
                    endIcon={<ArrowForwardIcon />}
                    onClick={() => navigate('/agents')}
                  >
                    View All
                  </Button>
                </Box>
                <Box>
                  {recentAgents.length > 0 ? (
                    recentAgents.slice(0, 4).map((agent, index) => (
                      <AgentCard key={agent.id} agent={agent} index={index} />
                    ))
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <SmartToyIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        No agents yet
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Create your first AI agent to get started
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/create-agent')}
                      >
                        Create Agent
                      </Button>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Fade>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} lg={4}>
          <Fade in={true} timeout={1300}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6" fontWeight="bold">
                    Recent Activity
                  </Typography>
                  <IconButton size="small">
                    <NotificationsIcon />
                  </IconButton>
                </Box>
                <List>
                  {recentActivity.map((activity, index) => (
                    <Grow in={true} timeout={1400 + index * 100} key={activity.id}>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon>
                          <Avatar
                            sx={{
                              bgcolor: alpha(theme.palette[activity.color].main, 0.1),
                              color: theme.palette[activity.color].main,
                              width: 32,
                              height: 32
                            }}
                          >
                            {React.cloneElement(activity.icon, { fontSize: 'small' })}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primary={activity.title}
                          secondary={activity.time}
                          primaryTypographyProps={{ fontSize: '0.9rem' }}
                          secondaryTypographyProps={{ fontSize: '0.8rem' }}
                        />
                      </ListItem>
                    </Grow>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Fade>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;