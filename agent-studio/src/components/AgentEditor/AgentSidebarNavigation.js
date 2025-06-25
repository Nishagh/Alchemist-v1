/**
 * Agent Sidebar Navigation
 * 
 * Left sidebar navigation component for the Agent Editor
 * Replaces the tab-based navigation with a more scalable sidebar approach
 */
import React, { useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Drawer,
  IconButton,
  Typography,
  Collapse,
  useTheme,
  useMediaQuery,
  alpha,
  Tooltip
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  BugReport as BugReportIcon,
  Tune as TuneIcon,
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  ExpandLess,
  ExpandMore
} from '@mui/icons-material';

// Import AgentConfigurationForm component
import AgentConfigurationForm from './AgentConfiguration/AgentConfigurationForm';

const SIDEBAR_WIDTH = 420;
const SIDEBAR_COLLAPSED_WIDTH = 64;

const navigationItems = [
  {
    id: 'definition',
    label: 'Agent Definition',
    icon: AutoAwesomeIcon,
    description: 'Configure agent behavior and personality'
  },
  {
    id: 'knowledge',
    label: 'Knowledge Base',
    icon: StorageIcon,
    description: 'Manage agent knowledge and documents'
  },
  {
    id: 'api',
    label: 'API Integration',
    icon: ApiIcon,
    description: 'Connect external APIs and services'
  },
  {
    id: 'testing',
    label: 'Pre-deployment Testing',
    icon: BugReportIcon,
    description: 'Test and validate agent responses'
  },
  {
    id: 'fine-tuning',
    label: 'Fine-tuning',
    icon: TuneIcon,
    description: 'Optimize agent responses with custom training'
  }
];

