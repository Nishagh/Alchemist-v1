import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  IconButton,
  CircularProgress,
  Alert,
  Chip,
  useTheme,
  alpha,
  Tooltip,
  Avatar,
  Container,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import { 
  Archive as ArchiveIcon,
  RestoreFromTrash as RestoreIcon,
  DeleteForever as DeleteForeverIcon,
  SmartToy as SmartToyIcon,
  Visibility as ViewIcon,
  CalendarToday as CalendarIcon,
  Person as PersonIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { getDeletedAgents, deleteAgent } from '../services/agents/agentService';
import { useAuth } from '../utils/AuthContext';

const AgentArchives = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const theme = useTheme();
  
  const [deletedAgents, setDeletedAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPermanentDeleteDialog, setShowPermanentDeleteDialog] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (currentUser) {
      loadDeletedAgents();
    }
  }, [currentUser]);

  const loadDeletedAgents = async () => {
    try {
      setLoading(true);
      const agents = await getDeletedAgents();
      setDeletedAgents(agents);
    } catch (err) {
      console.error('Error loading deleted agents:', err);
      setError('Failed to load archived agents');
    } finally {
      setLoading(false);
    }
  };

  const handleViewAgent = (agentId) => {
    navigate(`/agent-profile/${agentId}`);
  };

  const handlePermanentDelete = (agent) => {
    setAgentToDelete(agent);
    setShowPermanentDeleteDialog(true);
  };

  const confirmPermanentDelete = async () => {
    if (!agentToDelete) return;
    
    try {
      setIsDeleting(true);
      await deleteAgent(agentToDelete.id);
      
      // Remove from local state
      setDeletedAgents(prev => prev.filter(agent => agent.id !== agentToDelete.id));
      
      setShowPermanentDeleteDialog(false);
      setAgentToDelete(null);
    } catch (err) {
      console.error('Error permanently deleting agent:', err);
      alert('Failed to permanently delete agent: ' + err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const getAgentTypeIcon = (type) => {
    const iconMap = {
      'general': <PersonIcon />,
      'code': <SmartToyIcon />,
      'research': <SmartToyIcon />,
      'writing': <SmartToyIcon />,
      'data': <SmartToyIcon />,
      'customer': <SmartToyIcon />
    };
    return iconMap[type] || <SmartToyIcon />;
  };

  const formatDeletedDate = (deletedAt) => {
    if (!deletedAt) return 'Unknown';
    const date = new Date(deletedAt);
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString();
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton onClick={() => navigate('/')} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ArchiveIcon sx={{ mr: 2, fontSize: 32, color: 'text.secondary' }} />
            <Box>
              <Typography variant="h4" fontWeight="bold">
                Agent Archives
              </Typography>
              <Typography variant="body1" color="text.secondary">
                View and manage your deleted agents
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Empty State */}
      {deletedAgents.length === 0 ? (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '50vh',
            textAlign: 'center'
          }}
        >
          <ArchiveIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h5" color="text.secondary" gutterBottom>
            No Archived Agents
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Deleted agents will appear here for reference and potential restoration.
          </Typography>
          <Button
            variant="outlined"
            onClick={() => navigate('/')}
            startIcon={<ArrowBackIcon />}
          >
            Back to Agents
          </Button>
        </Box>
      ) : (
        <>
          {/* Stats */}
          <Box sx={{ mb: 3 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>{deletedAgents.length}</strong> archived agent{deletedAgents.length !== 1 ? 's' : ''} • 
                These agents are no longer active but their data is preserved for reference.
              </Typography>
            </Alert>
          </Box>

          {/* Archived Agents Grid */}
          <Grid container spacing={3}>
            {deletedAgents.map((agent) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={agent.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    opacity: 0.8,
                    border: 1,
                    borderColor: 'error.light',
                    '&:hover': {
                      opacity: 1,
                      transform: 'translateY(-2px)',
                      boxShadow: theme.shadows[4]
                    },
                    transition: 'all 0.2s ease-in-out'
                  }}
                >
                  {/* Archive Badge */}
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      zIndex: 1
                    }}
                  >
                    <Chip
                      label="ARCHIVED"
                      size="small"
                      color="error"
                      variant="filled"
                      sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}
                    />
                  </Box>

                  <CardContent sx={{ flexGrow: 1, p: 3 }}>
                    {/* Agent Avatar & Info */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar
                        src={agent.profile_picture_url}
                        sx={{
                          width: 48,
                          height: 48,
                          mr: 2,
                          bgcolor: alpha(theme.palette.error.main, 0.1),
                          border: 1,
                          borderColor: 'error.light'
                        }}
                      >
                        {!agent.profile_picture_url && getAgentTypeIcon(agent.type)}
                      </Avatar>
                      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                        <Typography
                          variant="h6"
                          sx={{
                            fontWeight: 600,
                            mb: 0.5,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            textDecoration: 'line-through',
                            color: 'text.secondary'
                          }}
                        >
                          {agent.name || `Agent ${agent.id?.slice(-4)}`}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {agent.type || 'General'}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Description */}
                    {agent.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mb: 2,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          opacity: 0.7
                        }}
                      >
                        {agent.description}
                      </Typography>
                    )}

                    {/* Deletion Info */}
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <CalendarIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                        <Typography variant="caption" color="text.secondary">
                          Deleted: {formatDeletedDate(agent.deleted_at)}
                        </Typography>
                      </Box>
                      {agent.deleted_by && (
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <PersonIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                          <Typography variant="caption" color="text.secondary">
                            By: You
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
                      <Tooltip title="View Agent Details">
                        <IconButton
                          size="small"
                          onClick={() => handleViewAgent(agent.id)}
                          sx={{
                            color: 'primary.main',
                            '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.1) }
                          }}
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Permanently Delete">
                        <IconButton
                          size="small"
                          onClick={() => handlePermanentDelete(agent)}
                          sx={{
                            color: 'error.main',
                            '&:hover': { bgcolor: alpha(theme.palette.error.main, 0.1) }
                          }}
                        >
                          <DeleteForeverIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {/* Permanent Delete Confirmation Dialog */}
      <Dialog
        open={showPermanentDeleteDialog}
        onClose={() => !isDeleting && setShowPermanentDeleteDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', color: 'error.main' }}>
          <DeleteForeverIcon sx={{ mr: 1 }} />
          Permanently Delete Agent
        </DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight="bold">
              ⚠️ This action is irreversible!
            </Typography>
          </Alert>
          <Typography gutterBottom>
            Are you sure you want to permanently delete "{agentToDelete?.name}"?
          </Typography>
          <Box component="ul" sx={{ mt: 2, pl: 2 }}>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              All agent data will be completely removed
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              Conversation history will be lost forever
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              Analytics data will be permanently deleted
            </Typography>
            <Typography component="li" variant="body2">
              This action cannot be undone
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button 
            onClick={() => setShowPermanentDeleteDialog(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button 
            onClick={confirmPermanentDelete}
            color="error"
            variant="contained"
            disabled={isDeleting}
            startIcon={isDeleting ? <CircularProgress size={16} color="inherit" /> : <DeleteForeverIcon />}
          >
            {isDeleting ? 'Deleting...' : 'Permanently Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AgentArchives;