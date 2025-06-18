import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Divider,
  Avatar,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  CloudQueue as ServicesIcon,
  Article as LogsIcon,
  Analytics as MetricsIcon,
  Warning as AlertsIcon,
  Settings as SettingsIcon,
  Science as AlchemistIcon,
} from '@mui/icons-material';

const drawerWidth = 280;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Service Status', icon: <ServicesIcon />, path: '/services' },
  { text: 'Log Viewer', icon: <LogsIcon />, path: '/logs' },
  { text: 'Metrics', icon: <MetricsIcon />, path: '/metrics' },
  { text: 'Alerts', icon: <AlertsIcon />, path: '/alerts' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: 'background.paper',
          borderRight: '1px solid #334155',
        },
      }}
    >
      {/* Header */}
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
            <AlchemistIcon />
          </Avatar>
          <Typography variant="h5" fontWeight="bold" color="primary">
            Alchemist
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Admin Dashboard
        </Typography>
      </Box>

      <Divider sx={{ borderColor: '#334155' }} />

      {/* Navigation */}
      <List sx={{ px: 2, py: 1 }}>
        {menuItems.map((item) => (
          <ListItem
            key={item.text}
            onClick={() => navigate(item.path)}
            sx={{
              borderRadius: 2,
              mb: 1,
              cursor: 'pointer',
              backgroundColor: location.pathname === item.path ? 'primary.main' : 'transparent',
              '&:hover': {
                backgroundColor: location.pathname === item.path ? 'primary.dark' : 'action.hover',
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            <ListItemIcon sx={{ 
              color: location.pathname === item.path ? 'white' : 'text.secondary',
              minWidth: 40 
            }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText 
              primary={item.text}
              sx={{
                '& .MuiListItemText-primary': {
                  color: location.pathname === item.path ? 'white' : 'text.primary',
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }
              }}
            />
          </ListItem>
        ))}
      </List>

      {/* Footer */}
      <Box sx={{ mt: 'auto', p: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          v1.0.0 | Admin Panel
        </Typography>
      </Box>
    </Drawer>
  );
}

export default Sidebar;