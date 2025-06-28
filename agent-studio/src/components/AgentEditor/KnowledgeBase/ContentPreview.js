/**
 * Content Preview Component
 * 
 * Displays before/after content comparison and processing details
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Divider,
  Chip,
  Stack,
  Alert,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Grid,
  useTheme,
  alpha
} from '@mui/material';
import {
  Visibility as PreviewIcon,
  VisibilityOff as HideIcon,
  ContentCopy as CopyIcon,
  Compare as CompareIcon,
  AutoFixHigh as CleanIcon,
  Analytics as AnalyticsIcon,
  Close as CloseIcon
} from '@mui/icons-material';

const ContentPreview = ({ 
  file,
  open = false,
  onClose,
  onReprocess,
  loading = false
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [showFullContent, setShowFullContent] = useState(false);
  const [selectedChunk, setSelectedChunk] = useState(null);

  // Reset state when file changes
  useEffect(() => {
    setActiveTab(0);
    setShowFullContent(false);
    setSelectedChunk(null);
  }, [file]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleCopyContent = (content) => {
    navigator.clipboard.writeText(content);
  };

  const formatContent = (content, maxLength = 500) => {
    if (!content) return 'No content available';
    
    if (showFullContent || content.length <= maxLength) {
      return content;
    }
    
    return content.substring(0, maxLength) + '...';
  };

  const getQualityColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const processingStats = file?.processing_stats || {};
  const contentMetadata = file?.content_metadata || {};
  const qualityScore = file?.quality_score || 0;

  if (!file) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogContent>
          <Alert severity="info">No file selected for preview</Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h6" component="div">
            Content Preview: {file.filename}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            {qualityScore > 0 && (
              <Chip
                label={`Quality: ${Math.round(qualityScore)}%`}
                size="small"
                color={getQualityColor(qualityScore)}
                variant="outlined"
              />
            )}
            <Chip
              label={`${file.chunk_count || 0} chunks`}
              size="small"
              variant="outlined"
            />
          </Stack>
        </Box>
        <IconButton onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box>
            <Tabs value={activeTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tab label="Processing Summary" />
              <Tab label="Content Comparison" />
              <Tab label="Chunk Analysis" />
              <Tab label="Quality Metrics" />
            </Tabs>

            {/* Processing Summary Tab */}
            {activeTab === 0 && (
              <Box sx={{ p: 3 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" sx={{ mb: 2 }}>
                          Processing Statistics
                        </Typography>
                        
                        {processingStats.original_length && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Original Length:
                            </Typography>
                            <Typography variant="body2">
                              {processingStats.original_length.toLocaleString()} chars
                            </Typography>
                          </Box>
                        )}
                        
                        {processingStats.final_length && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Final Length:
                            </Typography>
                            <Typography variant="body2">
                              {processingStats.final_length.toLocaleString()} chars
                            </Typography>
                          </Box>
                        )}
                        
                        {processingStats.characters_removed && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Characters Removed:
                            </Typography>
                            <Typography variant="body2" color="warning.main">
                              {processingStats.characters_removed.toLocaleString()}
                            </Typography>
                          </Box>
                        )}
                        
                        {processingStats.reduction_percentage && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Content Cleaned:
                            </Typography>
                            <Typography variant="body2" color="success.main">
                              {Math.round(processingStats.reduction_percentage)}%
                            </Typography>
                          </Box>
                        )}
                        
                        {processingStats.word_count && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Final Word Count:
                            </Typography>
                            <Typography variant="body2">
                              {processingStats.word_count.toLocaleString()}
                            </Typography>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" sx={{ mb: 2 }}>
                          Content Metadata
                        </Typography>
                        
                        {contentMetadata.estimated_title && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                              Detected Title:
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                              {contentMetadata.estimated_title}
                            </Typography>
                          </Box>
                        )}
                        
                        {contentMetadata.content_type_guess && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Content Type:
                            </Typography>
                            <Typography variant="body2">
                              {contentMetadata.content_type_guess}
                            </Typography>
                          </Box>
                        )}
                        
                        {contentMetadata.sentence_count && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Sentences:
                            </Typography>
                            <Typography variant="body2">
                              {contentMetadata.sentence_count}
                            </Typography>
                          </Box>
                        )}
                        
                        {contentMetadata.paragraph_count && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Paragraphs:
                            </Typography>
                            <Typography variant="body2">
                              {contentMetadata.paragraph_count}
                            </Typography>
                          </Box>
                        )}
                        
                        {contentMetadata.key_terms && contentMetadata.key_terms.length > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              Key Terms:
                            </Typography>
                            <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                              {contentMetadata.key_terms.slice(0, 8).map((term, index) => (
                                <Chip
                                  key={index}
                                  label={term}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: '0.7rem', height: 24 }}
                                />
                              ))}
                            </Stack>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

              </Box>
            )}

            {/* Content Comparison Tab */}
            {activeTab === 1 && (
              <Box sx={{ p: 3 }}>
                {processingStats.original_text && processingStats.processed_text ? (
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="h6">
                        Before vs After Cleaning
                      </Typography>
                      <Button
                        startIcon={showFullContent ? <HideIcon /> : <PreviewIcon />}
                        onClick={() => setShowFullContent(!showFullContent)}
                        size="small"
                      >
                        {showFullContent ? 'Show Preview' : 'Show Full Content'}
                      </Button>
                    </Box>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                              <Typography variant="subtitle1" color="error.main">
                                Original Content
                              </Typography>
                              <Tooltip title="Copy original content">
                                <IconButton size="small" onClick={() => handleCopyContent(processingStats.original_text || '')}>
                                  <CopyIcon />
                                </IconButton>
                              </Tooltip>
                            </Box>
                            <Box sx={{ 
                              maxHeight: 400, 
                              overflow: 'auto',
                              bgcolor: alpha(theme.palette.error.main, 0.05),
                              p: 2,
                              borderRadius: 1,
                              border: 1,
                              borderColor: alpha(theme.palette.error.main, 0.2)
                            }}>
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                                {formatContent(processingStats.original_text)}
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                              <Typography variant="subtitle1" color="success.main">
                                Cleaned Content
                              </Typography>
                              <Tooltip title="Copy cleaned content">
                                <IconButton size="small" onClick={() => handleCopyContent(processingStats.processed_text || '')}>
                                  <CopyIcon />
                                </IconButton>
                              </Tooltip>
                            </Box>
                            <Box sx={{ 
                              maxHeight: 400, 
                              overflow: 'auto',
                              bgcolor: alpha(theme.palette.success.main, 0.05),
                              p: 2,
                              borderRadius: 1,
                              border: 1,
                              borderColor: alpha(theme.palette.success.main, 0.2)
                            }}>
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                                {formatContent(processingStats.processed_text)}
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <CompareIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                      Content Comparison Data Missing
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Content comparison data is not available for this file. 
                      This may happen for files processed before the latest update.
                    </Typography>
                    {onReprocess && (
                      <Button 
                        variant="contained" 
                        startIcon={<CleanIcon />}
                        onClick={() => onReprocess(file)}
                      >
                        Reprocess File
                      </Button>
                    )}
                  </Box>
                )}
              </Box>
            )}

            {/* Chunk Analysis Tab */}
            {activeTab === 2 && (
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Chunk Analysis ({file.chunk_count || 0} chunks)
                </Typography>
                
                <Alert severity="info" sx={{ mb: 2 }}>
                  This view shows how the content was split into chunks for processing
                </Alert>
                
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <AnalyticsIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Chunk Details
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Detailed chunk analysis will be available in a future update
                  </Typography>
                </Box>
              </Box>
            )}

            {/* Quality Metrics Tab */}
            {activeTab === 3 && (
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Quality Assessment
                </Typography>
                
                {qualityScore > 0 ? (
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h3" color={getQualityColor(qualityScore) + '.main'} sx={{ mb: 1 }}>
                          {Math.round(qualityScore)}%
                        </Typography>
                        <Typography variant="h6" color="text.secondary">
                          Overall Quality Score
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Stack spacing={2}>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Quality Assessment:
                          </Typography>
                          <Typography variant="body1" color={getQualityColor(qualityScore) + '.main'}>
                            {qualityScore >= 80 ? 'High Quality' : 
                             qualityScore >= 60 ? 'Medium Quality' : 'Needs Review'}
                          </Typography>
                        </Box>
                        
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Recommendations:
                          </Typography>
                          <Typography variant="body2">
                            {qualityScore >= 80 ? 'Content is ready for use' :
                             qualityScore >= 60 ? 'Consider manual review' :
                             'Manual review and editing recommended'}
                          </Typography>
                        </Box>
                      </Stack>
                    </Grid>
                  </Grid>
                ) : (
                  <Alert severity="info">
                    Quality metrics are not available for this file
                  </Alert>
                )}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ContentPreview;