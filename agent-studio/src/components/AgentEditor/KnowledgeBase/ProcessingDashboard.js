/**
 * Processing Dashboard
 * 
 * Component for visualizing content cleaning and processing statistics
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Stack,
  Divider,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material';
import {
  AutoFixHigh as CleanIcon,
  Speed as QualityIcon,
  TextSnippet as ChunkIcon,
  Analytics as StatsIcon,
  TrendingUp as ImprovementIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material';

const ProcessingDashboard = ({ 
  files = [], 
  selectedFileId = null,
  onFileSelect,
  showGlobalStats = true 
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);

  // Find selected file
  useEffect(() => {
    if (selectedFileId) {
      const file = files.find(f => (f.id || f.file_id) === selectedFileId);
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  }, [selectedFileId, files]);

  // Calculate global statistics
  const globalStats = React.useMemo(() => {
    // All files now use enhanced processing (v2_enhanced)
    const totalFiles = files.length;
    const processingFiles = files.filter(f => f.indexing_status === 'processing').length;
    const failedFiles = files.filter(f => f.indexing_status === 'failed').length;
    
    // Quality statistics
    const qualityScores = files
      .map(f => f.quality_score)
      .filter(score => score && score > 0);
    
    const avgQuality = qualityScores.length > 0 
      ? qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length 
      : 0;
    
    // Content reduction statistics
    const reductionPercentages = files
      .map(f => f.processing_stats?.reduction_percentage)
      .filter(reduction => reduction && reduction > 0);
    
    const avgReduction = reductionPercentages.length > 0
      ? reductionPercentages.reduce((sum, reduction) => sum + reduction, 0) / reductionPercentages.length
      : 0;
    
    // Total chunks
    const totalChunks = files.reduce((sum, f) => sum + (f.chunk_count || 0), 0);
    
    return {
      totalFiles,
      processingFiles,
      failedFiles,
      successRate: totalFiles > 0 ? ((totalFiles - failedFiles) / totalFiles) * 100 : 0,
      avgQuality,
      avgReduction,
      totalChunks,
      qualityDistribution: {
        high: qualityScores.filter(s => s >= 80).length,
        medium: qualityScores.filter(s => s >= 60 && s < 80).length,
        low: qualityScores.filter(s => s < 60).length
      }
    };
  }, [files]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getQualityColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const StatCard = ({ title, value, subtitle, icon: Icon, color = 'primary' }) => (
    <Card sx={{ height: '100%', border: '1px solid', borderColor: 'divider' }}>
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Icon sx={{ color: `${color}.main`, mr: 1 }} />
          <Typography variant="h6" component="div">
            {value}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'medium' }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const QualityIndicator = ({ score, label, size = 'medium' }) => {
    const color = getQualityColor(score);
    const radius = size === 'small' ? 30 : 40;
    const strokeWidth = size === 'small' ? 3 : 4;
    const normalizedRadius = radius - strokeWidth * 2;
    const circumference = normalizedRadius * 2 * Math.PI;
    const strokeDasharray = `${(score / 100) * circumference} ${circumference}`;
    
    return (
      <Box sx={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg height={radius * 2} width={radius * 2}>
          <circle
            stroke={theme.palette.grey[300]}
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke={theme.palette[color].main}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={strokeDasharray}
            style={{ strokeLinecap: 'round', transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
        </svg>
        <Box
          sx={{
            position: 'absolute',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column'
          }}
        >
          <Typography variant={size === 'small' ? 'caption' : 'body2'} sx={{ fontWeight: 'bold' }}>
            {Math.round(score)}%
          </Typography>
          {label && (
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
              {label}
            </Typography>
          )}
        </Box>
      </Box>
    );
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Processing Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Monitor content cleaning and processing statistics
        </Typography>
      </Box>

      {/* Global Statistics */}
      {showGlobalStats && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'medium' }}>
            Overview
          </Typography>
          
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Files"
                value={globalStats.totalFiles}
                subtitle={`${globalStats.processingFiles} processing`}
                icon={TextSnippet}
                color="primary"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Files"
                value={globalStats.totalFiles}
                subtitle="all enhanced"
                icon={CleanIcon}
                color="info"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Average Quality"
                value={`${Math.round(globalStats.avgQuality)}%`}
                subtitle="Content quality score"
                icon={QualityIcon}
                color="success"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Content Cleaned"
                value={`${Math.round(globalStats.avgReduction)}%`}
                subtitle="Average reduction"
                icon={ImprovementIcon}
                color="warning"
              />
            </Grid>
          </Grid>

          {/* Quality Distribution */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Quality Distribution
              </Typography>
              
              <Grid container spacing={3} alignItems="center">
                <Grid item xs={12} md={8}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption">High Quality (80%+)</Typography>
                        <Typography variant="caption">{globalStats.qualityDistribution.high} files</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(globalStats.qualityDistribution.high / globalStats.processedCount) * 100 || 0}
                        color="success"
                        sx={{ mb: 1 }}
                      />
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption">Medium Quality (60-79%)</Typography>
                        <Typography variant="caption">{globalStats.qualityDistribution.medium} files</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(globalStats.qualityDistribution.medium / globalStats.processedCount) * 100 || 0}
                        color="warning"
                        sx={{ mb: 1 }}
                      />
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption">Needs Review (<60%)</Typography>
                        <Typography variant="caption">{globalStats.qualityDistribution.low} files</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(globalStats.qualityDistribution.low / globalStats.processedCount) * 100 || 0}
                        color="error"
                      />
                    </Box>
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                    <QualityIndicator score={globalStats.avgQuality} label="Avg Quality" />
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Detailed View */}
      <Box>
        <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label="Processing Status" />
          <Tab label="Content Analysis" />
          <Tab label="Quality Metrics" />
        </Tabs>

        {/* Processing Status Tab */}
        {activeTab === 0 && (
          <Box>
            {files.filter(f => f.indexing_status === 'processing').length > 0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                {files.filter(f => f.indexing_status === 'processing').length} files are currently being processed
              </Alert>
            )}
            
            <Grid container spacing={2}>
              {files.map((file) => (
                <Grid item xs={12} key={file.id || file.file_id}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      border: selectedFileId === (file.id || file.file_id) ? 2 : 1,
                      borderColor: selectedFileId === (file.id || file.file_id) ? 'primary.main' : 'divider'
                    }}
                    onClick={() => onFileSelect && onFileSelect(file.id || file.file_id)}
                  >
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'medium' }}>
                          {file.filename}
                        </Typography>
                        
                        <Stack direction="row" spacing={1}>
                          <Chip
                            label={file.indexing_status || 'unknown'}
                            size="small"
                            color={
                              file.indexing_status === 'complete' ? 'success' :
                              file.indexing_status === 'processing' ? 'info' :
                              file.indexing_status === 'failed' ? 'error' : 'default'
                            }
                          />
                          
                          
                          {file.quality_score > 0 && (
                            <Chip
                              icon={<QualityIcon sx={{ fontSize: 12 }} />}
                              label={`${Math.round(file.quality_score)}%`}
                              size="small"
                              color={getQualityColor(file.quality_score)}
                              variant="outlined"
                            />
                          )}
                        </Stack>
                      </Box>
                      
                      {file.indexing_status === 'processing' && (
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                            {file.indexing_phase || 'Processing...'}
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={file.progress_percent || 0}
                            sx={{ mb: 1 }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {file.progress_percent || 0}% complete
                          </Typography>
                        </Box>
                      )}
                      
                      {file.indexing_status === 'failed' && file.indexing_error && (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          <Typography variant="caption">
                            {file.indexing_error}
                          </Typography>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Content Analysis Tab */}
        {activeTab === 1 && (
          <Box>
            {selectedFile ? (
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    {selectedFile.filename}
                  </Typography>
                  
                  {selectedFile.processing_stats && (
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                          Content Processing
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Original Length
                          </Typography>
                          <Typography variant="body2">
                            {selectedFile.processing_stats.original_length?.toLocaleString()} chars
                          </Typography>
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Final Length
                          </Typography>
                          <Typography variant="body2">
                            {selectedFile.processing_stats.final_length?.toLocaleString()} chars
                          </Typography>
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Content Removed
                          </Typography>
                          <Typography variant="body2" color="warning.main">
                            {Math.round(selectedFile.processing_stats.reduction_percentage || 0)}%
                          </Typography>
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Word Count
                          </Typography>
                          <Typography variant="body2">
                            {selectedFile.processing_stats.word_count?.toLocaleString()}
                          </Typography>
                        </Box>
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                          Quality Metrics
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                          <QualityIndicator score={selectedFile.quality_score} label="Quality" />
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Chunks Created
                          </Typography>
                          <Typography variant="body2">
                            {selectedFile.chunk_count}
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  )}
                  
                  {selectedFile.content_metadata && (
                    <Box sx={{ mt: 3 }}>
                      <Divider sx={{ mb: 2 }} />
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Content Analysis
                      </Typography>
                      
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">
                            Content Type: {selectedFile.content_metadata.content_type_guess || 'Unknown'}
                          </Typography>
                        </Grid>
                        
                        {selectedFile.content_metadata.key_terms && (
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              Key Terms:
                            </Typography>
                            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                              {selectedFile.content_metadata.key_terms.slice(0, 10).map((term, index) => (
                                <Chip
                                  key={index}
                                  label={term}
                                  size="small"
                                  variant="outlined"
                                />
                              ))}
                            </Stack>
                          </Grid>
                        )}
                      </Grid>
                    </Box>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Alert severity="info">
                Select a file to view detailed content analysis
              </Alert>
            )}
          </Box>
        )}

        {/* Quality Metrics Tab */}
        {activeTab === 2 && (
          <Box>
            <Grid container spacing={2}>
              {files.filter(f => f.quality_score > 0).map((file) => (
                <Grid item xs={12} sm={6} md={4} key={file.id || file.file_id}>
                  <Card sx={{ height: '100%' }}>
                    <CardContent sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" sx={{ mb: 2 }} noWrap>
                        {file.filename}
                      </Typography>
                      
                      <QualityIndicator score={file.quality_score} size="small" />
                      
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          {file.chunk_count} chunks
                        </Typography>
                        
                        {file.processing_stats?.reduction_percentage && (
                          <Typography variant="caption" color="warning.main">
                            {Math.round(file.processing_stats.reduction_percentage)}% cleaned
                          </Typography>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default ProcessingDashboard;