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
import { getFileChunkAnalysis } from '../../../services/knowledgeBase/knowledgeBaseService';

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
  const [chunkAnalysis, setChunkAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // Reset state when file changes
  useEffect(() => {
    setActiveTab(0);
    setShowFullContent(false);
    setSelectedChunk(null);
    setChunkAnalysis(null);
  }, [file]);

  const loadChunkAnalysis = async () => {
    const fileId = file?.file_id || file?.id;
    console.log('ContentPreview loadChunkAnalysis called, fileId:', fileId, 'chunkAnalysis:', chunkAnalysis);
    
    if (chunkAnalysis || !fileId) {
      console.log('ContentPreview chunk analysis already loaded or no file, skipping');
      return; // Already loaded or no file
    }
    
    try {
      console.log('ContentPreview starting chunk analysis for file:', fileId);
      setAnalysisLoading(true);
      const analysis = await getFileChunkAnalysis(fileId);
      console.log('ContentPreview chunk analysis result:', analysis);
      setChunkAnalysis(analysis);
    } catch (error) {
      console.error('ContentPreview error loading chunk analysis:', error);
      setChunkAnalysis({ error: 'Failed to load chunk analysis' });
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Simple frontend quality calculation as fallback
  const calculateSimpleQuality = (text) => {
    if (!text || text.length < 10) return 0;
    
    let score = 100;
    
    // Length check
    if (text.length < 100) score -= 20;
    
    // Sentence structure
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length > 0) {
      const avgSentenceLength = text.length / sentences.length;
      if (avgSentenceLength >= 10 && avgSentenceLength <= 100) score += 10;
      else score -= 5;
    }
    
    // Vocabulary diversity
    const words = text.toLowerCase().split(/\s+/).filter(w => w.length > 0);
    if (words.length > 0) {
      const uniqueWords = new Set(words);
      const diversity = uniqueWords.size / words.length;
      if (diversity > 0.3) score += 10;
      else score -= 10;
    }
    
    return Math.max(0, Math.min(100, score));
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    if (newValue === 2) { // Chunk Analysis tab
      loadChunkAnalysis();
    }
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
                label={`File Quality: ${Math.round(qualityScore)}%`}
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

                    {/* Quality Comparison */}
                    {(() => {
                      // Calculate quality scores if not provided by backend
                      const originalQuality = processingStats.original_quality_score ?? calculateSimpleQuality(processingStats.original_text);
                      const cleanedQuality = processingStats.cleaned_quality_score ?? calculateSimpleQuality(processingStats.processed_text);
                      const qualityImprovement = cleanedQuality - originalQuality;
                      const qualityImprovementPercentage = originalQuality > 0 ? (qualityImprovement / originalQuality) * 100 : 0;
                      
                      return (
                        <Grid container spacing={2} sx={{ mb: 3 }}>
                          <Grid item xs={12} sm={3}>
                            <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Original Quality
                              </Typography>
                              <Typography variant="h5" color="error.main">
                                {Math.round(originalQuality)}%
                              </Typography>
                            </Card>
                          </Grid>
                          <Grid item xs={12} sm={3}>
                            <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Cleaned Quality
                              </Typography>
                              <Typography variant="h5" color="success.main">
                                {Math.round(cleanedQuality)}%
                              </Typography>
                            </Card>
                          </Grid>
                          <Grid item xs={12} sm={3}>
                            <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Improvement
                              </Typography>
                              <Typography 
                                variant="h5" 
                                color={qualityImprovement >= 0 ? "success.main" : "error.main"}
                              >
                                {qualityImprovement >= 0 ? '+' : ''}{Math.round(qualityImprovement)}
                              </Typography>
                            </Card>
                          </Grid>
                          <Grid item xs={12} sm={3}>
                            <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                % Change
                              </Typography>
                              <Typography 
                                variant="h5" 
                                color={qualityImprovementPercentage >= 0 ? "success.main" : "error.main"}
                              >
                                {qualityImprovementPercentage >= 0 ? '+' : ''}{Math.round(qualityImprovementPercentage)}%
                              </Typography>
                            </Card>
                          </Grid>
                        </Grid>
                      );
                    })()}
                    
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
                
                {analysisLoading && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                    <CircularProgress />
                    <Typography sx={{ ml: 2 }}>Analyzing chunks...</Typography>
                  </Box>
                )}

                {!analysisLoading && !chunkAnalysis && (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <AnalyticsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      Chunk Analysis
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      Get detailed insights into how this file was chunked
                    </Typography>
                    <Button 
                      variant="contained" 
                      startIcon={<AnalyticsIcon />}
                      onClick={() => {
                        console.log('ContentPreview Analyze Chunks button clicked');
                        loadChunkAnalysis();
                      }}
                    >
                      Analyze Chunks
                    </Button>
                  </Box>
                )}

                {chunkAnalysis && chunkAnalysis.error && (
                  <Alert severity="error">
                    {chunkAnalysis.error}
                  </Alert>
                )}

                {chunkAnalysis && !chunkAnalysis.error && (
                  <Box>
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={12} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="body2" color="text.secondary">
                              Total Chunks
                            </Typography>
                            <Typography variant="h6">
                              {chunkAnalysis.total_chunks}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="body2" color="text.secondary">
                              Avg Words/Chunk
                            </Typography>
                            <Typography variant="h6">
                              {Math.round(chunkAnalysis.content_distribution?.word_distribution?.avg_words || 0)}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="body2" color="text.secondary">
                              Avg Chunk Quality
                            </Typography>
                            <Typography variant="h6">
                              {Math.round(chunkAnalysis.quality_metrics?.content_quality?.avg_score || 0)}%
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    {chunkAnalysis.optimization_recommendations && chunkAnalysis.optimization_recommendations.length > 0 && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Optimization Recommendations:
                        </Typography>
                        {chunkAnalysis.optimization_recommendations.map((rec, index) => (
                          <Typography key={index} variant="body2">
                            • {rec.title}: {rec.suggestion}
                          </Typography>
                        ))}
                      </Alert>
                    )}

                    <Typography variant="subtitle1" sx={{ mb: 2 }}>
                      Chunk Details
                    </Typography>
                    <Stack spacing={1}>
                      {chunkAnalysis.chunk_details?.slice(0, 5).map((chunk, index) => (
                        <Card key={index} variant="outlined" sx={{ p: 2 }}>
                          <Typography variant="body2" color="text.secondary">
                            Chunk {chunk.chunk_index + 1} • {chunk.word_count} words • Quality: {Math.round(chunk.quality_score)}%
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            {chunk.content_preview}
                          </Typography>
                        </Card>
                      ))}
                      {chunkAnalysis.chunk_details?.length > 5 && (
                        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                          ... and {chunkAnalysis.chunk_details.length - 5} more chunks
                        </Typography>
                      )}
                    </Stack>
                  </Box>
                )}
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
                          File Quality Score
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