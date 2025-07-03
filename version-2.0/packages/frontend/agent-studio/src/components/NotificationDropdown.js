/**
 * Notification Dropdown Component
 * 
 * Shows recent activity in a dropdown from the navigation header
 */
import React, { useState, useEffect } from 'react';
import {
  IconButton,
  Menu,
  MenuList,
  MenuItem,
  Typography,
  Box,
  Avatar,
  Badge,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  useTheme,
  alpha,
  Grow
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  SmartToy as SmartToyIcon,
  RocketLaunch as RocketLaunchIcon,
  WhatsApp as WhatsAppIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { useAuth } from '../utils/AuthContext';
import { collection, query, where, orderBy, limit, onSnapshot } from 'firebase/firestore';
import { db } from '../utils/firebase';

const NotificationDropdown = () => {
  const theme = useTheme();
  const { currentUser } = useAuth();
  const [anchorEl, setAnchorEl] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [userAgentIds, setUserAgentIds] = useState(new Set());

  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  // Helper function to format time ago
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Just now';
    
    const now = new Date();
    const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  useEffect(() => {
    if (!currentUser) return;

    let unsubscribeAgents, unsubscribeDeployments, unsubscribePhones;

    // First get user's agents to track their deployments
    const agentsRef = collection(db, 'agents');
    const agentsQuery = query(
      agentsRef,
      where('userId', '==', currentUser.uid)
    );

    unsubscribeAgents = onSnapshot(agentsQuery, (snapshot) => {
      const agentIds = snapshot.docs.map(doc => doc.id);
      setUserAgentIds(new Set(agentIds));

      // Load deployment activity for user's agents
      if (agentIds.length > 0) {
        const deploymentsRef = collection(db, 'deployments');
        const deploymentsQuery = query(
          deploymentsRef,
          where('agentId', 'in', agentIds),
          orderBy('created_at', 'desc'),
          limit(5)
        );

        unsubscribeDeployments = onSnapshot(
          deploymentsQuery,
          (deploymentSnapshot) => {
            const deploymentActivity = deploymentSnapshot.docs.map(doc => {
              const deployment = doc.data();
              return {
                id: `deployment-${doc.id}`,
                title: `${deployment.agentName || 'Agent'} ${deployment.status === 'completed' || deployment.status === 'deployed' ? 'deployed successfully' : deployment.status === 'failed' ? 'deployment failed' : `deployment ${deployment.status}`}`,
                time: formatTimeAgo(deployment.created_at),
                icon: <RocketLaunchIcon />,
                color: deployment.status === 'completed' || deployment.status === 'deployed' ? 'success' : 
                      deployment.status === 'failed' ? 'error' : 'info'
              };
            });
            
            setRecentActivity(prev => [...prev.filter(a => !a.id.startsWith('deployment-')), ...deploymentActivity]);
          },
          (error) => {
            console.error('Error in deployments snapshot listener:', error);
          }
        );
      }

      // Load phone verification activity
      const phonesRef = collection(db, 'phone_verifications');
      const phonesQuery = query(
        phonesRef,
        where('userId', '==', currentUser.uid),
        orderBy('updated_at', 'desc'),
        limit(3)
      );
      
      unsubscribePhones = onSnapshot(
        phonesQuery,
        (phoneSnapshot) => {
          const phoneActivity = phoneSnapshot.docs.map(doc => {
            const phone = doc.data();
            return {
              id: `phone-${doc.id}`,
              title: `WhatsApp number ${phone.phone_number} ${phone.verified ? 'verified' : 'verification pending'}`,
              time: formatTimeAgo(phone.verified_at || phone.updated_at),
              icon: <WhatsAppIcon />,
              color: 'info'
            };
          });
          
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
      
      onSnapshot(
        recentAgentsQuery,
        (agentSnapshot) => {
          const agentActivity = agentSnapshot.docs.map(doc => {
            const agent = doc.data();
            return {
              id: `agent-${doc.id}`,
              title: `Created agent "${agent.name || 'Unnamed Agent'}"`,
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
    });

    return () => {
      unsubscribeAgents && unsubscribeAgents();
      unsubscribeDeployments && unsubscribeDeployments();
      unsubscribePhones && unsubscribePhones();
    };
  }, [currentUser]);

  // Sort activities by time (most recent first)
  const sortedActivity = recentActivity.sort((a, b) => {
    // Simple sorting by ID timestamp (newer activities have higher IDs)
    return b.id.localeCompare(a.id);
  });

  return (
    <>
      <IconButton
        onClick={handleClick}
        sx={{
          color: theme.palette.text.primary,
          bgcolor: 'transparent',
          border: `1px solid ${theme.palette.mode === 'dark' ? '#333333' : '#e5e7eb'}`,
          '&:hover': {
            bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb'
          }
        }}
      >
        <Badge 
          badgeContent={sortedActivity.length > 0 ? sortedActivity.length : null} 
          color="primary"
          max={9}
        >
          <NotificationsIcon />
        </Badge>
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            borderRadius: 2,
            mt: 1,
            minWidth: 350,
            maxWidth: 400,
            maxHeight: 400,
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.12)',
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
          }
        }}
      >
        <Box sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f9fafb' }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📈 Recent Activity
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Latest updates from your AI workforce
          </Typography>
        </Box>
        <Divider />
        
        <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
          {sortedActivity.length > 0 ? (
            <List sx={{ p: 0 }}>
              {sortedActivity.slice(0, 10).map((activity, index) => (
                <Grow in={true} timeout={200 + index * 50} key={activity.id}>
                  <ListItem sx={{ px: 2, py: 1.5 }}>
                    <ListItemIcon sx={{ minWidth: 40 }}>
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
                      primaryTypographyProps={{ 
                        fontSize: '0.9rem',
                        fontWeight: 500
                      }}
                      secondaryTypographyProps={{ 
                        fontSize: '0.8rem',
                        color: 'text.secondary'
                      }}
                    />
                  </ListItem>
                </Grow>
              ))}
            </List>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4, px: 2 }}>
              <TimelineIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No recent activity
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Activity will appear here as you use your agents
              </Typography>
            </Box>
          )}
        </Box>
      </Menu>
    </>
  );
};

export default NotificationDropdown;