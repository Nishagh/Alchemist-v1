/**
 * Knowledge Base File List
 * 
 * Displays files in table or card view with upload and delete functionality
 */
import React, { useState } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Typography,
  Grid,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fade,
  Chip,
  LinearProgress,
  CircularProgress
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Upload as UploadIcon,
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon
} from '@mui/icons-material';
import { formatDate, formatFileSize } from '../../../utils/agentEditorHelpers';
import { getFileTypeFromName } from '../../shared/FileIcon';
import FileUploadArea from '../AgentConversation/FileUploadArea';
import KBFileCard from './KBFileCard';
import StatusBadge from '../../shared/StatusBadge';

const KBFileList = ({ 
  files = [],
  viewMode = 'table',
  onFileUpload,
  onFileDelete,
  uploading = false,
  uploadProgress = {},
  searchMode = false,
  searchQuery = '',
  disabled = false 
}) => {
  const [showUpload, setShowUpload] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, file: null });

  const handleDeleteClick = (file) => {
    setDeleteDialog({ open: true, file });
  };

  const handleDeleteConfirm = () => {
    if (deleteDialog.file && onFileDelete) {
      onFileDelete(deleteDialog.file.id, deleteDialog.file.filename || deleteDialog.file.name);
    }
    setDeleteDialog({ open: false, file: null });
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, file: null });
  };

  const handleUploadComplete = (uploadedFiles) => {
    if (onFileUpload) {
      onFileUpload(uploadedFiles);
    }
    setShowUpload(false);
  };

  const renderFileStatus = (file) => {
    // Check if file is in upload progress by matching temp file ID or filename
    let progressInfo = null;
    
    // First try to match by file ID (for temporary files)
    if (file.id && uploadProgress[file.id]) {
      progressInfo = uploadProgress[file.id];
    } else {
      // Fallback to filename matching for edge cases
      progressInfo = Object.values(uploadProgress).find(p => 
        p.filename === (file.filename || file.name)
      );
    }

    if (progressInfo) {
      if (progressInfo.status === 'uploading') {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="body2" color="primary">
              Uploading... {progressInfo.progress}%
            </Typography>
          </Box>
        );
      } else if (progressInfo.status === 'indexing') {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="body2" color="warning.main">
              Starting processing...
            </Typography>
          </Box>
        );
      }
    }

    // Check indexing status from file properties
    if (file.indexing_status === 'uploading') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircularProgress size={16} />
          <Typography variant="body2" color="primary">
            Uploading...
          </Typography>
        </Box>
      );
    }

    if (file.indexing_status === 'processing' || file.indexing_status === 'pending') {
      const progress = file.progress_percent || 0;
      const phase = file.indexing_phase || 'preparing';
      
      // Enhanced phase display with cleaning visibility
      const getPhaseDisplay = (phase) => {
        switch (phase) {
          case 'preparing': return 'Preparing...';
          case 'extracting_text': return 'Extracting Text';
          case 'cleaning_content': return 'Cleaning Content 🧹';
          case 'smart_chunking': return 'Smart Chunking';
          case 'generating_embeddings': return 'Generating Embeddings';
          case 'storing_embeddings': return 'Storing Embeddings';
          default: return 'Processing...';
        }
      };
      
      return (
        <Box sx={{ minWidth: 140 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <CircularProgress size={16} />
            <Typography variant="body2" color="warning.main" sx={{ fontSize: '0.75rem' }}>
              {getPhaseDisplay(phase)}
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ height: 4, borderRadius: 1 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
            {progress}% complete
          </Typography>
        </Box>
      );
    }

    if (file.indexing_status === 'failed') {
      return (
        <Chip 
          label="Failed" 
          color="error" 
          size="small"
          sx={{ fontSize: '0.75rem' }}
        />
      );
    }

    if (file.indexing_status === 'complete' && file.indexed) {
      return (
        <Chip 
          label="Indexed" 
          color="success" 
          size="small"
          sx={{ fontSize: '0.75rem' }}
        />
      );
    }

    // Fallback to original status badge
    return <StatusBadge status={file.indexed ? 'indexed' : 'not_indexed'} />;
  };

  const EmptyState = () => (
    <Box 
      sx={{ 
        textAlign: 'center', 
        py: 8,
        color: 'text.secondary'
      }}
    >
      <FileIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
      <Typography variant="h6" sx={{ mb: 1 }}>
        {searchMode ? 'No files found' : 'No files uploaded yet'}
      </Typography>
      <Typography variant="body2" sx={{ mb: 3 }}>
        {searchMode 
          ? `No files match "${searchQuery}"`
          : 'Upload files to build your agent\'s knowledge base'
        }
      </Typography>
      {!searchMode && (
        <Button
          variant="contained"
          onClick={() => setShowUpload(true)}
          startIcon={<CloudUploadIcon />}
          disabled={disabled}
        >
          Upload Files
        </Button>
      )}
    </Box>
  );

  const TableView = () => (
    <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>File Name</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Size</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Uploaded</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {files.map((file, index) => (
            <Fade in={true} key={file.id || index} timeout={300 + index * 100}>
              <TableRow hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <FileIcon filename={file.filename || file.name} sx={{ mr: 2, color: 'text.secondary' }} />
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {file.filename || file.name || 'Unknown File'}
                    </Typography>
                  </Box>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {getFileTypeFromName(file.filename || file.name)}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {formatFileSize(file.size)}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  {renderFileStatus(file)}
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(file.upload_date || file.created_at)}
                  </Typography>
                </TableCell>
                
                <TableCell align="right">
                  <IconButton
                    onClick={() => handleDeleteClick(file)}
                    size="small"
                    color="error"
                    disabled={disabled}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            </Fade>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const CardView = () => (
    <Grid container spacing={2}>
      {files.map((file, index) => (
        <Grid item xs={12} sm={6} md={4} key={file.id || index}>
          <Fade in={true} timeout={300 + index * 100}>
            <div>
              <KBFileCard
                file={file}
                onDelete={() => handleDeleteClick(file)}
                disabled={disabled}
                renderStatus={() => renderFileStatus(file)}
              />
            </div>
          </Fade>
        </Grid>
      ))}
    </Grid>
  );

  return (
    <Box>
      {/* Upload Button */}
      {!searchMode && files.length > 0 && (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={() => setShowUpload(true)}
            startIcon={uploading ? null : <UploadIcon />}
            disabled={disabled || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload More Files'}
          </Button>
        </Box>
      )}

      {/* File List */}
      {files.length === 0 ? (
        <EmptyState />
      ) : (
        viewMode === 'table' ? <TableView /> : <CardView />
      )}

      {/* Upload Dialog */}
      <Dialog
        open={showUpload}
        onClose={() => setShowUpload(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Upload Files to Knowledge Base</DialogTitle>
        <DialogContent>
          <FileUploadArea
            onFilesUploaded={handleUploadComplete}
            onCancel={() => setShowUpload(false)}
            accept=".txt,.md,.pdf,.doc,.docx,.json,.yaml,.yml,.csv"
            maxFiles={10}
            title="Select Files"
            description="Upload documents that your agent can reference"
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog.open}
        onClose={handleDeleteCancel}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete File</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{deleteDialog.file?.filename || deleteDialog.file?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KBFileList;