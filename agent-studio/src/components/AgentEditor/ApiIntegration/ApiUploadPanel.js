/**
 * API Upload Panel
 * 
 * Component for uploading and managing API specification files
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Fade,
  Chip
} from '@mui/material';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Api as ApiIcon,
  Description as DescriptionIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { formatFileSize, formatDate } from '../../../utils/agentEditorHelpers';
import FileUploadArea from '../AgentConversation/FileUploadArea';

const ApiUploadPanel = ({ 
  agentId,
  apiFiles = [],
  onApiUpload,
  onApiDelete,
  uploading = false,
  disabled = false 
}) => {
  const [showUpload, setShowUpload] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, file: null });
  const [apiName, setApiName] = useState('');

  const handleUploadClick = () => {
    setShowUpload(true);
    setApiName('');
  };

  const handleUploadComplete = (files) => {
    if (files && files.length > 0 && onApiUpload) {
      onApiUpload(files[0], apiName); // Only take the first file
    }
    setShowUpload(false);
    setApiName('');
  };

  const handleDeleteClick = (file) => {
    setDeleteDialog({ open: true, file });
  };

  const handleDeleteConfirm = () => {
    if (deleteDialog.file && onApiDelete) {
      onApiDelete(deleteDialog.file.id, deleteDialog.file.filename || deleteDialog.file.name);
    }
    setDeleteDialog({ open: false, file: null });
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, file: null });
  };

  const EmptyState = () => (
    <Box 
      sx={{ 
        textAlign: 'center', 
        py: 6,
        color: 'text.secondary'
      }}
    >
      <ApiIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
      <Typography variant="h6" sx={{ mb: 1 }}>
        No API specifications uploaded
      </Typography>
      <Typography variant="body2" sx={{ mb: 3 }}>
        Upload OpenAPI specifications or MCP configurations to extend your agent's capabilities
      </Typography>
      <Button
        variant="contained"
        onClick={handleUploadClick}
        startIcon={<CloudUploadIcon />}
        disabled={disabled}
      >
        Upload API Specification
      </Button>
    </Box>
  );

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        height: '100%',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
              API Files
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Manage your API specifications and configurations
            </Typography>
          </Box>
          
          {apiFiles.length > 0 && (
            <Button
              variant="contained"
              onClick={handleUploadClick}
              startIcon={uploading ? null : <UploadIcon />}
              disabled={disabled || uploading}
              size="small"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </Button>
          )}
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, p: apiFiles.length === 0 ? 0 : 3, overflowY: 'auto', minHeight: 0 }}>
        {apiFiles.length === 0 ? (
          <EmptyState />
        ) : (
          <List sx={{ width: '100%' }}>
            {apiFiles.map((file, index) => (
              <Fade in={true} key={file.id || index} timeout={300 + index * 100}>
                <ListItem
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    '&:last-child': { mb: 0 }
                  }}
                >
                  <ListItemIcon>
                    <DescriptionIcon color="primary" />
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                          {file.filename || file.name || 'Unknown File'}
                        </Typography>
                        <Chip 
                          label={file.type || 'API'} 
                          size="small" 
                          color="primary" 
                          variant="outlined" 
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          {formatFileSize(file.size)} • Uploaded {formatDate(file.uploaded_at || file.created_at)}
                        </Typography>
                        {file.description && (
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                            {file.description}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  
                  <ListItemSecondaryAction>
                    <IconButton
                      onClick={() => handleDeleteClick(file)}
                      size="small"
                      color="error"
                      disabled={disabled}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              </Fade>
            ))}
          </List>
        )}
      </Box>

      {/* Upload Dialog */}
      <Dialog
        open={showUpload}
        onClose={() => setShowUpload(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Upload API Specification</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              label="API Name (Optional)"
              value={apiName}
              onChange={(e) => setApiName(e.target.value)}
              placeholder="Enter a descriptive name for this API"
              helperText="This will help you identify the API specification later"
              sx={{ mb: 3 }}
            />
          </Box>
          
          <Alert severity="info" sx={{ mb: 3 }}>
            Upload OpenAPI 3.0+ specifications (YAML or JSON) or MCP configuration files
          </Alert>
          
          <FileUploadArea
            onFilesUploaded={handleUploadComplete}
            onCancel={() => setShowUpload(false)}
            accept=".yaml,.yml,.json"
            maxFiles={1}
            multiple={false}
            title="Select API Specification"
            description="Upload OpenAPI spec or MCP config file"
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
        <DialogTitle>Delete API Specification</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{deleteDialog.file?.filename || deleteDialog.file?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will also remove any deployed MCP servers using this specification.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ApiUploadPanel;