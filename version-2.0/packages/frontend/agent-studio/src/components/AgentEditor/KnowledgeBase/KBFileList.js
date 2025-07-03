/**
 * Knowledge Base File List
 * 
 * Displays files in table or card view with upload and delete functionality
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fade,
  Chip,
  LinearProgress,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Upload as UploadIcon,
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Assessment as AssessmentIcon,
  PlayArrow as IndexIcon,
  CleaningServices as CleanAndIndexIcon
} from '@mui/icons-material';
import { formatDate, formatFileSize } from '../../../utils/agentEditorHelpers';
import { getFileTypeFromName } from '../../shared/FileIcon';
import FileUploadArea from '../AgentConversation/FileUploadArea';
import StatusBadge from '../../shared/StatusBadge';

const KBFileList = ({ 
  files = [],
  agentId,
  onFileUpload,
  onFileDelete,
  uploading = false,
  uploadProgress = {},
  searchMode = false,
  searchQuery = '',
  disabled = false,
  // New workflow props
  onAssessQuality,
  onIndexFile,
  qualityAssessments = {},
  indexingStates = {},
  assessmentLoading = {},
  indexingLoading = {},
  deleteLoading = {},
  getFileWorkflowStatus,
  isFileReadyForAssessment,
  isFileReadyForIndexing
}) => {
  const navigate = useNavigate();
  const [showUpload, setShowUpload] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, file: null });

  const handleDeleteClick = (file) => {
    setDeleteDialog({ open: true, file });
  };

  const handleFileClick = (file) => {
    // Navigate to existing file detail page using the correct route
    if (agentId) {
      navigate(`/knowledge-base/${agentId}/file/${file.id}`, {
        state: { file }
      });
    } else {
      console.error('Agent ID not provided for navigation');
    }
  };

  const handleDeleteConfirm = async () => {
    if (deleteDialog.file && onFileDelete) {
      try {
        await onFileDelete(deleteDialog.file.id, deleteDialog.file.filename || deleteDialog.file.name);
        // Close dialog only after successful deletion
        setDeleteDialog({ open: false, file: null });
      } catch (error) {
        // Keep dialog open on error so user can retry
        console.error('Delete failed, keeping dialog open');
      }
    }
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
              <TableRow 
                hover={!deleteLoading[file.id]}
                onClick={() => !deleteLoading[file.id] && handleFileClick(file)}
                sx={{ 
                  cursor: deleteLoading[file.id] ? 'not-allowed' : 'pointer',
                  opacity: deleteLoading[file.id] ? 0.6 : 1,
                  backgroundColor: deleteLoading[file.id] ? 'action.hover' : 'transparent',
                  '&:hover': {
                    backgroundColor: deleteLoading[file.id] ? 'action.hover' : 'action.hover'
                  }
                }}
              >
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {deleteLoading[file.id] ? (
                      <CircularProgress size={20} sx={{ mr: 2 }} />
                    ) : (
                      <FileIcon filename={file.filename || file.name} sx={{ mr: 2, color: 'text.secondary' }} />
                    )}
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {file.filename || file.name || 'Unknown File'}
                      {deleteLoading[file.id] && (
                        <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                          (Deleting...)
                        </Typography>
                      )}
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
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    {/* New Workflow Buttons */}
                    {isFileReadyForAssessment && isFileReadyForAssessment(file) && (
                      <Tooltip title={assessmentLoading[file.id] ? "Analyzing content..." : "Assess Content Quality"}>
                        <IconButton
                          onClick={(e) => {
                            e.stopPropagation();
                            onAssessQuality && onAssessQuality(file);
                          }}
                          size="small"
                          disabled={disabled || assessmentLoading[file.id] || deleteLoading[file.id]}
                          sx={{ mr: 0.5 }}
                          color="primary"
                        >
                          {assessmentLoading[file.id] ? <CircularProgress size={20} /> : <AssessmentIcon />}
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    {isFileReadyForIndexing && isFileReadyForIndexing(file) && (
                      <Tooltip title={indexingLoading[file.id] ? "Indexing..." : "Index Without Cleaning"}>
                        <IconButton
                          onClick={(e) => {
                            e.stopPropagation();
                            onIndexFile && onIndexFile(file.id, false);
                          }}
                          size="small"
                          disabled={disabled || indexingStates[file.id] === 'processing' || indexingLoading[file.id] || deleteLoading[file.id]}
                          sx={{ mr: 0.5 }}
                          color="success"
                        >
                          {indexingLoading[file.id] ? <CircularProgress size={20} /> : <IndexIcon />}
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    {isFileReadyForIndexing && isFileReadyForIndexing(file) && (
                      <Tooltip title={indexingLoading[file.id] ? "Cleaning & Indexing..." : "Clean Content & Index"}>
                        <IconButton
                          onClick={(e) => {
                            e.stopPropagation();
                            onIndexFile && onIndexFile(file.id, true);
                          }}
                          size="small"
                          disabled={disabled || indexingStates[file.id] === 'processing' || indexingLoading[file.id] || deleteLoading[file.id]}
                          sx={{ mr: 0.5 }}
                          color="warning"
                        >
                          {indexingLoading[file.id] ? <CircularProgress size={20} /> : <CleanAndIndexIcon />}
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    <IconButton
                      onClick={(e) => {
                        e.stopPropagation();
                        !deleteLoading[file.id] && handleDeleteClick(file);
                      }}
                      size="small"
                      color="error"
                      disabled={disabled || deleteLoading[file.id]}
                    >
                      {deleteLoading[file.id] ? <CircularProgress size={20} /> : <DeleteIcon />}
                    </IconButton>
                  </Box>
                </TableCell>
              </TableRow>
            </Fade>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
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
        <TableView />
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
          <Button 
            onClick={handleDeleteCancel}
            disabled={deleteLoading[deleteDialog.file?.id]}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            disabled={deleteLoading[deleteDialog.file?.id]}
            startIcon={deleteLoading[deleteDialog.file?.id] ? <CircularProgress size={16} /> : null}
          >
            {deleteLoading[deleteDialog.file?.id] ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KBFileList;