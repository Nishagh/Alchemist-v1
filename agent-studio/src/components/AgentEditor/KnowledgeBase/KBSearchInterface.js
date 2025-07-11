/**
 * Knowledge Base Search Interface
 * 
 * Search controls and view options for the knowledge base
 */
import React, { useState } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Chip,
  InputAdornment,
  Typography,
  Divider
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon
} from '@mui/icons-material';
import { debounce } from '../../../utils/agentEditorHelpers';

const KBSearchInterface = ({ 
  searchQuery,
  onSearch,
  onClear,
  searching = false,
  filesCount = 0,
  disabled = false 
}) => {
  const [inputValue, setInputValue] = useState(searchQuery || '');

  // Debounced search function
  const debouncedSearch = debounce(onSearch, 500);

  const handleInputChange = (event) => {
    const value = event.target.value;
    setInputValue(value);
    
    if (value.trim()) {
      debouncedSearch(value);
    } else {
      onClear();
    }
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    if (inputValue.trim()) {
      onSearch(inputValue);
    }
  };

  const handleClear = () => {
    setInputValue('');
    onClear();
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Search Controls */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', mb: 2 }}>
        {/* Search Input */}
        <Box sx={{ flex: 1 }}>
          <form onSubmit={handleSearchSubmit}>
            <TextField
              fullWidth
              placeholder="Search knowledge base files..."
              value={inputValue}
              onChange={handleInputChange}
              disabled={disabled || searching}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color={searching ? 'action' : 'primary'} />
                  </InputAdornment>
                ),
                endAdornment: inputValue && (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleClear}
                      size="small"
                      disabled={disabled || searching}
                    >
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                )
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2
                }
              }}
            />
          </form>
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Status Bar */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {searchQuery ? (
              searching ? 'Searching...' : `Search results for "${searchQuery}"`
            ) : (
              `${filesCount} file${filesCount !== 1 ? 's' : ''} in knowledge base`
            )}
          </Typography>

          {searchQuery && (
            <Chip
              label={`Clear search`}
              size="small"
              onDelete={handleClear}
              color="primary"
              variant="outlined"
            />
          )}
        </Box>

        {/* Additional Status Info */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {searching && (
            <Chip
              label="Searching..."
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default KBSearchInterface;