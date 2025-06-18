/**
 * Knowledge Base File Card
 * 
 * Card view component for individual files in the knowledge base
 */
import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  IconButton,
  Box,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { formatDate, formatFileSize } from '../../../utils/agentEditorHelpers';
import { getFileTypeFromName } from '../../shared/FileIcon';
import StatusBadge from '../../shared/StatusBadge';
import FileIcon from '../../shared/FileIcon';

const KBFileCard = ({ 
  file, 
  onDelete, 
  onDownload,
  disabled = false 
}) => {
  const theme = useTheme();

  const fileName = file.filename || file.name || 'Unknown File';
  const fileType = getFileTypeFromName(fileName);
  const fileSize = formatFileSize(file.size);
  const uploadDate = formatDate(file.upload_date);
  const isIndexed = file.indexed;

  const handleDeleteClick = (event) => {
    event.stopPropagation();
    if (onDelete) {
      onDelete(file);
    }
  };

  const handleDownloadClick = (event) => {
    event.stopPropagation();
    if (onDownload) {
      onDownload(file);
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
        border: '1px solid',
        borderColor: 'divider',
        '&:hover': {
          boxShadow: theme.shadows[4],
          borderColor: 'primary.main',
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent sx={{ flex: 1, p: 3 }}>
        {/* File Icon and Status */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <FileIcon 
              filename={fileName} 
              sx={{ 
                fontSize: 32, 
                color: 'primary.main',
                mr: 1
              }} 
            />
            <StatusBadge 
              status={isIndexed ? 'indexed' : 'not_indexed'} 
              size="small"
            />
          </Box>
        </Box>

        {/* File Name */}
        <Typography 
          variant="h6" 
          component="h3"
          sx={{ 
            mb: 1,
            fontSize: '1rem',
            fontWeight: 'bold',
            wordBreak: 'break-word',
            lineHeight: 1.3
          }}
        >
          {fileName}
        </Typography>

        {/* File Type */}
        <Typography 
          variant="body2" 
          color="text.secondary"
          sx={{ mb: 2 }}
        >
          {fileType}
        </Typography>

        {/* File Details */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              Size
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
              {fileSize}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              Uploaded
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
              {uploadDate}
            </Typography>
          </Box>

          {file.service && (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">
                Service
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
                {file.service}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Additional Info */}
        {file.description && (
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ 
              mt: 2,
              fontSize: '0.875rem',
              fontStyle: 'italic'
            }}
          >
            {file.description}
          </Typography>
        )}
      </CardContent>

      {/* Actions */}
      <CardActions sx={{ p: 2, pt: 0, justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {file.score !== undefined && (
            <Typography variant="caption" color="text.secondary">
              Relevance: {(file.score * 100).toFixed(0)}%
            </Typography>
          )}
        </Box>

        <Box>
          {onDownload && (
            <Tooltip title="Download file">
              <IconButton
                onClick={handleDownloadClick}
                size="small"
                disabled={disabled}
                sx={{ mr: 1 }}
              >
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          )}
          
          <Tooltip title="Delete file">
            <IconButton
              onClick={handleDeleteClick}
              size="small"
              color="error"
              disabled={disabled}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </CardActions>
    </Card>
  );
};

export default KBFileCard;