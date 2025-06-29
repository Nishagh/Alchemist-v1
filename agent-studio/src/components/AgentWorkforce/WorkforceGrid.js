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
  Menu,
  ListItemIcon,
  ListItemText,
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
  AutoAwesome as AutoAwesomeIcon,
  Delete as DeleteIcon,
  Assignment as AssignmentIcon,
  Launch as LaunchIcon,
  Settings as SettingsIcon
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
  const [actionMenuAnchor, setActionMenuAnchor] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);

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

  const handleActionMenu = (event, agent) => {
    event.stopPropagation();
    setActionMenuAnchor(event.currentTarget);
    setSelectedAgent(agent);
  };

  const closeActionMenu = () => {
    setActionMenuAnchor(null);
    setSelectedAgent(null);
  };

  const EmployeeCard = ({ agent, index }) => {
    const identity = agentIdentities[agent.id];
    const jobTitle = generateJobTitle(agent.id);
    const profileColor = generateProfilePicture(identity);
    
    // Check if agent is deployed/active to show meaningful metrics
    const isDeployed = agent.status === 'deployed' || agent.status === 'active';
    const agentData = workforceData[agent.id];
    const hasConversations = agentData?.conversations?.length > 0;
    
    // Only calculate metrics for deployed agents with conversations
    const experience = isDeployed && hasConversations ? calculateExperienceYears(agent.id) : 0;
    const costs = isDeployed && hasConversations ? calculateUsageCosts(agent.id) : 0;
    const performance = isDeployed && hasConversations ? getPerformanceScore(agent.id) : 0;
    
    if (viewMode === 'list') {
      return (
        <Card sx={{ mb: 1 }}>
          <CardContent sx={{ py: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                <Badge
                  badgeContent={identity?.development_stage?.charAt(0)?.toUpperCase()}
                  color={isDeployed ? "primary" : "default"}
                  overlap="circular"
                  sx={{
                    '& .MuiBadge-badge': {
                      opacity: isDeployed ? 1 : 0.6
                    }
                  }}
                >
                  <Avatar sx={{ 
                    bgcolor: isDeployed ? profileColor : '#9e9e9e', 
                    width: 50, 
                    height: 50,
                    opacity: isDeployed ? 1 : 0.6
                  }}>
                    <SmartToyIcon sx={{ color: isDeployed ? 'inherit' : '#666666' }} />
                  </Avatar>
                </Badge>
                
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography 
                      variant="h6" 
                      fontWeight="bold"
                      sx={{ opacity: isDeployed ? 1 : 0.7 }}
                    >
                      {agent.name || 'Unnamed Agent'}
                    </Typography>
                    <Chip 
                      label={agent.status || 'Draft'} 
                      size="small" 
                      color={getStatusColor(agent.status)}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {jobTitle}
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', minWidth: 80 }}>
                  <Typography variant="body2" color="text.secondary">Experience</Typography>
                  <Typography variant="h6">
                    {isDeployed && hasConversations ? `${experience} yrs` : '-'}
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', minWidth: 100 }}>
                  <Typography variant="body2" color="text.secondary">Usage Cost</Typography>
                  <Typography variant="h6" color={isDeployed && hasConversations ? "warning.main" : "text.disabled"}>
                    {isDeployed && hasConversations ? `₹${costs.toLocaleString('en-IN')}` : '-'}
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', minWidth: 80 }}>
                  <Typography variant="body2" color="text.secondary">Performance</Typography>
                  <Typography variant="h6" color={isDeployed && hasConversations ? (performance >= 90 ? 'success.main' : performance >= 75 ? 'warning.main' : 'error.main') : 'text.disabled'}>
                    {isDeployed && hasConversations ? `${performance}%` : '-'}
                  </Typography>
                </Box>
              </Box>
              
              {showActions && (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="View Profile">
                    <IconButton onClick={() => navigate(`/agent-profile/${agent.id}`)}>
                      <VisibilityIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Manage Agent">
                    <IconButton onClick={() => navigate(`/agent/${agent.id}`)}>
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <IconButton onClick={(e) => handleActionMenu(e, agent)}>
                    <MoreVertIcon />
                  </IconButton>
                </Box>
              )}
            </Box>
            
            {!isDeployed && (
              <Box sx={{ mt: 2, p: 1, bgcolor: 'background.default', borderRadius: 1, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  Deploy this agent to see usage metrics
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      );
    }
    
    return (
      <Grow in={true} timeout={300 + index * 50}>
        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <CardContent sx={{ flexGrow: 1 }}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Badge
                badgeContent={identity?.development_stage}
                color={isDeployed ? "primary" : "default"}
                overlap="circular"
                sx={{
                  '& .MuiBadge-badge': {
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    opacity: isDeployed ? 1 : 0.6
                  }
                }}
              >
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    bgcolor: isDeployed ? profileColor : '#9e9e9e',
                    mx: 'auto',
                    border: '3px solid',
                    borderColor: 'background.paper',
                    boxShadow: 2,
                    opacity: isDeployed ? 1 : 0.6
                  }}
                >
                  <SmartToyIcon sx={{ fontSize: '2rem', color: isDeployed ? 'inherit' : '#666666' }} />
                </Avatar>
              </Badge>
              
              <Typography 
                variant="h6" 
                fontWeight="bold" 
                sx={{ 
                  mt: 1,
                  opacity: isDeployed ? 1 : 0.7
                }}
              >
                {agent.name || 'Unnamed Agent'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {jobTitle}
              </Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Experience</Typography>
                  <Typography variant="h6">
                    {isDeployed && hasConversations ? `${experience} yrs` : '-'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Performance</Typography>
                  <Typography 
                    variant="h6" 
                    color={isDeployed && hasConversations ? (performance >= 90 ? 'success.main' : performance >= 75 ? 'warning.main' : 'error.main') : 'text.disabled'}
                  >
                    {isDeployed && hasConversations ? `${performance}%` : '-'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Typography variant="body2" color="text.secondary">Usage Cost</Typography>
              <Typography variant="h5" color={isDeployed && hasConversations ? "warning.main" : "text.disabled"} fontWeight="bold">
                {isDeployed && hasConversations ? `₹${costs.toLocaleString('en-IN')}` : '-'}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Chip 
                label={agent.status || 'Draft'} 
                size="small" 
                color={getStatusColor(agent.status)}
              />
              {identity?.dominant_personality_traits?.slice(0, 2).map((trait, idx) => (
                <Chip
                  key={idx}
                  label={trait}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
            
            {!isDeployed && (
              <Box sx={{ textAlign: 'center', mt: 2, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Deploy this agent to see usage metrics
                </Typography>
              </Box>
            )}
          </CardContent>
          
          {showActions && (
            <CardActions sx={{ justifyContent: 'center', gap: 1 }}>
              <Button
                size="small"
                startIcon={<VisibilityIcon />}
                onClick={() => navigate(`/agent-profile/${agent.id}`)}
              >
                Profile
              </Button>
              <Button
                size="small"
                startIcon={<EditIcon />}
                onClick={() => navigate(`/agent/${agent.id}`)}
              >
                Manage
              </Button>
              <IconButton
                size="small"
                onClick={(e) => handleActionMenu(e, agent)}
              >
                <MoreVertIcon />
              </IconButton>
            </CardActions>
          )}
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
        PaperProps={{
          sx: { minWidth: 200 }
        }}
      >
        <MenuItem onClick={() => {
          navigate(`/agent-profile/${selectedAgent?.id}`);
          closeActionMenu();
        }}>
          <ListItemIcon><VisibilityIcon fontSize="small" /></ListItemIcon>
          <ListItemText>View Profile</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => {
          navigate(`/agent/${selectedAgent?.id}`);
          closeActionMenu();
        }}>
          <ListItemIcon><EditIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Manage Agent</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => {
          navigate(`/agent-deployment/${selectedAgent?.id}`);
          closeActionMenu();
        }}>
          <ListItemIcon><LaunchIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Deploy</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => {
          // Handle delete action
          closeActionMenu();
        }}>
          <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon>
          <ListItemText>Delete Agent</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
};

export default WorkforceGrid;