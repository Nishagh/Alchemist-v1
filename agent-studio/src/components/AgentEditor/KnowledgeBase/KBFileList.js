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
  Chip
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
                  <StatusBadge status={file.indexed ? 'indexed' : 'not_indexed'} />
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