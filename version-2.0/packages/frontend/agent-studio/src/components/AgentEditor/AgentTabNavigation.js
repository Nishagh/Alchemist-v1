/**
 * Agent Tab Navigation
 * 
 * Tab navigation component for the Agent Editor
 */
import React from 'react';
import {
  Tabs,
  Tab,
  Box,
  useTheme,
  alpha
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  BugReport as BugReportIcon
} from '@mui/icons-material';

const TabPanel = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`agent-tabpanel-${index}`}
      aria-labelledby={`agent-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const AgentTabNavigation = ({ 
  activeTab, 
  onTabChange, 
  children,
  disabled = false 
}) => {
  const theme = useTheme();

  const handleTabChange = (event, newValue) => {
    if (!disabled) {
      onTabChange(newValue);
    }
  };

  const tabProps = (index) => ({
    id: `agent-tab-${index}`,
    'aria-controls': `agent-tabpanel-${index}`,
  });

  return (
    <Box sx={{ width: '100%' }}>
      {/* Tab Navigation */}
      <Box 
        sx={{ 
          borderBottom: 1, 
          borderColor: 'divider',
          bgcolor: alpha(theme.palette.background.paper, 0.5),
          borderRadius: '8px 8px 0 0',
          px: 2
        }}
      >
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              minHeight: 60,
              fontSize: '0.95rem',
              fontWeight: 600,
              textTransform: 'none',
              color: 'text.secondary',
              '&.Mui-selected': {
                color: 'primary.main',
                fontWeight: 700
              },
              '&.Mui-disabled': {
                color: 'text.disabled'
              }
            },
            '& .MuiTabs-indicator': {
              height: 3,
              borderRadius: '3px 3px 0 0'
            }
          }}
        >
          <Tab 
            icon={<AutoAwesomeIcon />} 
            label="Agent Definition" 
            iconPosition="start"
            disabled={disabled}
            {...tabProps(0)} 
          />
          <Tab 
            icon={<StorageIcon />} 
            label="Knowledge Base" 
            iconPosition="start"
            disabled={disabled}
            {...tabProps(1)} 
          />
          <Tab 
            icon={<ApiIcon />} 
            label="API Integration" 
            iconPosition="start"
            disabled={disabled}
            {...tabProps(2)} 
          />
          <Tab 
            icon={<BugReportIcon />} 
            label="Agent Testing" 
            iconPosition="start"
            disabled={disabled}
            {...tabProps(3)} 
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <Box 
        sx={{ 
          bgcolor: 'background.paper',
          borderRadius: '0 0 8px 8px',
          minHeight: '600px'
        }}
      >
        {React.Children.map(children, (child, index) => (
          <TabPanel value={activeTab} index={index} key={index}>
            {child}
          </TabPanel>
        ))}
      </Box>
    </Box>
  );
};

export { TabPanel };
export default AgentTabNavigation;