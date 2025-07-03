/**
 * Knowledge Base File Card
 * 
 * Card view component for individual files in the knowledge base
 */
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  IconButton,
  Box,
  Tooltip,
  useTheme,
  alpha,
  LinearProgress,
  Chip,
  Collapse,
  Stack,
  CircularProgress
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  AutoFixHigh as CleanIcon,
  Speed as QualityIcon,
  Preview as PreviewIcon,
  Assessment as AssessmentIcon,
  PlayArrow as IndexIcon,
  CleaningServices as CleanAndIndexIcon
} from '@mui/icons-material';
import { formatDate, formatFileSize } from '../../../utils/agentEditorHelpers';
import { getFileTypeFromName } from '../../shared/FileIcon';
import StatusBadge from '../../shared/StatusBadge';
import FileIcon from '../../shared/FileIcon';
import ContentPreview from './ContentPreview';
import { getFileContentPreview } from '../../../services/knowledgeBase/knowledgeBaseService';

const KBFileCard = ({ 
  file, 
  onDelete, 
  onDownload,
  onReprocess,
  disabled = false,
  renderStatus,
  showDetails = false,
  onToggleDetails,
  // New workflow props
  onAssessQuality,
  onIndexFile,
  qualityAssessments = {},
  indexingStates = {},
  assessmentLoading = {},
  indexingLoading = {},
  getFileWorkflowStatus,
  isFileReadyForAssessment,
  isFileReadyForIndexing
}) => {
  const theme = useTheme();
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const fileName = file.filename || file.name || 'Unknown File';
  const fileType = getFileTypeFromName(fileName);
  const fileSize = formatFileSize(file.size);
  const uploadDate = formatDate(file.upload_date);
  const isIndexed = file.indexed;
  
  // Enhanced processing status
  const indexingStatus = file.indexing_status || 'unknown';
  const indexingPhase = file.indexing_phase || 'unknown';
  const progressPercent = file.progress_percent || 0;
  const qualityScore = file.quality_score || 0;
  const processingStats = file.processing_stats || {};
  const contentMetadata = file.content_metadata || {};
  const processingVersion = file.processing_version || 'v2_enhanced';
  const chunkCount = file.chunk_count || 0;
  
  // Processing phase display mapping with cleaning visibility
  const phaseDisplayMap = {
    'preparing': 'Preparing...',
    'extracting_text': 'Extracting Text',
    'cleaning_content': 'Cleaning Content 🧹',
    'smart_chunking': 'Smart Chunking 🧩',
    'generating_embeddings': 'Generating Embeddings',
    'storing_embeddings': 'Storing Embeddings',
    'complete': 'Complete',
    'failed': 'Failed'
  };
  
  // Quality score color mapping
  const getQualityColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };
  
  // Processing status color mapping
  const getStatusColor = (status) => {
    switch (status) {
      case 'complete': return 'success';
      case 'processing': return 'info';
      case 'failed': return 'error';
      case 'pending': return 'default';
      case 'uploaded': return 'warning'; // New status for uploaded but not indexed
      default: return 'default';
    }
  };

  const handleDeleteClick = (event) => {
    event.stopPropagation();
    if (onDelete) {
      onDelete(file);
    }
  };

  const handleDownloadClick = (event) => {
    event.stopPropagation();
    if (onDownload) {
      onDownload(file);
    }
  };

  const handleReprocessClick = (event) => {
    event.stopPropagation();
    if (onReprocess) {
      onReprocess(file);
    }
  };

  const handleToggleDetails = (event) => {
    event.stopPropagation();
    if (onToggleDetails) {
      onToggleDetails(file.id || file.file_id);
    }
  };

  const handlePreviewClick = async (event) => {
    event.stopPropagation();
    setLoadingPreview(true);
    try {
      const data = await getFileContentPreview(file.id || file.file_id);
      console.log('Preview data received for debugging:', {
        filename: data?.filename,
        processing_version: data?.processing_version,
        has_original_text: !!data?.processing_stats?.original_text,
        has_processed_text: !!data?.processing_stats?.processed_text,
        original_length: data?.processing_stats?.original_text?.length || 0,
        processed_length: data?.processing_stats?.processed_text?.length || 0
      });
      setPreviewData(data);
      setShowPreview(true);
    } catch (error) {
      console.error('Error loading preview:', error);
      // Show error to user
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleClosePreview = () => {
    setShowPreview(false);
    setPreviewData(null);
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
        border: '1px solid',
        borderColor: 'divider',
        '&:hover': {
          boxShadow: theme.shadows[4],
          borderColor: 'primary.main',
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent sx={{ flex: 1, p: 3 }}>
        {/* File Icon and Status */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <FileIcon 
              filename={fileName} 
              sx={{ 
                fontSize: 32, 
                color: 'primary.main',
                mr: 1
              }} 
            />
            {renderStatus ? renderStatus() : (
              <StatusBadge 
                status={isIndexed ? 'indexed' : 'not_indexed'} 
                size="small"
              />
            )}
          </Box>
          
          {/* Quality Score Indicator */}
          {qualityScore > 0 && (
            <Chip
              icon={<QualityIcon sx={{ fontSize: 16 }} />}
              label={`${Math.round(qualityScore)}%`}
              size="small"
              color={getQualityColor(qualityScore)}
              variant="outlined"
            />
          )}
        </Box>

        {/* Processing Progress */}
        {indexingStatus === 'processing' && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              {phaseDisplayMap[indexingPhase] || indexingPhase}
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={progressPercent} 
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              {progressPercent}% complete
            </Typography>
          </Box>
        )}

        {/* Processing Status Chip */}
        {indexingStatus !== 'unknown' && (
          <Box sx={{ mb: 2 }}>
            <Chip
              label={getFileWorkflowStatus ? getFileWorkflowStatus(file) : indexingStatus.charAt(0).toUpperCase() + indexingStatus.slice(1)}
              size="small"
              color={getStatusColor(indexingStatus)}
              variant="filled"
            />
          </Box>
        )}

        {/* File Name */}
        <Typography 
          variant="h6" 
          component="h3"
          sx={{ 
            mb: 1,
            fontSize: '1rem',
            fontWeight: 'bold',
            wordBreak: 'break-word',
            lineHeight: 1.3
          }}
        >
          {fileName}
        </Typography>

        {/* File Type */}
        <Typography 
          variant="body2" 
          color="text.secondary"
          sx={{ mb: 2 }}
        >
          {fileType}
        </Typography>

        {/* File Details */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              Size
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
              {fileSize}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              Uploaded
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
              {uploadDate}
            </Typography>
          </Box>

          {chunkCount > 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">
                Chunks
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
                {chunkCount}
              </Typography>
            </Box>
          )}


          {file.service && (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">
                Service
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
                {file.service}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Enhanced Details Collapse */}
        <Collapse in={showDetails}>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="caption" sx={{ fontWeight: 'bold', mb: 1, display: 'block' }}>
              Processing Details
            </Typography>
            
            {processingStats.reduction_percentage && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Content Cleaned
                </Typography>
                <Typography variant="caption">
                  {Math.round(processingStats.reduction_percentage)}%
                </Typography>
              </Box>
            )}
            
            {contentMetadata.word_count && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Word Count
                </Typography>
                <Typography variant="caption">
                  {contentMetadata.word_count.toLocaleString()}
                </Typography>
              </Box>
            )}
            
            {contentMetadata.content_type_guess && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Content Type
                </Typography>
                <Typography variant="caption">
                  {contentMetadata.content_type_guess}
                </Typography>
              </Box>
            )}
            
            {contentMetadata.key_terms && contentMetadata.key_terms.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                  Key Terms
                </Typography>
                <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                  {contentMetadata.key_terms.slice(0, 5).map((term, index) => (
                    <Chip
                      key={index}
                      label={term}
                      size="small"
                      variant="outlined"
                      sx={{ height: 18, fontSize: '0.6rem' }}
                    />
                  ))}
                </Stack>
              </Box>
            )}
          </Box>
        </Collapse>

        {/* Additional Info */}
        {file.description && (
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ 
              mt: 2,
              fontSize: '0.875rem',
              fontStyle: 'italic'
            }}
          >
            {file.description}
          </Typography>
        )}
      </CardContent>

      {/* Actions */}
      <CardActions sx={{ p: 2, pt: 0, justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {file.score !== undefined && (
            <Typography variant="caption" color="text.secondary">
              Relevance: {(file.score * 100).toFixed(0)}%
            </Typography>
          )}
        </Box>

        <Box>
          {onToggleDetails && (
            <Tooltip title={showDetails ? "Hide details" : "Show details"}>
              <IconButton
                onClick={handleToggleDetails}
                size="small"
                disabled={disabled}
                sx={{ mr: 1 }}
              >
                <InfoIcon />
              </IconButton>
            </Tooltip>
          )}
          
          {/* New Workflow Buttons */}
          {isFileReadyForAssessment && isFileReadyForAssessment(file) && (
            <Tooltip title={assessmentLoading[file.id] ? "Analyzing content..." : "Assess Content Quality"}>
              <IconButton
                onClick={() => onAssessQuality && onAssessQuality(file)}
                size="small"
                disabled={disabled || assessmentLoading[file.id]}
                sx={{ mr: 1 }}
                color="primary"
              >
                {assessmentLoading[file.id] ? <CircularProgress size={20} /> : <AssessmentIcon />}
              </IconButton>
            </Tooltip>
          )}
          
          {isFileReadyForIndexing && isFileReadyForIndexing(file) && (
            <Tooltip title={indexingLoading[file.id] ? "Indexing..." : "Index Without Cleaning"}>
              <IconButton
                onClick={() => onIndexFile && onIndexFile(file.id, false)}
                size="small"
                disabled={disabled || indexingStates[file.id] === 'processing' || indexingLoading[file.id]}
                sx={{ mr: 1 }}
                color="success"
              >
                {indexingLoading[file.id] ? <CircularProgress size={20} /> : <IndexIcon />}
              </IconButton>
            </Tooltip>
          )}
          
          {isFileReadyForIndexing && isFileReadyForIndexing(file) && (
            <Tooltip title={indexingLoading[file.id] ? "Cleaning & Indexing..." : "Clean Content & Index"}>
              <IconButton
                onClick={() => onIndexFile && onIndexFile(file.id, true)}
                size="small"
                disabled={disabled || indexingStates[file.id] === 'processing' || indexingLoading[file.id]}
                sx={{ mr: 1 }}
                color="warning"
              >
                {indexingLoading[file.id] ? <CircularProgress size={20} /> : <CleanAndIndexIcon />}
              </IconButton>
            </Tooltip>
          )}
          
          {indexingStatus === 'complete' && (
            <Tooltip title="Preview content comparison">
              <IconButton
                onClick={handlePreviewClick}
                size="small"
                disabled={disabled || loadingPreview}
                sx={{ mr: 1 }}
              >
                <PreviewIcon />
              </IconButton>
            </Tooltip>
          )}
          
          {onReprocess && indexingStatus === 'complete' && (
            <Tooltip title="Reprocess with enhanced cleaning">
              <IconButton
                onClick={handleReprocessClick}
                size="small"
                disabled={disabled}
                sx={{ mr: 1 }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          )}
          
          {onDownload && (
            <Tooltip title="Download file">
              <IconButton
                onClick={handleDownloadClick}
                size="small"
                disabled={disabled}
                sx={{ mr: 1 }}
              >
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          )}
          
          <Tooltip title="Delete file">
            <IconButton
              onClick={handleDeleteClick}
              size="small"
              color="error"
              disabled={disabled}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </CardActions>
      
      {/* Content Preview Dialog */}
      {previewData && (
        <ContentPreview
          file={previewData}
          open={showPreview}
          onClose={handleClosePreview}
          onReprocess={onReprocess}
          loading={loadingPreview}
        />
      )}
    </Card>
  );
};

export default KBFileCard;