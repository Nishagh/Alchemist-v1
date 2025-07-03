import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Divider,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Grid,
  Card
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  Compare as CompareIcon,
  Visibility as VisibilityIcon,
  Code as CodeIcon,
  Highlight as HighlightIcon,
  Analytics as AnalyticsIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight, oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { getFileContentPreview, reprocessKnowledgeBaseFile, updateFileContent, getFileChunkAnalysis } from '../services/knowledgeBase/knowledgeBaseService';

const KnowledgeBaseContentViewer = () => {
  const { agentId, fileId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [fileData, setFileData] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [confirmReindex, setConfirmReindex] = useState(false);
  const [viewMode, setViewMode] = useState('split'); // 'original', 'clean', 'split', 'diff'
  const [chunkAnalysis, setChunkAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  useEffect(() => {
    if (agentId && fileId) {
      loadFileContent();
    }
  }, [agentId, fileId]);

  const loadFileContent = async () => {
    try {
      setLoading(true);
      const data = await getFileContentPreview(fileId);
      console.log('File content data received:', data);
      console.log('Processing stats:', data.processing_stats);
      setFileData(data);
      setEditedContent(data.original_content || '');
    } catch (error) {
      console.error('Error loading file content:', error);
      setNotification({
        open: true,
        message: 'Failed to load file content',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadChunkAnalysis = async () => {
    console.log('loadChunkAnalysis called, fileId:', fileId, 'chunkAnalysis:', chunkAnalysis);
    
    if (chunkAnalysis) {
      console.log('Chunk analysis already loaded, skipping');
      return; // Already loaded
    }
    
    try {
      console.log('Starting chunk analysis for file:', fileId);
      setAnalysisLoading(true);
      const analysis = await getFileChunkAnalysis(fileId);
      console.log('Chunk analysis result:', analysis);
      setChunkAnalysis(analysis);
    } catch (error) {
      console.error('Error loading chunk analysis:', error);
      setNotification({
        open: true,
        message: 'Failed to load chunk analysis',
        severity: 'error'
      });
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await updateFileContent(fileId, editedContent);
      
      // Update the file data with the new content
      setFileData(prev => ({
        ...prev,
        original_content: editedContent
      }));
      
      setNotification({
        open: true,
        message: 'Content saved successfully',
        severity: 'success'
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving content:', error);
      setNotification({
        open: true,
        message: 'Failed to save content',
        severity: 'error'
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReindex = async () => {
    try {
      setReindexing(true);
      await reprocessKnowledgeBaseFile(fileId);
      setNotification({
        open: true,
        message: 'File reindexing started successfully',
        severity: 'success'
      });
      setConfirmReindex(false);
      // Reload content after reindexing
      setTimeout(() => {
        loadFileContent();
      }, 2000);
    } catch (error) {
      console.error('Error reindexing file:', error);
      setNotification({
        open: true,
        message: 'Failed to reindex file',
        severity: 'error'
      });
    } finally {
      setReindexing(false);
    }
  };

  const getDiffHighlightedContent = (original, cleaned) => {
    if (!original || !cleaned) return { original: '', cleaned: '', removed: [] };
    
    const originalLines = original.split('\n');
    const cleanedLines = cleaned.split('\n');
    const removedLines = [];
    
    // Simple diff algorithm - find lines that exist in original but not in cleaned
    originalLines.forEach((line, index) => {
      if (!cleanedLines.includes(line) && line.trim()) {
        removedLines.push({ lineNumber: index + 1, content: line });
      }
    });
    
    return {
      original: original,
      cleaned: cleaned,
      removed: removedLines
    };
  };

  const renderContent = (content, title, isOriginal = false) => {
    if (!content) return <Typography color="text.secondary">No content available</Typography>;
    
    const language = getLanguageFromFilename(fileData?.filename || '');
    const isDarkMode = theme.palette.mode === 'dark';
    
    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" color="primary">
            {title}
          </Typography>
          {isOriginal && (
            <Chip
              icon={<CodeIcon />}
              label={language || 'text'}
              size="small"
              sx={{ ml: 2 }}
            />
          )}
        </Box>
        
        <Paper 
          elevation={0} 
          sx={{ 
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
            borderRadius: 2,
            overflow: 'hidden'
          }}
        >
          <SyntaxHighlighter
            language={language || 'text'}
            style={isDarkMode ? oneDark : oneLight}
            customStyle={{
              margin: 0,
              padding: theme.spacing(2),
              fontSize: '14px',
              lineHeight: 1.5,
              maxHeight: '600px',
              overflow: 'auto'
            }}
            showLineNumbers
            wrapLines
          >
            {content}
          </SyntaxHighlighter>
        </Paper>
      </Box>
    );
  };

  const renderChunkAnalysis = () => {
    if (analysisLoading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Analyzing chunks...</Typography>
        </Box>
      );
    }

    if (!chunkAnalysis) {
      return (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <AnalyticsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Chunk Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Detailed analysis of how this file was chunked for semantic search
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<AnalyticsIcon />}
            onClick={() => {
              console.log('KnowledgeBaseContentViewer Analyze Chunks button clicked');
              loadChunkAnalysis();
            }}
          >
            Analyze Chunks
          </Button>
        </Box>
      );
    }

    if (chunkAnalysis.error) {
      return (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body1" fontWeight="bold" gutterBottom>
            Analysis Failed
          </Typography>
          <Typography variant="body2">
            {chunkAnalysis.error}
          </Typography>
        </Alert>
      );
    }

    return (
      <Box>
        <Typography variant="h5" gutterBottom color="primary">
          <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Chunk Analysis Report
        </Typography>
        
        {/* Overview Statistics */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.50' }}>
              <Typography variant="h3" color="primary">{chunkAnalysis.total_chunks}</Typography>
              <Typography variant="body2" color="text.secondary">Total Chunks</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.50' }}>
              <Typography variant="h3" color="success.main">
                {Math.round(chunkAnalysis.content_distribution?.word_distribution?.avg_words || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">Avg Words/Chunk</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.50' }}>
              <Typography variant="h3" color="warning.main">
                {Math.round(chunkAnalysis.quality_metrics?.content_quality?.avg_score || 0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">Avg Quality Score</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.50' }}>
              <Typography variant="h3" color="info.main">
                {chunkAnalysis.content_type_analysis?.dominant_type || 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">Dominant Type</Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Optimization Recommendations */}
        {chunkAnalysis.optimization_recommendations?.length > 0 && (
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Optimization Recommendations
            </Typography>
            {chunkAnalysis.optimization_recommendations.map((rec, index) => (
              <Alert 
                key={index} 
                severity={rec.severity} 
                sx={{ mb: 2 }}
                icon={
                  rec.severity === 'high' ? <WarningIcon /> :
                  rec.severity === 'medium' ? <InfoIcon /> :
                  <CheckCircleIcon />
                }
              >
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  {rec.title}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  {rec.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Suggestion:</strong> {rec.suggestion}
                </Typography>
              </Alert>
            ))}
          </Paper>
        )}

        {/* Detailed Metrics */}
        <Grid container spacing={3}>
          {/* Content Distribution */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Content Distribution
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Character Count</Typography>
                <Typography variant="body2" color="text.secondary">
                  Min: {chunkAnalysis.content_distribution?.size_distribution?.min_chars || 0} • 
                  Max: {chunkAnalysis.content_distribution?.size_distribution?.max_chars || 0} • 
                  Avg: {Math.round(chunkAnalysis.content_distribution?.size_distribution?.avg_chars || 0)}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Word Count</Typography>
                <Typography variant="body2" color="text.secondary">
                  Total: {chunkAnalysis.content_distribution?.word_distribution?.total_words || 0} • 
                  Avg/Chunk: {Math.round(chunkAnalysis.content_distribution?.word_distribution?.avg_words || 0)}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2">Sentences</Typography>
                <Typography variant="body2" color="text.secondary">
                  Total: {chunkAnalysis.content_distribution?.sentence_distribution?.total_sentences || 0} • 
                  Avg/Chunk: {Math.round(chunkAnalysis.content_distribution?.sentence_distribution?.avg_sentences || 0)}
                </Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Quality Analysis */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                <SpeedIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Quality Analysis
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Quality Distribution</Typography>
                <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                  <Chip 
                    label={`High: ${chunkAnalysis.quality_metrics?.content_quality?.distribution?.high || 0}`}
                    color="success" 
                    size="small" 
                  />
                  <Chip 
                    label={`Medium: ${chunkAnalysis.quality_metrics?.content_quality?.distribution?.medium || 0}`}
                    color="warning" 
                    size="small" 
                  />
                  <Chip 
                    label={`Low: ${chunkAnalysis.quality_metrics?.content_quality?.distribution?.low || 0}`}
                    color="error" 
                    size="small" 
                  />
                </Box>
              </Box>
              
              {chunkAnalysis.readability_analysis && (
                <Box>
                  <Typography variant="subtitle2">Readability</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Grade Level: {Math.round(chunkAnalysis.readability_analysis.flesch_kincaid_grade?.avg_grade || 0)} • 
                    Difficulty: {chunkAnalysis.readability_analysis.reading_ease?.difficulty_level || 'Unknown'}
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Content Types */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                <CodeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Content Types
              </Typography>
              
              {chunkAnalysis.content_type_analysis?.content_characteristics && (
                <Box>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                    <Chip 
                      label={`Code: ${chunkAnalysis.content_type_analysis.content_characteristics.code_chunks}`}
                      size="small" 
                    />
                    <Chip 
                      label={`Tables: ${chunkAnalysis.content_type_analysis.content_characteristics.table_chunks}`}
                      size="small" 
                    />
                    <Chip 
                      label={`Lists: ${chunkAnalysis.content_type_analysis.content_characteristics.list_chunks}`}
                      size="small" 
                    />
                    <Chip 
                      label={`Text: ${chunkAnalysis.content_type_analysis.content_characteristics.plain_text_chunks}`}
                      size="small" 
                    />
                  </Box>
                </Box>
              )}
              
              {chunkAnalysis.content_type_analysis?.type_distribution && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>Type Distribution</Typography>
                  {Object.entries(chunkAnalysis.content_type_analysis.type_distribution).map(([type, count]) => (
                    <Typography key={type} variant="body2" color="text.secondary">
                      {type}: {count} chunks
                    </Typography>
                  ))}
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Semantic Analysis */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Semantic Analysis
              </Typography>
              
              {chunkAnalysis.semantic_analysis?.similarity_statistics ? (
                <Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2">Similarity Statistics</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg: {(chunkAnalysis.semantic_analysis.similarity_statistics.avg_similarity * 100).toFixed(1)}% • 
                      Range: {(chunkAnalysis.semantic_analysis.similarity_statistics.min_similarity * 100).toFixed(1)}% - {(chunkAnalysis.semantic_analysis.similarity_statistics.max_similarity * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary">
                    Analyzed {chunkAnalysis.semantic_analysis.chunks_analyzed} chunks with embeddings
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {chunkAnalysis.semantic_analysis?.similarity_analysis || 'Semantic analysis unavailable'}
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Detailed Chunk Information */}
        {chunkAnalysis.chunk_details && chunkAnalysis.chunk_details.length > 0 && (
          <Paper sx={{ p: 3, mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Detailed Chunk Information
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Individual analysis for each chunk in the file
            </Typography>
            
            <Box sx={{ maxHeight: '600px', overflow: 'auto' }}>
              {chunkAnalysis.chunk_details.slice(0, 10).map((chunk, index) => (
                <Paper 
                  key={index} 
                  variant="outlined" 
                  sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      Chunk #{chunk.chunk_index + 1}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip 
                        label={`${chunk.quality_score.toFixed(0)}%`} 
                        color={chunk.quality_score >= 80 ? 'success' : chunk.quality_score >= 60 ? 'warning' : 'error'}
                        size="small" 
                      />
                      <Chip 
                        label={chunk.content_type} 
                        size="small" 
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 1, fontFamily: 'monospace', bgcolor: 'white', p: 1, borderRadius: 1 }}>
                    {chunk.content_preview}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Typography variant="caption" color="text.secondary">
                      {chunk.word_count} words
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {chunk.full_content_length} chars
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {chunk.sentence_count} sentences
                    </Typography>
                    {chunk.readability && !chunk.readability.error && (
                      <Typography variant="caption" color="text.secondary">
                        Grade {chunk.readability.flesch_kincaid_grade?.toFixed(1)}
                      </Typography>
                    )}
                  </Box>
                </Paper>
              ))}
              
              {chunkAnalysis.chunk_details.length > 10 && (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 2 }}>
                  Showing first 10 chunks. Total: {chunkAnalysis.chunk_details.length} chunks.
                </Typography>
              )}
            </Box>
          </Paper>
        )}
      </Box>
    );
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

  const renderDiffView = () => {
    if (!fileData?.original_content || !fileData?.cleaned_content) {
      return <Typography color="text.secondary">Diff view not available</Typography>;
    }
    
    const diff = getDiffHighlightedContent(fileData.original_content, fileData.cleaned_content);
    
    // Calculate quality scores if not provided by backend
    const originalQuality = fileData?.processing_stats?.original_quality_score ?? calculateSimpleQuality(fileData.original_content);
    const cleanedQuality = fileData?.processing_stats?.cleaned_quality_score ?? calculateSimpleQuality(fileData.cleaned_content);
    const qualityImprovement = cleanedQuality - originalQuality;
    const qualityImprovementPercentage = originalQuality > 0 ? (qualityImprovement / originalQuality) * 100 : 0;
    
    return (
      <Box>
        <Typography variant="h6" color="primary" gutterBottom>
          Content Comparison
        </Typography>
        
        {/* Quality Comparison */}
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
        
        {diff.removed.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" color="error" gutterBottom>
              Removed Content ({diff.removed.length} sections)
            </Typography>
            <Paper 
              elevation={0} 
              sx={{ 
                border: `1px solid ${alpha(theme.palette.error.main, 0.3)}`,
                borderRadius: 2,
                p: 2,
                bgcolor: alpha(theme.palette.error.main, 0.05)
              }}
            >
              {diff.removed.map((removal, index) => (
                <Box key={index} sx={{ mb: 1 }}>
                  <Typography variant="caption" color="error">
                    Line {removal.lineNumber}:
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontFamily: 'monospace',
                      bgcolor: alpha(theme.palette.error.main, 0.1),
                      p: 1,
                      borderRadius: 1,
                      textDecoration: 'line-through'
                    }}
                  >
                    {removal.content}
                  </Typography>
                </Box>
              ))}
            </Paper>
          </Box>
        )}
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            {renderContent(diff.original, 'Original Content', true)}
          </Grid>
          <Grid item xs={12} md={6}>
            {renderContent(diff.cleaned, 'Cleaned Content')}
          </Grid>
        </Grid>
      </Box>
    );
  };

  const renderEditor = () => {
    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" color="primary">
            Edit Content
          </Typography>
          <Box>
            <Button
              startIcon={<CancelIcon />}
              onClick={() => {
                setIsEditing(false);
                setEditedContent(fileData?.original_content || '');
              }}
              sx={{ mr: 1 }}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </Box>
        </Box>
        
        <TextField
          fullWidth
          multiline
          minRows={20}
          maxRows={30}
          value={editedContent}
          onChange={(e) => setEditedContent(e.target.value)}
          sx={{
            '& .MuiInputBase-root': {
              fontFamily: 'monospace',
              fontSize: '14px',
              lineHeight: 1.5
            }
          }}
        />
      </Box>
    );
  };

  const getLanguageFromFilename = (filename) => {
    if (!filename) return 'text';
    
    const extension = filename.split('.').pop().toLowerCase();
    const languageMap = {
      'js': 'javascript',
      'jsx': 'jsx',
      'ts': 'typescript',
      'tsx': 'tsx',
      'py': 'python',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'cs': 'csharp',
      'php': 'php',
      'rb': 'ruby',
      'go': 'go',
      'rs': 'rust',
      'swift': 'swift',
      'kt': 'kotlin',
      'scala': 'scala',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'less': 'less',
      'json': 'json',
      'xml': 'xml',
      'yaml': 'yaml',
      'yml': 'yaml',
      'md': 'markdown',
      'sql': 'sql',
      'sh': 'bash',
      'bash': 'bash',
      'zsh': 'bash',
      'ps1': 'powershell',
      'dockerfile': 'dockerfile'
    };
    
    return languageMap[extension] || 'text';
  };

  if (loading) {
    return (
      <Box sx={{ 
        height: 'calc(100vh - 64px)', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center' 
      }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ 
        px: 3, 
        py: 2, 
        borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
        backgroundColor: alpha(theme.palette.background.paper, 0.9)
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate(`/knowledge-base/${agentId}`)}
              variant="outlined"
              size="small"
              sx={{ mr: 2 }}
            >
              Back to Knowledge Base
            </Button>
            <Typography variant="h5" color="primary">
              {fileData?.filename || 'File Content'}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Refresh content">
              <IconButton onClick={loadFileContent} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            
            {!isEditing && (
              <Button
                startIcon={<EditIcon />}
                onClick={() => setIsEditing(true)}
                variant="outlined"
              >
                Edit
              </Button>
            )}
            
            <Button
              startIcon={reindexing ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={() => setConfirmReindex(true)}
              disabled={reindexing}
              variant="contained"
              color="secondary"
            >
              {reindexing ? 'Reindexing...' : 'Reindex'}
            </Button>
          </Box>
        </Box>
        
        {fileData && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip label={`Size: ${formatFileSize(fileData.size)}`} size="small" />
            <Chip label={`Type: ${fileData.content_type || 'Unknown'}`} size="small" />
            {fileData.chunk_count && (
              <Chip label={`Chunks: ${fileData.chunk_count}`} size="small" />
            )}
          </Box>
        )}
      </Box>

      {/* Content Area */}
      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        {isEditing ? (
          <Box sx={{ p: 3, height: '100%' }}>
            {renderEditor()}
          </Box>
        ) : (
          <>
            <Tabs 
              value={activeTab} 
              onChange={(e, newValue) => {
                setActiveTab(newValue);
                if (newValue === 3) { // Chunk Analysis tab
                  loadChunkAnalysis();
                }
              }}
              sx={{ borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.1)}` }}
            >
              <Tab label="Original Content" icon={<VisibilityIcon />} />
              <Tab label="Cleaned Content" icon={<HighlightIcon />} />
              <Tab label="Comparison" icon={<CompareIcon />} />
              <Tab label="Chunk Analysis" icon={<AnalyticsIcon />} />
            </Tabs>
            
            <Box sx={{ p: 3, height: 'calc(100% - 48px)', overflow: 'auto' }}>
              {activeTab === 0 && renderContent(fileData?.original_content, 'Original Content', true)}
              {activeTab === 1 && renderContent(fileData?.cleaned_content, 'Cleaned Content')}
              {activeTab === 2 && renderDiffView()}
              {activeTab === 3 && renderChunkAnalysis()}
            </Box>
          </>
        )}
      </Box>

      {/* Notifications */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setNotification({ ...notification, open: false })} 
          severity={notification.severity}
          elevation={6}
          variant="filled"
        >
          {notification.message}
        </Alert>
      </Snackbar>

      {/* Reindex Confirmation Dialog */}
      <Dialog
        open={confirmReindex}
        onClose={() => setConfirmReindex(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reindex File</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to reindex this file? This will reprocess the content and update the knowledge base.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmReindex(false)}>Cancel</Button>
          <Button onClick={handleReindex} variant="contained" disabled={reindexing}>
            {reindexing ? 'Reindexing...' : 'Reindex'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// Helper function to format file size
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return 'Unknown';
  
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default KnowledgeBaseContentViewer;