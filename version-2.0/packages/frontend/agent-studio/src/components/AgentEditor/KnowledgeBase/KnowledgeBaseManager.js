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
  Fade,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Chip,
  Divider,
  Grid
} from '@mui/material';
import {
  Storage as StorageIcon
} from '@mui/icons-material';
import { 
  getAgentKnowledgeBase, 
  uploadKnowledgeBaseFile, 
  deleteKnowledgeBaseFile,
  searchKnowledgeBase,
  cleanAndReindexFile,
  batchCleanAndReindexFiles,
  previewContentCleaning,
  // New workflow methods
  assessFileQuality,
  indexUploadedFile,
  getFileWorkflowStatus,
  isFileReadyForAssessment,
  isFileReadyForIndexing
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
  // Removed viewMode - only table view now
  
  // New workflow state
  const [qualityAssessments, setQualityAssessments] = useState({}); // fileId -> assessment data
  const [indexingStates, setIndexingStates] = useState({}); // fileId -> indexing status
  const [showQualityDialog, setShowQualityDialog] = useState(false);
  const [selectedFileForAssessment, setSelectedFileForAssessment] = useState(null);
  const [assessmentLoading, setAssessmentLoading] = useState({}); // fileId -> loading state
  const [indexingLoading, setIndexingLoading] = useState({}); // fileId -> indexing loading state
  const [deleteLoading, setDeleteLoading] = useState({}); // fileId -> delete loading state

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

          // Use new workflow: upload without auto-indexing
          const response = await uploadKnowledgeBaseFile(agentId, file, false);
          clearInterval(progressInterval);
          
          if (response.success && response.file) {
            // Update progress to complete - file is uploaded but not indexed
            setUploadProgress(prev => ({
              ...prev,
              [fileId]: {
                ...prev[fileId],
                status: 'uploaded',
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
            
            // No need to monitor indexing - file is uploaded but not indexed yet
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
          `Successfully uploaded ${uploadResults.length} file${uploadResults.length > 1 ? 's' : ''}. Click "Assess Quality" to review before indexing.`,
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
    // Set loading state for this specific file
    setDeleteLoading(prev => ({
      ...prev,
      [fileId]: true
    }));

    // Show immediate feedback
    onNotification?.(createNotification(
      `Deleting ${filename}...`,
      'info'
    ));

    try {
      console.log(`Deleting file: ${filename} (ID: ${fileId})`);
      await deleteKnowledgeBaseFile(agentId, fileId);
      
      // Remove the file from the local state immediately
      setKbFiles(prev => prev.filter(file => file.id !== fileId));
      
      // Clear loading state
      setDeleteLoading(prev => {
        const updated = { ...prev };
        delete updated[fileId];
        return updated;
      });

      onNotification?.(createNotification(
        `Successfully deleted ${filename}`,
        'success'
      ));
    } catch (error) {
      console.error('Error deleting file:', error);
      
      // Clear loading state on error
      setDeleteLoading(prev => {
        const updated = { ...prev };
        delete updated[fileId];
        return updated;
      });

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

  // === NEW WORKFLOW METHODS ===

  const handleAssessQuality = async (file) => {
    if (!isFileReadyForAssessment(file)) {
      onNotification?.(createNotification(
        'File is not ready for quality assessment',
        'warning'
      ));
      return;
    }

    // Check if assessment already exists
    if (qualityAssessments[file.id]) {
      console.log('Using cached assessment for file:', file.filename);
      setSelectedFileForAssessment(file);
      setShowQualityDialog(true);
      onNotification?.(createNotification(
        `Showing cached quality assessment for ${file.filename}`,
        'info'
      ));
      return;
    }

    // Set loading state immediately
    setAssessmentLoading(prev => ({
      ...prev,
      [file.id]: true
    }));

    // Show immediate feedback
    onNotification?.(createNotification(
      `Analyzing content quality for ${file.filename}... This may take 1-2 minutes.`,
      'info'
    ));

    // Open dialog immediately with loading state
    setSelectedFileForAssessment(file);
    setShowQualityDialog(true);

    try {
      console.log('Generating new assessment for file:', file.filename);
      const assessment = await assessFileQuality(file.id);
      
      setQualityAssessments(prev => ({
        ...prev,
        [file.id]: assessment
      }));

      onNotification?.(createNotification(
        `Quality assessment completed for ${file.filename}`,
        'success'
      ));
      
    } catch (error) {
      console.error('Error assessing file quality:', error);
      onNotification?.(createNotification(
        `Failed to assess quality for ${file.filename}: ${error.message}`,
        'error'
      ));
      
      // Close dialog on error
      setShowQualityDialog(false);
      setSelectedFileForAssessment(null);
    } finally {
      // Clear loading state
      setAssessmentLoading(prev => ({
        ...prev,
        [file.id]: false
      }));
    }
  };

  const handleIndexFile = async (fileId, enableCleaning = false) => {
    const file = kbFiles.find(f => f.id === fileId);
    if (!file || !isFileReadyForIndexing(file)) {
      onNotification?.(createNotification(
        'File is not ready for indexing',
        'warning'
      ));
      return;
    }

    // Set loading state immediately
    setIndexingLoading(prev => ({
      ...prev,
      [fileId]: true
    }));

    try {
      console.log(`Indexing file ${file.filename} with cleaning ${enableCleaning ? 'enabled' : 'disabled'}`);
      
      // Show immediate feedback
      onNotification?.(createNotification(
        `Starting to index ${file.filename}${enableCleaning ? ' with content cleaning' : ''}... This may take 1-2 minutes.`,
        'info'
      ));
      
      // Update local state to show indexing in progress
      setIndexingStates(prev => ({
        ...prev,
        [fileId]: 'processing'
      }));

      setKbFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, indexing_status: 'processing', indexed: false } : f
      ));

      const result = await indexUploadedFile(fileId, enableCleaning);
      
      if (result.status === 'success') {
        // Update file with new indexed status
        setKbFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            ...result.file_data,
            indexed: true,
            indexing_status: 'complete'
          } : f
        ));

        setIndexingStates(prev => ({
          ...prev,
          [fileId]: 'complete'
        }));

        onNotification?.(createNotification(
          `Successfully indexed ${file.filename} ${enableCleaning ? 'with content cleaning' : 'without cleaning'}`,
          'success'
        ));

        // Close quality dialog if open
        if (showQualityDialog && selectedFileForAssessment?.id === fileId) {
          setShowQualityDialog(false);
        }

        // Start monitoring for complete status
        monitorIndexingStatus(fileId);
      }
    } catch (error) {
      console.error('Error indexing file:', error);
      
      // Reset indexing state on error
      setIndexingStates(prev => ({
        ...prev,
        [fileId]: 'failed'
      }));

      setKbFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, indexing_status: 'failed' } : f
      ));

      onNotification?.(createNotification(
        `Failed to index ${file.filename}: ${error.message}`,
        'error'
      ));
    } finally {
      // Clear loading state
      setIndexingLoading(prev => ({
        ...prev,
        [fileId]: false
      }));
    }
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
          Upload files, assess their quality and relevance, then choose whether to apply content cleaning before indexing
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
            filesCount={kbFiles.length}
            disabled={disabled}
          />
        </Paper>

        {/* File List */}
        <Box>
          <KBFileList
            files={searchQuery ? searchResults : kbFiles}
            agentId={agentId}
            onFileUpload={handleFileUpload}
            onFileDelete={handleFileDelete}
            uploading={uploading}
            uploadProgress={uploadProgress}
            searchMode={!!searchQuery}
            searchQuery={searchQuery}
            disabled={disabled}
            // New workflow props
            onAssessQuality={handleAssessQuality}
            onIndexFile={handleIndexFile}
            qualityAssessments={qualityAssessments}
            indexingStates={indexingStates}
            assessmentLoading={assessmentLoading}
            indexingLoading={indexingLoading}
            deleteLoading={deleteLoading}
            getFileWorkflowStatus={getFileWorkflowStatus}
            isFileReadyForAssessment={isFileReadyForAssessment}
            isFileReadyForIndexing={isFileReadyForIndexing}
          />
        </Box>
      </Box>

      {/* Quality Assessment Dialog */}
      <Dialog
        open={showQualityDialog}
        onClose={() => setShowQualityDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Content Quality Assessment
          {selectedFileForAssessment && (
            <Typography variant="subtitle2" color="text.secondary">
              {selectedFileForAssessment.filename}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedFileForAssessment && (
            <Box sx={{ mt: 2 }}>
              {indexingLoading[selectedFileForAssessment.id] ? (
                // Indexing Loading State
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CircularProgress size={60} sx={{ mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Indexing Content
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Please wait while we index the content into the knowledge base...
                  </Typography>
                  
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      📂 Processing file content
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      🔧 {indexingStates[selectedFileForAssessment.id] === 'processing' ? 'Applying content processing' : 'Preparing for indexing'}
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      🧩 Creating semantic chunks
                    </Typography>
                    <Typography variant="body2">
                      🔍 Generating embeddings
                    </Typography>
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary">
                    This typically takes 1-2 minutes
                  </Typography>
                </Box>
              ) : assessmentLoading[selectedFileForAssessment.id] ? (
                // Assessment Loading State
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CircularProgress size={60} sx={{ mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Analyzing Content Quality
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Please wait while we analyze the content quality and relevance...
                  </Typography>
                  
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      🔍 Extracting and processing content
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      🧠 Analyzing quality and relevance
                    </Typography>
                    <Typography variant="body2">
                      📊 Generating quality comparison
                    </Typography>
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary">
                    This typically takes 1-2 minutes
                  </Typography>
                </Box>
              ) : qualityAssessments[selectedFileForAssessment.id] ? (
                // Assessment Results
                (() => {
                  const assessment = qualityAssessments[selectedFileForAssessment.id].assessment;
                  const recommendation = assessment.quality_improvement.recommendation;
                  const improvement = assessment.quality_improvement.score_difference;
                
                return (
                  <>
                    {/* Quality Scores */}
                    <Grid container spacing={3} sx={{ mb: 3 }}>
                      <Grid item xs={6}>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="primary">
                            {assessment.original_quality.score.toFixed(1)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Original Quality
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6}>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="secondary">
                            {assessment.cleaned_quality.score.toFixed(1)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Cleaned Quality
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>

                    {/* Recommendation */}
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Recommendation
                      </Typography>
                      <Chip
                        label={recommendation === 'clean' ? 'Apply Content Cleaning' : 'Index As-Is'}
                        color={recommendation === 'clean' ? 'warning' : 'success'}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Quality improvement: {improvement > 0 ? '+' : ''}{improvement.toFixed(1)} points
                        ({assessment.quality_improvement.improvement_percentage.toFixed(1)}%)
                      </Typography>
                    </Box>

                    {/* Relevance */}
                    {assessment.relevance && (
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="h6" gutterBottom>
                          Agent Relevance
                        </Typography>
                        <Typography variant="body1">
                          Score: {assessment.relevance.relevance_score}/100
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {assessment.relevance.relevance_explanation}
                        </Typography>
                      </Box>
                    )}

                    <Divider sx={{ my: 3 }} />

                    {/* Content Preview */}
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Content Preview
                      </Typography>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Original Content:
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {assessment.original_quality.content_preview}
                          </Typography>
                        </Paper>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Cleaned Content:
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {assessment.cleaned_quality.content_preview}
                          </Typography>
                        </Paper>
                      </Box>
                    </Box>
                  </>
                );
              })()) : (
                // No assessment data available
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    No assessment data available. Please try again.
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setShowQualityDialog(false)}
            disabled={
              selectedFileForAssessment && (
                assessmentLoading[selectedFileForAssessment.id] ||
                indexingLoading[selectedFileForAssessment.id]
              )
            }
          >
            {selectedFileForAssessment && (
              assessmentLoading[selectedFileForAssessment.id] ? 'Analyzing...' :
              indexingLoading[selectedFileForAssessment.id] ? 'Indexing...' :
              'Cancel'
            )}
          </Button>
          <Button
            onClick={() => handleIndexFile(selectedFileForAssessment?.id, false)}
            variant="outlined"
            disabled={
              !selectedFileForAssessment || 
              indexingStates[selectedFileForAssessment.id] === 'processing' ||
              assessmentLoading[selectedFileForAssessment.id] ||
              indexingLoading[selectedFileForAssessment.id] ||
              !qualityAssessments[selectedFileForAssessment.id]
            }
            startIcon={indexingLoading[selectedFileForAssessment?.id] && !assessmentLoading[selectedFileForAssessment?.id] ? <CircularProgress size={16} /> : null}
          >
            {indexingLoading[selectedFileForAssessment?.id] && !assessmentLoading[selectedFileForAssessment?.id] ? 'Indexing...' : 'Index As-Is'}
          </Button>
          <Button
            onClick={() => handleIndexFile(selectedFileForAssessment?.id, true)}
            variant="contained"
            disabled={
              !selectedFileForAssessment || 
              indexingStates[selectedFileForAssessment.id] === 'processing' ||
              assessmentLoading[selectedFileForAssessment.id] ||
              indexingLoading[selectedFileForAssessment.id] ||
              !qualityAssessments[selectedFileForAssessment.id]
            }
            startIcon={indexingLoading[selectedFileForAssessment?.id] && !assessmentLoading[selectedFileForAssessment?.id] ? <CircularProgress size={16} /> : null}
          >
            {indexingLoading[selectedFileForAssessment?.id] && !assessmentLoading[selectedFileForAssessment?.id] ? 'Cleaning & Indexing...' : 'Clean & Index'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KnowledgeBaseManager;