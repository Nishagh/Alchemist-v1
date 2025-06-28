/**
 * Knowledge Base Manager
 * 
 * Main component for managing knowledge base files and search
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Fade
} from '@mui/material';
import {
  Storage as StorageIcon
} from '@mui/icons-material';
import { 
  getAgentKnowledgeBase, 
  uploadKnowledgeBaseFile, 
  deleteKnowledgeBaseFile,
  searchKnowledgeBase 
} from '../../../services';
import { createNotification } from '../../shared/NotificationSystem';
import KBSearchInterface from './KBSearchInterface';
import KBFileList from './KBFileList';

const KnowledgeBaseManager = ({ 
  agentId, 
  onNotification,
  disabled = false 
}) => {
  const [kbFiles, setKbFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'card'

  // Load knowledge base files
  useEffect(() => {
    if (agentId) {
      loadKnowledgeBase();
    }
  }, [agentId]);

  const loadKnowledgeBase = async () => {
    try {
      setLoading(true);
      setError('');
      
      const files = await getAgentKnowledgeBase(agentId);
      console.log('Loaded KB files:', files);
      setKbFiles(files || []);
    } catch (err) {
      console.error('Error loading knowledge base:', err);
      setError('Failed to load knowledge base files');
      setKbFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadProgress({});
    const uploadResults = [];
    const errors = [];

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileId = `temp_${Date.now()}_${i}`;
        
        try {
          console.log(`Uploading file: ${file.name}`);
          
          // Set initial upload status
          setUploadProgress(prev => ({
            ...prev,
            [fileId]: {
              filename: file.name,
              status: 'uploading',
              progress: 0
            }
          }));

          // Add temporary file to list for immediate display
          const tempFile = {
            id: fileId,
            filename: file.name,
            size: file.size,
            content_type: file.type,
            upload_date: new Date().toISOString(),
            indexed: false,
            indexing_status: 'uploading',
            progress_percent: 0,
            isTemporary: true
          };
          
          setKbFiles(prev => [...prev, tempFile]);
          
          // Simulate upload progress
          const progressInterval = setInterval(() => {
            setUploadProgress(prev => {
              const current = prev[fileId];
              if (current && current.status === 'uploading' && current.progress < 90) {
                return {
                  ...prev,
                  [fileId]: {
                    ...current,
                    progress: Math.min(current.progress + 10, 90)
                  }
                };
              }
              return prev;
            });
          }, 200);

          const response = await uploadKnowledgeBaseFile(agentId, file);
          clearInterval(progressInterval);
          
          if (response.success && response.file) {
            // Update progress to complete
            setUploadProgress(prev => ({
              ...prev,
              [fileId]: {
                ...prev[fileId],
                status: 'indexing',
                progress: 100
              }
            }));

            // Replace temporary file with actual response and clear progress
            setKbFiles(prev => prev.map(f => 
              f.id === fileId ? { ...response.file, id: response.file.id } : f
            ));
            
            // Clear the upload progress for this file
            setUploadProgress(prev => {
              const updated = { ...prev };
              delete updated[fileId];
              return updated;
            });

            uploadResults.push(response.file);
            
            // Start monitoring indexing status
            monitorIndexingStatus(response.file.id);
          } else {
            errors.push(`Failed to upload ${file.name}`);
            // Remove failed file
            setKbFiles(prev => prev.filter(f => f.id !== fileId));
          }
        } catch (error) {
          console.error(`Error uploading ${file.name}:`, error);
          errors.push(`Failed to upload ${file.name}: ${error.message}`);
          // Remove failed file and clear progress
          setKbFiles(prev => prev.filter(f => f.id !== fileId));
          setUploadProgress(prev => {
            const updated = { ...prev };
            delete updated[fileId];
            return updated;
          });
        }
      }

      // Clear upload progress after completion
      setTimeout(() => {
        setUploadProgress({});
      }, 2000);

      // Update the files list notification
      if (uploadResults.length > 0) {
        onNotification?.(createNotification(
          `Successfully uploaded ${uploadResults.length} file${uploadResults.length > 1 ? 's' : ''}`,
          'success'
        ));
      }

      // Show errors if any
      if (errors.length > 0) {
        onNotification?.(createNotification(
          `Upload completed with errors: ${errors.join(', ')}`,
          'warning'
        ));
      }

    } catch (error) {
      console.error('Error during file upload:', error);
      onNotification?.(createNotification(
        'Failed to upload files. Please try again.',
        'error'
      ));
    } finally {
      setUploading(false);
    }
  };

  const handleFileDelete = async (fileId, filename) => {
    try {
      console.log(`Deleting file: ${filename} (ID: ${fileId})`);
      await deleteKnowledgeBaseFile(agentId, fileId);
      
      // Remove the file from the local state
      setKbFiles(prev => prev.filter(file => file.id !== fileId));
      
      onNotification?.(createNotification(
        `Successfully deleted ${filename}`,
        'success'
      ));
    } catch (error) {
      console.error('Error deleting file:', error);
      onNotification?.(createNotification(
        `Failed to delete ${filename}. Please try again.`,
        'error'
      ));
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      setSearchQuery('');
      return;
    }

    setSearching(true);
    setSearchQuery(query);

    try {
      const results = await searchKnowledgeBase(agentId, query);
      console.log('Search results:', results);
      setSearchResults(results || []);
    } catch (error) {
      console.error('Error searching knowledge base:', error);
      setSearchResults([]);
      onNotification?.(createNotification(
        'Search failed. Please try again.',
        'error'
      ));
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
  };

  const monitorIndexingStatus = (fileId) => {
    const checkStatus = async () => {
      try {
        // Refresh the file list to get updated indexing status
        const files = await getAgentKnowledgeBase(agentId);
        const updatedFile = files.find(f => f.id === fileId);
        
        if (updatedFile) {
          setKbFiles(prev => prev.map(f => 
            f.id === fileId ? updatedFile : f
          ));
          
          // If still processing, check again in 2 seconds
          if (updatedFile.indexing_status === 'processing' || updatedFile.indexing_status === 'pending') {
            setTimeout(checkStatus, 2000);
          }
        }
      } catch (error) {
        console.error('Error checking indexing status:', error);
      }
    };
    
    // Start checking after a short delay
    setTimeout(checkStatus, 1000);
  };

  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 8 
        }}
      >
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          Loading knowledge base...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Sticky Header */}
      <Box sx={{ 
        position: 'sticky',
        top: 0,
        zIndex: 100,
        p: 3,
        borderBottom: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        backdropFilter: 'blur(8px)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
            Knowledge Base
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Upload and manage files that your agent can reference during conversations
        </Typography>
      </Box>

      {/* Scrollable Content */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
        {/* Error Display */}
        {error && (
          <Fade in={true}>
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
              {error}
            </Alert>
          </Fade>
        )}

        {/* Search Interface */}
        <Paper variant="outlined" sx={{ mb: 3, borderRadius: 2 }}>
          <KBSearchInterface
            searchQuery={searchQuery}
            onSearch={handleSearch}
            onClear={clearSearch}
            searching={searching}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            filesCount={kbFiles.length}
            disabled={disabled}
          />
        </Paper>

        {/* File List */}
        <Box>
          <KBFileList
            files={searchQuery ? searchResults : kbFiles}
            viewMode={viewMode}
            onFileUpload={handleFileUpload}
            onFileDelete={handleFileDelete}
            uploading={uploading}
            uploadProgress={uploadProgress}
            searchMode={!!searchQuery}
            searchQuery={searchQuery}
            disabled={disabled}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default KnowledgeBaseManager;