import React, { useState, useEffect, useRef } from 'react';
import { Chart as ChartJS, registerables } from 'chart.js';
import { Line } from 'react-chartjs-2';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Tooltip,
  IconButton,
  Menu,
  MenuItem
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  MoreVert,
  Refresh
} from '@mui/icons-material';

// Register Chart.js components
ChartJS.register(...registerables);

const StoryLossSparkline = ({ agentId, height = 80, showDetails = false }) => {
  const [storyLossData, setStoryLossData] = useState([]);
  const [currentStoryLoss, setCurrentStoryLoss] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [thresholdExceeded, setThresholdExceeded] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const intervalRef = useRef(null);

  const threshold = 0.15;
  const refreshInterval = 30000; // 30 seconds

  useEffect(() => {
    if (agentId) {
      fetchStoryLossData();
      
      // Set up automatic refresh
      intervalRef.current = setInterval(fetchStoryLossData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [agentId]);

  const fetchStoryLossData = async () => {
    if (!agentId) return;

    try {
      setLoading(true);
      setError(null);

      // Fetch 24-hour story-loss history
      const response = await fetch(`/api/metrics/agent/${agentId}/story-loss?hours=24`);
      const result = await response.json();

      if (result.success) {
        const data = result.data;
        setStoryLossData(data.story_loss_history || []);
        setCurrentStoryLoss(data.current_story_loss);
        setThresholdExceeded(data.threshold_exceeded || false);
        setLastUpdated(new Date());
      } else {
        setError(result.message || 'Failed to fetch story-loss data');
      }
    } catch (err) {
      console.error('Error fetching story-loss data:', err);
      setError('Network error fetching story-loss data');
    } finally {
      setLoading(false);
    }
  };

  const formatDataForChart = () => {
    if (!storyLossData.length) return null;

    // Sort by timestamp
    const sortedData = [...storyLossData].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    );

    // Generate hourly buckets for the last 24 hours
    const now = new Date();
    const hourlyBuckets = [];
    for (let i = 23; i >= 0; i--) {
      const bucketTime = new Date(now.getTime() - i * 60 * 60 * 1000);
      hourlyBuckets.push({
        hour: bucketTime.getHours(),
        timestamp: bucketTime,
        storyLoss: null
      });
    }

    // Fill buckets with data
    sortedData.forEach(point => {
      const pointTime = new Date(point.timestamp);
      const bucketIndex = hourlyBuckets.findIndex(bucket => 
        Math.abs(bucket.timestamp - pointTime) < 30 * 60 * 1000 // Within 30 minutes
      );
      
      if (bucketIndex >= 0) {
        // Use the latest value for this hour
        if (hourlyBuckets[bucketIndex].storyLoss === null || 
            pointTime > new Date(hourlyBuckets[bucketIndex].latestTimestamp || 0)) {
          hourlyBuckets[bucketIndex].storyLoss = point.story_loss;
          hourlyBuckets[bucketIndex].latestTimestamp = pointTime;
        }
      }
    });

    // Create labels and data arrays
    const labels = hourlyBuckets.map(bucket => 
      bucket.timestamp.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    );

    const data = hourlyBuckets.map(bucket => bucket.storyLoss);

    return { labels, data };
  };

  const getChartConfig = () => {
    const chartData = formatDataForChart();
    if (!chartData) return null;

    const { labels, data } = chartData;

    // Color data points based on threshold
    const pointColors = data.map(value => 
      value === null ? 'rgba(158, 158, 158, 0.5)' :
      value > threshold ? '#ef4444' : '#10b981'
    );

    const borderColor = thresholdExceeded ? '#ef4444' : '#10b981';
    const backgroundColor = thresholdExceeded ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)';

    return {
      labels,
      datasets: [
        {
          label: 'Story Loss',
          data,
          borderColor,
          backgroundColor,
          pointBackgroundColor: pointColors,
          pointBorderColor: pointColors,
          pointRadius: showDetails ? 3 : 1,
          pointHoverRadius: 4,
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          spanGaps: true
        },
        // Threshold line
        {
          label: 'Threshold',
          data: new Array(labels.length).fill(threshold),
          borderColor: '#f59e0b',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          pointRadius: 0,
          pointHoverRadius: 0,
          borderWidth: 1
        }
      ]
    };
  };

  const getChartOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index'
    },
    plugins: {
      legend: {
        display: showDetails,
        position: 'top',
        labels: {
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#374151',
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            if (context.datasetIndex === 0) {
              const value = context.parsed.y;
              if (value === null) return 'No data';
              const status = value > threshold ? ' (⚠️ Above threshold)' : ' (✅ Normal)';
              return `Story Loss: ${value.toFixed(3)}${status}`;
            } else {
              return `Threshold: ${threshold}`;
            }
          }
        }
      }
    },
    scales: {
      x: {
        display: showDetails,
        grid: {
          display: false
        },
        ticks: {
          maxTicksLimit: 6
        }
      },
      y: {
        display: showDetails,
        min: 0,
        max: Math.max(0.5, Math.max(...(storyLossData.map(d => d.story_loss) || [0])) * 1.1),
        grid: {
          color: 'rgba(158, 158, 158, 0.2)'
        },
        ticks: {
          stepSize: 0.1,
          callback: (value) => value.toFixed(1)
        }
      }
    },
    elements: {
      line: {
        borderJoinStyle: 'round'
      }
    }
  });

  const getTrendIcon = () => {
    if (storyLossData.length < 2) return null;

    const recent = storyLossData.slice(-2);
    if (recent.length < 2) return null;

    const trend = recent[1].story_loss - recent[0].story_loss;
    
    if (Math.abs(trend) < 0.01) return null; // No significant change
    
    return trend > 0 ? (
      <TrendingUp color="error" fontSize="small" />
    ) : (
      <TrendingDown color="success" fontSize="small" />
    );
  };

  const getStatusIcon = () => {
    if (currentStoryLoss === null) return null;
    
    return currentStoryLoss > threshold ? (
      <Warning color="error" fontSize="small" />
    ) : (
      <CheckCircle color="success" fontSize="small" />
    );
  };

  const handleMenuOpen = (event) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleRefresh = () => {
    handleMenuClose();
    fetchStoryLossData();
  };

  if (loading && !storyLossData.length) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" height={height}>
        <CircularProgress size={24} />
        <Typography variant="body2" sx={{ ml: 1 }}>
          Loading story-loss data...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="warning" sx={{ height: 'auto' }}>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  if (!storyLossData.length) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" height={height}>
        <Typography variant="body2" color="textSecondary">
          No story-loss data available
        </Typography>
      </Box>
    );
  }

  const chartConfig = getChartConfig();
  if (!chartConfig) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" height={height}>
        <Typography variant="body2" color="textSecondary">
          Unable to render chart
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header with current status */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="subtitle2" component="div">
            Story Loss (24h)
          </Typography>
          {getStatusIcon()}
          {getTrendIcon()}
        </Box>
        
        <Box display="flex" alignItems="center" gap={1}>
          {currentStoryLoss !== null && (
            <Chip
              size="small"
              label={currentStoryLoss.toFixed(3)}
              color={thresholdExceeded ? 'error' : 'success'}
              variant={thresholdExceeded ? 'filled' : 'outlined'}
            />
          )}
          
          <IconButton size="small" onClick={handleMenuOpen}>
            <MoreVert fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      {/* Alert for threshold exceedance */}
      {thresholdExceeded && (
        <Alert severity="warning" sx={{ mb: 1, py: 0 }}>
          <Typography variant="body2">
            Story-loss above threshold ({threshold}) - self-reflection triggered
          </Typography>
        </Alert>
      )}

      {/* Chart */}
      <Box height={height} position="relative">
        <Line data={chartConfig} options={getChartOptions()} />
      </Box>

      {/* Details */}
      {showDetails && (
        <Box mt={1}>
          <Typography variant="caption" color="textSecondary">
            Data points: {storyLossData.length} | 
            Threshold: {threshold} | 
            {lastUpdated && ` Updated: ${lastUpdated.toLocaleTimeString()}`}
          </Typography>
        </Box>
      )}

      {/* Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleRefresh}>
          <Refresh fontSize="small" sx={{ mr: 1 }} />
          Refresh Data
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default StoryLossSparkline;