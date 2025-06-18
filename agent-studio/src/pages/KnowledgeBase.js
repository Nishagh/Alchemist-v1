import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  LinearProgress,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Divider,
  TextField,
  InputAdornment,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Tooltip,
  Badge,
  ToggleButtonGroup,
  ToggleButton,
  Avatar,
  useTheme,
  alpha
} from '@mui/material';
import {
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
  Search as SearchIcon,
  CloudUpload as CloudUploadIcon,
  FileCopy as FileCopyIcon,
  PictureAsPdf as PdfIcon,
  Description as DocIcon,
  Code as CodeIcon,
  Image as ImageIcon,
  InsertDriveFile as DefaultFileIcon,
  ViewList as TableViewIcon,
  ViewModule as CardViewIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { getAgentKnowledgeBase, uploadKnowledgeBaseFile, deleteKnowledgeBaseFile, searchKnowledgeBase } from '../services';
import { format, formatDistance } from 'date-fns';

// Helper function to extract file type from filename
const getFileTypeFromName = (filename) => {
  if (!filename) return 'Unknown';
  
  const extension = filename.split('.').pop().toLowerCase();
  
  const typeMap = {
    'pdf': 'PDF Document',
    'doc': 'Word Document',
    'docx': 'Word Document',
    'txt': 'Text File',
    'csv': 'CSV Spreadsheet',
    'xls': 'Excel Spreadsheet',
    'xlsx': 'Excel Spreadsheet',
    'ppt': 'PowerPoint',
    'pptx': 'PowerPoint',
    'jpg': 'Image',
    'jpeg': 'Image',
    'png': 'Image',
    'gif': 'Image',
    'md': 'Markdown',
    'json': 'JSON Data',
    'html': 'HTML Document',
    'htm': 'HTML Document'
  };
  
  return typeMap[extension] || `${extension.toUpperCase()} File`;
};

// Helper function to get file icon based on file type
const getFileIcon = (filename, contentType) => {
  if (!filename && !contentType) return <DefaultFileIcon />;
  
  // First check content type if available
  if (contentType) {
    if (contentType.includes('pdf')) return <PdfIcon color="error" />;
    if (contentType.includes('word') || contentType.includes('doc')) return <DocIcon color="primary" />;
    if (contentType.includes('image')) return <ImageIcon color="success" />;
    if (contentType.includes('json') || contentType.includes('javascript') || contentType.includes('text/plain')) return <CodeIcon color="secondary" />;
  }
  
  // Fallback to checking extension
  const extension = filename ? filename.split('.').pop().toLowerCase() : '';
  
  switch (extension) {
    case 'pdf': return <PdfIcon color="error" />;
    case 'doc': case 'docx': return <DocIcon color="primary" />;
    case 'jpg': case 'jpeg': case 'png': case 'gif': return <ImageIcon color="success" />;
    case 'txt': case 'md': case 'json': case 'html': case 'htm': case 'js': case 'css': return <CodeIcon color="secondary" />;
    default: return <DefaultFileIcon />;
  }
};

// Helper function to format file size
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return 'Unknown';
  
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Helper function to format date
const formatDate = (dateString) => {
  if (!dateString) return 'Unknown';
  try {
    const date = new Date(dateString);
    return format(date, 'MMM d, yyyy h:mm a');
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid date';
  }
};

// Helper function to get relative time
const getRelativeTime = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return formatDistance(date, new Date(), { addSuffix: true });
  } catch (error) {
    return '';
  }
};

// Helper function to get status badge for indexing
const getStatusBadge = (file) => {
  if (!file) return null;
  
  if (file.indexing_error) {
    return (
      <Tooltip title={`Error: ${file.indexing_error}`}>
        <Chip 
          icon={<ErrorIcon />} 
          label="Error" 
          color="error" 
          size="small" 
          variant="outlined"
        />
      </Tooltip>
    );
  }
  
  if (file.indexing_status === 'complete' && file.indexed) {
    return (
      <Tooltip title="File has been successfully indexed and is ready for search">
        <Chip 
          icon={<CheckCircleIcon />} 
          label="Indexed" 
          color="success" 
          size="small"
          variant="outlined"
        />
      </Tooltip>
    );
  }
  
  if (file.indexing_phase === 'uploading' || file.progress_percent < 100) {
    return (
      <Tooltip title={`Uploading: ${file.progress_percent || 0}% complete`}>
        <Chip 
          icon={<PendingIcon />} 
          label="Uploading" 
          color="info" 
          size="small"
          variant="outlined"
        />
      </Tooltip>
    );
  }
  
  if (file.indexing_phase === 'processing' || file.indexing_status === 'processing') {
    return (
      <Tooltip title="File is being processed and indexed">
        <Chip 
          icon={<ScheduleIcon />} 
          label="Processing" 
          color="warning" 
          size="small"
          variant="outlined"
        />
      </Tooltip>
    );
  }
  
  return (
    <Tooltip title="File status is unknown">
      <Chip 
        icon={<InfoIcon />} 
        label="Unknown" 
        color="default" 
        size="small"
        variant="outlined"
      />
    </Tooltip>
  );
};

