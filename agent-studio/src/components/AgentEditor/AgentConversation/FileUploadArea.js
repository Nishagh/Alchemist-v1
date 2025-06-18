/**
 * File Upload Area
 * 
 * Reusable file upload component with drag and drop support
 */
import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  LinearProgress,
  Alert,
  Fade
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  AttachFile as AttachFileIcon,
  Delete as DeleteIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { formatFileSize, isValidFileType } from '../../../utils/agentEditorHelpers';
import FileIcon from '../../shared/FileIcon';

const FileUploadArea = ({ 
  onFilesUploaded,
  onCancel,
  accept = "*",
  maxFiles = 10,
  maxSize = 10 * 1024 * 1024, // 10MB
  multiple = true,
  title = "Upload Files",
  description = "Drag and drop files here or click to browse"
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const acceptedTypes = accept === "*" ? [] : accept.split(',').map(type => type.trim().replace('.', ''));

  const validateFile = (file) => {
    if (file.size > maxSize) {
      return `File "${file.name}" is too large. Maximum size is ${formatFileSize(maxSize)}.`;
    }
    
    if (acceptedTypes.length > 0 && !isValidFileType(file, acceptedTypes)) {
      return `File "${file.name}" type is not supported. Accepted types: ${accept}`;
    }
    
    return null;
  };

  const handleFiles = (files) => {
    setError('');
    const fileArray = Array.from(files);
    
    if (fileArray.length > maxFiles) {
      setError(`Too many files selected. Maximum is ${maxFiles} files.`);
      return;
    }

    const validFiles = [];
    const errors = [];

    fileArray.forEach(file => {
      const error = validateFile(file);
      if (error) {
        errors.push(error);
      } else {
        validFiles.push(file);
      }
    });

    if (errors.length > 0) {
      setError(errors.join(' '));
      return;
    }

    if (!multiple && validFiles.length > 1) {
      setError('Only one file can be selected.');
      return;
    }

    setSelectedFiles(validFiles);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setError('');

    try {
      await onFilesUploaded(selectedFiles);
      setSelectedFiles([]);
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(files => files.filter((_, i) => i !== index));
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
          {title}
        </Typography>
        {onCancel && (
          <IconButton onClick={onCancel} size="small">
            <CloseIcon />
          </IconButton>
        )}
      </Box>

      {/* Upload Area */}
      <Paper
        variant="outlined"
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          bgcolor: dragActive ? 'action.hover' : 'background.default',
          borderStyle: dragActive ? 'solid' : 'dashed',
          borderColor: dragActive ? 'primary.main' : 'divider',
          borderWidth: 2,
          borderRadius: 2,
          transition: 'all 0.2s ease',
          '&:hover': {
            bgcolor: 'action.hover',
            borderColor: 'primary.main'
          }
        }}
        onClick={handleBrowseClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple={multiple}
          accept={accept}
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />

        <CloudUploadIcon 
          sx={{ 
            fontSize: 48, 
            color: dragActive ? 'primary.main' : 'text.secondary',
            mb: 2 
          }} 
        />
        
        <Typography variant="h6" sx={{ mb: 1, color: dragActive ? 'primary.main' : 'text.primary' }}>
          {dragActive ? 'Drop files here' : title}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {description}
        </Typography>

        <Button
          variant="outlined"
          startIcon={<AttachFileIcon />}
          onClick={handleBrowseClick}
          sx={{ mt: 1 }}
        >
          Browse Files
        </Button>

        {acceptedTypes.length > 0 && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Accepted types: {accept} • Max size: {formatFileSize(maxSize)}
          </Typography>
        )}
      </Paper>

      {/* Error Display */}
      {error && (
        <Fade in={true}>
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        </Fade>
      )}

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
            Selected Files ({selectedFiles.length})
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {selectedFiles.map((file, index) => (
              <Fade in={true} key={index} timeout={300}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    display: 'flex',
                    alignItems: 'center',
                    borderRadius: 1
                  }}
                >
                  <FileIcon filename={file.name} sx={{ mr: 2, color: 'text.secondary' }} />
                  
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {file.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatFileSize(file.size)}
                    </Typography>
                  </Box>
                  
                  <IconButton
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                    size="small"
                    sx={{ color: 'error.main' }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Paper>
              </Fade>
            ))}
          </Box>

          {/* Upload Progress */}
          {uploading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                Uploading files...
              </Typography>
            </Box>
          )}

          {/* Upload Button */}
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={uploading || selectedFiles.length === 0}
              startIcon={<CloudUploadIcon />}
            >
              Upload {selectedFiles.length} File{selectedFiles.length > 1 ? 's' : ''}
            </Button>
            
            <Button
              variant="outlined"
              onClick={() => setSelectedFiles([])}
              disabled={uploading}
            >
              Clear
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default FileUploadArea;