import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  Stack,
  Paper,
  CircularProgress,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as MoneyIcon,
  Message as MessageIcon,
  Token as TokenIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { useAuth } from '../utils/AuthContext';
import { getAgent } from '../services/agents/agentService';
import { 
  getBillingAnalytics,
  getConversationHistory,
  getTestConversationHistory 
} from '../services/conversations/conversationService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

const AgentAnalytics = ({ agentId: propAgentId, embedded = false }) => {
  const { agentId: routeAgentId } = useParams();
  const agentId = propAgentId || routeAgentId;
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  // Core state
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Analytics state
  const [analytics, setAnalytics] = useState({
    totalConversations: 0,
    totalMessages: 0,
    totalTokens: 0,
    totalCost: 0,
    averageTokensPerMessage: 0,
    averageCostPerMessage: 0,
    dailyBreakdown: {}
  });
  
  const [conversationHistory, setConversationHistory] = useState([]);
  const [testConversationHistory, setTestConversationHistory] = useState([]);
  const [timeframe, setTimeframe] = useState('30days');
  const [activeTab, setActiveTab] = useState(0);
  const [showTestData, setShowTestData] = useState(false);

  // Load data
  useEffect(() => {
    const loadData = async () => {
      if (!agentId || !currentUser) return;

      try {
        setLoading(true);
        
        // Load agent details
        const agentData = await getAgent(agentId);
        if (!agentData || agentData.userId !== currentUser.uid) {
          setError('Agent not found or access denied');
          return;
        }
        setAgent(agentData);

        // Load analytics
        await loadAnalytics();

      } catch (err) {
        console.error('Error loading analytics:', err);
        setError('Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [agentId, currentUser, timeframe]);

  const loadAnalytics = async () => {
    try {
      setRefreshing(true);
      
      // Get billing analytics
      const analyticsData = await getBillingAnalytics(agentId, timeframe);
      setAnalytics(analyticsData);

      // Get conversation history (deployed agent)
      const historyData = await getConversationHistory(agentId, { limit: 100 });
      setConversationHistory(historyData);

      // Get test conversation history (pre-deployment)
      const testHistoryData = await getTestConversationHistory(agentId, { limit: 100 });
      setTestConversationHistory(testHistoryData);

    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Failed to load analytics');
    } finally {
      setRefreshing(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleTimeframeChange = (event) => {
    setTimeframe(event.target.value);
  };

  const downloadReport = () => {
    const reportData = {
      agent: {
        id: agent.agent_id,
        name: agent.name,
        model: agent.model
      },
      timeframe,
      analytics,
      conversationHistory: conversationHistory.slice(0, 50),
      generatedAt: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-analytics-${agentId}-${timeframe}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Chart data
  const dailyUsageData = {
    labels: Object.keys(analytics.dailyBreakdown).slice(-7),
    datasets: [
      {
        label: 'Messages',
        data: Object.values(analytics.dailyBreakdown).slice(-7).map(day => day.messages),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1
      },
      {
        label: 'Tokens (÷100)',
        data: Object.values(analytics.dailyBreakdown).slice(-7).map(day => day.tokens / 100),
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.1
      }
    ]
  };

  const costBreakdownData = {
    labels: ['Prompt Tokens', 'Completion Tokens'],
    datasets: [
      {
        data: [
          analytics.totalTokens * 0.4, // Approximate prompt tokens
          analytics.totalTokens * 0.6  // Approximate completion tokens
        ],
        backgroundColor: [
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 99, 132, 0.8)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)'
        ],
        borderWidth: 1
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Daily Usage Trends'
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button 
          variant="outlined" 
          onClick={() => navigate('/agents')}
          sx={{
            color: '#6366f1',
            borderColor: '#6366f1',
            '&:hover': {
              bgcolor: '#6366f115',
              borderColor: '#4f46e5'
            }
          }}
        >
          Back to Agents
        </Button>
      </Container>
    );
  }

  const content = (
    <>
      {/* Header */}
      <Box sx={{ mb: embedded ? 2 : 4 }}>
        <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
          <Box display="flex" alignItems="center" gap={2}>
            {!embedded && (
              <IconButton 
                onClick={() => navigate('/agents')}
                sx={{
                  color: '#6366f1',
                  '&:hover': {
                    bgcolor: '#6366f115',
                    color: '#4f46e5'
                  }
                }}
              >
                <ArrowBackIcon />
              </IconButton>
            )}
            <Box>
              {!embedded && (
                <>
                  <Typography variant="h4" fontWeight="bold">
                    Agent Analytics: {agent?.name}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Billing and usage analytics for your deployed agent
                  </Typography>
                </>
              )}
            </Box>
          </Box>
          
          <Box display="flex" gap={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Timeframe</InputLabel>
              <Select
                value={timeframe}
                onChange={handleTimeframeChange}
                label="Timeframe"
              >
                <MenuItem value="24hours">Last 24 Hours</MenuItem>
                <MenuItem value="7days">Last 7 Days</MenuItem>
                <MenuItem value="30days">Last 30 Days</MenuItem>
              </Select>
            </FormControl>
            
            <Tooltip title="Refresh Data">
              <IconButton 
                onClick={loadAnalytics} 
                disabled={refreshing}
                sx={{
                  color: '#10b981',
                  '&:hover': {
                    bgcolor: '#10b98115',
                    color: '#059669'
                  },
                  '&:disabled': {
                    color: '#9ca3af'
                  }
                }}
              >
                {refreshing ? <CircularProgress size={24} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
            
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={downloadReport}
              sx={{
                color: '#f59e0b',
                borderColor: '#f59e0b',
                '&:hover': {
                  bgcolor: '#f59e0b15',
                  borderColor: '#d97706'
                }
              }}
            >
              Export Report
            </Button>
          </Box>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <MessageIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Messages</Typography>
                </Box>
                <Typography variant="h3" color="primary">
                  {analytics.totalMessages.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {analytics.totalConversations} conversations
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TokenIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Tokens</Typography>
                </Box>
                <Typography variant="h3" color="success.main">
                  {analytics.totalTokens.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg: {analytics.averageTokensPerMessage} per message
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <MoneyIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Cost</Typography>
                </Box>
                <Typography variant="h3" color="warning.main">
                  ${analytics.totalCost.toFixed(4)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg: ${analytics.averageCostPerMessage.toFixed(4)} per message
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TrendingUpIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Efficiency</Typography>
                </Box>
                <Typography variant="h3" color="info.main">
                  {analytics.totalTokens > 0 ? ((analytics.totalCost / analytics.totalTokens) * 1000).toFixed(2) : '0.00'}¢
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  per 1K tokens
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Usage Trends" />
          <Tab label="Cost Analysis" />
          <Tab label="Conversation History" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          {/* Daily Usage Chart */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Daily Usage Trends
                </Typography>
                <Box sx={{ height: 400 }}>
                  <Line data={dailyUsageData} options={chartOptions} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Token Distribution */}
          <Grid item xs={12} lg={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Token Distribution
                </Typography>
                <Box sx={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <Doughnut data={costBreakdownData} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Daily Breakdown Table */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Daily Breakdown
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell align="right">Messages</TableCell>
                        <TableCell align="right">Tokens</TableCell>
                        <TableCell align="right">Cost</TableCell>
                        <TableCell align="right">Avg Cost/Message</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(analytics.dailyBreakdown)
                        .slice(-10)
                        .reverse()
                        .map(([date, data]) => (
                        <TableRow key={date}>
                          <TableCell>{new Date(date).toLocaleDateString()}</TableCell>
                          <TableCell align="right">{data.messages}</TableCell>
                          <TableCell align="right">{data.tokens.toLocaleString()}</TableCell>
                          <TableCell align="right">${data.cost.toFixed(4)}</TableCell>
                          <TableCell align="right">
                            ${data.messages > 0 ? (data.cost / data.messages).toFixed(4) : '0.0000'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 1 && (
        <Grid container spacing={3}>
          {/* Cost Analysis */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Cost Efficiency Analysis</Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Cost per Message
                    </Typography>
                    <Typography variant="h4">
                      ${analytics.averageCostPerMessage.toFixed(4)}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Cost per 1K Tokens
                    </Typography>
                    <Typography variant="h4">
                      ${analytics.totalTokens > 0 ? (analytics.totalCost / analytics.totalTokens * 1000).toFixed(4) : '0.0000'}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Estimated Monthly Cost
                    </Typography>
                    <Typography variant="h4" color="warning.main">
                      ${(analytics.totalCost * 30 / Math.max(Object.keys(analytics.dailyBreakdown).length, 1)).toFixed(2)}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Cost Optimization Tips</Typography>
                <Stack spacing={2}>
                  <Alert severity="info">
                    <Typography variant="body2">
                      <strong>Optimize System Prompts:</strong> Shorter, more focused prompts can reduce token usage.
                    </Typography>
                  </Alert>
                  
                  <Alert severity="success">
                    <Typography variant="body2">
                      <strong>Use GPT-3.5 for Simple Tasks:</strong> Consider using GPT-3.5 for basic queries to reduce costs.
                    </Typography>
                  </Alert>
                  
                  <Alert severity="warning">
                    <Typography variant="body2">
                      <strong>Monitor Usage:</strong> Set up alerts when daily costs exceed your budget.
                    </Typography>
                  </Alert>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 2 && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Recent Conversations
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={showTestData}
                    onChange={(e) => setShowTestData(e.target.checked)}
                  />
                }
                label="Include Pre-deployment Tests"
              />
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>User Message</TableCell>
                    <TableCell>Agent Response</TableCell>
                    <TableCell align="right">Tokens</TableCell>
                    <TableCell align="right">Cost</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(showTestData 
                    ? [...conversationHistory, ...testConversationHistory]
                      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                    : conversationHistory
                  ).slice(0, 20).map((conversation, index) => (
                    <TableRow key={conversation.id || index}>
                      <TableCell>
                        {new Date(conversation.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell sx={{ maxWidth: 200 }}>
                        <Typography variant="body2" noWrap>
                          {conversation.userMessage}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ maxWidth: 300 }}>
                        <Typography variant="body2" noWrap>
                          {conversation.agentResponse}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {conversation.tokens?.total || 0}
                      </TableCell>
                      <TableCell align="right">
                        ${(conversation.cost || 0).toFixed(4)}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={
                            conversation.deploymentType === 'pre-deployment' 
                              ? 'Pre-deployment Test' 
                              : conversation.isProduction 
                                ? 'Production' 
                                : 'Development'
                          } 
                          color={
                            conversation.deploymentType === 'pre-deployment' 
                              ? 'info' 
                              : conversation.isProduction 
                                ? 'success' 
                                : 'warning'
                          }
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Test Agent Button */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate(`/agent-testing/${agentId}`)}
          sx={{ 
            mr: 2,
            bgcolor: '#10b981',
            '&:hover': {
              bgcolor: '#059669'
            }
          }}
        >
          Test Agent
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={() => navigate(`/agent-editor/${agentId}`)}
          sx={{
            color: '#6b7280',
            borderColor: '#6b7280',
            '&:hover': {
              bgcolor: '#6b728015',
              borderColor: '#4b5563'
            }
          }}
        >
          Edit Agent
        </Button>
      </Box>
    </>
  );

  return embedded ? content : <Container maxWidth="xl" sx={{ py: 4 }}>{content}</Container>;
};

export default AgentAnalytics;