const AgentSidebarNavigation = ({ 
  activeSection, 
  onSectionChange, 
  children,
  disabled = false,
  workflow = null,
  agent = null,
  onAgentUpdate = null,
  onAgentSave = null,
  saving = false
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [expandedSections, setExpandedSections] = useState(new Set());

  const handleSectionChange = (sectionId) => {
    if (!disabled) {
      onSectionChange(sectionId);
      if (isMobile) {
        setMobileOpen(false);
      }
    }
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleCollapse = () => {
    setCollapsed(!collapsed);
  };

  const toggleSection = (sectionId) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const getVisibleNavigationItems = () => {
    return navigationItems;
  };

  const NavigationContent = ({ isCollapsed = false }) => (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box 
        sx={{ 
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
          borderBottom: `1px solid ${theme.palette.divider}`,
          minHeight: 64
        }}
      >
        {!isCollapsed && (
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 600,
              color: 'text.primary'
            }}
          >
            Agent Editor
          </Typography>
        )}
        {!isMobile && (
          <IconButton 
            onClick={handleCollapse}
            size="small"
            sx={{ 
              color: 'text.secondary',
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.1)
              }
            }}
          >
            {isCollapsed ? <MenuIcon /> : <ChevronLeftIcon />}
          </IconButton>
        )}
      </Box>

      {/* Workflow Status - Compact overview when not on definition page */}
      {!isCollapsed && activeSection !== 'definition' && workflow && (
        <Box sx={{ 
          p: 2, 
          borderBottom: `1px solid ${theme.palette.divider}`,
          bgcolor: alpha(theme.palette.primary.main, 0.02)
        }}>
          <Typography 
            variant="subtitle2" 
            sx={{ 
              fontWeight: 600,
              mb: 1,
              color: 'text.primary'
            }}
          >
            Workflow Status
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {workflow.stages.map(stage => (
              <Box
                key={stage.id}
                sx={{
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  fontSize: '0.75rem',
                  bgcolor: stage.completed 
                    ? alpha(theme.palette.success.main, 0.1)
                    : stage.current 
                      ? alpha(theme.palette.primary.main, 0.1)
                      : alpha(theme.palette.grey[500], 0.1),
                  color: stage.completed 
                    ? 'success.main'
                    : stage.current 
                      ? 'primary.main'
                      : 'text.secondary'
                }}
              >
                {stage.name}
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Navigation Items */}
      <List sx={{ flex: 1, py: 1 }}>
        {getVisibleNavigationItems().map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id || (item.subItems && item.subItems.some(sub => activeSection === sub.id));
          const isExpanded = expandedSections.has(item.id);
          const hasSubItems = item.subItems && item.subItems.length > 0;

          return (
            <Box key={item.id}>
              <Tooltip 
                title={isCollapsed ? item.label : ''} 
                placement="right"
                disableHoverListener={!isCollapsed}
              >
                <ListItem disablePadding sx={{ px: 1 }}>
                  <ListItemButton
                    onClick={() => {
                      if (hasSubItems) {
                        toggleSection(item.id);
                      } else {
                        handleSectionChange(item.id);
                      }
                    }}
                    disabled={disabled}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      minHeight: 48,
                      bgcolor: isActive ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
                      color: isActive ? 'primary.main' : 'text.primary',
                      '&:hover': {
                        bgcolor: isActive 
                          ? alpha(theme.palette.primary.main, 0.15)
                          : alpha(theme.palette.action.hover, 0.1)
                      },
                      '&.Mui-disabled': {
                        color: 'text.disabled'
                      },
                      px: isCollapsed ? 1 : 2
                    }}
                  >
                    <ListItemIcon 
                      sx={{ 
                        color: 'inherit',
                        minWidth: isCollapsed ? 0 : 40,
                        justifyContent: 'center'
                      }}
                    >
                      <Icon />
                    </ListItemIcon>
                    {!isCollapsed && (
                      <>
                        <ListItemText 
                          primary={item.label}
                          secondary={item.description}
                          primaryTypographyProps={{
                            fontWeight: isActive ? 600 : 500,
                            fontSize: '0.9rem'
                          }}
                          secondaryTypographyProps={{
                            fontSize: '0.75rem',
                            sx: { mt: 0.5 }
                          }}
                        />
                        {hasSubItems && (
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSection(item.id);
                            }}
                          >
                            {isExpanded ? <ExpandLess /> : <ExpandMore />}
                          </IconButton>
                        )}
                      </>
                    )}
                  </ListItemButton>
                </ListItem>
              </Tooltip>

              {/* Sub Items */}
              {hasSubItems && !isCollapsed && (
                <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding sx={{ pl: 2 }}>
                    {item.subItems.map((subItem) => {
                      const SubIcon = subItem.icon;
                      const isSubActive = activeSection === subItem.id;
                      
                      return (
                        <ListItem key={subItem.id} disablePadding sx={{ px: 1 }}>
                          <ListItemButton
                            onClick={() => handleSectionChange(subItem.id)}
                            disabled={disabled}
                            sx={{
                              borderRadius: 1,
                              mb: 0.5,
                              minHeight: 40,
                              bgcolor: isSubActive ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
                              color: isSubActive ? 'primary.main' : 'text.primary',
                              '&:hover': {
                                bgcolor: isSubActive 
                                  ? alpha(theme.palette.primary.main, 0.15)
                                  : alpha(theme.palette.action.hover, 0.1)
                              },
                              '&.Mui-disabled': {
                                color: 'text.disabled'
                              },
                              px: 2
                            }}
                          >
                            <ListItemIcon 
                              sx={{ 
                                color: 'inherit',
                                minWidth: 36,
                                justifyContent: 'center'
                              }}
                            >
                              <SubIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={subItem.label}
                              secondary={subItem.description}
                              primaryTypographyProps={{
                                fontWeight: isSubActive ? 600 : 500,
                                fontSize: '0.85rem'
                              }}
                              secondaryTypographyProps={{
                                fontSize: '0.7rem',
                                sx: { mt: 0.5 }
                              }}
                            />
                          </ListItemButton>
                        </ListItem>
                      );
                    })}
                  </List>
                </Collapse>
              )}
            </Box>
          );
        })}
      </List>

      {/* Agent Configuration Form - only show on definition section and when not collapsed */}
      {!isCollapsed && activeSection === 'definition' && agent && onAgentUpdate && onAgentSave && (
        <Box sx={{ 
          borderTop: `1px solid ${theme.palette.divider}`,
          p: 2,
          maxHeight: '50vh',
          overflow: 'auto'
        }}>
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 600,
              mb: 2,
              color: 'text.primary'
            }}
          >
            Agent Configuration
          </Typography>
          <AgentConfigurationForm
            agent={agent}
            onAgentUpdate={onAgentUpdate}
            onSave={onAgentSave}
            saving={saving}
            disabled={disabled}
            compact={true}
          />
        </Box>
      )}

      {/* Footer */}
      {!isCollapsed && (
        <Box sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
          <Typography 
            variant="caption" 
            color="text.secondary"
            sx={{ display: 'block', textAlign: 'center' }}
          >
            Agent Editor v2.0
          </Typography>
        </Box>
      )}
    </Box>
  );

  const drawer = (
    <NavigationContent isCollapsed={!isMobile && collapsed} />
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* Mobile Menu Button */}
      {isMobile && (
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={handleDrawerToggle}
          sx={{ 
            position: 'fixed',
            top: 16,
            left: 16,
            zIndex: theme.zIndex.drawer + 1,
            bgcolor: 'background.paper',
            boxShadow: 2,
            '&:hover': {
              bgcolor: 'background.paper'
            }
          }}
        >
          <MenuIcon />
        </IconButton>
      )}

      {/* Desktop Sidebar */}
      {!isMobile && (
        <Drawer
          variant="permanent"
          sx={{
            width: collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH,
              boxSizing: 'border-box',
              bgcolor: 'background.paper',
              borderRight: `1px solid ${theme.palette.divider}`,
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            },
          }}
        >
          {drawer}
        </Drawer>
      )}

      {/* Mobile Sidebar */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            '& .MuiDrawer-paper': {
              width: SIDEBAR_WIDTH,
              boxSizing: 'border-box',
              bgcolor: 'background.paper',
            },
          }}
        >
          {drawer}
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ml: isMobile ? 0 : 0, // No margin on mobile, handled by drawer positioning
          pt: isMobile ? 8 : 0, // Add top padding on mobile for menu button
        }}
      >
        {/* Render the active section content */}
        <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default AgentSidebarNavigation;