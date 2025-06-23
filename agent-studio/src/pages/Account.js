import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Avatar,
  Divider,
  Switch,
  FormControlLabel,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useTheme,
  alpha,
  IconButton,
  Chip
} from '@mui/material';
import {
  Person as PersonIcon,
  Edit as EditIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Language as LanguageIcon,
  Palette as PaletteIcon,
  CreditCard as CreditCardIcon,
  Delete as DeleteIcon,
  Lock as LockIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';
import { useAuth } from '../utils/AuthContext';
import { useThemeMode } from '../App';

const Account = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();
  const { mode, toggleTheme } = useThemeMode();
  
  // State management
  const [editing, setEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    displayName: currentUser?.displayName || '',
    email: currentUser?.email || '',
    phone: '',
    company: '',
    timezone: 'Asia/Kolkata'
  });
  
  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    pushNotifications: false,
    marketingEmails: false,
    securityAlerts: true
  });
  
  const [passwordDialog, setPasswordDialog] = useState(false);
  const [deleteAccountDialog, setDeleteAccountDialog] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSaveProfile = () => {
    // Here you would typically save to backend
    setEditing(false);
    // Show success message
  };

  const handlePreferenceChange = (key) => (event) => {
    setPreferences({
      ...preferences,
      [key]: event.target.checked
    });
  };

  const handleDeleteAccount = () => {
    // Handle account deletion
    setDeleteAccountDialog(false);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Account Settings
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Manage your profile, preferences, and security settings
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" fontWeight="bold">
                  Profile Information
                </Typography>
                <Button
                  startIcon={<EditIcon />}
                  onClick={() => setEditing(!editing)}
                  variant={editing ? "contained" : "outlined"}
                  sx={{
                    borderColor: theme.palette.text.primary,
                    color: editing ? (theme.palette.mode === 'dark' ? '#000000' : '#ffffff') : theme.palette.text.primary,
                    bgcolor: editing ? (theme.palette.mode === 'dark' ? '#ffffff' : '#000000') : 'transparent',
                    '&:hover': {
                      borderColor: theme.palette.text.primary,
                      backgroundColor: editing ? 
                        (theme.palette.mode === 'dark' ? '#e5e5e5' : '#333333') :
                        (theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0')
                    }
                  }}
                >
                  {editing ? 'Save' : 'Edit'}
                </Button>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar
                  src={currentUser?.photoURL}
                  sx={{
                    width: 80,
                    height: 80,
                    mr: 3,
                    bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
                    color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff'
                  }}
                >
                  {!currentUser?.photoURL && <PersonIcon sx={{ fontSize: 40 }} />}
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    {currentUser?.displayName || 'User'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {currentUser?.email}
                  </Typography>
                  <Chip
                    label="Verified"
                    size="small"
                    sx={{
                      mt: 1,
                      bgcolor: theme.palette.mode === 'dark' ? '#333333' : '#f0f0f0',
                      color: theme.palette.text.primary
                    }}
                  />
                </Box>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Display Name"
                    value={profileData.displayName}
                    onChange={(e) => setProfileData({...profileData, displayName: e.target.value})}
                    disabled={!editing}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    value={profileData.email}
                    disabled={true}
                    margin="normal"
                    helperText="Email cannot be changed"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Phone"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                    disabled={!editing}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Company"
                    value={profileData.company}
                    onChange={(e) => setProfileData({...profileData, company: e.target.value})}
                    disabled={!editing}
                    margin="normal"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Security Settings */}
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Security & Privacy
              </Typography>
              
              <List>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <LockIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Password"
                    secondary="Last changed 3 months ago"
                  />
                  <ListItemSecondaryAction>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => setPasswordDialog(true)}
                      sx={{
                        borderColor: theme.palette.text.primary,
                        color: theme.palette.text.primary,
                        '&:hover': {
                          borderColor: theme.palette.text.primary,
                          backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                        }
                      }}
                    >
                      Change
                    </Button>
                  </ListItemSecondaryAction>
                </ListItem>
                
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <SecurityIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Two-Factor Authentication"
                    secondary="Add an extra layer of security"
                  />
                  <ListItemSecondaryAction>
                    <Button
                      size="small"
                      variant="outlined"
                      sx={{
                        borderColor: theme.palette.text.primary,
                        color: theme.palette.text.primary,
                        '&:hover': {
                          borderColor: theme.palette.text.primary,
                          backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                        }
                      }}
                    >
                      Enable
                    </Button>
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Preferences & Quick Actions */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Preferences
              </Typography>
              
              <List>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <PaletteIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Theme"
                    secondary={`Currently ${mode} mode`}
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={mode === 'dark'}
                      onChange={toggleTheme}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <EmailIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Email Notifications"
                    secondary="Receive updates via email"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={preferences.emailNotifications}
                      onChange={handlePreferenceChange('emailNotifications')}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <SecurityIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Security Alerts"
                    secondary="Get notified of security events"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={preferences.securityAlerts}
                      onChange={handlePreferenceChange('securityAlerts')}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Quick Actions
              </Typography>
              
              <Button
                fullWidth
                variant="outlined"
                startIcon={<CreditCardIcon />}
                onClick={() => navigate('/credits')}
                sx={{
                  mb: 2,
                  borderColor: theme.palette.text.primary,
                  color: theme.palette.text.primary,
                  '&:hover': {
                    borderColor: theme.palette.text.primary,
                    backgroundColor: theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
                  }
                }}
              >
                Credits & Usage
              </Button>
              
              <Divider sx={{ my: 2 }} />
              
              <Button
                fullWidth
                variant="outlined"
                startIcon={<DeleteIcon />}
                onClick={() => setDeleteAccountDialog(true)}
                color="error"
                sx={{ mb: 1 }}
              >
                Delete Account
              </Button>
              
              <Typography variant="caption" color="text.secondary" align="center" display="block">
                This action cannot be undone
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Password Change Dialog */}
      <Dialog open={passwordDialog} onClose={() => setPasswordDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Current Password"
            type={showPassword ? 'text' : 'password'}
            margin="normal"
            InputProps={{
              endAdornment: (
                <IconButton onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                </IconButton>
              )
            }}
          />
          <TextField
            fullWidth
            label="New Password"
            type="password"
            margin="normal"
            helperText="Must be at least 8 characters"
          />
          <TextField
            fullWidth
            label="Confirm New Password"
            type="password"
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialog(false)}>Cancel</Button>
          <Button 
            variant="contained"
            sx={{
              bgcolor: theme.palette.mode === 'dark' ? '#ffffff' : '#000000',
              color: theme.palette.mode === 'dark' ? '#000000' : '#ffffff',
              '&:hover': {
                bgcolor: theme.palette.mode === 'dark' ? '#e5e5e5' : '#333333'
              }
            }}
          >
            Update Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={deleteAccountDialog} onClose={() => setDeleteAccountDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle color="error">Delete Account</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            This action is permanent and cannot be undone!
          </Alert>
          <Typography variant="body1" gutterBottom>
            Deleting your account will:
          </Typography>
          <Typography variant="body2" component="ul" sx={{ ml: 2 }}>
            <li>Permanently delete all your agents</li>
            <li>Remove all conversation history</li>
            <li>Cancel any active subscriptions</li>
            <li>Delete all associated data</li>
          </Typography>
          <TextField
            fullWidth
            label="Type 'DELETE' to confirm"
            margin="normal"
            helperText="This confirms you understand the consequences"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAccountDialog(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDeleteAccount}>
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Account;