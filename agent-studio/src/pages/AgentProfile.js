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
  Tooltip
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
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { workforceService } from '../services/workforce/workforceService';
import { useAuth } from '../utils/AuthContext';

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
  const [loading, setLoading] = useState(true);
  const [workforceData, setWorkforceData] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [costMetrics, setCostMetrics] = useState(null);

  // Handle back navigation
  const handleBackClick = () => {
    navigate('/');
  };

  useEffect(() => {
    if (currentUser && agentId) {
      fetchAgentProfile();
    }
  }, [agentId, currentUser]);

  const fetchAgentProfile = async () => {
    try {
      setLoading(true);
      
      // Get comprehensive workforce data from backend
      const agentData = await workforceService.getAgentWorkforceData(agentId, currentUser.uid);
      setWorkforceData(agentData);
      
      // Calculate performance and cost metrics
      const performance = workforceService.calculatePerformanceMetrics(agentData);
      const costs = workforceService.calculateUsageCosts(agentData, performance);
      const experience = workforceService.calculateExperience(agentData);
      const efficiency = workforceService.calculateCostEfficiency(agentData);
      
      setPerformanceMetrics(performance);
      setCostMetrics(costs);
      
      // Create agent profile focused on business value
      const profileData = {
        id: agentId,
        name: agentData.identity?.name || `Agent ${agentId.slice(-4)}`,
        role: workforceService.generateJobTitle(agentData),
        department: workforceService.determineDepartment(agentData),
        status: 'Active', // Could be derived from deployment status
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
        roi: efficiency.roi,
        skills: agentData.identity?.dominant_personality_traits || ['Problem Solving', 'Communication'],
        specializations: agentData.identity?.primary_goals || ['Customer Support', 'Data Analysis'],
        lastActive: new Date().toISOString(),
        joinDate: agentData.identity?.created_at || new Date().toISOString()
      };

      setAgent(profileData);
    } catch (error) {
      console.error('Error fetching agent profile:', error);
      // No fallback data - let user know there's an error
      setAgent(null);
    } finally {
      setLoading(false);
    }
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );


  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography>Loading agent profile...</Typography>
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

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Back Navigation */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={handleBackClick} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5" fontWeight="bold">
          Agent Profile
        </Typography>
      </Box>

      {/* Agent Header Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  bgcolor: 'primary.main',
                  fontSize: '2.5rem'
                }}
              >
                <SmartToy sx={{ fontSize: '3rem' }} />
              </Avatar>
            </Grid>
            
            <Grid item xs>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography variant="h4" fontWeight="bold">
                  {agent.name}
                </Typography>
                <Chip 
                  label={agent.status} 
                  color={getStatusColor(agent.status)}
                  sx={{ fontWeight: 'bold' }}
                />
              </Box>
              
              <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                {agent.role} • {agent.department}
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold">
                      {agent.experience}y
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Experience
                    </Typography>
                  </Box>
                </Grid>
                <Grid item>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold" color={getPerformanceColor(agent.successRate)}>
                      {agent.successRate}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Success Rate
                    </Typography>
                  </Box>
                </Grid>
                <Grid item>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold">
                      {agent.totalTasks}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Tasks Completed
                    </Typography>
                  </Box>
                </Grid>
                <Grid item>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold" color="warning.main">
                      ₹{agent.totalCosts?.toLocaleString('en-IN') || '0'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Total Usage Cost
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Grid>

            <Grid item>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.50' }}>
                <Typography variant="h3" fontWeight="bold" color="primary">
                  {agent.reliability}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Reliability Score
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<Person />} label="Identity & Skills" />
          <Tab icon={<Assessment />} label="Performance" />
          <Tab icon={<MonetizationOn />} label="Cost Analysis" />
          <Tab icon={<Shield />} label="Accountability" />
          <Tab icon={<History />} label="Activity History" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={activeTab} index={0}>
        <IdentityTab agent={agent} />
      </TabPanel>
      
      <TabPanel value={activeTab} index={1}>
        <PerformanceTab agent={agent} />
      </TabPanel>
      
      <TabPanel value={activeTab} index={2}>
        <CostAnalysisTab agent={agent} />
      </TabPanel>
      
      <TabPanel value={activeTab} index={3}>
        <AccountabilityTab agent={agent} />
      </TabPanel>
      
      <TabPanel value={activeTab} index={4}>
        <ActivityHistoryTab agent={agent} />
      </TabPanel>
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
            {agent.name} is an AI agent specializing in {agent.department.toLowerCase()} with {agent.experience} years of operational experience. 
            This agent has successfully completed {agent.totalTasks} tasks with a {agent.successRate}% success rate, 
            demonstrating reliable performance in their assigned role.
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

// Activity History Tab
const ActivityHistoryTab = ({ agent }) => {
  const recentActivities = [
    {
      id: 1,
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      type: 'task_completed',
      title: 'Customer Support Query Resolved',
      description: 'Successfully resolved billing inquiry for customer #12345',
      status: 'completed',
      duration: '5 minutes'
    },
    {
      id: 2,
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      type: 'task_completed',
      title: 'Data Analysis Report Generated',
      description: 'Created monthly sales analysis report for management review',
      status: 'completed',
      duration: '15 minutes'
    },
    {
      id: 3,
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      type: 'escalation',
      title: 'Complex Issue Escalated',
      description: 'Escalated technical issue to specialized team',
      status: 'escalated',
      duration: '2 minutes'
    }
  ];

  const getActivityIcon = (type) => {
    switch (type) {
      case 'task_completed': return <CheckCircle color="success" />;
      case 'escalation': return <Warning color="warning" />;
      case 'error': return <Error color="error" />;
      default: return <Info color="info" />;
    }
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <History sx={{ mr: 1, verticalAlign: 'middle' }} />
              Recent Activity
            </Typography>
            
            <List>
              {recentActivities.map((activity) => (
                <ListItem key={activity.id} sx={{ mb: 2, border: 1, borderColor: 'grey.200', borderRadius: 1 }}>
                  <ListItemIcon>
                    {getActivityIcon(activity.type)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {activity.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(activity.timestamp).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {activity.description}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Chip label={activity.status} size="small" />
                          <Chip label={activity.duration} size="small" variant="outlined" />
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Activity Summary</Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary">Tasks Today</Typography>
              <Typography variant="h4" color="primary">12</Typography>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary">This Week</Typography>
              <Typography variant="h4" color="success.main">67</Typography>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary">This Month</Typography>
              <Typography variant="h4" color="info.main">289</Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">Average Daily Tasks</Typography>
              <Typography variant="h6">9.6</Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="text.secondary">Peak Performance Hour</Typography>
              <Typography variant="h6">2:00 PM - 3:00 PM</Typography>
            </Box>
          </CardContent>
        </Card>
        
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Quick Actions</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Button variant="outlined" startIcon={<Assessment />}>
                View Full Report
              </Button>
              <Button variant="outlined" startIcon={<Timeline />}>
                Performance History
              </Button>
              <Button variant="outlined" startIcon={<Visibility />}>
                Audit Trail
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default AgentProfile;