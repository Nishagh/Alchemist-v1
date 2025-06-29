/**
 * Workforce Controls Component
 * 
 * Search, filter, sort, and view controls for the AI workforce
 */
import React from 'react';
import {
  Box,
  TextField,
  MenuItem,
  IconButton,
  Tooltip,
  Chip,
  Stack
} from '@mui/material';
import {
  Search as SearchIcon,
  Sort as SortIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon
} from '@mui/icons-material';

const WorkforceControls = ({
  searchTerm,
  setSearchTerm,
  sortBy,
  setSortBy,
  viewMode,
  setViewMode,
  statusFilter,
  setStatusFilter,
  agentCounts = {}
}) => {
  
  const statusFilters = [
    { value: 'all', label: 'All Agents', count: agentCounts.total || 0 },
    { value: 'draft', label: 'Draft', count: agentCounts.draft || 0 },
    { value: 'deployed', label: 'Deployed', count: agentCounts.deployed || 0 }
  ];

  const sortOptions = [
    { value: 'name', label: 'Name' },
    { value: 'performance', label: 'Performance' },
    { value: 'costs', label: 'Costs' },
    { value: 'experience', label: 'Experience' }
  ];

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
      {/* Search */}
      <TextField
        size="small"
        placeholder="Search employees..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        InputProps={{
          startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
        }}
        sx={{ width: { xs: '100%', sm: 200 } }}
      />
      
      {/* Status Filter */}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {statusFilters.map(filter => (
          <Chip
            key={filter.value}
            label={`${filter.label} (${filter.count})`}
            variant={statusFilter === filter.value ? 'filled' : 'outlined'}
            color={statusFilter === filter.value ? 'primary' : 'default'}
            onClick={() => setStatusFilter(filter.value)}
            sx={{ 
              '& .MuiChip-label': { 
                fontSize: '0.75rem' 
              },
              minWidth: 'auto'
            }}
          />
        ))}
      </Box>
      
      {/* Sort */}
      <TextField
        select
        size="small"
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        sx={{ width: 120 }}
        InputProps={{
          startAdornment: <SortIcon sx={{ mr: 0.5, color: 'text.secondary' }} />
        }}
      >
        {sortOptions.map(option => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
      
      {/* View Mode Toggle */}
      <Box sx={{ display: 'flex', border: 1, borderColor: 'divider', borderRadius: 1 }}>
        <Tooltip title="Grid View">
          <IconButton 
            size="small" 
            onClick={() => setViewMode('grid')}
            sx={{ 
              bgcolor: viewMode === 'grid' ? 'primary.main' : 'transparent',
              color: viewMode === 'grid' ? 'white' : 'inherit',
              borderRadius: 0,
              '&:hover': {
                bgcolor: viewMode === 'grid' ? 'primary.dark' : 'action.hover'
              }
            }}
          >
            <ViewModuleIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="List View">
          <IconButton 
            size="small" 
            onClick={() => setViewMode('list')}
            sx={{ 
              bgcolor: viewMode === 'list' ? 'primary.main' : 'transparent',
              color: viewMode === 'list' ? 'white' : 'inherit',
              borderRadius: 0,
              '&:hover': {
                bgcolor: viewMode === 'list' ? 'primary.dark' : 'action.hover'
              }
            }}
          >
            <ViewListIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
};

export default WorkforceControls;