const KnowledgeBase = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const fileInputRef = useRef(null);
  
  // State
  const [agent, setAgent] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fileLoading, setFileLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [confirmDelete, setConfirmDelete] = useState({ open: false, fileId: null });
  const [uploadStatus, setUploadStatus] = useState({ show: false, phase: 'preparing', progress: 0, error: null });
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'card'
  
  // Load agent data and knowledge base files
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch agent data
        //const agentData = await getAgent(agentId);
        //setAgent(agentData);
        
        // Fetch knowledge base files
        await fetchKnowledgeBaseFiles();
      } catch (error) {
        console.error('Error loading data:', error);
        setNotification({
          open: true,
          message: 'Failed to load knowledge base data',
          severity: 'error'
        });
      } finally {
        setLoading(false);
      }
    };
    
    if (agentId) {
      fetchData();
    }
  }, [agentId]);
  
  const fetchKnowledgeBaseFiles = async () => {
    try {
      const files = await getAgentKnowledgeBase(agentId);
      console.log('Fetched files:', files);
      setFiles(files);
    } catch (error) {
      console.error('Error fetching knowledge base files:', error);
      setNotification({
        open: true,
        message: 'Failed to load knowledge base files',
        severity: 'error'
      });
    }
  };
  
  const handleFileUpload = () => {
    fileInputRef.current.click();
  };
  
  const handleFileSelected = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    try {
      setFileLoading(true);
      setUploadStatus({ show: true, phase: 'uploading', progress: 10, error: null });
      
      // Create form data
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // Simulate progress (in a real app, you'd use upload progress events)
      const progressInterval = setInterval(() => {
        setUploadStatus(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90)
        }));
      }, 300);
      
      // Get agent details to ensure we have the correct ID format
      // Some components might use agent.id while others use agent.agent_id
      //const agentData = await getAgent(agentId);
      const effectiveAgentId = agent.id || agentId;
      
      // Upload file with the agent_id field
      await uploadKnowledgeBaseFile(effectiveAgentId, selectedFile);
      
      clearInterval(progressInterval);
      
      // Refresh file list
      await fetchKnowledgeBaseFiles();
      
      setUploadStatus({ show: true, phase: 'complete', progress: 100, error: null });
      setNotification({
        open: true,
        message: 'File uploaded successfully',
        severity: 'success'
      });
      
      // Reset form
      e.target.value = null;
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadStatus({ 
        show: true, 
        phase: 'failed', 
        progress: 0, 
        error: error.message || 'Failed to upload file' 
      });
      setNotification({
        open: true,
        message: `Upload failed: ${error.message}`,
        severity: 'error'
      });
    } finally {
      setFileLoading(false);
    }
  };
  
  const handleDeleteFile = async (fileId) => {
    try {
      setLoading(true);
      
      await deleteKnowledgeBaseFile(agentId, fileId);
      
      // Refresh file list
      await fetchKnowledgeBaseFiles();
      
      setNotification({
        open: true,
        message: 'File deleted successfully',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error deleting file:', error);
      setNotification({
        open: true,
        message: `Delete failed: ${error.message}`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      setLoading(true);
      
      const results = await searchKnowledgeBase(agentId, searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching knowledge base:', error);
      setNotification({
        open: true,
        message: `Search failed: ${error.message}`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };
  
  const handleOpenDeleteConfirm = (fileId) => {
    setConfirmDelete({ open: true, fileId });
  };
  
  const handleCloseDeleteConfirm = () => {
    setConfirmDelete({ open: false, fileId: null });
  };
  
  const handleConfirmDelete = () => {
    if (confirmDelete.fileId) {
      handleDeleteFile(confirmDelete.fileId);
    }
    handleCloseDeleteConfirm();
  };
  
  return (
    <Box sx={{ 
      height: 'calc(100vh - 64px)', 
      display: 'flex', 
      flexDirection: 'column',
      backgroundColor: alpha(theme.palette.primary.light, 0.05),
      width: '100%',
      maxWidth: '100%'
    }}>
      {/* Action Bar */}
      <Box sx={{ 
        px: 2, 
        py: 1.5, 
        display: 'flex', 
        justifyContent: 'space-between', 
        borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
        backgroundColor: alpha(theme.palette.background.paper, 0.9),
        width: '100%'
      }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/agent-editor/${agentId}`)}
          variant="outlined"
          size="small"
          sx={{
            borderColor: theme.palette.primary.main,
            color: theme.palette.primary.main,
            '&:hover': {
              backgroundColor: alpha(theme.palette.primary.main, 0.05)
            }
          }}
        >
          Back to Agent
        </Button>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
            sx={{
              mr: 2,
              width: '250px',
              '& .MuiOutlinedInput-root': {
                borderRadius: 1.5,
              }
            }}
          />
          <Button
            variant="outlined"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            disabled={!searchQuery.trim()}
            sx={{
              mr: 2,
              borderColor: theme.palette.primary.main,
              color: theme.palette.primary.main,
              '&:hover': {
                backgroundColor: alpha(theme.palette.primary.main, 0.05)
              }
            }}
          >
            Search
          </Button>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
            sx={{ mr: 2 }}
          >
            <ToggleButton value="table" aria-label="table view">
              <TableViewIcon />
            </ToggleButton>
            <ToggleButton value="card" aria-label="card view">
              <CardViewIcon />
            </ToggleButton>
          </ToggleButtonGroup>
          <Button
            variant="contained"
            startIcon={<CloudUploadIcon />}
            onClick={handleFileUpload}
            sx={{ 
              fontWeight: 'bold',
              boxShadow: 'none',
              '&:hover': {
                boxShadow: '0 2px 5px rgba(0, 0, 0, 0.1)'
              }
            }}
          >
            Upload File
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileSelected}
          />
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ 
        flexGrow: 1, 
        overflow: 'auto', 
        p: 0, 
        position: 'relative',
        backgroundColor: '#ffffff' 
      }}>
        {loading ? (
          <LinearProgress />
        ) : (
          <>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom color={theme.palette.primary.main}>
                Knowledge Base: {agent?.name || 'Agent'}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Files uploaded to this knowledge base will be accessible to your agent.
              </Typography>
            </Box>

            {uploadStatus.show && (
              <Box sx={{ px: 3, pb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">Uploading file...</Typography>
                  <Typography variant="body2">{uploadStatus.progress}%</Typography>
                </Box>
                <Box sx={{ width: '100%', bgcolor: alpha(theme.palette.primary.main, 0.1), borderRadius: 1, height: 10 }}>
                  <Box 
                    sx={{ 
                      width: `${uploadStatus.progress}%`, 
                      bgcolor: theme.palette.primary.main,
                      height: '100%',
                      borderRadius: 1,
                      transition: 'width 0.3s ease'
                    }} 
                  />
                </Box>
              </Box>
            )}

            {/* File listing */}
            <Box sx={{ px: 3, py: 2 }}>
              {files.length === 0 ? (
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 4, 
                  borderRadius: 2, 
                  border: `1px dashed ${alpha(theme.palette.primary.main, 0.2)}`,
                  bgcolor: alpha(theme.palette.primary.light, 0.02) 
                }}>
                  <Typography variant="body1" color="text.secondary">
                    No files in knowledge base. Upload files to get started.
                  </Typography>
                </Box>
              ) : viewMode === 'table' ? (
                /* Table View */
                <TableContainer sx={{ 
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`, 
                  borderRadius: 2, 
                  overflow: 'hidden'
                }}>
                  <Table stickyHeader>
                    <TableHead>
                      <TableRow sx={{ bgcolor: alpha(theme.palette.primary.light, 0.05) }}>
                        <TableCell>File Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Size</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Upload Date</TableCell>
                        <TableCell>Chunks</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {files.map((file) => (
                        <TableRow key={file.id || `file-${files.indexOf(file)}`} hover>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              {getFileIcon(file.filename, file.content_type)}
                              <Box sx={{ ml: 1 }}>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                  {file.filename || file.name || 'Unnamed File'}
                                </Typography>
                                {file.id && (
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                    ID: {file.id.substring(0, 8)}...
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {file.content_type || getFileTypeFromName(file.filename || file.name) || 'Unknown'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {formatFileSize(file.size)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {getStatusBadge(file)}
                            {file.progress_percent < 100 && file.progress_percent > 0 && (
                              <Box sx={{ width: '100%', mt: 1 }}>
                                <LinearProgress 
                                  variant="determinate" 
                                  value={file.progress_percent} 
                                  sx={{ height: 5, borderRadius: 5 }}
                                />
                              </Box>
                            )}
                          </TableCell>
                          <TableCell>
                            <Tooltip title={formatDate(file.upload_date)}>
                              <Typography variant="body2">
                                {getRelativeTime(file.upload_date)}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Tooltip title={file.chunk_count ? `${file.chunk_count} searchable chunks` : 'Not chunked yet'}>
                              <Typography variant="body2">
                                {file.chunk_count || '-'}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell align="right">
                            <IconButton 
                              color="error" 
                              onClick={() => handleOpenDeleteConfirm(file.id || `file-${files.indexOf(file)}`)}
                              size="small"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                /* Card View */
                <Grid container spacing={2}>
                  {files.map((file) => (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={file.id || `file-${files.indexOf(file)}`}>
                      <Card 
                        elevation={0} 
                        sx={{
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          position: 'relative',
                          transition: 'transform 0.2s, box-shadow 0.2s',
                          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)'
                          }
                        }}
                      >
                        {file.progress_percent < 100 && file.progress_percent > 0 && (
                          <LinearProgress 
                            variant="determinate" 
                            value={file.progress_percent} 
                            sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, borderRadius: '4px 4px 0 0' }}
                          />
                        )}
                        
                        <CardContent sx={{ flexGrow: 1, pt: file.progress_percent < 100 ? 2 : 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                            <Avatar 
                              variant="rounded" 
                              sx={{ 
                                bgcolor: alpha(theme.palette.primary.light, 0.05),
                                width: 40,
                                height: 40,
                                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}
                            >
                              {getFileIcon(file.filename, file.content_type)}
                            </Avatar>
                            {getStatusBadge(file)}
                          </Box>
                          
                          <Typography variant="subtitle1" component="div" noWrap sx={{ fontWeight: 500 }}>
                            {file.filename || file.name || 'Unnamed File'}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              {formatFileSize(file.size)}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {file.chunk_count ? `${file.chunk_count} chunks` : ''}
                            </Typography>
                          </Box>
                          
                          <Divider sx={{ my: 1 }} />
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Tooltip title={formatDate(file.upload_date)}>
                              <Typography variant="caption" color="text.secondary">
                                Uploaded {getRelativeTime(file.upload_date)}
                              </Typography>
                            </Tooltip>
                            {file.last_updated && file.last_updated !== file.upload_date && (
                              <Tooltip title={formatDate(file.last_updated)}>
                                <Typography variant="caption" color="text.secondary">
                                  Updated {getRelativeTime(file.last_updated)}
                                </Typography>
                              </Tooltip>
                            )}
                          </Box>
                          
                          {file.indexing_error && (
                            <Box sx={{ mt: 1, p: 1, bgcolor: alpha(theme.palette.error.main, 0.1), borderRadius: 1 }}>
                              <Typography variant="caption" color="error.dark">
                                Error: {file.indexing_error}
                              </Typography>
                            </Box>
                          )}
                        </CardContent>
                        
                        <CardActions sx={{ justifyContent: 'flex-end', p: 1 }}>
                          <IconButton 
                            color="error" 
                            onClick={() => handleOpenDeleteConfirm(file.id || `file-${files.indexOf(file)}`)} 
                            size="small"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </CardActions>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
              
              {/* Search Results Section */}
              {searchResults.length > 0 && (
                <Box sx={{ mt: 4 }}>
                  <Typography variant="h6" color={theme.palette.primary.main} gutterBottom>
                    Search Results
                  </Typography>
                  {searchResults.map((result, index) => (
                    <Paper 
                      key={index} 
                      elevation={0} 
                      sx={{ 
                        p: 2, 
                        mb: 2, 
                        borderRadius: 2,
                        border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                        bgcolor: alpha(theme.palette.primary.light, 0.02)
                      }}
                    >
                      <Typography variant="subtitle2" color={theme.palette.primary.main}>
                        {result.file_name || 'Untitled'} 
                        {result.score && ` - Match Score: ${result.score.toFixed(2)}`}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {result.text || 'No preview available'}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              )}
            </Box>
          </>
        )}
      </Box>

      {/* Notifications */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          elevation={6} 
          variant="filled"
        >
          {notification.message}
        </Alert>
      </Snackbar>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={confirmDelete.open}
        onClose={handleCloseDeleteConfirm}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this file from the knowledge base? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteConfirm} color="primary">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KnowledgeBase;
