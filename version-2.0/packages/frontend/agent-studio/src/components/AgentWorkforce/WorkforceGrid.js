/**
 * Workforce Grid Component
 * 
 * Displays AI agents as employee cards with comprehensive workforce metrics
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Avatar,
  Chip,
  Badge,
  LinearProgress,
  Divider,
  IconButton,
  Tooltip,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grow,
  alpha,
  useTheme
} from '@mui/material';
import {
  SmartToy as SmartToyIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
  AttachMoney as AttachMoneyIcon,
  TrendingUp as TrendingUpIcon,
  Star as StarIcon,
  Shield as ShieldIcon,
  Work as WorkIcon,
  Group as GroupIcon,
  BarChart as BarChartIcon,
  AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';
import { gnfApi } from '../../services/config/apiConfig';
import { workforceService } from '../../services/workforce/workforceService';

const WorkforceGrid = ({ 
  agents, 
  loading, 
  viewMode = 'grid',
  searchTerm = '',
  sortBy = 'name',
  statusFilter = 'all',
  showActions = true,
  maxItems = null,
  workforceData: externalWorkforceData = null,
  agentIdentities: externalAgentIdentities = null
}) => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [agentIdentities, setAgentIdentities] = useState({});
  const [workforceData, setWorkforceData] = useState({});
  const [identitiesLoading, setIdentitiesLoading] = useState(true);
  
  // Add totalTasks to component scope
  const getTotalTasks = (agentId) => {
    const agentData = workforceData[agentId];
    return agentData?.conversations?.length || 0;
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

  const getAgentProfilePicture = (agent) => {
    // Return the agent's profile picture URL if available
    return agent.profilePictureUrl || agent.profile_picture_url || null;
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

  // Load real workforce data
  useEffect(() => {
    // Use external data if provided, otherwise load our own
    if (externalWorkforceData && externalAgentIdentities) {
      setWorkforceData(externalWorkforceData);
      setAgentIdentities(externalAgentIdentities);
      setIdentitiesLoading(false);
      return;
    }

    const loadRealWorkforceData = async () => {
      if (agents.length === 0) {
        setIdentitiesLoading(false);
        return;
      }

      try {
        const identities = {};
        const workforceDataMap = {};
        
        for (const agent of agents) {
          try {
            // Get comprehensive workforce data for each agent
            const agentData = await workforceService.getAgentWorkforceData(agent.id, agent.userId);
            workforceDataMap[agent.id] = agentData;
            identities[agent.id] = agentData.identity;
          } catch (error) {
            console.warn(`Failed to load workforce data for agent ${agent.id}:`, error);
            // Don't set fallback data - let the error propagate
            throw error;
          }
        }
        
        setWorkforceData(workforceDataMap);
        setAgentIdentities(identities);
      } catch (error) {
        console.error('Error loading workforce data:', error);
      } finally {
        setIdentitiesLoading(false);
      }
    };

    loadRealWorkforceData();
  }, [agents, externalWorkforceData, externalAgentIdentities]);

  // Filter and sort agents
  const filterAgents = () => {
    let filtered = agents;
    
    if (searchTerm) {
      filtered = filtered.filter(agent => 
        (agent.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (agent.description || '').toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Filter by status
    if (statusFilter && statusFilter !== 'all') {
      filtered = filtered.filter(agent => {
        const status = agent.status || 'draft';
        return status === statusFilter;
      });
    }
    
    // Sort agents
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.name || '').localeCompare(b.name || '');
        case 'performance':
          return getPerformanceScore(b.id) - getPerformanceScore(a.id);
        case 'costs':
          return calculateUsageCosts(b.id) - calculateUsageCosts(a.id);
        case 'experience':
          return parseFloat(calculateExperienceYears(b.id)) - parseFloat(calculateExperienceYears(a.id));
        default:
          return 0;
      }
    });
    
    if (maxItems) {
      filtered = filtered.slice(0, maxItems);
    }
    
    return filtered;
  };


  const EmployeeCard = ({ agent, index }) => {
    const identity = agentIdentities[agent.id];
    const jobTitle = generateJobTitle(agent.id);
    const profileColor = generateProfilePicture(identity);
    const profilePictureUrl = getAgentProfilePicture(agent);
    
    // Check if agent is deployed/active to show meaningful metrics
    const isDeployed = agent.status === 'deployed' || agent.status === 'active';
    const agentData = workforceData[agent.id];
    const hasConversations = agentData?.conversations?.length > 0;
    
    // Only calculate metrics for deployed agents with conversations
    const experience = isDeployed && hasConversations ? calculateExperienceYears(agent.id) : 0;
    const costs = isDeployed && hasConversations ? calculateUsageCosts(agent.id) : 0;
    const performance = isDeployed && hasConversations ? getPerformanceScore(agent.id) : 0;
    const totalTasks = isDeployed && hasConversations ? getTotalTasks(agent.id) : 0;
    
    if (viewMode === 'list') {
      return (
        <Card 
          sx={{ 
            mb: 1.5,
            border: 1,
            borderColor: isDeployed ? 'primary.light' : 'grey.200',
            borderRadius: 2,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 2,
              transform: 'translateY(-1px)'
            },
            cursor: 'pointer'
          }}
          onClick={() => navigate(`/agent-profile/${agent.id}`)}
        >
          <CardContent sx={{ py: 2.5, px: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              {/* Agent Avatar & Basic Info */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                <Avatar 
                  src={profilePictureUrl}
                  sx={{ 
                    width: 48, 
                    height: 48,
                    bgcolor: profilePictureUrl ? 'transparent' : (isDeployed ? profileColor : 'grey.300'),
                    border: 2,
                    borderColor: isDeployed ? 'primary.main' : 'grey.400',
                    opacity: isDeployed ? 1 : 0.7
                  }}
                >
                  {!profilePictureUrl && <SmartToyIcon sx={{ fontSize: '1.5rem' }} />}
                </Avatar>
                
                <Box sx={{ flex: 1 }}>
                  <Typography 
                    variant="h6" 
                    fontWeight="600"
                    sx={{ 
                      mb: 0.5,
                      color: isDeployed ? 'text.primary' : 'text.secondary'
                    }}
                  >
                    {agent.name || 'Unnamed Agent'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip 
                      label={agent.status || 'Draft'} 
                      size="small" 
                      variant={isDeployed ? 'filled' : 'outlined'}
                      color={getStatusColor(agent.status)}
                      sx={{ fontSize: '0.75rem', height: 24 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {jobTitle}
                    </Typography>
                  </Box>
                </Box>
              </Box>
              
              {/* Metrics - Only show for deployed agents */}
              {isDeployed && hasConversations && (
                <Box sx={{ display: 'flex', gap: 4 }}>
                  <Box sx={{ textAlign: 'center', minWidth: 70 }}>
                    <Typography variant="h6" fontWeight="600" color="primary.main">
                      {performance}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Success
                    </Typography>
                  </Box>
                  
                  <Box sx={{ textAlign: 'center', minWidth: 80 }}>
                    <Typography variant="h6" fontWeight="600" color="warning.main">
                      ₹{costs.toLocaleString('en-IN')}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Usage Cost
                    </Typography>
                  </Box>
                  
                  <Box sx={{ textAlign: 'center', minWidth: 60 }}>
                    <Typography variant="h6" fontWeight="600">
                      {totalTasks}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Tasks
                    </Typography>
                  </Box>
                </Box>
              )}
              
              {/* Draft/Not Deployed State */}
              {!isDeployed && (
                <Box sx={{ textAlign: 'center', px: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    Ready to deploy
                  </Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      );
    }
    
    return (
      <Grow in={true} timeout={300 + index * 50}>
        <Card 
          sx={{ 
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            border: 1,
            borderColor: isDeployed ? 'primary.light' : 'grey.200',
            borderRadius: 3,
            transition: 'all 0.3s ease-in-out',
            cursor: 'pointer',
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 4,
              transform: 'translateY(-4px)'
            },
            overflow: 'hidden'
          }}
          onClick={() => navigate(`/agent-profile/${agent.id}`)}
        >
          {/* Status Bar */}
          <Box 
            sx={{ 
              height: 4,
              bgcolor: isDeployed ? 'primary.main' : 'grey.300',
              width: '100%'
            }} 
          />
          
          <CardContent sx={{ flexGrow: 1, p: 3, textAlign: 'center' }}>
            {/* Avatar */}
            <Box sx={{ mb: 2 }}>
              <Avatar
                src={profilePictureUrl}
                sx={{
                  width: 64,
                  height: 64,
                  bgcolor: profilePictureUrl ? 'transparent' : (isDeployed ? profileColor : 'grey.300'),
                  mx: 'auto',
                  border: 3,
                  borderColor: isDeployed ? 'primary.main' : 'grey.400',
                  boxShadow: isDeployed ? 2 : 1,
                  opacity: isDeployed ? 1 : 0.7,
                  transition: 'all 0.2s ease-in-out'
                }}
              >
                {!profilePictureUrl && <SmartToyIcon sx={{ fontSize: '1.8rem' }} />}
              </Avatar>
            </Box>
            
            {/* Agent Name & Status */}
            <Typography 
              variant="h6" 
              fontWeight="600" 
              sx={{ 
                mb: 0.5,
                color: isDeployed ? 'text.primary' : 'text.secondary',
                lineHeight: 1.2
              }}
            >
              {agent.name || 'Unnamed Agent'}
            </Typography>
            
            <Chip 
              label={agent.status || 'Draft'} 
              size="small" 
              variant={isDeployed ? 'filled' : 'outlined'}
              color={getStatusColor(agent.status)}
              sx={{ 
                mb: 2,
                fontSize: '0.75rem',
                fontWeight: '500'
              }}
            />
            
            {/* Key Metrics for Deployed Agents */}
            {isDeployed && hasConversations ? (
              <Box sx={{ mb: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Typography variant="h6" fontWeight="600" color="primary.main">
                      {performance}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Success Rate
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="h6" fontWeight="600">
                      {totalTasks}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Tasks
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="h6" fontWeight="600" color="warning.main">
                      ₹{Math.round(costs/1000)}k
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Usage
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            ) : (
              <Box sx={{ mb: 2, py: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  {agent.status === 'draft' ? 'Ready to configure' : 'Ready to deploy'}
                </Typography>
              </Box>
            )}
            
            {/* Job Title */}
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ 
                fontSize: '0.875rem',
                fontWeight: '400'
              }}
            >
              {jobTitle}
            </Typography>
          </CardContent>
        </Card>
      </Grow>
    );
  };

  const filteredAgents = filterAgents();

  if (loading || identitiesLoading) {
    return (
      <Grid container spacing={viewMode === 'grid' ? 3 : 1}>
        {[...Array(6)].map((_, index) => (
          <Grid item xs={12} sm={viewMode === 'grid' ? 6 : 12} md={viewMode === 'grid' ? 4 : 12} key={index}>
            <Skeleton variant="rectangular" height={viewMode === 'grid' ? 350 : 80} />
          </Grid>
        ))}
      </Grid>
    );
  }

  return (
    <>
      {filteredAgents.length > 0 ? (
        viewMode === 'grid' ? (
          <Grid container spacing={3}>
            {filteredAgents.map((agent, index) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={agent.id}>
                <EmployeeCard agent={agent} index={index} />
              </Grid>
            ))}
          </Grid>
        ) : (
          <Box>
            {filteredAgents.map((agent, index) => (
              <EmployeeCard key={agent.id} agent={agent} index={index} />
            ))}
          </Box>
        )
      ) : (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <GroupIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h5" color="text.secondary" gutterBottom>
            {agents.length === 0 ? 'No employees yet' : 'No employees match your filters'}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            {agents.length === 0 
              ? 'Start building your AI workforce by hiring your first agent'
              : 'Try adjusting your search or filter criteria'
            }
          </Typography>
        </Box>
      )}
    </>
  );
};

export default WorkforceGrid;