import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Divider,
  CircularProgress,
  Snackbar,
  Alert,
  AlertTitle,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  useTheme,
  alpha,
  Fade,
  Slide,
  Zoom,
  Avatar,
  Chip,
  Card,
  CardContent,
  Tooltip,
  Badge,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  InputAdornment,
  Grid,
  CardActions,
  ToggleButtonGroup,
  ToggleButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Link
} from '@mui/material';
import {
  Send as SendIcon,
  ArrowBack as ArrowBackIcon,
  AttachFile as AttachFileIcon,
  PlayArrow as PlayIcon,
  MenuBook as MenuBookIcon,
  Psychology as PsychologyIcon,
  Lock as LockIcon,
  Code as CodeIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
  AutoAwesome as AutoAwesomeIcon,
  Refresh as RefreshIcon,
  Lightbulb as LightbulbIcon,
  Timeline as TimelineIcon,
  Edit as EditIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  BugReport as BugReportIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  CloudUpload as CloudUploadIcon,
  FileCopy as FileCopyIcon,
  PictureAsPdf as PdfIcon,
  Description as DocIcon,
  Image as ImageIcon,
  InsertDriveFile as DefaultFileIcon,
  ViewList as TableViewIcon,
  ViewModule as CardViewIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
  ContentCopy as CopyAllIcon,
  KeyboardArrowRight as ArrowRightIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  Send as SendIcon2,
  PlayArrow as PlayArrowIcon,
  Download as DownloadIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { getAgentConversations, uploadKnowledgeBaseFile, interactWithAlchemist, getAgentKnowledgeBase, deleteKnowledgeBaseFile, searchKnowledgeBase, uploadApiSpecification, deployMcpServer, checkDeploymentStatus, checkServerStatus, getLiveTools, testTool, getDeploymentLogs, deleteMcpServer } from '../services';
import { useAuth } from '../utils/AuthContext';
import { format, formatDistance } from 'date-fns';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco, atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { db } from '../utils/firebase';
import { doc, getDoc, onSnapshot, collection, query, orderBy, getDocs } from 'firebase/firestore';

// Ensure we have a valid URL by providing a fallback if env variable isn't loaded
const user_agent_url = process.env.REACT_APP_USER_AGENT_URL || 'https://standalone-agent-851487020021.us-central1.run.app';
console.log('Using user agent URL:', user_agent_url);




// TabPanel component
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`agent-tabpanel-${index}`}
      aria-labelledby={`agent-tab-${index}`}
      {...other}
      style={{ height: '100%', display: value === index ? 'flex' : 'none', flexDirection: 'column' }}
    >
      {value === index && (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

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

// Helper function to convert Firestore timestamp to JavaScript Date
const convertTimestamp = (timestamp) => {
  if (!timestamp) return null;
  
  // If it's already a JavaScript Date object, return it
  if (timestamp instanceof Date) {
    return timestamp;
  }
  
  // If it's a Firestore timestamp object with seconds property
  if (timestamp && typeof timestamp === 'object' && timestamp.seconds) {
    return new Date(timestamp.seconds * 1000);
  }
  
  // If it's an ISO string or number, try to parse it
  if (typeof timestamp === 'string' || typeof timestamp === 'number') {
    const date = new Date(timestamp);
    if (!isNaN(date.getTime())) {
      return date;
    }
  }
  
  return null;
};

// Helper function to format date
const formatDate = (timestamp) => {
  if (!timestamp) return 'Unknown';
  try {
    const date = convertTimestamp(timestamp);
    if (!date) return 'Invalid date';
    return format(date, 'MMM d, yyyy h:mm a');
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid date';
  }
};

// Helper function to get relative time
const getRelativeTime = (timestamp) => {
  if (!timestamp) return '';
  try {
    const date = convertTimestamp(timestamp);
    if (!date) return '';
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

const AgentEditor = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const { currentUser } = useAuth();
  
  const [agent, setAgent] = useState({
    id: (agentId && agentId !== 'undefined' && agentId !== 'null') ? agentId : uuidv4(),
    name: '',
    description: '',
    type: 'generic', // Default value for the Select component
    model: 'gpt-4',
    prompt: '',
    knowledge_base: [],
    tools: [],
    system_name: 'Alchemist',
    user_name: 'Human',
    custom_instructions: '',
    owner_id: currentUser?.uid || null
  });
  
  // Tab state
  const [activeTab, setActiveTab] = useState(0);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [testMessages, setTestMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [testInput, setTestInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [conversation, setConversation] = useState({ id: null });
  const [conversations, setConversations] = useState([]);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [showThoughtProcess, setShowThoughtProcess] = useState(false);
  const [thoughtProcess, setThoughtProcess] = useState([]);
  const [files, setFiles] = useState([]);
  const [creatingConversation, setCreatingConversation] = useState(false);
  const [testConversationId, setTestConversationId] = useState(null);
  const fileInputRef = useRef(null);
  
  // Additional state for Knowledge Base functionality
  const [kbFiles, setKbFiles] = useState([]);
  const [fileLoading, setFileLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [confirmDelete, setConfirmDelete] = useState({ open: false, fileId: null });
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'card'
  const kbFileInputRef = useRef(null);
  
  // Additional state for API Integration functionality
  const apiFileInputRef = useRef(null);
  const [apiName, setApiName] = useState('');
  const [showNameDialog, setShowNameDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [apiSpecPreview, setApiSpecPreview] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [apiTabValue, setApiTabValue] = useState(0);
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [endpoints, setEndpoints] = useState([]);
  const [requestMethod, setRequestMethod] = useState('GET');
  const [pathParams, setPathParams] = useState({});
  const [queryParams, setQueryParams] = useState({});
  const [headerParams, setHeaderParams] = useState({});
  const [requestBody, setRequestBody] = useState('');
  const [requestUrl, setRequestUrl] = useState('');
  const [responseData, setResponseData] = useState(null);
  const [responseStatus, setResponseStatus] = useState(null);
  const [isTestingApi, setIsTestingApi] = useState(false);
  const [missingRequiredParams, setMissingRequiredParams] = useState([]);
  const [paramErrors, setParamErrors] = useState({});
  const [isRequestValid, setIsRequestValid] = useState(false);
  const [paramFieldsTouched, setParamFieldsTouched] = useState({});
  const [mcpDeploymentStatus, setMcpDeploymentStatus] = useState({
    isDeployed: false,
    isRunning: false,
    lastChecked: null,
    error: null
  });
  
  // UI state
  const [loading, setLoading] = useState(!!agentId);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [uploadStatus, setUploadStatus] = useState({ show: false, phase: 'preparing', progress: 0, error: null });
  const [apiUploadStatus, setApiUploadStatus] = useState({ show: false, progress: 0, error: null, openapi_spec: null, mcp_config: null });
  const [firestoreApiFiles, setFirestoreApiFiles] = useState(null);
  const [isDeployingMcp, setIsDeployingMcp] = useState(false);
  const [deploymentId, setDeploymentId] = useState(null);
  const [deploymentHistory, setDeploymentHistory] = useState([]);
  const [integrationSummary, setIntegrationSummary] = useState(null);
  const [liveTools, setLiveTools] = useState([]);
  const [successModal, setSuccessModal] = useState(false);
  const [unauthorized, setUnauthorized] = useState(false);
  
  // Deployment logs dialog state
  const [logsDialog, setLogsDialog] = useState({
    open: false,
    deploymentId: null,
    logs: '',
    loading: false
  });
  
  // Tool test dialog state
  const [toolTestDialog, setToolTestDialog] = useState({
    open: false,
    toolName: '',
    parameters: '{}',
    result: null,
    loading: false,
    error: null
  });
  
  const messagesEndRef = useRef(null);
  const testMessagesEndRef = useRef(null);

  // Redirect to login if user is not logged in
  useEffect(() => {
    console.log("AgentEditor: Checking authentication");
    console.log("AgentEditor: Current user:", currentUser);
    console.log("AgentEditor: Loading state:", loading);
    
    // Let the ProtectedRoute handle redirects instead of doing it here
    // This prevents potential redirect loops
  }, [currentUser, loading, navigate, agentId]);

  useEffect(() => {
    console.log('Agent:', agent);
    if (agentId && agentId !== 'undefined' && agentId !== 'null') {
      const agentDocRef = doc(db, 'alchemist_agents', agentId);
      const unsubscribe = onSnapshot(agentDocRef, (docSnapshot) => {
        console.log('Agent doc:', docSnapshot.data());
        if (docSnapshot.exists()) {
          const agentData = docSnapshot.data();
          setAgent(agentData);
          console.log(agentData)
          setIntegrationSummary(agentData.api_integration)
          
          // Check for API upload progress updates (legacy format)
          if (agentData.openapi_spec || agentData.mcp_config) {
            const uploadProgress = {
              show: true,
              openapi_spec: agentData.openapi_spec || null,
              mcp_config: agentData.mcp_config || null,
              error: null
            };
            
            // Calculate overall progress based on completion status
            let progress = 0;
            const hasOpenApi = agentData.openapi_spec;
            const hasMcpConfig = agentData.mcp_config;
            const totalFiles = (hasOpenApi ? 1 : 0) + (hasMcpConfig ? 1 : 0);
            
            if (totalFiles === 0) {
              progress = 0;
            } else {
              let completedFiles = 0;
              if (agentData.openapi_spec?.status === 'uploaded') {
                completedFiles += 1;
              }
              if (agentData.mcp_config?.status === 'converted' || agentData.mcp_config?.status === 'uploaded_directly') {
                completedFiles += 1;
              }
              progress = (completedFiles / totalFiles) * 100;
            }
            uploadProgress.progress = progress;
            
            setApiUploadStatus(uploadProgress);
            
            // Auto-hide after both are complete
            //if (progress >= 100) {
            //  setTimeout(() => {
            //    setApiUploadStatus(prev => ({ ...prev, show: false }));
            //  }, 3000);
            //}
          }
          
          // Check for API files information (correct format)
          if (agentData.openapi_spec || agentData.mcp_config) {
            console.log('Firestore API files data - openapi_spec:', agentData.openapi_spec);
            console.log('Firestore API files data - mcp_config:', agentData.mcp_config);
            console.log('Full agent data:', agentData);
            setFirestoreApiFiles({
              openapi_spec: agentData.openapi_spec || null,
              mcp_config: agentData.mcp_config || null
            });
          }
          
          // Fetch MCP deployment status from separate collection
          fetchMcpDeploymentStatus();
        }
      });
      
      // Return cleanup function
      return () => unsubscribe();
    }
  }, [agentId]);

  // Load agent data if editing an existing agent
  useEffect(() => {
    // Only fetch if agentId is valid (not undefined, null, or empty) and user is authenticated
    if (agentId && agentId !== 'undefined' && agentId !== 'null' && currentUser) {
      fetchConversationMessages();
    } else if (agentId === 'undefined' || agentId === 'null') {
      // If we got an invalid ID in the URL, just show the empty form
      setLoading(false);
    }
  }, [agentId, currentUser]);

  // Listen to deployment history from Firestore and track current deployment status
  useEffect(() => {
    if (agentId && currentUser) {
      console.log('Setting up deployment history listener for agent:', agentId);
      
      // Create a reference to the deployments subcollection
      const deploymentsRef = collection(db, 'alchemist_agents', agentId, 'deployments');
      const deploymentsQuery = query(deploymentsRef, orderBy('created_at', 'desc'));
      
      const unsubscribe = onSnapshot(deploymentsQuery, (snapshot) => {
        const deployments = [];
        snapshot.forEach((doc) => {
          deployments.push({
            id: doc.id,
            ...doc.data()
          });
        });
        
        console.log('Deployment history updated:', deployments);
        setDeploymentHistory(deployments);
        
        // Check the most recent deployment to determine current state
        if (deployments.length > 0) {
          const latestDeployment = deployments[0];
          console.log('Latest deployment:', latestDeployment);
          
          // Update deployment tracking state based on latest deployment
          if (latestDeployment.status === 'in_progress' || latestDeployment.status === 'pending') {
            setIsDeployingMcp(true);
            setDeploymentId(latestDeployment.deployment_id || latestDeployment.id);
          } else {
            setIsDeployingMcp(false);
            setDeploymentId(null);
            
            // Update MCP deployment status based on latest deployment result
            if (latestDeployment.status === 'completed') {
              setMcpDeploymentStatus(prev => ({
                ...prev,
                isDeployed: true,
                isRunning: latestDeployment.health_status === 'healthy' || latestDeployment.server_status === 'running',
                lastChecked: new Date().toISOString(),
                error: null
              }));
            } else if (latestDeployment.status === 'failed') {
              setMcpDeploymentStatus(prev => ({
                ...prev,
                isDeployed: false,
                isRunning: false,
                lastChecked: new Date().toISOString(),
                error: latestDeployment.error_message || 'Deployment failed'
              }));
            }
          }
        } else {
          // No deployments found, reset state
          setIsDeployingMcp(false);
          setDeploymentId(null);
        }
      });
      
      return () => unsubscribe();
    }
  }, [agentId, currentUser]);

  // Monitor deployment status and server status
  useEffect(() => {
    let intervalId = null;
    
    console.log('Deployment monitoring useEffect triggered:', {
      isDeployingMcp,
      agentId: agent?.agent_id,
      deploymentId
    });
    
    if (isDeployingMcp && agent?.agent_id) {
      const checkStatus = async () => {
        try {
          console.log('Checking deployment status...', { deploymentId, agentId: agent.agent_id });
          
          // Check deployment status if we have a deployment ID
          if (deploymentId) {
            console.log('Calling checkDeploymentStatus with:', agent.agent_id, deploymentId);
            const deploymentStatus = await checkDeploymentStatus(agent.agent_id, deploymentId);
            console.log('Deployment status response:', deploymentStatus);
            
            // If deployment is complete (success or failed), check server status
            if (deploymentStatus.status === 'completed' || deploymentStatus.status === 'failed') {
              setIsDeployingMcp(false);
              
              if (deploymentStatus.status === 'completed') {
                // Check server status
                try {
                  const serverStatus = await checkServerStatus(agent.agent_id);
                  console.log('Server status:', serverStatus);
                  
                  setMcpDeploymentStatus(prev => ({
                    ...prev,
                    isDeployed: true,
                    isRunning: serverStatus.status === 'running',
                    lastChecked: new Date().toISOString(),
                    error: null
                  }));
                  
                  setNotification({
                    open: true,
                    message: serverStatus.status === 'running' 
                      ? 'MCP server deployed and running successfully' 
                      : 'MCP server deployed but not running',
                    severity: serverStatus.status === 'running' ? 'success' : 'warning'
                  });
                } catch (serverError) {
                  console.error('Error checking server status:', serverError);
                  setMcpDeploymentStatus(prev => ({
                    ...prev,
                    isDeployed: true,
                    isRunning: false,
                    lastChecked: new Date().toISOString(),
                    error: 'Failed to check server status'
                  }));
                }
              } else {
                // Deployment failed
                setMcpDeploymentStatus(prev => ({
                  ...prev,
                  isDeployed: false,
                  isRunning: false,
                  lastChecked: new Date().toISOString(),
                  error: deploymentStatus.error || 'Deployment failed'
                }));
                
                setNotification({
                  open: true,
                  message: deploymentStatus.error || 'MCP server deployment failed',
                  severity: 'error'
                });
              }
            }
          } else {
            // If no deployment ID, just check server status periodically
            console.log('No deployment ID, checking server status directly');
            try {
              const serverStatus = await checkServerStatus(agent.agent_id);
              console.log('Server status (no deployment ID):', serverStatus);
              if (serverStatus.status === 'running') {
                setIsDeployingMcp(false);
                setMcpDeploymentStatus(prev => ({
                  ...prev,
                  isDeployed: true,
                  isRunning: true,
                  lastChecked: new Date().toISOString(),
                  error: null
                }));
                
                setNotification({
                  open: true,
                  message: 'MCP server deployed and running successfully',
                  severity: 'success'
                });
              }
            } catch (serverError) {
              console.error('Error checking server status:', serverError);
            }
          }
        } catch (error) {
          console.error('Error monitoring deployment:', error);
        }
      };
      
      // Check immediately
      checkStatus();
      
      // Set up interval to check every 5 seconds
      intervalId = setInterval(checkStatus, 5000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isDeployingMcp, agent?.agent_id, deploymentId]);


  const fetchKnowledgeBaseFiles = async () => {
    try {
      const files = await getAgentKnowledgeBase(agentId);
      console.log('Fetched knowledge base files:', files);
      setKbFiles(files);
    } catch (error) {
      console.error('Error fetching knowledge base files:', error);
      setNotification({
        open: true,
        message: 'Failed to load knowledge base files',
        severity: 'error'
      });
    }
  };

  // Fetch MCP deployment status from Firestore
  const fetchMcpDeploymentStatus = async () => {
    if (!agent?.agent_id) return;
    
    try {
      console.log('Fetching MCP deployment status for agent:', agent.agent_id);
      
      // Get deployments collection from alchemist_agents/[agentId]/deployments/
      const deploymentsRef = collection(db, 'alchemist_agents', agent.agent_id, 'deployments');
      const deploymentsSnapshot = await getDocs(deploymentsRef);
      
      if (!deploymentsSnapshot.empty) {
        // Get the most recent deployment (assuming there might be multiple)
        const deployments = [];
        deploymentsSnapshot.forEach((doc) => {
          deployments.push({
            id: doc.id,
            ...doc.data()
          });
        });
        
        // Sort by created_at or updated_at to get the most recent
        deployments.sort((a, b) => {
          const aTime = a.updated_at || a.created_at || 0;
          const bTime = b.updated_at || b.created_at || 0;
          return (bTime.seconds || bTime) - (aTime.seconds || aTime);
        });
        
        if (deployments.length > 0) {
          const latestDeployment = deployments[0];
          console.log('Latest deployment status:', latestDeployment);
          
          setMcpDeploymentStatus({
            isDeployed: latestDeployment.status === 'deployed' || latestDeployment.status === 'running',
            isRunning: latestDeployment.status === 'running',
            lastChecked: latestDeployment.updated_at || latestDeployment.created_at || null,
            error: latestDeployment.error || null,
            deploymentId: latestDeployment.id,
            status: latestDeployment.status,
            serviceUrl: latestDeployment.service_url,
            deployedAt: latestDeployment.deployed_at
          });
        }
      } else {
        console.log('No deployments found for agent');
        setMcpDeploymentStatus({
          isDeployed: false,
          isRunning: false,
          lastChecked: null,
          error: null
        });
      }
    } catch (error) {
      console.error('Error fetching MCP deployment status:', error);
      setMcpDeploymentStatus({
        isDeployed: false,
        isRunning: false,
        lastChecked: null,
        error: `Error fetching status: ${error.message}`
      });
    }
  };

  // Deploy MCP server function
  const handleDeployMcp = async () => {
    console.log(agent.agent_id)
    if (!agent.agent_id) return;
    
    // Set deploying state immediately to show loading
    setIsDeployingMcp(true);
    
    try {
      console.log('Deploying MCP server for agent:', agent.agent_id);
      const deploymentResponse = await deployMcpServer(agent.agent_id);
      
      // Store deployment ID if provided in response
      if (deploymentResponse?.deployment_id) {
        setDeploymentId(deploymentResponse.deployment_id);
        console.log('Deployment ID received:', deploymentResponse.deployment_id);
      }
      
      setNotification({
        open: true,
        message: 'MCP server deployment initiated successfully',
        severity: 'success'
      });
      
      // Clear any previous deployment errors
      setMcpDeploymentStatus(prev => ({
        ...prev,
        error: null
      }));
      
      // Note: isDeployingMcp will be managed by the Firestore listener
      // based on the actual deployment document status
      
    } catch (error) {
      console.error('Error deploying MCP server:', error);
      setNotification({
        open: true,
        message: error.message || 'Failed to deploy MCP server',
        severity: 'error'
      });
      
      // Only set error and stop deploying state if API call itself failed
      setMcpDeploymentStatus(prev => ({
        ...prev,
        error: error.message || 'Failed to deploy MCP server'
      }));
      setIsDeployingMcp(false);
    }
  };

  // Handle deleting MCP server
  const handleDeleteMcpServer = async () => {
    if (!agent.agent_id) return;
    
    // Confirm deletion
    if (!window.confirm('Are you sure you want to delete the MCP server? This action cannot be undone.')) {
      return;
    }
    
    try {
      console.log('Deleting MCP server for agent:', agent.agent_id);
      await deleteMcpServer(agent.agent_id);
      
      // Reset deployment status
      setMcpDeploymentStatus({
        isDeployed: false,
        isRunning: false,
        serverUrl: null,
        lastChecked: null,
        error: null
      });
      
      // Clear integration summary
      setIntegrationSummary(null);
      setLiveTools([]);
      
      setNotification({
        open: true,
        message: 'MCP server deleted successfully',
        severity: 'success'
      });
      
    } catch (error) {
      console.error('Error deleting MCP server:', error);
      setNotification({
        open: true,
        message: error.message || 'Failed to delete MCP server',
        severity: 'error'
      });
    }
  };

  // Handle viewing deployment logs
  const handleViewLogs = async (deploymentId) => {
    if (!agent.agent_id || !deploymentId) return;
    
    setLogsDialog({
      open: true,
      deploymentId,
      logs: '',
      loading: true
    });
    
    try {
      console.log('Fetching deployment logs for:', deploymentId);
      const response = await getDeploymentLogs(agent.agent_id, deploymentId);
      
      setLogsDialog(prev => ({
        ...prev,
        logs: response.logs || 'No logs available',
        loading: false
      }));
      
    } catch (error) {
      console.error('Error fetching deployment logs:', error);
      setLogsDialog(prev => ({
        ...prev,
        logs: `Error fetching logs: ${error.message}`,
        loading: false
      }));
    }
  };

  const handleApiFileUpload = () => {
    apiFileInputRef.current.click();
  };

  const handleApiFileSelected = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setSelectedFile(file);
    setShowNameDialog(true);
  };

  const handleUploadApiSpec = async () => {
    if (!selectedFile || !apiName.trim()) return;
    
    try {
      setFileLoading(true);
      
      // Initialize API upload status
      setApiUploadStatus({
        show: true,
        progress: 10,
        error: null,
        openapi_spec: null,
        mcp_config: null
      });
      
      await uploadApiSpecification(agentId, selectedFile, apiName, apiKey);
      
      setNotification({
        open: true,
        message: 'API specification upload started. Check progress below.',
        severity: 'info'
      });
      
      // Reset state
      setShowNameDialog(false);
      setApiName('');
      setApiKey('');
      setSelectedFile(null);
      
      // Clear the file input
      if (apiFileInputRef.current) {
        apiFileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error uploading API spec:', error);
      setApiUploadStatus({
        show: true,
        progress: 0,
        error: error.message,
        openapi_spec: null,
        mcp_config: null
      });
      setNotification({
        open: true,
        message: `Failed to upload API specification: ${error.message}`,
        severity: 'error'
      });
    } finally {
      setFileLoading(false);
    }
  };





  // Placeholder functions for testing interface (will be removed)
  const handleEndpointSelect = () => {};
  const buildFullUrl = () => '';
  const handleParamChange = () => {};
  const getParamValue = () => '';
  const shouldShowError = () => false;
  const handleTestEndpoint = () => {};







  // Scroll to bottom of messages when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    if (testMessagesEndRef.current) {
      testMessagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [testMessages]);

  const fetchConversationMessages = async () => {
    try {
      setIsLoading(true);
      
      // Use the apiService to fetch the agent's conversation messages
      const messagesData = await getAgentConversations(agentId);
      console.log('Loaded conversation data:', messagesData);
      
      // From the logs, it appears the API returns an array of message objects directly
      if (messagesData && messagesData.length > 0) {
        // Get the conversation ID from the first message
        const conversationId = messagesData[0].conversation_id;
        setConversation({ id: conversationId });
        
        // Sort messages by created_at to display in proper sequence
        const sortedMessages = [...messagesData].sort((a, b) => {
          // Parse the timestamps and compare them
          const dateA = convertTimestamp(a.created_at);
          const dateB = convertTimestamp(b.created_at);
          if (!dateA || !dateB) return 0;
          return dateA - dateB;
        });
        
        // Format the messages for display
        const formattedMessages = sortedMessages.map(msg => ({
          role: msg.role || 'user',
          content: msg.content || ''
        }));
        
        setMessages(formattedMessages);
        console.log('Loaded and formatted messages:', formattedMessages.length);
      } else {
        // No messages found, initialize with empty state
        console.log('No messages found for this agent');
        setMessages([]);
        setConversation({ id: null });
      }
    } catch (error) {
      console.error('Error fetching conversation:', error);
      setError('Failed to load conversation data.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setAgent({ ...agent, [name]: value });
  };

  const handleSendMessage = async () => {
    if (!userInput.trim()) return;
    
    try {
      setIsLoading(true);
      
      // Add user message to chat
      const userMessage = { role: 'user', content: userInput };
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setUserInput('');
      
      // Scroll to bottom
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
      const response = await interactWithAlchemist(userInput, agent.agent_id);
      console.log('Alchemist response:', response);
      
      // Add assistant response to chat
      const assistantMessage = { role: 'assistant', content: response.response || 'I\'m not sure how to respond to that.' };
      setMessages([...updatedMessages, assistantMessage]);
      
      // Store thought process if available
      if (response.thought_process) {
        setThoughtProcess(response.thought_process);
      }
      // Scroll to bottom after response
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const createNewConversation = async () => {
    if (!agentId) {
      setNotification({
        open: true,
        message: 'Please save the agent first to create a conversation',
        severity: 'warning'
      });
      return;
    }
    
    setCreatingConversation(true);
    
    try {
      // Call the provided API endpoint to create a new conversation
      const apiUrl = new URL('/api/agent/create_conversation', user_agent_url).toString();
      console.log('Making request to:', apiUrl);
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify({
          agent_id: agentId
        })
      });
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const data = await response.json();
      setTestConversationId(data.conversation_id);
      setTestMessages([]);
      
      setNotification({
        open: true,
        message: 'New conversation created successfully',
        severity: 'success'
      });
      
      return data.conversation_id;
    } catch (error) {
      console.error('Error creating conversation:', error);
      setNotification({
        open: true,
        message: `Failed to create conversation: ${error.message}`,
        severity: 'error'
      });
      return null;
    } finally {
      setCreatingConversation(false);
    }
  };

  const handleTestMessage = async () => {
    if (!testInput.trim()) return;
    
    const userMessage = {
      role: 'user',
      content: testInput
    };
    
    setTestMessages([...testMessages, userMessage]);
    setTestInput('');
    setIsTestLoading(true);
    
    try {
      // Create a new conversation if one doesn't exist yet
      let conversationId = testConversationId;
      if (!conversationId) {
        conversationId = await createNewConversation();
        if (!conversationId) {
          throw new Error('Unable to create conversation for testing');
        }
      }
      
      // Use the direct API call to process the message
      const apiUrl = new URL('/api/agent/process_message', user_agent_url).toString();
      console.log('Making request to:', apiUrl);
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify({
          conversation_id: conversationId,
          agent_id: agentId,
          message: testInput
        })
      });
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Test response:', result);
      
      // Update to use the correct response format
      const assistantMessage = {
        role: 'assistant',
        content: result.response.content || 'I processed your request, but no response was generated.'
      };
      
      // Store conversation ID if it was returned
      if (result.conversation_id && result.conversation_id !== testConversationId) {
        setTestConversationId(result.conversation_id);
      }
      
      setTestMessages([...testMessages, userMessage, assistantMessage]);
    } catch (error) {
      console.error('Error testing agent:', error);
      
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message || 'An unexpected error occurred'}`
      };
      
      setTestMessages([...testMessages, userMessage, errorMessage]);
    } finally {
      setIsTestLoading(false);
    }
  };

  // Handle tool testing
  const handleTestTool = async (toolName) => {
    if (!agent?.agent_id) return;
    
    // Open test dialog for parameter input
    setToolTestDialog({
      open: true,
      toolName,
      parameters: '{}',
      result: null,
      loading: false,
      error: null
    });
  };
  
  // Execute tool test with parameters
  const executeToolTest = async () => {
    if (!agent?.agent_id || !toolTestDialog.toolName) return;
    
    setToolTestDialog(prev => ({ 
      ...prev, 
      loading: true, 
      result: null, 
      error: null 
    }));
    
    try {
      console.log(`Testing tool: ${toolTestDialog.toolName} for agent: ${agent.agent_id}`);
      
      // Parse parameters
      let params = {};
      try {
        params = JSON.parse(toolTestDialog.parameters);
      } catch (parseError) {
        throw new Error('Invalid JSON parameters');
      }
      
      const result = await testTool(agent.agent_id, toolTestDialog.toolName, params);
      console.log('Tool test result:', result);
      
      setToolTestDialog(prev => ({ 
        ...prev, 
        result: result, 
        loading: false 
      }));
      
      setNotification({
        open: true,
        message: `Tool "${toolTestDialog.toolName}" tested successfully`,
        severity: 'success'
      });
      
    } catch (error) {
      console.error('Error testing tool:', error);
      setToolTestDialog(prev => ({ 
        ...prev, 
        error: error.message || 'Unknown error', 
        loading: false 
      }));
      
      setNotification({
        open: true,
        message: `Tool test failed: ${error.message || 'Unknown error'}`,
        severity: 'error'
      });
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current.click();
  };

  const handleFileSelected = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setUploadStatus({
      show: true,
      phase: 'preparing',
      progress: 0,
      error: null
    });
    
    try {
      // Simulate progress for UI feedback
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        if (progress <= 90) { // Only up to 90% for simulation, actual completion will be set after upload
          setUploadStatus(prev => ({
            ...prev,
            phase: progress < 30 ? 'uploading' : 
                   progress < 60 ? 'extracting_text' : 
                   progress < 90 ? 'storing_chunks' : 'complete',
            progress
          }));
        }
      }, 300);
      
      // Determine the correct agent ID to use (handle both agent.id and agent.agent_id formats)
      const agentIdToUse = agent.agent_id || agent.id;
      console.log('Uploading file for agent ID:', agentIdToUse);
      
      // Use the API service function to upload the file
      const result = await uploadKnowledgeBaseFile(agentIdToUse, file);
      
      // Clear the interval
      clearInterval(interval);
      
      // Mark upload as complete
      setUploadStatus({
        show: true,
        phase: 'complete',
        progress: 100,
        error: null
      });
      
      // If we get back file data, update the files state
      if (result && result.file) {
        const newFile = result.file;
        setFiles(prev => [...prev, newFile]);
        setAgent(prev => ({
          ...prev,
          knowledge_base: [...(prev.knowledge_base || []), newFile]
        }));
      }
      
      setNotification({
        open: true,
        message: 'File uploaded successfully!',
        severity: 'success'
      });
      
      // Hide upload status after a delay
      setTimeout(() => {
        setUploadStatus({ show: false, phase: 'complete', progress: 100, error: null });
      }, 2000);
      
      // Clear the file input
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
        message: `Upload failed: ${error.message || 'Unknown error'}`,
        severity: 'error'
      });
    }
  };

  const handleKBFileUpload = () => {
    kbFileInputRef.current.click();
  };

  const handleKBFileSelected = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    try {
      setFileLoading(true);
      setUploadStatus({ show: true, phase: 'uploading', progress: 10, error: null });
      
      // Simulate progress (in a real app, you'd use upload progress events)
      const progressInterval = setInterval(() => {
        setUploadStatus(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90)
        }));
      }, 300);
      
      // Determine the correct agent ID to use
      const agentIdToUse = agent.agent_id || agent.id;
      console.log('Uploading file for agent ID:', agentIdToUse);
      
      // Upload file
      await uploadKnowledgeBaseFile(agentIdToUse, selectedFile);
      
      clearInterval(progressInterval);
      
      // Refresh file list
      await fetchKnowledgeBaseFiles();
      
      setUploadStatus({ show: true, phase: 'complete', progress: 100, error: null });
      setNotification({
        open: true,
        message: 'File uploaded successfully',
        severity: 'success'
      });
      
      // Hide upload status after a delay
      setTimeout(() => {
        setUploadStatus({ show: false, phase: 'complete', progress: 100, error: null });
      }, 2000);
      
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

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  const handleCloseSuccessModal = () => {
    setSuccessModal(false);
  };

  const handleStartTesting = () => {
    setSuccessModal(false);
    // Focus on the test input
    document.getElementById('test-input')?.focus();
  };

  // Show unauthorized message if the user doesn't have access
  if (unauthorized) {
    return (
      <Box sx={{ 
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${alpha(theme.palette.error.light, 0.1)} 0%, ${alpha(theme.palette.error.dark, 0.05)} 100%)`,
        p: 3
      }}>
        <Card sx={{ 
          maxWidth: 500, 
          textAlign: 'center',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          borderRadius: 3,
          overflow: 'hidden'
        }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ 
              width: 80, 
              height: 80, 
              borderRadius: '50%', 
              bgcolor: alpha(theme.palette.error.main, 0.1),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 3
            }}>
              <LockIcon sx={{ fontSize: 40, color: theme.palette.error.main }} />
            </Box>
            <Typography variant="h4" gutterBottom fontWeight="bold" color="error">
              Access Denied
            </Typography>
            <Typography variant="body1" paragraph color="text.secondary" sx={{ mb: 3 }}>
              You don't have permission to edit this agent. You can only edit agents that you have created.
            </Typography>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={() => navigate('/agents')}
              startIcon={<ArrowBackIcon />}
              size="large"
              sx={{ 
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 'bold',
                px: 3,
                py: 1.5
              }}
            >
              Back to My Agents
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.03)} 0%, ${alpha(theme.palette.secondary.light, 0.02)} 100%)`,
      width: '100%',
      maxWidth: '100%',
      overflow: 'auto'
    }}>
      {/* Enhanced Action Bar */}
      <Box sx={{ 
        px: 3, 
        py: 2, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        background: `linear-gradient(90deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.primary.light, 0.05)} 100%)`,
        borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
        backdropFilter: 'blur(10px)',
        boxShadow: '0 2px 20px rgba(0, 0, 0, 0.05)',
        width: '100%'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title="Back to Agents">
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/agents')}
              sx={{ 
                mr: 3,
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 'medium',
                borderColor: alpha(theme.palette.primary.main, 0.2),
                '&:hover': {
                  borderColor: theme.palette.primary.main,
                  backgroundColor: alpha(theme.palette.primary.main, 0.05)
                }
              }}
            >
              Back
            </Button>
          </Tooltip>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Avatar sx={{ 
              bgcolor: theme.palette.primary.main, 
              mr: 2,
              width: 40,
              height: 40
            }}>
              <SmartToyIcon />
            </Avatar>
            <Box>
              <Typography variant="h5" sx={{ 
                fontWeight: 'bold',
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                textFillColor: 'transparent',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                {agentId ? 'Edit Agent' : 'Create New Agent'}
              </Typography>
              {agent.name && (
                <Typography variant="body2" color="text.secondary">
                  {agent.name}
                </Typography>
              )}
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Enhanced Error Message */}
      {error && (
        <Slide direction="down" in={!!error} mountOnEnter unmountOnExit>
          <Alert 
            severity="error" 
            sx={{ 
              mx: 0, 
              borderRadius: 0,
              backgroundColor: alpha(theme.palette.error.main, 0.1),
              borderLeft: `4px solid ${theme.palette.error.main}`
            }}
          >
            {error}
          </Alert>
        </Slide>
      )}

      {/* Main Content with Tabs */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'visible' }}>
        {/* Tab Headers */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
          <Tabs 
            value={activeTab} 
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{
              px: 3,
              '& .MuiTab-root': {
                textTransform: 'none',
                fontWeight: 'medium',
                minHeight: 56,
                px: 3
              }
            }}
          >
            <Tab 
              icon={<EditIcon sx={{ fontSize: 20 }} />} 
              iconPosition="start" 
              label="Agent Definition" 
            />
            <Tab 
              icon={<StorageIcon sx={{ fontSize: 20 }} />} 
              iconPosition="start" 
              label="Knowledge Base" 
              onClick={() => fetchKnowledgeBaseFiles()}
            />
            <Tab 
              icon={<ApiIcon sx={{ fontSize: 20 }} />} 
              iconPosition="start" 
              label="API Integration" 
            />
            <Tab 
              icon={<BugReportIcon sx={{ fontSize: 20 }} />} 
              iconPosition="start" 
              label="Agent Testing" 
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <Box sx={{ flexGrow: 1, overflow: 'visible' }}>
          {/* Agent Definition Tab */}
          <TabPanel value={activeTab} index={0}>
            <Box sx={{ display: 'flex', height: 'calc(100vh - 200px)', overflow: 'hidden' }}>
              {/* Enhanced Left Panel: Alchemist Conversation */}
              <Fade in={true} timeout={800}>
                <Box 
                  sx={{ 
                    width: '50%',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    backgroundColor: '#ffffff',
                    boxShadow: '2px 0 20px rgba(0, 0, 0, 0.05)'
                  }}
                >
                  {/* Enhanced Panel Title */}
                  <Box sx={{ 
                    py: 2.5, 
                    px: 3, 
                    borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                    background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.02)} 100%)`
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Avatar sx={{ 
                        bgcolor: theme.palette.primary.main, 
                        mr: 2,
                        width: 32,
                        height: 32
                      }}>
                        <PsychologyIcon fontSize="small" />
                      </Avatar>
                      <Typography variant="h6" sx={{ 
                        fontWeight: 'bold',
                        color: theme.palette.primary.main
                      }}>
                        Alchemist Conversation
                      </Typography>
                      <Chip 
                        label="AI Assistant" 
                        size="small" 
                        sx={{ 
                          ml: 'auto',
                          bgcolor: alpha(theme.palette.primary.main, 0.1),
                          color: theme.palette.primary.main,
                          fontWeight: 'medium'
                        }} 
                      />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Collaborate with Alchemist to design your perfect agent
                      </Typography>
                    </Box>
                  </Box>

                  {/* Enhanced Conversation Container */}
                  <Box sx={{ 
                    flexGrow: 1, 
                    overflow: 'auto', 
                    p: 3, 
                    maxHeight: 'calc(100vh - 350px)',
                    background: `linear-gradient(180deg, ${alpha(theme.palette.background.default, 0.3)} 0%, ${alpha(theme.palette.primary.light, 0.02)} 100%)`
                  }}>
                    {messages.length === 0 ? (
                      <Zoom in={true} timeout={1000}>
                        <Card sx={{ 
                          textAlign: 'center', 
                          mt: 8,
                          p: 4,
                          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.08)} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
                          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                          borderRadius: 3,
                          boxShadow: 'none'
                        }}>
                          <Avatar sx={{ 
                            bgcolor: alpha(theme.palette.primary.main, 0.1), 
                            mx: 'auto',
                            mb: 2,
                            width: 60,
                            height: 60
                          }}>
                            <PsychologyIcon sx={{ fontSize: 30, color: theme.palette.primary.main }} />
                          </Avatar>
                          <Typography variant="h6" gutterBottom fontWeight="bold" color="primary">
                            Start Your Journey
                          </Typography>
                          <Typography variant="body1" color="text.secondary">
                            Begin a conversation with Alchemist to bring your agent vision to life
                          </Typography>
                        </Card>
                      </Zoom>
                    ) : (
                      messages.map((message, index) => (
                        <Fade key={index} in={true} timeout={300} style={{ transitionDelay: `${index * 100}ms` }}>
                          <Card
                            elevation={0}
                            sx={{
                              p: 2.5,
                              mb: 2,
                              maxWidth: '85%',
                              ml: message.role === 'user' ? 'auto' : 0,
                              mr: message.role === 'assistant' ? 'auto' : 0,
                              background: message.role === 'user' 
                                ? `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.15)} 0%, ${alpha(theme.palette.primary.main, 0.1)} 100%)`
                                : `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
                              border: `1px solid ${alpha(theme.palette.primary.main, message.role === 'user' ? 0.2 : 0.08)}`,
                              borderRadius: 3,
                              boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
                              position: 'relative',
                              '&::before': message.role === 'user' ? {
                                content: '""',
                                position: 'absolute',
                                right: -8,
                                top: 12,
                                width: 0,
                                height: 0,
                                borderLeft: `8px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                                borderTop: '8px solid transparent',
                                borderBottom: '8px solid transparent'
                              } : {
                                content: '""',
                                position: 'absolute',
                                left: -8,
                                top: 12,
                                width: 0,
                                height: 0,
                                borderRight: `8px solid ${theme.palette.background.paper}`,
                                borderTop: '8px solid transparent',
                                borderBottom: '8px solid transparent'
                              }
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                              <Avatar sx={{ 
                                bgcolor: message.role === 'user' ? theme.palette.primary.main : theme.palette.secondary.main,
                                width: 32,
                                height: 32
                              }}>
                                {message.role === 'user' ? <PersonIcon fontSize="small" /> : <SmartToyIcon fontSize="small" />}
                              </Avatar>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="body1" sx={{ 
                                  lineHeight: 1.6,
                                  fontSize: '0.95rem'
                                }}>
                                  {message.content}
                                </Typography>
                              </Box>
                            </Box>
                          </Card>
                        </Fade>
                      ))
                    )}
                    {isLoading && (
                      <Fade in={isLoading}>
                        <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
                          <Card sx={{ 
                            p: 2, 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 2,
                            background: alpha(theme.palette.primary.main, 0.05),
                            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
                          }}>
                            <CircularProgress size={20} color="primary" />
                            <Typography variant="body2" color="primary">
                              Alchemist is thinking...
                            </Typography>
                          </Card>
                        </Box>
                      </Fade>
                    )}
                    <div ref={messagesEndRef} />

                    {/* Enhanced Thought Process */}
                    {showThoughtProcess && thoughtProcess.length > 0 && (
                      <Slide direction="up" in={showThoughtProcess} mountOnEnter unmountOnExit>
                        <Card 
                          elevation={0} 
                          sx={{ 
                            p: 3, 
                            mt: 3, 
                            background: `linear-gradient(135deg, ${alpha(theme.palette.info.light, 0.05)} 0%, ${alpha(theme.palette.primary.light, 0.03)} 100%)`,
                            border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                            borderRadius: 3,
                            maxHeight: '300px',
                            overflow: 'auto'
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <TimelineIcon sx={{ color: theme.palette.info.main, mr: 1 }} />
                            <Typography variant="h6" fontWeight="bold" color="info.main">
                              AI Thought Process
                            </Typography>
                          </Box>
                          {thoughtProcess.map((thought, index) => (
                            <Box key={index} sx={{ 
                              mb: 2, 
                              pb: 2, 
                              borderBottom: index < thoughtProcess.length - 1 ? `1px dotted ${alpha(theme.palette.info.main, 0.2)}` : 'none'
                            }}>
                              <Typography variant="caption" sx={{ 
                                display: 'block',
                                color: 'text.secondary',
                                mb: 0.5,
                                fontFamily: 'monospace'
                              }}>
                                {convertTimestamp(thought.timestamp)?.toLocaleTimeString() || 'Unknown time'}
                              </Typography>
                              <Typography variant="body2" sx={{ 
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'monospace',
                                fontSize: '0.85rem',
                                lineHeight: 1.5
                              }}>
                                {thought.content}
                              </Typography>
                            </Box>
                          ))}
                        </Card>
                      </Slide>
                    )}
                  </Box>

                  {/* Enhanced Input Container */}
                  <Box sx={{ 
                    p: 3, 
                    borderTop: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                    background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.primary.light, 0.03)} 100%)`,
                    backdropFilter: 'blur(10px)'
                  }}>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <TextField
                        fullWidth
                        placeholder="Share your vision with Alchemist..."
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        disabled={isLoading}
                        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                        multiline
                        maxRows={3}
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            borderRadius: 2,
                            backgroundColor: alpha(theme.palette.background.paper, 0.8),
                            '&:hover': {
                              backgroundColor: theme.palette.background.paper
                            },
                            '&.Mui-focused': {
                              backgroundColor: theme.palette.background.paper,
                              boxShadow: `0 0 0 2px ${alpha(theme.palette.primary.main, 0.2)}`
                            }
                          }
                        }}
                      />
                      <Button
                        variant="contained"
                        endIcon={<SendIcon />}
                        onClick={handleSendMessage}
                        disabled={isLoading || !userInput.trim()}
                        sx={{ 
                          borderRadius: 2,
                          textTransform: 'none',
                          fontWeight: 'bold',
                          minWidth: 100,
                          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                          boxShadow: '0 3px 12px rgba(0, 0, 0, 0.15)',
                          '&:hover': {
                            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.25)',
                            transform: 'translateY(-1px)'
                          },
                          '&:disabled': {
                            background: alpha(theme.palette.action.disabledBackground, 0.3)
                          },
                          transition: 'all 0.2s ease-in-out'
                        }}
                      >
                        Send
                      </Button>
                    </Box>
                    
                    <input
                      type="file"
                      ref={fileInputRef}
                      style={{ display: 'none' }}
                      onChange={handleFileSelected}
                    />
                    
                    {/* Enhanced Upload Status */}
                    {uploadStatus.show && (
                      <Fade in={uploadStatus.show}>
                        <Card sx={{ mt: 2, p: 2, bgcolor: alpha(theme.palette.info.light, 0.05) }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="body2" fontWeight="medium" color="info.main">
                              {uploadStatus.phase === 'preparing' && '🔄 Preparing file...'}
                              {uploadStatus.phase === 'uploading' && '📤 Uploading file...'}
                              {uploadStatus.phase === 'extracting_text' && '📝 Extracting text...'}
                              {uploadStatus.phase === 'storing_chunks' && '🧠 Processing knowledge...'}
                              {uploadStatus.phase === 'complete' && '✅ Upload complete!'}
                              {uploadStatus.phase === 'failed' && '❌ Upload failed!'}
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">{uploadStatus.progress}%</Typography>
                          </Box>
                          <LinearProgress 
                            variant="determinate" 
                            value={uploadStatus.progress}
                            sx={{ 
                              height: 8,
                              borderRadius: 1,
                              backgroundColor: alpha(theme.palette.primary.main, 0.1),
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 1,
                                background: uploadStatus.phase === 'failed' 
                                  ? `linear-gradient(45deg, ${theme.palette.error.main}, ${theme.palette.error.dark})`
                                  : `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                              }
                            }}
                          />
                          {uploadStatus.error && (
                            <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                              {uploadStatus.error}
                            </Typography>
                          )}
                        </Card>
                      </Fade>
                    )}
                  </Box>
                </Box>
              </Fade>

              {/* Right Panel: Agent Configuration Form */}
              <Box sx={{ 
                width: '50%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                backgroundColor: '#ffffff',
                boxShadow: '-2px 0 20px rgba(0, 0, 0, 0.05)'
              }}>
                <Box sx={{ 
                  py: 2.5, 
                  px: 3, 
                  borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.02)} 100%)`
                }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}>
                    Agent Configuration
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Define your agent's capabilities and behavior
                  </Typography>
                </Box>
                
                <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Agent Name"
                      name="name"
                      value={agent.name}
                      onChange={handleInputChange}
                      fullWidth
                      required
                      sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                    />
                    
                    <TextField
                      label="Description"
                      name="description"
                      value={agent.description}
                      onChange={handleInputChange}
                      fullWidth
                      multiline
                      rows={3}
                      sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                    />
                    <TextField
                      label="System Prompt"
                      name="prompt"
                      value={agent.system_prompt}
                      onChange={handleInputChange}
                      fullWidth
                      multiline
                      rows={6}
                      placeholder="Define the agent's personality, capabilities, and behavior..."
                      sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                    />
                  </Box>
                </Box>
              </Box>
            </Box>
          </TabPanel>

          {/* Knowledge Base Tab */}
          <TabPanel value={activeTab} index={1}>
            <Box sx={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              backgroundColor: '#ffffff'
            }}>
              {/* Enhanced Panel Title with Search and Controls */}
              <Box sx={{ 
                py: 2.5, 
                px: 3, 
                borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.02)} 100%)`
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ 
                      bgcolor: theme.palette.primary.main, 
                      mr: 2,
                      width: 32,
                      height: 32
                    }}>
                      <StorageIcon fontSize="small" />
                    </Avatar>
                    <Typography variant="h6" sx={{ 
                      fontWeight: 'bold',
                      color: theme.palette.primary.main
                    }}>
                      Knowledge Base
                    </Typography>
                    {kbFiles.length > 0 && (
                      <Chip 
                        label={`${kbFiles.length} files`} 
                        size="small" 
                        sx={{ 
                          ml: 2,
                          bgcolor: alpha(theme.palette.primary.main, 0.1),
                          color: theme.palette.primary.main,
                          fontWeight: 'medium'
                        }} 
                      />
                    )}
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
                      size="small"
                      sx={{
                        borderColor: theme.palette.primary.main,
                        color: theme.palette.primary.main,
                        '&:hover': {
                          backgroundColor: alpha(theme.palette.primary.main, 0.05)
                        }
                      }}
                    >
                      Search
                    </Button>
                    <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
                    <ToggleButtonGroup
                      value={viewMode}
                      exclusive
                      onChange={(e, newMode) => newMode && setViewMode(newMode)}
                      size="small"
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
                      onClick={handleKBFileUpload}
                      size="small"
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
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Upload documents and files to enhance your agent's knowledge
                </Typography>
              </Box>

              <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
                {uploadStatus.show && (
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2">
                        {uploadStatus.phase === 'preparing' && '🔄 Preparing file...'}
                        {uploadStatus.phase === 'uploading' && '📤 Uploading file...'}
                        {uploadStatus.phase === 'extracting_text' && '📝 Extracting text...'}
                        {uploadStatus.phase === 'storing_chunks' && '🧠 Processing knowledge...'}
                        {uploadStatus.phase === 'complete' && '✅ Upload complete!'}
                        {uploadStatus.phase === 'failed' && '❌ Upload failed!'}
                      </Typography>
                      <Typography variant="body2">{uploadStatus.progress}%</Typography>
                    </Box>
                    <Box sx={{ width: '100%', bgcolor: alpha(theme.palette.primary.main, 0.1), borderRadius: 1, height: 10 }}>
                      <Box 
                        sx={{ 
                          width: `${uploadStatus.progress}%`, 
                          bgcolor: uploadStatus.phase === 'failed' ? theme.palette.error.main : theme.palette.primary.main,
                          height: '100%',
                          borderRadius: 1,
                          transition: 'width 0.3s ease'
                        }} 
                      />
                    </Box>
                    {uploadStatus.error && (
                      <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                        {uploadStatus.error}
                      </Typography>
                    )}
                  </Box>
                )}

                {/* File listing */}
                {kbFiles.length === 0 ? (
                  <Box sx={{ 
                    textAlign: 'center', 
                    p: 4, 
                    borderRadius: 2, 
                    border: `1px dashed ${alpha(theme.palette.primary.main, 0.2)}`,
                    bgcolor: alpha(theme.palette.primary.light, 0.02) 
                  }}>
                    <Avatar sx={{ 
                      bgcolor: alpha(theme.palette.primary.main, 0.1), 
                      mx: 'auto',
                      mb: 2,
                      width: 60,
                      height: 60
                    }}>
                      <MenuBookIcon sx={{ fontSize: 30, color: theme.palette.primary.main }} />
                    </Avatar>
                    <Typography variant="h6" gutterBottom fontWeight="bold" color="primary">
                      No Knowledge Base Files
                    </Typography>
                    <Typography variant="body1" color="text.secondary" paragraph>
                      Upload documents to give your agent specialized knowledge
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<CloudUploadIcon />}
                      onClick={handleKBFileUpload}
                      sx={{ 
                        borderRadius: 2,
                        textTransform: 'none',
                        fontWeight: 'bold',
                        background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                      }}
                    >
                      Upload File
                    </Button>
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
                        {kbFiles.map((file) => (
                          <TableRow key={file.id || `file-${kbFiles.indexOf(file)}`} hover>
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
                                onClick={() => handleOpenDeleteConfirm(file.id || `file-${kbFiles.indexOf(file)}`)}
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
                    {kbFiles.map((file) => (
                      <Grid item xs={12} sm={6} md={4} lg={3} key={file.id || `file-${kbFiles.indexOf(file)}`}>
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
                              onClick={() => handleOpenDeleteConfirm(file.id || `file-${kbFiles.indexOf(file)}`)} 
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

                <input
                  type="file"
                  ref={kbFileInputRef}
                  style={{ display: 'none' }}
                  onChange={handleKBFileSelected}
                />
              </Box>
            </Box>
          </TabPanel>

          {/* API Integration Tab */}
          <TabPanel value={activeTab} index={2}>
            <Box sx={{ 
              minHeight: '100%',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'visible',
              backgroundColor: '#ffffff'
            }}>
              <Box sx={{ 
                py: 2.5, 
                px: 3, 
                borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.02)} 100%)`
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ 
                    bgcolor: theme.palette.primary.main, 
                    mr: 2,
                    width: 32,
                    height: 32
                  }}>
                    <ApiIcon fontSize="small" />
                  </Avatar>
                  <Typography variant="h6" sx={{ 
                    fontWeight: 'bold',
                    color: theme.palette.primary.main
                  }}>
                    API Integration
                  </Typography>
                  <Chip 
                    label="Developer Tools" 
                    size="small" 
                    sx={{ 
                      ml: 'auto',
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      fontWeight: 'medium'
                    }} 
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Upload API specifications and test endpoints for your agent
                </Typography>
              </Box>

              <Box sx={{ 
                flexGrow: 1, 
                display: 'grid',
                gridTemplateColumns: 'minmax(300px, 400px) 1fr',
                gap: 0,
                minHeight: 'calc(100vh - 300px)'
              }}>
                {/* Left Panel: API List */}
                <Box sx={{ 
                  borderRight: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                  p: 2,
                  overflow: 'auto',
                  display: 'flex',
                  flexDirection: 'column'
                }}>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<CloudUploadIcon />}
                    onClick={handleApiFileUpload}
                    sx={{ mb: 2, flexShrink: 0 }}
                  >
                    Upload API Spec
                  </Button>
                  
                  {/* API Upload Progress */}
                  {apiUploadStatus.show && (
                    <Card sx={{ mb: 2, p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <ApiIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                          API Upload Progress
                        </Typography>
                        {apiUploadStatus.progress >= 100 && (
                          <CheckCircleIcon color="success" />
                        )}
                      </Box>
                      
                      {apiUploadStatus.error ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <ErrorIcon color="error" sx={{ mr: 1 }} />
                          <Typography variant="body2" color="error">
                            {apiUploadStatus.error}
                          </Typography>
                        </Box>
                      ) : (
                        <>
                          <LinearProgress 
                            variant="determinate" 
                            value={apiUploadStatus.progress} 
                            sx={{ mb: 1, height: 6, borderRadius: 3 }}
                          />
                          
                          <Box sx={{ mb: 1 }}>
                            {apiUploadStatus.openapi_spec && (
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                                {apiUploadStatus.openapi_spec.status === 'uploaded' ? (
                                  <CheckCircleIcon color="success" sx={{ mr: 1, fontSize: 16 }} />
                                ) : (
                                  <PendingIcon color="info" sx={{ mr: 1, fontSize: 16 }} />
                                )}
                                <Typography variant="caption" color="text.secondary">
                                  OpenAPI Spec: {apiUploadStatus.openapi_spec.status}
                                </Typography>
                                {apiUploadStatus.openapi_spec.filename && (
                                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                    ({apiUploadStatus.openapi_spec.filename})
                                  </Typography>
                                )}
                              </Box>
                            )}
                            
                            {apiUploadStatus.mcp_config && (
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                {apiUploadStatus.mcp_config.status === 'converted' ? (
                                  <CheckCircleIcon color="success" sx={{ mr: 1, fontSize: 16 }} />
                                ) : (
                                  <PendingIcon color="info" sx={{ mr: 1, fontSize: 16 }} />
                                )}
                                <Typography variant="caption" color="text.secondary">
                                  MCP Config: {apiUploadStatus.mcp_config.status}
                                </Typography>
                                {apiUploadStatus.mcp_config.filename && (
                                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                    ({apiUploadStatus.mcp_config.filename})
                                  </Typography>
                                )}
                              </Box>
                            )}
                          </Box>
                          
                          <Typography variant="caption" color="text.secondary">
                            {apiUploadStatus.progress}% complete
                          </Typography>
                        </>
                      )}
                    </Card>
                  )}
                  
                  {/* Firestore API Files Display */}
                  {firestoreApiFiles && (
                    <Card sx={{ mb: 2, p: 2, bgcolor: alpha(theme.palette.success.main, 0.05), border: `1px solid ${alpha(theme.palette.success.main, 0.2)}` }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                        <Typography variant="subtitle2" color="success.main">
                          API Files Ready
                        </Typography>
                      </Box>
                      
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                        {firestoreApiFiles.message}
                      </Typography>
                      
                      {/* OpenAPI File */}
                      {firestoreApiFiles.openapi_spec && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" fontWeight="medium" sx={{ mb: 1 }}>
                            OpenAPI Specification
                          </Typography>
                          <Box sx={{ bgcolor: 'background.paper', p: 1.5, borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              <DocIcon sx={{ mr: 1, fontSize: 16 }} />
                              <Typography variant="caption" fontWeight="medium">
                                {firestoreApiFiles.openapi_spec.filename}
                              </Typography>
                            </Box>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Size: {formatFileSize(firestoreApiFiles.openapi_spec.file_size)}
                            </Typography>
                            {firestoreApiFiles.openapi_spec.public_url && (
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<DownloadIcon />}
                                href={firestoreApiFiles.openapi_spec.public_url}
                                target="_blank"
                                sx={{ mt: 1 }}
                              >
                                Download
                              </Button>
                            )}
                          </Box>
                        </Box>
                      )}
                      
                      {/* MCP Config File */}
                      {firestoreApiFiles.mcp_config && (
                        <Box>
                          <Typography variant="body2" fontWeight="medium" sx={{ mb: 1 }}>
                            MCP Configuration
                          </Typography>
                          <Box sx={{ bgcolor: 'background.paper', p: 1.5, borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              <CodeIcon sx={{ mr: 1, fontSize: 16 }} />
                              <Typography variant="caption" fontWeight="medium">
                                {firestoreApiFiles.mcp_config.filename}
                              </Typography>
                            </Box>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Size: {formatFileSize(firestoreApiFiles.mcp_config.file_size)}
                            </Typography>
                            {firestoreApiFiles.mcp_config.server_name && (
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                Server: {firestoreApiFiles.mcp_config.server_name}
                              </Typography>
                            )}
                            {firestoreApiFiles.mcp_config.public_url && (
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<DownloadIcon />}
                                href={firestoreApiFiles.mcp_config.public_url}
                                target="_blank"
                                sx={{ mt: 1 }}
                              >
                                Download
                              </Button>
                            )}
                          </Box>
                        </Box>
                      )}
                    </Card>
                  )}
                  
                  <Box sx={{ textAlign: 'center', mt: 4 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Upload OpenAPI specifications or MCP config files to enable API integrations
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Supported formats: OpenAPI (.json, .yaml, .yml) or MCP config (.yaml, .yml)
                    </Typography>
                  </Box>
                </Box>

                {/* Right Panel: Status Display */}
                <Box sx={{ 
                  p: 3,
                  overflow: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 3
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
                    <Typography variant="h6">
                      API Integration Status
                    </Typography>
                    <Chip 
                      label="Real-time" 
                      size="small" 
                      color="success"
                      icon={<CheckCircleIcon />}
                      sx={{ fontSize: '0.75rem' }}
                    />
                  </Box>
                  
                  {/* Status Steps */}
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: 3,
                    minWidth: 0,
                    maxWidth: '100%'
                  }}>
                    
                    {/* Step 1: OpenAPI Upload */}
                    <Card sx={{ 
                      p: 3, 
                      bgcolor: firestoreApiFiles?.openapi_spec 
                        ? alpha(theme.palette.success.main, 0.05) 
                        : alpha(theme.palette.grey[500], 0.05),
                      border: `1px solid ${firestoreApiFiles?.openapi_spec 
                        ? alpha(theme.palette.success.main, 0.2) 
                        : alpha(theme.palette.grey[500], 0.2)}`,
                      minWidth: 0,
                      maxWidth: '100%',
                      overflow: 'hidden'
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        {firestoreApiFiles?.openapi_spec ? (
                          <CheckCircleIcon color="success" sx={{ mr: 2 }} />
                        ) : (
                          <PendingIcon color="disabled" sx={{ mr: 2 }} />
                        )}
                        <Typography variant="h6">
                          1. OpenAPI Specification Upload
                        </Typography>
                      </Box>
                      
                      {firestoreApiFiles?.openapi_spec ? (
                        <Box>
                          <Typography variant="body2" color="success.main" sx={{ mb: 1 }}>
                            ✓ OpenAPI file uploaded successfully
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                            Filename: {firestoreApiFiles.openapi_spec.filename}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ 
                            display: 'block', 
                            mb: 0.5,
                            wordBreak: 'break-all',
                            overflowWrap: 'break-word'
                          }}>
                            Storage Path: {firestoreApiFiles.openapi_spec.storage_path}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                            File Size: {formatFileSize(firestoreApiFiles.openapi_spec.file_size)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                            Status: {firestoreApiFiles.openapi_spec.status}
                          </Typography>
                          {firestoreApiFiles.openapi_spec.upload_timestamp && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Uploaded: {formatDate(firestoreApiFiles.openapi_spec.upload_timestamp)}
                            </Typography>
                          )}
                          {firestoreApiFiles.openapi_spec.public_url && (
                            <Box sx={{ mt: 1 }}>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<DownloadIcon />}
                                href={firestoreApiFiles.openapi_spec.public_url}
                                target="_blank"
                                sx={{ mr: 1 }}
                              >
                                Download
                              </Button>
                              <Button
                                size="small"
                                variant="text"
                                startIcon={<ApiIcon />}
                                href={firestoreApiFiles.openapi_spec.public_url}
                                target="_blank"
                              >
                                View File
                              </Button>
                            </Box>
                          )}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Upload an OpenAPI YAML file to start the integration process
                        </Typography>
                      )}
                    </Card>
                    
                    {/* Step 2: MCP Config Generation */}
                    <Card sx={{ 
                      p: 3, 
                      bgcolor: firestoreApiFiles?.mcp_config 
                        ? alpha(theme.palette.success.main, 0.05) 
                        : alpha(theme.palette.grey[500], 0.05),
                      border: `1px solid ${firestoreApiFiles?.mcp_config 
                        ? alpha(theme.palette.success.main, 0.2) 
                        : alpha(theme.palette.grey[500], 0.2)}`,
                      minWidth: 0,
                      maxWidth: '100%',
                      overflow: 'hidden'
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        {firestoreApiFiles?.mcp_config ? (
                          <CheckCircleIcon color="success" sx={{ mr: 2 }} />
                        ) : firestoreApiFiles?.openapi_spec ? (
                          <PendingIcon color="info" sx={{ mr: 2 }} />
                        ) : (
                          <PendingIcon color="disabled" sx={{ mr: 2 }} />
                        )}
                        <Typography variant="h6">
                          2. MCP Configuration Generated
                        </Typography>
                      </Box>
                      
                      {firestoreApiFiles?.mcp_config ? (
                        <Box>
                          <Typography variant="body2" color="success.main" sx={{ mb: 1 }}>
                            ✓ MCP configuration generated successfully
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                            Filename: {firestoreApiFiles.mcp_config.filename}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ 
                            display: 'block', 
                            mb: 0.5,
                            wordBreak: 'break-all',
                            overflowWrap: 'break-word'
                          }}>
                            Storage Path: {firestoreApiFiles.mcp_config.storage_path}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                            File Size: {formatFileSize(firestoreApiFiles.mcp_config.file_size)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                            Status: {firestoreApiFiles.mcp_config.status}
                          </Typography>
                          {firestoreApiFiles.mcp_config.server_name && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Server Name: {firestoreApiFiles.mcp_config.server_name}
                            </Typography>
                          )}
                          {firestoreApiFiles.mcp_config.conversion_timestamp && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Converted: {formatDate(firestoreApiFiles.mcp_config.conversion_timestamp)}
                            </Typography>
                          )}
                          {firestoreApiFiles.mcp_config.public_url && (
                            <Box sx={{ mt: 1 }}>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<DownloadIcon />}
                                href={firestoreApiFiles.mcp_config.public_url}
                                target="_blank"
                                sx={{ mr: 1 }}
                              >
                                Download MCP Config
                              </Button>
                              <Button
                                size="small"
                                variant="text"
                                startIcon={<CodeIcon />}
                                href={firestoreApiFiles.mcp_config.public_url}
                                target="_blank"
                              >
                                View Config
                              </Button>
                            </Box>
                          )}
                        </Box>
                      ) : firestoreApiFiles?.openapi_spec ? (
                        <Typography variant="body2" color="info.main">
                          ⏳ Converting OpenAPI spec to MCP configuration...
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          MCP configuration will be generated after OpenAPI upload
                        </Typography>
                      )}
                    </Card>
                    
                    {/* Step 3: MCP Deployment */}
                    <Card sx={{ 
                      p: 3, 
                      bgcolor: mcpDeploymentStatus.isDeployed && mcpDeploymentStatus.isRunning
                        ? alpha(theme.palette.success.main, 0.05) 
                        : mcpDeploymentStatus.isDeployed 
                        ? alpha(theme.palette.warning.main, 0.05)
                        : alpha(theme.palette.grey[500], 0.05),
                      border: `1px solid ${mcpDeploymentStatus.isDeployed && mcpDeploymentStatus.isRunning
                        ? alpha(theme.palette.success.main, 0.2) 
                        : mcpDeploymentStatus.isDeployed 
                        ? alpha(theme.palette.warning.main, 0.2)
                        : alpha(theme.palette.grey[500], 0.2)}`,
                      wordWrap: 'break-word'
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        {mcpDeploymentStatus.isDeployed && mcpDeploymentStatus.isRunning ? (
                          <CheckCircleIcon color="success" sx={{ mr: 2 }} />
                        ) : mcpDeploymentStatus.isDeployed ? (
                          <ErrorIcon color="warning" sx={{ mr: 2 }} />
                        ) : firestoreApiFiles?.mcp_config ? (
                          <PendingIcon color="info" sx={{ mr: 2 }} />
                        ) : (
                          <PendingIcon color="disabled" sx={{ mr: 2 }} />
                        )}
                        <Typography variant="h6">
                          3. MCP Deployment & Running
                        </Typography>
                      </Box>
                      
                      {mcpDeploymentStatus.error ? (
                        <Box>
                          <Typography variant="body2" color="error.main" sx={{ mb: 1 }}>
                            ✗ Deployment error
                          </Typography>
                          <Typography variant="caption" color="error.main" sx={{ mb: 2, display: 'block' }}>
                            {mcpDeploymentStatus.error}
                          </Typography>
                          <Button
                            variant="contained"
                            color="primary"
                            onClick={handleDeployMcp}
                            disabled={isDeployingMcp}
                            startIcon={<RefreshIcon />}
                            size="small"
                            sx={{ 
                              bgcolor: theme.palette.primary.main,
                              '&:hover': {
                                bgcolor: theme.palette.primary.dark
                              }
                            }}
                          >
                            Redeploy MCP Server
                          </Button>
                        </Box>
                      ) : mcpDeploymentStatus.isDeployed && mcpDeploymentStatus.isRunning ? (
                        <Box>
                          <Typography variant="body2" color="success.main" sx={{ mb: 1 }}>
                            ✓ MCP server deployed and running
                          </Typography>
                          {mcpDeploymentStatus.lastChecked && (
                            <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                              Last checked: {new Date(mcpDeploymentStatus.lastChecked).toLocaleString()}
                            </Typography>
                          )}
                          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                            <Button
                              variant="outlined"
                              color="primary"
                              size="small"
                              onClick={handleDeployMcp}
                              disabled={isDeployingMcp}
                              startIcon={<PlayIcon />}
                              sx={{ 
                                borderColor: alpha(theme.palette.primary.main, 0.5),
                                color: theme.palette.primary.main,
                                '&:hover': {
                                  borderColor: theme.palette.primary.main,
                                  bgcolor: alpha(theme.palette.primary.main, 0.08)
                                }
                              }}
                            >
                              Redeploy
                            </Button>
                            <Button
                              variant="outlined"
                              color="error"
                              size="small"
                              onClick={handleDeleteMcpServer}
                              startIcon={<DeleteIcon />}
                              sx={{ 
                                borderColor: alpha(theme.palette.error.main, 0.5),
                                color: theme.palette.error.main,
                                '&:hover': {
                                  borderColor: theme.palette.error.main,
                                  bgcolor: alpha(theme.palette.error.main, 0.08)
                                }
                              }}
                            >
                              Delete
                            </Button>
                          </Box>
                        </Box>
                      ) : mcpDeploymentStatus.isDeployed ? (
                        <Box>
                          <Typography variant="body2" color="warning.main" sx={{ mb: 1 }}>
                            ⚠️ MCP server deployed but not running
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                            <Button
                              variant="outlined"
                              color="primary"
                              size="small"
                              onClick={handleDeployMcp}
                              disabled={isDeployingMcp}
                              startIcon={<PlayIcon />}
                              sx={{ 
                                borderColor: alpha(theme.palette.primary.main, 0.5),
                                color: theme.palette.primary.main,
                                '&:hover': {
                                  borderColor: theme.palette.primary.main,
                                  bgcolor: alpha(theme.palette.primary.main, 0.08)
                                }
                              }}
                            >
                              Redeploy
                            </Button>
                            <Button
                              variant="outlined"
                              color="error"
                              size="small"
                              onClick={handleDeleteMcpServer}
                              startIcon={<DeleteIcon />}
                              sx={{ 
                                borderColor: alpha(theme.palette.error.main, 0.5),
                                color: theme.palette.error.main,
                                '&:hover': {
                                  borderColor: theme.palette.error.main,
                                  bgcolor: alpha(theme.palette.error.main, 0.08)
                                }
                              }}
                            >
                              Delete
                            </Button>
                          </Box>
                        </Box>
                      ) : firestoreApiFiles?.mcp_config && firestoreApiFiles.mcp_config.status === 'generated' && !isDeployingMcp ? (
                        <Box>
                          <Typography variant="body2" color="success.main" sx={{ mb: 2 }}>
                            ✓ MCP configuration ready for deployment
                          </Typography>
                          <Button
                            variant="contained"
                            color="primary"
                            onClick={handleDeployMcp}
                            disabled={isDeployingMcp}
                            startIcon={<PlayIcon />}
                            sx={{ 
                              bgcolor: theme.palette.primary.main,
                              '&:hover': {
                                bgcolor: theme.palette.primary.dark
                              }
                            }}
                          >
                            Deploy MCP Server
                          </Button>
                        </Box>
                      ) : isDeployingMcp ? (
                        <Box>
                          <Typography variant="body2" color="info.main" sx={{ mb: 1 }}>
                            ⏳ Deploying MCP server...
                          </Typography>
                          <LinearProgress 
                            color="primary" 
                            sx={{ 
                              mt: 1,
                              height: 6,
                              borderRadius: 3
                            }} 
                          />
                        </Box>
                      ) : firestoreApiFiles?.mcp_config ? (
                        <Box>
                          <Typography variant="body2" color="warning.main" sx={{ mb: 2 }}>
                            ⚡ MCP configuration available
                          </Typography>
                          <Button
                            variant="contained"
                            color="primary"
                            onClick={handleDeployMcp}
                            disabled={isDeployingMcp}
                            startIcon={<PlayIcon />}
                            sx={{ 
                              bgcolor: theme.palette.primary.main,
                              '&:hover': {
                                bgcolor: theme.palette.primary.dark
                              }
                            }}
                          >
                            Deploy MCP Server
                          </Button>
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          MCP server will be deployed after configuration is ready
                        </Typography>
                      )}
                    </Card>
                    
                    {/* Deployment History - Show when there are any deployments */}
                    {deploymentHistory.length > 0 ? (
                      <Accordion sx={{ mt: 2, bgcolor: 'transparent', boxShadow: 'none', border: `1px solid ${alpha(theme.palette.grey[500], 0.2)}`, borderRadius: 1 }}>
                        <AccordionSummary 
                          expandIcon={<ExpandMoreIcon />}
                          sx={{ 
                            minHeight: 'auto',
                            '&.Mui-expanded': { minHeight: 'auto' },
                            '& .MuiAccordionSummary-content': { 
                              margin: '8px 0',
                              '&.Mui-expanded': { margin: '8px 0' }
                            }
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <TimelineIcon sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary" fontWeight="medium">
                              Deployment History ({deploymentHistory.length})
                            </Typography>
                            {deploymentHistory.some(d => d.status === 'failed') && (
                              <Chip 
                                label="Issues Found" 
                                size="small" 
                                color="error" 
                                variant="outlined"
                                sx={{ ml: 2, fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails sx={{ pt: 0 }}>
                        
                          <Box sx={{ maxHeight: 250, overflow: 'auto' }}>
                            {deploymentHistory.map((deployment, index) => (
                              <Box 
                                key={deployment.id} 
                                sx={{ 
                                  mb: index < deploymentHistory.length - 1 ? 1 : 0,
                                  p: 1.5,
                                  border: `1px solid ${alpha(theme.palette.grey[500], 0.1)}`,
                                  borderRadius: 1,
                                  bgcolor: deployment.status === 'completed' 
                                    ? alpha(theme.palette.success.main, 0.02)
                                    : deployment.status === 'failed'
                                    ? alpha(theme.palette.error.main, 0.03)
                                    : alpha(theme.palette.info.main, 0.02)
                                }}
                            >
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  {deployment.status === 'completed' ? (
                                    <CheckCircleIcon color="success" sx={{ mr: 1, fontSize: 16 }} />
                                  ) : deployment.status === 'failed' ? (
                                    <ErrorIcon color="error" sx={{ mr: 1, fontSize: 16 }} />
                                  ) : deployment.status === 'in_progress' ? (
                                    <PendingIcon color="info" sx={{ mr: 1, fontSize: 16 }} />
                                  ) : (
                                    <ScheduleIcon color="warning" sx={{ mr: 1, fontSize: 16 }} />
                                  )}
                                  <Typography variant="caption" fontWeight="medium" sx={{ fontSize: '0.8rem' }}>
                                    {deployment.deployment_id ? `Deployment ${deployment.deployment_id.slice(-8)}` : `Deployment ${deployment.id.slice(-8)}`}
                                  </Typography>
                                </Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  {deployment.deployment_id && (
                                    <Button
                                      size="small"
                                      variant="outlined"
                                      onClick={() => handleViewLogs(deployment.deployment_id)}
                                      sx={{ 
                                        fontSize: '0.7rem',
                                        minWidth: 'auto',
                                        px: 1,
                                        py: 0.25,
                                        height: '24px'
                                      }}
                                    >
                                      Logs
                                    </Button>
                                  )}
                                  <Chip
                                    label={deployment.status || 'pending'}
                                    size="small"
                                    color={
                                      deployment.status === 'completed' ? 'success' :
                                      deployment.status === 'failed' ? 'error' :
                                      deployment.status === 'in_progress' ? 'info' : 'default'
                                    }
                                    variant="outlined"
                                  />
                                </Box>
                              </Box>
                              
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                {deployment.created_at ? (
                                  `Started: ${formatDate(deployment.created_at)}`
                                ) : deployment.started_at ? (
                                  `Started: ${formatDate(deployment.started_at)}`
                                ) : (
                                  'Start time not available'
                                )}
                              </Typography>
                              
                              {deployment.completed_at && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                  {deployment.status === 'failed' ? 'Failed' : 'Completed'}: {formatDate(deployment.completed_at)}
                                </Typography>
                              )}
                              
                              {deployment.last_updated && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                  Last updated: {formatDate(deployment.last_updated)}
                                </Typography>
                              )}
                              
                              {deployment.current_step && (
                                <Typography variant="caption" color="info.main" sx={{ display: 'block', mb: 1 }}>
                                  Step: {deployment.current_step}
                                </Typography>
                              )}
                              
                              {deployment.progress !== undefined && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                  Progress: {deployment.progress}%
                                </Typography>
                              )}
                              
                              {deployment.error_message && (
                                <Box sx={{ mt: 1, p: 1, bgcolor: alpha(theme.palette.error.main, 0.1), borderRadius: 1 }}>
                                  <Typography variant="caption" color="error.main" sx={{ display: 'block', fontWeight: 'medium', mb: 1 }}>
                                    Error Details:
                                  </Typography>
                                  <Typography variant="caption" color="error.main" sx={{ display: 'block', whiteSpace: 'pre-wrap', maxHeight: 150, overflow: 'auto' }}>
                                    {deployment.error_message}
                                  </Typography>
                                </Box>
                              )}
                              
                              {(deployment.server_url || deployment.health_status || deployment.mcp_config_path) && (
                                <Accordion sx={{ mt: 1, bgcolor: 'transparent', boxShadow: 'none' }}>
                                  <AccordionSummary 
                                    expandIcon={<ExpandMoreIcon />}
                                    sx={{ 
                                      minHeight: 'auto',
                                      '&.Mui-expanded': { minHeight: 'auto' },
                                      '& .MuiAccordionSummary-content': { 
                                        margin: '8px 0',
                                        '&.Mui-expanded': { margin: '8px 0' }
                                      }
                                    }}
                                  >
                                    <Typography variant="caption" fontWeight="medium">
                                      View Details
                                    </Typography>
                                  </AccordionSummary>
                                  <AccordionDetails sx={{ pt: 0, pb: 1 }}>
                                    {deployment.server_url && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                        <strong>Server URL:</strong> {deployment.server_url}
                                      </Typography>
                                    )}
                                    {deployment.health_status && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                        <strong>Health Status:</strong> {deployment.health_status}
                                      </Typography>
                                    )}
                                    {deployment.mcp_config_path && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                        <strong>Config Path:</strong> {deployment.mcp_config_path}
                                      </Typography>
                                    )}
                                    {deployment.deployment_id && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                        <strong>Deployment ID:</strong> {deployment.deployment_id}
                                      </Typography>
                                    )}
                                    {deployment.agent_id && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                        <strong>Agent ID:</strong> {deployment.agent_id}
                                      </Typography>
                                    )}
                                  </AccordionDetails>
                                </Accordion>
                              )}
                            </Box>
                          ))}
                        </Box>
                        </AccordionDetails>
                      </Accordion>
                    ) : null}
                    
                  </Box>
                  
                  {/* MCP Manager Integration Summary */}
                  {(integrationSummary) && (
                    <Card sx={{ 
                      mt: 4, 
                      p: 3, 
                      bgcolor: integrationSummary?.status === 'active' 
                        ? alpha(theme.palette.success.main, 0.05)
                        : alpha(theme.palette.info.main, 0.05), 
                      border: `1px solid ${integrationSummary?.status === 'active' 
                        ? alpha(theme.palette.success.main, 0.2)
                        : alpha(theme.palette.info.main, 0.2)}`,
                      wordWrap: 'break-word',
                      minHeight: '300px',
                      display: 'flex',
                      flexDirection: 'column'
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                        <Typography variant="h6" color={integrationSummary?.status === 'active' ? 'success.main' : 'info.main'} sx={{ display: 'flex', alignItems: 'center' }}>
                          <InfoIcon sx={{ mr: 1 }} />
                          Live Integration Status
                        </Typography>
                      </Box>
                      
                      {integrationSummary ? (
                        <Box sx={{ flex: 1, overflow: 'auto' }}>
                          {/* Status and Service URL */}
                          <Box sx={{ mb: 3 }}>
                            <Chip
                              label={integrationSummary.status}
                              color={integrationSummary.status === 'active' ? 'success' : 'default'}
                              variant="outlined"
                              sx={{ mb: 2 }}
                            />
                            
                            {integrationSummary.service_url && (
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                <strong>Service URL:</strong> 
                                <Link 
                                  href={integrationSummary.service_url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  sx={{ ml: 1 }}
                                >
                                  {integrationSummary.service_url}
                                </Link>
                              </Typography>
                            )}
                            
                            {integrationSummary.deployed_at && (
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                Deployed: {formatDate(integrationSummary.deployed_at)}
                              </Typography>
                            )}
                          </Box>
                          
                          {/* Server Information */}
                          {integrationSummary.server_info && (
                            <Box sx={{ mb: 3 }}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'medium' }}>
                                Server Information
                              </Typography>
                              <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                                <Typography variant="body2" sx={{ mb: 0.5 }}>
                                  <strong>Name:</strong> {integrationSummary.server_info.name}
                                </Typography>
                                <Typography variant="body2" sx={{ mb: 0.5 }}>
                                  <strong>Version:</strong> {integrationSummary.server_info.version}
                                </Typography>
                                {integrationSummary.server_info.description && (
                                  <Typography variant="body2" color="text.secondary">
                                    {integrationSummary.server_info.description}
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                          )}
                          
                          {/* Tools Summary */}
                          <Box sx={{ mb: 3 }}>
                            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'medium' }}>
                              Available Tools ({integrationSummary.tools_count || 0})
                            </Typography>
                            
                            {integrationSummary.tools && integrationSummary.tools.length > 0 ? (
                              <Box sx={{ maxHeight: 250, overflow: 'auto' }}>
                                {integrationSummary.tools.map((tool, index) => (
                                  <Accordion key={index} sx={{ bgcolor: 'background.paper', boxShadow: 'none', '&:before': { display: 'none' } }}>
                                    <AccordionSummary 
                                      expandIcon={<ExpandMoreIcon />}
                                      sx={{ minHeight: 'auto', '&.Mui-expanded': { minHeight: 'auto' } }}
                                    >
                                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                        <Typography variant="body2" fontWeight="medium" sx={{ mr: 2 }}>
                                          {tool.name}
                                        </Typography>
                                        <Chip 
                                          label={tool.method || 'N/A'} 
                                          size="small" 
                                          variant="outlined" 
                                          sx={{ mr: 1 }}
                                        />
                                        {tool.args_count !== undefined && (
                                          <Typography variant="caption" color="text.secondary">
                                            {tool.args_count} args
                                          </Typography>
                                        )}
                                      </Box>
                                    </AccordionSummary>
                                    <AccordionDetails sx={{ pt: 0 }}>
                                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                        {tool.description}
                                      </Typography>
                                      {tool.url_template && (
                                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontFamily: 'monospace', bgcolor: alpha(theme.palette.grey[500], 0.1), p: 1, borderRadius: 1 }}>
                                          {tool.url_template}
                                        </Typography>
                                      )}
                                      <Box sx={{ mt: 1 }}>
                                        <Button
                                          size="small"
                                          variant="outlined"
                                          onClick={() => handleTestTool(tool.name)}
                                          startIcon={<PlayIcon />}
                                        >
                                          Test Tool
                                        </Button>
                                      </Box>
                                    </AccordionDetails>
                                  </Accordion>
                                ))}
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                No tools available
                              </Typography>
                            )}
                          </Box>
                          
                          {/* Endpoints */}
                          {integrationSummary.endpoints && (
                            <Box>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'medium' }}>
                                Service Endpoints
                              </Typography>
                              <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                                {Object.entries(integrationSummary.endpoints).map(([key, url]) => (
                                  <Typography key={key} variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                    <strong>{key}:</strong> 
                                    <Link 
                                      href={url} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      sx={{ ml: 1, fontSize: 'inherit' }}
                                    >
                                      {url}
                                    </Link>
                                  </Typography>
                                ))}
                              </Box>
                            </Box>
                          )}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No integration data available. Deploy MCP server to see live integration status.
                        </Typography>
                      )}
                    </Card>
                  )}
                </Box>
              </Box>

              {/* File input (hidden) */}
              <input
                type="file"
                ref={apiFileInputRef}
                style={{ display: 'none' }}
                accept=".json,.yaml,.yml"
                onChange={handleApiFileSelected}
              />
            </Box>
          </TabPanel>

          {/* Agent Testing Tab */}
          <TabPanel value={activeTab} index={3}>
            <Box sx={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              backgroundColor: '#ffffff'
            }}>
              {/* Enhanced Panel Title */}
              <Box sx={{ 
                py: 2.5, 
                px: 3, 
                borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.secondary.light, 0.05)} 0%, ${alpha(theme.palette.primary.light, 0.02)} 100%)`
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ 
                    bgcolor: theme.palette.secondary.main, 
                    mr: 2,
                    width: 32,
                    height: 32
                  }}>
                    <PlayIcon fontSize="small" />
                  </Avatar>
                  <Typography variant="h6" sx={{ 
                    fontWeight: 'bold',
                    color: theme.palette.secondary.main
                  }}>
                    Agent Testing
                  </Typography>
                  <Chip 
                    label="Live Testing" 
                    size="small" 
                    sx={{ 
                      ml: 'auto',
                      bgcolor: alpha(theme.palette.secondary.main, 0.1),
                      color: theme.palette.secondary.main,
                      fontWeight: 'medium'
                    }} 
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Test your agent with real-world scenarios
                    </Typography>
                    {testConversationId && (
                      <Chip 
                        label={`Session: ${testConversationId.substring(0, 8)}...`}
                        size="small"
                        variant="outlined"
                        sx={{ 
                          mt: 0.5,
                          fontSize: '0.7rem',
                          height: 20
                        }}
                      />
                    )}
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Tooltip title="Start fresh conversation">
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={createNewConversation}
                        disabled={creatingConversation || !agentId}
                        startIcon={creatingConversation ? <CircularProgress size={16} /> : <RefreshIcon />}
                        sx={{ 
                          borderRadius: 2,
                          textTransform: 'none',
                          fontWeight: 'medium',
                          borderColor: alpha(theme.palette.secondary.main, 0.3),
                          color: theme.palette.secondary.main,
                          '&:hover': {
                            borderColor: theme.palette.secondary.main,
                            backgroundColor: alpha(theme.palette.secondary.main, 0.05)
                          }
                        }}
                      >
                        {creatingConversation ? 'Creating...' : 'New Session'}
                      </Button>
                    </Tooltip>
                  </Box>
                </Box>
              </Box>

              {/* Enhanced Testing Conversation Container */}
              <Box sx={{ 
                flexGrow: 1, 
                overflow: 'auto', 
                p: 3, 
                background: `linear-gradient(180deg, ${alpha(theme.palette.background.default, 0.3)} 0%, ${alpha(theme.palette.secondary.light, 0.02)} 100%)`
              }}>
                {testMessages.length === 0 ? (
                  <Zoom in={true} timeout={1200}>
                    <Card sx={{ 
                      textAlign: 'center', 
                      mt: 8,
                      p: 4,
                      background: `linear-gradient(135deg, ${alpha(theme.palette.secondary.light, 0.08)} 0%, ${alpha(theme.palette.primary.light, 0.05)} 100%)`,
                      border: `1px solid ${alpha(theme.palette.secondary.main, 0.1)}`,
                      borderRadius: 3,
                      boxShadow: 'none'
                    }}>
                      <Avatar sx={{ 
                        bgcolor: alpha(theme.palette.secondary.main, 0.1), 
                        mx: 'auto',
                        mb: 2,
                        width: 60,
                        height: 60
                      }}>
                        <PlayIcon sx={{ fontSize: 30, color: theme.palette.secondary.main }} />
                      </Avatar>
                      <Typography variant="h6" gutterBottom fontWeight="bold" color="secondary">
                        Ready for Testing
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Put your agent through its paces with real conversations
                      </Typography>
                    </Card>
                  </Zoom>
                ) : (
                  testMessages.map((message, index) => (
                    <Fade key={index} in={true} timeout={300} style={{ transitionDelay: `${index * 100}ms` }}>
                      <Card
                        elevation={0}
                        sx={{
                          p: 2.5,
                          mb: 2,
                          maxWidth: '85%',
                          ml: message.role === 'user' ? 'auto' : 0,
                          mr: message.role === 'assistant' ? 'auto' : 0,
                          background: message.role === 'user' 
                            ? `linear-gradient(135deg, ${alpha(theme.palette.secondary.light, 0.15)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`
                            : `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${alpha(theme.palette.primary.light, 0.05)} 100%)`,
                          border: `1px solid ${alpha(theme.palette.secondary.main, message.role === 'user' ? 0.2 : 0.08)}`,
                          borderRadius: 3,
                          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
                          position: 'relative',
                          '&::before': message.role === 'user' ? {
                            content: '""',
                            position: 'absolute',
                            right: -8,
                            top: 12,
                            width: 0,
                            height: 0,
                            borderLeft: `8px solid ${alpha(theme.palette.secondary.main, 0.1)}`,
                            borderTop: '8px solid transparent',
                            borderBottom: '8px solid transparent'
                          } : {
                            content: '""',
                            position: 'absolute',
                            left: -8,
                            top: 12,
                            width: 0,
                            height: 0,
                            borderRight: `8px solid ${theme.palette.background.paper}`,
                            borderTop: '8px solid transparent',
                            borderBottom: '8px solid transparent'
                          }
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                          <Avatar sx={{ 
                            bgcolor: message.role === 'user' ? theme.palette.secondary.main : theme.palette.primary.main,
                            width: 32,
                            height: 32
                          }}>
                            {message.role === 'user' ? <PersonIcon fontSize="small" /> : <SmartToyIcon fontSize="small" />}
                          </Avatar>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="body1" sx={{ 
                              lineHeight: 1.6,
                              fontSize: '0.95rem'
                            }}>
                              {message.content}
                            </Typography>
                          </Box>
                        </Box>
                      </Card>
                    </Fade>
                  ))
                )}
                {isTestLoading && (
                  <Fade in={isTestLoading}>
                    <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
                      <Card sx={{ 
                        p: 2, 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 2,
                        background: alpha(theme.palette.secondary.main, 0.05),
                        border: `1px solid ${alpha(theme.palette.secondary.main, 0.1)}`
                      }}>
                        <CircularProgress size={20} color="secondary" />
                        <Typography variant="body2" color="secondary">
                          Agent is responding...
                        </Typography>
                      </Card>
                    </Box>
                  </Fade>
                )}
                <div ref={testMessagesEndRef} />
              </Box>

              {/* Enhanced Test Input Container */}
              <Box sx={{ 
                p: 3, 
                borderTop: `1px solid ${alpha(theme.palette.secondary.main, 0.08)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.secondary.light, 0.03)} 100%)`,
                backdropFilter: 'blur(10px)'
              }}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    id="test-input"
                    fullWidth
                    placeholder="Test your agent here..."
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    disabled={isTestLoading}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleTestMessage()}
                    multiline
                    maxRows={3}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        backgroundColor: alpha(theme.palette.background.paper, 0.8),
                        '&:hover': {
                          backgroundColor: theme.palette.background.paper
                        },
                        '&.Mui-focused': {
                          backgroundColor: theme.palette.background.paper,
                          boxShadow: `0 0 0 2px ${alpha(theme.palette.secondary.main, 0.2)}`
                        }
                      }
                    }}
                  />
                  <Button
                    variant="contained"
                    endIcon={<PlayIcon />}
                    onClick={handleTestMessage}
                    disabled={isTestLoading || !testInput.trim()}
                    sx={{ 
                      borderRadius: 2,
                      textTransform: 'none',
                      fontWeight: 'bold',
                      minWidth: 100,
                      background: `linear-gradient(45deg, ${theme.palette.secondary.main}, ${theme.palette.primary.main})`,
                      boxShadow: '0 3px 12px rgba(0, 0, 0, 0.15)',
                      '&:hover': {
                        boxShadow: '0 4px 15px rgba(0, 0, 0, 0.25)',
                        transform: 'translateY(-1px)'
                      },
                      '&:disabled': {
                        background: alpha(theme.palette.action.disabledBackground, 0.3)
                      },
                      transition: 'all 0.2s ease-in-out'
                    }}
                  >
                    Test
                  </Button>
                </Box>
              </Box>
            </Box>
          </TabPanel>
        </Box>
      </Box>

      {/* Enhanced Notifications */}
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
          sx={{
            borderRadius: 2,
            fontWeight: 'medium',
            '& .MuiAlert-icon': {
              fontSize: '1.2rem'
            }
          }}
        >
          {notification.message}
        </Alert>
      </Snackbar>

      {/* Enhanced Success Modal */}
      <Dialog
        open={successModal}
        onClose={handleCloseSuccessModal}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: `linear-gradient(135deg, ${alpha(theme.palette.success.light, 0.05)} 0%, ${alpha(theme.palette.primary.light, 0.03)} 100%)`
          }
        }}
      >
        <DialogTitle sx={{ textAlign: 'center', pt: 3 }}>
          <Avatar sx={{ 
            bgcolor: theme.palette.success.main, 
            mx: 'auto',
            mb: 2,
            width: 56,
            height: 56
          }}>
            <AutoAwesomeIcon sx={{ fontSize: 30 }} />
          </Avatar>
          <Typography variant="h5" fontWeight="bold">
            Agent Created Successfully!
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ textAlign: 'center', pb: 2 }}>
          <Typography variant="body1" color="text.secondary">
            Your agent is now ready for action. Start testing it with real conversations or continue refining its capabilities.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 3, gap: 1 }}>
          <Button 
            onClick={handleCloseSuccessModal} 
            color="primary"
            variant="outlined"
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 'medium'
            }}
          >
            Continue Editing
          </Button>
          <Button 
            onClick={handleStartTesting} 
            color="primary" 
            variant="contained"
            startIcon={<PlayIcon />}
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 'bold',
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
            }}
          >
            Start Testing
          </Button>
        </DialogActions>
      </Dialog>

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

      {/* API Name Dialog */}
      <Dialog open={showNameDialog} onClose={() => setShowNameDialog(false)}>
        <DialogTitle>Upload API Specification</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <TextField
            autoFocus
            margin="dense"
            label="API Name"
            fullWidth
            variant="outlined"
            value={apiName}
            onChange={(e) => setApiName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="API Key (Optional)"
            fullWidth
            variant="outlined"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            helperText="Enter if your API requires authentication"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setShowNameDialog(false);
            setApiName('');
            setApiKey('');
            setSelectedFile(null);
          }}>
            Cancel
          </Button>
          <Button 
            onClick={handleUploadApiSpec} 
            disabled={!apiName.trim() || fileLoading}
            variant="contained"
          >
            {fileLoading ? <CircularProgress size={20} /> : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Deployment Logs Dialog */}
      <Dialog 
        open={logsDialog.open} 
        onClose={() => setLogsDialog(prev => ({ ...prev, open: false }))}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            height: '80vh',
            maxHeight: '80vh'
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}>
          <Box>
            <Typography variant="h6">Deployment Logs</Typography>
            {logsDialog.deploymentId && (
              <Typography variant="caption" color="text.secondary">
                Deployment ID: {logsDialog.deploymentId}
              </Typography>
            )}
          </Box>
          <IconButton 
            onClick={() => setLogsDialog(prev => ({ ...prev, open: false }))}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column' }}>
          {logsDialog.loading ? (
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              minHeight: 200,
              flexDirection: 'column',
              gap: 2
            }}>
              <CircularProgress />
              <Typography variant="body2" color="text.secondary">
                Loading deployment logs...
              </Typography>
            </Box>
          ) : (
            <Box sx={{ 
              flex: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
              p: 2,
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.4
            }}>
              {logsDialog.logs || 'No logs available'}
            </Box>
          )}
        </DialogContent>
        
        <DialogActions sx={{ borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
          <Button 
            onClick={() => setLogsDialog(prev => ({ ...prev, open: false }))}
            variant="outlined"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Tool Test Dialog */}
      <Dialog 
        open={toolTestDialog.open} 
        onClose={() => setToolTestDialog(prev => ({ ...prev, open: false }))}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            minHeight: '500px'
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}>
          <Box>
            <Typography variant="h6">Test Tool</Typography>
            {toolTestDialog.toolName && (
              <Typography variant="caption" color="text.secondary">
                Tool: {toolTestDialog.toolName}
              </Typography>
            )}
          </Box>
          <IconButton 
            onClick={() => setToolTestDialog(prev => ({ ...prev, open: false }))}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent sx={{ p: 3 }}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Parameters (JSON)
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={toolTestDialog.parameters}
              onChange={(e) => setToolTestDialog(prev => ({ ...prev, parameters: e.target.value }))}
              placeholder='{"param1": "value1", "param2": "value2"}'
              sx={{
                fontFamily: 'monospace',
                '& .MuiInputBase-input': {
                  fontFamily: 'monospace'
                }
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Enter parameters as valid JSON. Use {"{}"} for no parameters.
            </Typography>
          </Box>
          
          {toolTestDialog.loading && (
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              py: 3,
              flexDirection: 'column',
              gap: 2
            }}>
              <CircularProgress />
              <Typography variant="body2" color="text.secondary">
                Testing tool...
              </Typography>
            </Box>
          )}
          
          {toolTestDialog.error && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="error" sx={{ mb: 1 }}>
                Error
              </Typography>
              <Box sx={{ 
                p: 2, 
                bgcolor: alpha(theme.palette.error.main, 0.1), 
                borderRadius: 1,
                border: `1px solid ${alpha(theme.palette.error.main, 0.3)}`
              }}>
                <Typography variant="body2" color="error" sx={{ fontFamily: 'monospace' }}>
                  {toolTestDialog.error}
                </Typography>
              </Box>
            </Box>
          )}
          
          {toolTestDialog.result && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Result
              </Typography>
              <Box sx={{ 
                p: 2, 
                bgcolor: alpha(theme.palette.success.main, 0.1), 
                borderRadius: 1,
                border: `1px solid ${alpha(theme.palette.success.main, 0.3)}`,
                maxHeight: '300px',
                overflow: 'auto'
              }}>
                <pre style={{ 
                  margin: 0, 
                  fontFamily: 'monospace', 
                  fontSize: '0.875rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {JSON.stringify(toolTestDialog.result, null, 2)}
                </pre>
              </Box>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions sx={{ borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`, p: 3 }}>
          <Button 
            onClick={() => setToolTestDialog(prev => ({ ...prev, open: false }))}
            variant="outlined"
          >
            Close
          </Button>
          <Button 
            onClick={executeToolTest}
            variant="contained"
            disabled={toolTestDialog.loading}
            startIcon={toolTestDialog.loading ? <CircularProgress size={16} /> : <PlayArrowIcon />}
          >
            {toolTestDialog.loading ? 'Testing...' : 'Test Tool'}
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};

export default AgentEditor;
