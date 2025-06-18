/**
 * Thought Process Display
 * 
 * Component to visualize AI reasoning steps and thought process
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  IconButton,
  Collapse,
  Fade
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Lightbulb as LightbulbIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';

const ThoughtProcessDisplay = ({ thoughtProcess = [] }) => {
  const [expanded, setExpanded] = useState(false);
  const [visible, setVisible] = useState(true);

  if (!thoughtProcess || thoughtProcess.length === 0) {
    return null;
  }

  const handleToggleVisibility = () => {
    setVisible(!visible);
  };

  const renderThoughtStep = (step, index) => {
    const getStepIcon = (type) => {
      switch (type?.toLowerCase()) {
        case 'analysis':
          return <PsychologyIcon sx={{ fontSize: 16 }} />;
        case 'decision':
          return <LightbulbIcon sx={{ fontSize: 16 }} />;
        case 'action':
          return <TimelineIcon sx={{ fontSize: 16 }} />;
        default:
          return <PsychologyIcon sx={{ fontSize: 16 }} />;
      }
    };

    const getStepColor = (type) => {
      switch (type?.toLowerCase()) {
        case 'analysis':
          return 'info';
        case 'decision':
          return 'warning';
        case 'action':
          return 'success';
        default:
          return 'default';
      }
    };

    return (
      <Fade in={true} key={index} timeout={300 + index * 100}>
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Chip
              icon={getStepIcon(step.type)}
              label={step.type || 'Thought'}
              size="small"
              color={getStepColor(step.type)}
              variant="outlined"
              sx={{ mr: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              Step {index + 1}
              {step.timestamp && (
                <> • {new Date(step.timestamp).toLocaleTimeString()}</>
              )}
            </Typography>
          </Box>
          
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              bgcolor: 'background.default',
              borderRadius: 1,
              ml: 2
            }}
          >
            <Typography
              variant="body2"
              sx={{
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6,
                fontSize: '0.875rem'
              }}
            >
              {step.content || step.description || step.text}
            </Typography>
            
            {step.confidence && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Confidence: {(step.confidence * 100).toFixed(0)}%
                </Typography>
              </Box>
            )}
          </Paper>
        </Box>
      </Fade>
    );
  };

  return (
    <Box sx={{ p: 3, bgcolor: 'background.default' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <PsychologyIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
            AI Thought Process
          </Typography>
          <Chip 
            label={`${thoughtProcess.length} steps`} 
            size="small" 
            variant="outlined" 
            sx={{ ml: 2 }}
          />
        </Box>
        
        <IconButton
          onClick={handleToggleVisibility}
          size="small"
          sx={{ color: 'text.secondary' }}
        >
          {visible ? <VisibilityOffIcon /> : <VisibilityIcon />}
        </IconButton>
      </Box>

      <Collapse in={visible}>
        <Box>
          {thoughtProcess.length <= 3 ? (
            // Show all steps if 3 or fewer
            thoughtProcess.map((step, index) => renderThoughtStep(step, index))
          ) : (
            // Use accordion for many steps
            <Accordion
              expanded={expanded}
              onChange={() => setExpanded(!expanded)}
              sx={{
                boxShadow: 'none',
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                '&:before': { display: 'none' }
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  bgcolor: 'background.paper',
                  borderRadius: expanded ? '4px 4px 0 0' : 1,
                  minHeight: 48,
                  '&.Mui-expanded': {
                    minHeight: 48
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                    {expanded ? 'Hide detailed steps' : 'Show detailed thinking process'}
                  </Typography>
                  <Box sx={{ ml: 'auto', mr: 2 }}>
                    {!expanded && renderThoughtStep(thoughtProcess[0], 0)}
                  </Box>
                </Box>
              </AccordionSummary>
              
              <AccordionDetails sx={{ pt: 2 }}>
                <Divider sx={{ mb: 2 }} />
                {thoughtProcess.map((step, index) => renderThoughtStep(step, index))}
              </AccordionDetails>
            </Accordion>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

export default ThoughtProcessDisplay;