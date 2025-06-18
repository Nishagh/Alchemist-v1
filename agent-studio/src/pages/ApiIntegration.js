import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Divider,
  Tab,
  Tabs,
  TextField,
  Card,
  CardContent,
  Alert,
  Chip,
  CircularProgress,
  Grid,
  IconButton,
  Snackbar,
  LinearProgress,
  Fade,
  useTheme,
  alpha,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  InputAdornment
} from '@mui/material';
import { 
  ContentCopy as CopyAllIcon,
  KeyboardArrowRight as ArrowRightIcon,
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  CloudUpload as UploadIcon,
  Api as ApiIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Code as CodeIcon,
  ExpandMore as ExpandMoreIcon,
  Send as SendIcon,
  PlayArrow as PlayArrowIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { uploadApiSpecification, getApiIntegrations, deleteApiIntegration, getApiSpecification, downloadApiSpecification, getTestableEndpoints, testApiEndpoint, getApiIntegrationFiles } from '../services';
import { useAuth } from '../utils/AuthContext';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco, atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import axios from 'axios';
import { auth } from '../utils/firebase';

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

// TabPanel component for the tabs
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`api-tabpanel-${index}`}
      aria-labelledby={`api-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const ApiIntegration = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const { currentUser } = useAuth();
  const fileInputRef = useRef(null);
  
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedApis, setUploadedApis] = useState([]);
  const [currentApiSpec, setCurrentApiSpec] = useState('');
  const [apiSpecPreview, setApiSpecPreview] = useState('');
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [apiToDelete, setApiToDelete] = useState(null);
  const [apiName, setApiName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [showNameDialog, setShowNameDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedApi, setSelectedApi] = useState(null);
  const [selectedEndpoint, setSelectedEndpoint] = useState('');
  const [endpoints, setEndpoints] = useState([]);
  const [requestMethod, setRequestMethod] = useState('GET');
  const [requestUrl, setRequestUrl] = useState('');
  const [requestHeaders, setRequestHeaders] = useState({});
  const [requestBody, setRequestBody] = useState('');
  const [responseData, setResponseData] = useState(null);
  const [responseStatus, setResponseStatus] = useState(null);
  const [isTestingApi, setIsTestingApi] = useState(false);
  const [pathParams, setPathParams] = useState({});
  const [queryParams, setQueryParams] = useState({});
  const [headerParams, setHeaderParams] = useState({});
  const [missingRequiredParams, setMissingRequiredParams] = useState([]);
  const [paramErrors, setParamErrors] = useState({});
  const [paramFieldsTouched, setParamFieldsTouched] = useState({});
  const [isRequestValid, setIsRequestValid] = useState(false);
  const [apiFiles, setApiFiles] = useState([]);
  const [selectedApiFile, setSelectedApiFile] = useState(null);
  
  // Load agent data, API integrations, and API files
  useEffect(() => {
    if (agentId && currentUser) {
      fetchAgentData();
      fetchApiIntegrations();
      fetchApiFiles();
    }
  }, [agentId, currentUser]);
  
  const fetchAgentData = async () => {
    try {
      setLoading(true);
      //const agentData = await getAgent(agentId);
      
      // Check if the current user is the owner of this agent
      if (agent.owner_id && agent.owner_id !== currentUser?.uid) {
        setError('You do not have permission to view API integrations for this agent');
        setLoading(false);
        return;
      }
      
      //setAgent(agentata);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching agent data:', err);
      setError('Failed to load agent data. Please try again.');
      setLoading(false);
    }
  };
  
  const fetchApiIntegrations = async () => {
    try {
      console.log(`Fetching API integrations for agent ID: ${agentId}`);
      const integrations = await getApiIntegrations(agentId);
      console.log('Received API integrations:', integrations);
      
      // Ensure we always set an array, even if the API returns null/undefined or a non-array
      const safeIntegrations = Array.isArray(integrations) ? integrations : [];
      console.log('Setting uploadedApis state to:', safeIntegrations);
      setUploadedApis(safeIntegrations);
      
      // Clear any previous error notifications
      if (notification.severity === 'error' && notification.message.includes('OpenAPI validator')) {
        setNotification({
          open: false,
          message: '',
          severity: 'info'
        });
      }
    } catch (err) {
      console.error('Error fetching API integrations:', err);
      
      // Check for specific OpenAPI validator error
      if (err.isOpenApiValidationError || 
          err.message?.includes('OpenAPI validator') || 
          err.message?.includes('openapi_spec_validator')) {
        console.log('Detected OpenAPI validation error from server');
        setNotification({
          open: true,
          message: 'There is an issue with the OpenAPI validator on the server. This is a backend configuration problem that needs to be fixed by the development team.',
          severity: 'error'
        });
      } else {
        setNotification({
          open: true,
          message: 'Failed to load API integrations. Please try again.',
          severity: 'error'
        });
      }
      
      // Set to empty array on error
      setUploadedApis([]);
    }
  };
  
  const fetchApiFiles = async () => {
    try {
      setIsLoading(true);
      console.log(`Fetching API files for agent ID: ${agentId}`);
      const files = await getApiIntegrationFiles(agentId);
      console.log('Received API files:', files);
      
      // Ensure we always set an array, even if the API returns null/undefined or a non-array
      const safeFiles = Array.isArray(files) ? files : [];
      console.log('Setting apiFiles state to:', safeFiles);
      setApiFiles(safeFiles);
      setIsLoading(false);
    } catch (err) {
      console.error('Error fetching API files:', err);
      setNotification({
        open: true,
        message: 'Failed to load API specification files. Please try again.',
        severity: 'error'
      });
      setIsLoading(false);
    }
  };
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    if (newValue === 2) {
      loadTestableEndpoints(agentId, null);
    }
  };
  
  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setNotification({ open: true, message: 'Copied to clipboard!', severity: 'success' });
  };
  
  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };
  
  const handleFileUploadClick = () => {
    fileInputRef.current.click();
  };
  
  const handleFileSelected = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type (accept .yaml, .yml, .json)
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!['yaml', 'yml', 'json'].includes(fileExt)) {
      setNotification({
        open: true,
        message: 'Invalid file format. Please upload a YAML or JSON file.',
        severity: 'error'
      });
      return;
    }
    
    // Store the file and show the name dialog
    setSelectedFile(file);
    setApiName(file.name);
    setShowNameDialog(true);
    
    // Reset file input
    e.target.value = null;
  };
  
  const handleUploadCancel = () => {
    setSelectedFile(null);
    setApiName('');
    setApiKey('');
    setShowNameDialog(false);
  };
  
  const handleUploadConfirm = async () => {
    if (!selectedFile || !apiName.trim()) {
      setNotification({
        open: true,
        message: 'Please provide a name for the API',
        severity: 'warning'
      });
      return;
    }
    
    setShowNameDialog(false);
    setIsUploading(true);
    setUploadProgress(10);
    
    try {
      // Read the file content for preview
      const reader = new FileReader();
      
      reader.onload = async (event) => {
        const fileContent = event.target.result;
        setApiSpecPreview(fileContent);
        setUploadProgress(30);
        
        try {
          // Upload to the server with optional API key
          const result = await uploadApiSpecification(agentId, selectedFile, apiName, apiKey);
          setUploadProgress(90);
          
          // Refresh the list of API integrations
          await fetchApiIntegrations();
          setUploadProgress(100);
          
          setNotification({
            open: true,
            message: 'API specification uploaded successfully!',
            severity: 'success'
          });
          
          // After a delay, reset the progress
          setTimeout(() => {
            setIsUploading(false);
            setUploadProgress(0);
            setSelectedFile(null);
            setApiKey(''); // Reset API key after successful upload
            // Automatically switch to the APIs tab
            setTabValue(1); 
          }, 1000);
        } catch (error) {
          console.error('Error uploading API spec:', error);
          setNotification({
            open: true,
            message: `Failed to upload API specification: ${error.message || 'Unknown error'}`,
            severity: 'error'
          });
          setIsUploading(false);
          setUploadProgress(0);
        }
      };
      
      reader.onerror = () => {
        setNotification({
          open: true,
          message: 'Error reading file. Please try again.',
          severity: 'error'
        });
        setIsUploading(false);
        setUploadProgress(0);
      };
      
      reader.readAsText(selectedFile);
    } catch (error) {
      console.error('Error processing file:', error);
      setNotification({
        open: true,
        message: `Failed to process file: ${error.message || 'Unknown error'}`,
        severity: 'error'
      });
      setIsUploading(false);
      setUploadProgress(0);
    }
  };
  
  const handleViewApiSpec = (api) => {
    setCurrentApiSpec(api);
    setIsLoading(true);
    
    // Use the dedicated API endpoint to fetch the specification content
    getApiSpecification(agentId, api.id)
      .then(specData => {
        console.log('Received API spec data:', specData);
        
        // If the API returns formatted content directly
        if (specData.content) {
          setApiSpecPreview(specData.content);
        } else if (specData.spec) {
          setApiSpecPreview(specData.spec);
        } else if (typeof specData === 'string') {
          // If the response is the content directly as a string
          setApiSpecPreview(specData);
        } else {
          // If we receive a complex object, stringify it for display
          setApiSpecPreview(JSON.stringify(specData, null, 2));
        }
        
        setTabValue(1); // Switch to the API Spec tab (index 1 after removing Available APIs tab)
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error fetching API spec content:', error);
        
        // Fallback to spec_url if the direct API call fails
        if (api.spec_url) {
          console.log('Falling back to spec_url:', api.spec_url);
          fetch(api.spec_url)
            .then(response => response.text())
            .then(content => {
              setApiSpecPreview(content);
              setIsLoading(false);
            })
            .catch(fallbackError => {
              console.error('Error with fallback to spec_url:', fallbackError);
              setNotification({
                open: true,
                message: 'Failed to load API specification content',
                severity: 'error'
              });
              setIsLoading(false);
            });
        } else {
          setNotification({
            open: true,
            message: 'Failed to load API specification content',
            severity: 'error'
          });
          setIsLoading(false);
        }
      });
  };
  
  const handleDownloadApiSpec = async (api) => {
    try {
      setIsLoading(true);
      
      // Get the download URL
      const downloadUrl = await downloadApiSpecification(agentId, api.id);
      
      // Create a hidden anchor element to trigger the download
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      // Set a default filename based on the API name
      const fileName = `${api.name || 'api-spec'}.${api.spec_type || 'yaml'}`;
      link.setAttribute('download', fileName);
      
      // Append to the document, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      setNotification({
        open: true,
        message: 'API specification download started',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error downloading API specification:', error);
      setNotification({
        open: true,
        message: `Failed to download API specification: ${error.message || 'Unknown error'}`,
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDeleteApiSpec = (api) => {
    setApiToDelete(api);
    setShowConfirmDelete(true);
  };
  
  const confirmDeleteApiSpec = async () => {
    try {
      await deleteApiIntegration(agentId, apiToDelete.id);
      
      // Refresh the list of API integrations
      await fetchApiIntegrations();
      
      setNotification({
        open: true,
        message: 'API specification deleted successfully',
        severity: 'success'
      });
      
      // If we were viewing the deleted API spec, clear it
      if (currentApiSpec && currentApiSpec.id === apiToDelete.id) {
        setCurrentApiSpec('');
        setApiSpecPreview('');
      }
    } catch (error) {
      console.error('Error deleting API spec:', error);
      setNotification({
        open: true,
        message: `Failed to delete API specification: ${error.message || 'Unknown error'}`,
        severity: 'error'
      });
    } finally {
      setShowConfirmDelete(false);
      setApiToDelete(null);
    }
  };
  
  // Function to parse OpenAPI spec and extract endpoints
  const parseApiSpec = (api, specData) => {
    try {
      // If the specData is a string, try to parse it as JSON
      let parsedSpec = specData;
      if (typeof specData === 'string') {
        try {
          parsedSpec = JSON.parse(specData);
        } catch (e) {
          // If it's not valid JSON, it might be YAML, but we can't parse that here
          console.log('API spec is not valid JSON, might be YAML');
          setNotification({
            open: true,
            message: 'Cannot parse YAML specifications for testing. Please convert to JSON.',
            severity: 'warning'
          });
          return [];
        }
      }
      
      // Extract endpoints from the parsed OpenAPI spec
      const extractedEndpoints = [];
      
      if (parsedSpec && parsedSpec.paths) {
        // Iterate through paths
        for (const path in parsedSpec.paths) {
          // Iterate through methods (GET, POST, etc.)
          for (const method in parsedSpec.paths[path]) {
            const endpointInfo = parsedSpec.paths[path][method];
            
            // Create an endpoint object with all the necessary info
            extractedEndpoints.push({
              path,
              method: method.toUpperCase(),
              summary: endpointInfo.summary || '',
              description: endpointInfo.description || '',
              parameters: endpointInfo.parameters || [],
              requestBody: endpointInfo.requestBody || null,
              responses: endpointInfo.responses || {}
            });
          }
        }
      }
      
      console.log(`Extracted ${extractedEndpoints.length} endpoints from API spec`, extractedEndpoints);
      return extractedEndpoints;
    } catch (error) {
      console.error('Error parsing API spec:', error);
      setNotification({
        open: true,
        message: 'Error parsing API specification',
        severity: 'error'
      });
      return [];
    }
  };

  // Function to handle endpoint selection
  const handleEndpointSelect = (endpointId) => {
    const endpoint = endpoints.find(e => e.id === endpointId);
    if (endpoint) {
      setSelectedEndpoint(endpointId);      
      // Track the API ID from the endpoint if available
      if (endpoint.api_id) {
        console.log(`Endpoint belongs to API ID: ${endpoint.api_id}`);
        setSelectedApi({
          id: endpoint.id,
          name: endpoint.api_name || 'API'
        });
      }
      
      // Set request method and base URL if available
      setRequestMethod(endpoint.method || 'GET');
      
      // Reset parameters and body
      const newPathParams = {};
      const newQueryParams = {};
      const newHeaderParams = {};
      const newParamErrors = {};
      const newFieldsTouched = {};
      
      // Process all types of parameters
      
      // Process path parameters
      if (endpoint.path_params && Array.isArray(endpoint.path_params)) {
        endpoint.path_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.in === 'path') {
              // Use example value if available
              newPathParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`path_${param.name}`] = !param.example;
              }
            }
          } catch (e) {
            console.error('Error parsing path parameter:', e);
          }
        });
      }
      
      // Process query parameters
      if (endpoint.query_params && Array.isArray(endpoint.query_params)) {
        endpoint.query_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.in === 'query') {
              // Use example value if available
              newQueryParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`query_${param.name}`] = !param.example;
              }
            }
          } catch (e) {
            console.error('Error parsing query parameter:', e);
          }
        });
      }
      
      // Process header parameters
      if (endpoint.header_params && Array.isArray(endpoint.header_params)) {
        endpoint.header_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.in === 'header') {
              // Use example value if available
              newHeaderParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`header_${param.name}`] = !param.example;
              }
            }
          } catch (e) {
            console.error('Error parsing header parameter:', e);
          }
        });
      }
      
      // Also check the required_parameters object if available
      if (endpoint.required_parameters) {
        // Process path parameters from required_parameters
        if (endpoint.required_parameters.path && Array.isArray(endpoint.required_parameters.path)) {
          endpoint.required_parameters.path.forEach(paramStr => {
            try {
              const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
              newPathParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`path_${param.name}`] = !param.example;
              }
            } catch (e) {
              console.error('Error parsing required path parameter:', e);
            }
          });
        }
        
        // Process query parameters from required_parameters
        if (endpoint.required_parameters.query && Array.isArray(endpoint.required_parameters.query)) {
          endpoint.required_parameters.query.forEach(paramStr => {
            try {
              const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
              newQueryParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`query_${param.name}`] = !param.example;
              }
            } catch (e) {
              console.error('Error parsing required query parameter:', e);
            }
          });
        }
        
        // Process header parameters from required_parameters
        if (endpoint.required_parameters.header && Array.isArray(endpoint.required_parameters.header)) {
          endpoint.required_parameters.header.forEach(paramStr => {
            try {
              const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
              newHeaderParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`header_${param.name}`] = !param.example;
              }
            } catch (e) {
              console.error('Error parsing required header parameter:', e);
            }
          });
        }
      }
      
      // Fall back to general parameters array if other specific arrays are not found
      if (endpoint.parameters && Array.isArray(endpoint.parameters)) {
        endpoint.parameters.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.in === 'path') {
              newPathParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`path_${param.name}`] = !param.example;
              }
            } else if (param.in === 'query') {
              newQueryParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`query_${param.name}`] = !param.example;
              }
            } else if (param.in === 'header') {
              newHeaderParams[param.name] = param.example || '';
              if (param.required) {
                newParamErrors[`header_${param.name}`] = !param.example;
              }
            }
          } catch (e) {
            console.error('Error parsing parameter:', e);
          }
        });
      }
      
      // Handle API key in header if specified in the endpoint
      if (endpoint.api_key_name && endpoint.api_key_location === 'header' && endpoint.requires_api_key) {
        // Only set this if it's not already set from the parameters
        if (!newHeaderParams[endpoint.api_key_name]) {
          newHeaderParams[endpoint.api_key_name] = 'YOUR_API_KEY';
          newParamErrors[`header_${endpoint.api_key_name}`] = true;
        }
      }
      
      setPathParams(newPathParams);
      setQueryParams(newQueryParams);
      setHeaderParams(newHeaderParams);
      setParamErrors(newParamErrors);
      setParamFieldsTouched(newFieldsTouched);
      setIsRequestValid(Object.keys(newParamErrors).length === 0);
      
      // Set default request body if available
      if (endpoint.requestBody) {
        if (endpoint.requestBody.parsedExample) {
          // Use the parsed example if available
          setRequestBody(JSON.stringify(endpoint.requestBody.parsedExample, null, 2));
        } else if (endpoint.requestBody.example) {
          // Use the example string if available
          setRequestBody(endpoint.requestBody.example);
        } else if (endpoint.requestBody.content && endpoint.requestBody.content['application/json']) {
          const schema = endpoint.requestBody.content['application/json'].schema;
          // Create a default request body based on the schema (simplified)
          try {
            const defaultBody = {};
            if (schema && schema.properties) {
              Object.keys(schema.properties).forEach(prop => {
                defaultBody[prop] = '';
              });
            }
            setRequestBody(JSON.stringify(defaultBody, null, 2));
          } catch (e) {
            setRequestBody('{}');
          }
        } else {
          setRequestBody('{}');
        }
      } else {
        setRequestBody('');
      }
      
      // Reset response
      setResponseData(null);
      setResponseStatus(null);
      
      // Validate all required parameters
      setTimeout(validateAllRequiredParams, 50);
    }
  };

  // Function to handle header parameter change
  const handleHeaderParamChange = (paramName, value) => {
    setHeaderParams(prev => ({
      ...prev,
      [paramName]: value
    }));
    
    // Mark field as touched
    setParamFieldsTouched(prev => ({
      ...prev,
      [`header_${paramName}`]: true
    }));
    
    // Update validation state
    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
    if (endpoint) {
      let isRequired = false;
      
      // Check if this is a required header parameter
      if (endpoint.header_params) {
        endpoint.header_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.in === 'header' && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error parsing header parameter:', e);
          }
        });
      }
      
      // Also check if this is the API key header
      if (endpoint.api_key_name === paramName && endpoint.api_key_location === 'header' && endpoint.requires_api_key) {
        isRequired = true;
      }
      
      if (isRequired && !value.trim()) {
        setParamErrors(prev => ({
          ...prev,
          [`header_${paramName}`]: true
        }));
      } else {
        setParamErrors(prev => {
          const updated = { ...prev };
          delete updated[`header_${paramName}`];
          return updated;
        });
      }
    }
    
    // Validate all required parameters after a short delay to ensure state is updated
    setTimeout(validateAllRequiredParams, 50);
  };

  // Function to update path parameter
  const handlePathParamChange = (paramName, value) => {
    setPathParams(prev => ({
      ...prev,
      [paramName]: value
    }));
    
    // Mark field as touched
    setParamFieldsTouched(prev => ({
      ...prev,
      [`path_${paramName}`]: true
    }));
    
    // Update validation state
    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
    if (endpoint) {
      let isRequired = false;
      
      // Check if this is a required path parameter
      if (endpoint.path_params) {
        endpoint.path_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error parsing path parameter:', e);
          }
        });
      }
      
      // Also check in required_parameters.path array
      if (endpoint.required_parameters && endpoint.required_parameters.path) {
        endpoint.required_parameters.path.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking required path parameter:', e);
          }
        });
      }
      
      if (isRequired && !value.trim()) {
        setParamErrors(prev => ({
          ...prev,
          [`path_${paramName}`]: true
        }));
      } else {
        setParamErrors(prev => {
          const updated = { ...prev };
          delete updated[`path_${paramName}`];
          return updated;
        });
      }
    }
    
    // Validate all required parameters after a short delay to ensure state is updated
    setTimeout(validateAllRequiredParams, 50);
  };

  // Function to update query parameter
  const handleQueryParamChange = (paramName, value) => {
    setQueryParams(prev => ({
      ...prev,
      [paramName]: value
    }));
    
    // Mark field as touched
    setParamFieldsTouched(prev => ({
      ...prev,
      [`query_${paramName}`]: true
    }));
    
    // Update validation state
    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
    if (endpoint) {
      let isRequired = false;
      
      // Check if this is a required query parameter
      if (endpoint.query_params) {
        endpoint.query_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error parsing query parameter:', e);
          }
        });
      }
      
      // Also check in required_parameters.query array
      if (endpoint.required_parameters && endpoint.required_parameters.query) {
        endpoint.required_parameters.query.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking required query parameter:', e);
          }
        });
      }
      
      if (isRequired && !value.trim()) {
        setParamErrors(prev => ({
          ...prev,
          [`query_${paramName}`]: true
        }));
      } else {
        setParamErrors(prev => {
          const updated = { ...prev };
          delete updated[`query_${paramName}`];
          return updated;
        });
      }
    }
    
    // Validate all required parameters after a short delay to ensure state is updated
    setTimeout(validateAllRequiredParams, 50);
  };

  // Function to handle API selection for testing
  const loadTestableEndpoints = (agentId, api = null) => {
    setIsLoading(true);
    
    // If an API is provided, set it as the selected API
    if (api) {
      setSelectedApi(api);
    }
    
    // Fetch testable endpoints directly from the backend
    getTestableEndpoints(agentId, api?.id)
      .then(testableEndpoints => {
        console.log('Received testable endpoints:', testableEndpoints);
        
        // If the endpoints belong to a specific API, store that API information
        if (testableEndpoints.length > 0 && testableEndpoints[0].api_id) {
          setSelectedApi({
            id: testableEndpoints[0].api_id,
            name: testableEndpoints[0].api_name || 'API'
          });
        } else if (api) {
          // Ensure each endpoint has the API ID associated with it
          testableEndpoints.forEach(endpoint => {
            endpoint.api_id = api.id;
            endpoint.api_name = api.name || api.api_name;
          });
        }
        
        // Format endpoints to match our expected structure
        const formattedEndpoints = testableEndpoints.map(endpoint => {
          // Parse parameters which come as JSON strings
          const parsedParameters = endpoint.parameters?.map(param => {
            if (typeof param === 'string') {
              try {
                return JSON.parse(param);
              } catch (e) {
                console.error('Error parsing parameter:', e, param);
                return null;
              }
            }
            return param;
          }).filter(Boolean); // Remove any null values from failed parsing
          
          // Parse responses which also come as JSON strings
          const parsedResponses = endpoint.responses?.map(resp => {
            if (typeof resp === 'string') {
              try {
                return JSON.parse(resp);
              } catch (e) {
                console.error('Error parsing response:', e, resp);
                return null;
              }
            }
            return resp;
          }).filter(Boolean);
          
          // Parse request body if it exists
          let parsedRequestBody = endpoint.request_body;
          if (parsedRequestBody && typeof parsedRequestBody === 'object') {
            // If the request body has an example that's a string, try to parse it
            if (parsedRequestBody.example && typeof parsedRequestBody.example === 'string') {
              try {
                parsedRequestBody.parsedExample = JSON.parse(parsedRequestBody.example);
              } catch (e) {
                console.error('Error parsing request body example:', e);
                parsedRequestBody.parsedExample = parsedRequestBody.example;
              }
            }
          }

          return {
            path: endpoint.path,
            method: endpoint.method.toUpperCase(),
            summary: endpoint.summary || '',
            description: endpoint.description || '',
            parameters: parsedParameters || [],
            requestBody: parsedRequestBody || null,
            responses: parsedResponses || [],
            baseUrl: endpoint.base_url || '',
            // Ensure API ID is tracked with each endpoint
            api_id: endpoint.api_id || (api ? api.id : null),
            api_name: endpoint.api_name || (api ? (api.name || api.api_name) : null),
            // Add any additional fields from the backend
            ...endpoint
          };
        });
        
        setEndpoints(formattedEndpoints);
        setSelectedEndpoint('');
        setRequestMethod('GET');
        setRequestUrl('');
        setRequestBody('');
        setResponseData(null);
        setResponseStatus(null);
        setPathParams({});
        setQueryParams({});
        setHeaderParams({});
        setIsLoading(false);
        
        // Switch to the API Testing tab
        setTabValue(2);
      })
      .catch(error => {
        console.error('Error fetching testable endpoints:', error);
        setNotification({
          open: true,
          message: `Failed to load testable endpoints: ${error.message || 'Unknown error'}`,
          severity: 'error'
        });
        setIsLoading(false);
      });
  };
  
  // Helper function to check if a string is valid JSON
  const isValidJson = (str) => {
    try {
      JSON.parse(str);
      return true;
    } catch (e) {
      return false;
    }
  };
  
  const handleApiFileSelect = (file) => {
    setSelectedApiFile(file);
    setIsLoading(true);
    
    // If file_content is available directly in the response
    if (file.file_content) {
      setApiSpecPreview(file.file_content);
      setIsLoading(false);
      return;
    }
    
    // Fetch file content from URL if available (spec_url or download_url)
    const url = file.spec_url || file.download_url || file.url;
    if (url) {
      fetch(url)
        .then(response => response.text())
        .then(content => {
          setApiSpecPreview(content);
          setIsLoading(false);
        })
        .catch(error => {
          console.error('Error fetching API file content:', error);
          setNotification({
            open: true,
            message: 'Failed to load API file content',
            severity: 'error'
          });
          setIsLoading(false);
        });
    } else if (file.content) {
      // If content is directly available in the file object
      setApiSpecPreview(file.content);
      setIsLoading(false);
    } else {
      setNotification({
        open: true,
        message: 'No content available for this API file',
        severity: 'warning'
      });
      setIsLoading(false);
    }
  };
  
  // Function to validate all required parameters
  const validateAllRequiredParams = () => {
    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
    if (!endpoint) return;
    
    const errors = {};
    const missing = [];
    
    // Check path parameters
    Object.entries(pathParams).forEach(([paramName, value]) => {
      let isRequired = false;
      
      // Check in path_params array
      if (endpoint.path_params) {
        endpoint.path_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking path parameter requirement:', e);
          }
        });
      }
      
      // Check in required_parameters.path array
      if (endpoint.required_parameters && endpoint.required_parameters.path) {
        endpoint.required_parameters.path.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking required path parameter:', e);
          }
        });
      }
      
      // Also check in general parameters array
      if (endpoint.parameters) {
        endpoint.parameters.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.in === 'path' && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking parameter requirement:', e);
          }
        });
      }
      
      if (isRequired && (!value || !value.trim())) {
        errors[`path_${paramName}`] = true;
        missing.push(`Path parameter: ${paramName}`);
      }
    });
    
    // Check query parameters
    Object.entries(queryParams).forEach(([paramName, value]) => {
      let isRequired = false;
      
      // Check in query_params array
      if (endpoint.query_params) {
        endpoint.query_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking query parameter requirement:', e);
          }
        });
      }
      
      // Check in required_parameters.query array
      if (endpoint.required_parameters && endpoint.required_parameters.query) {
        endpoint.required_parameters.query.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking required query parameter:', e);
          }
        });
      }
      
      // Also check in general parameters array
      if (endpoint.parameters) {
        endpoint.parameters.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.in === 'query' && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking parameter requirement:', e);
          }
        });
      }
      
      if (isRequired && (!value || !value.trim())) {
        errors[`query_${paramName}`] = true;
        missing.push(`Query parameter: ${paramName}`);
      }
    });
    
    // Check header parameters
    Object.entries(headerParams).forEach(([paramName, value]) => {
      let isRequired = false;
      
      // Check in header_params array
      if (endpoint.header_params) {
        endpoint.header_params.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking header parameter requirement:', e);
          }
        });
      }
      
      // Check in required_parameters.header array
      if (endpoint.required_parameters && endpoint.required_parameters.header) {
        endpoint.required_parameters.header.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking required header parameter:', e);
          }
        });
      }
      
      // Also check in general parameters array
      if (endpoint.parameters) {
        endpoint.parameters.forEach(paramStr => {
          try {
            const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
            if (param.name === paramName && param.in === 'header' && param.required) {
              isRequired = true;
            }
          } catch (e) {
            console.error('Error checking parameter requirement:', e);
          }
        });
      }
      
      // Check if this is the API key header
      if (endpoint.api_key_name === paramName && endpoint.api_key_location === 'header' && endpoint.requires_api_key) {
        isRequired = true;
      }
      
      if (isRequired && (!value || !value.trim())) {
        errors[`header_${paramName}`] = true;
        missing.push(`Header parameter: ${paramName}`);
      }
    });
    
    // For POST/PUT/PATCH requests, check if body is valid JSON when required
    if (['POST', 'PUT', 'PATCH'].includes(requestMethod) && 
        endpoint.requestBody?.required && 
        (!requestBody.trim() || !isValidJson(requestBody))) {
      errors.requestBody = true;
      missing.push('Request body (valid JSON required)');
    }
    
    setParamErrors(errors);
    setMissingRequiredParams(missing);
    setIsRequestValid(missing.length === 0);
  };

  // Function to execute the API test
  const executeApiTest = async () => {
    try {
      // Validate before sending
      validateAllRequiredParams();
      
      // Check if there are missing required parameters
      if (!isRequestValid) {
        setNotification({
          open: true,
          message: `Missing required parameters: ${missingRequiredParams.join(', ')}`,
          severity: 'error'
        });
        return;
      }
      
      setIsTestingApi(true);
      
      // Find the selected endpoint
      const endpoint = endpoints.find(e => e.id === selectedEndpoint);
      if (!endpoint) {
        throw new Error('No endpoint selected');
      }

      // Prepare query parameters
      const queryParams2 = {};
      Object.entries(queryParams)
        .filter(([key, value]) => value !== '')
        .forEach(([key, value]) => {
          queryParams2[key] = value;
        });

      // Call the API test endpoint with all parameters
      const testResponse = await testApiEndpoint(
        agentId, 
        endpoint.id, 
        queryParams2,
        pathParams
      );
      
      if (testResponse.error) {
        // Handle error from the test endpoint
        setResponseStatus(testResponse.status || 500);
        setResponseData(testResponse.data || {
          error: 'API test failed',
          message: 'The test endpoint returned an error',
          timestamp: new Date().toISOString()
        });
      } else {
        // Process successful response
        setResponseStatus(testResponse.status || 200);
        
        // Check different response formats
        if (testResponse.data) {
          setResponseData(testResponse.data);
        } else if (testResponse.response) {
          setResponseStatus(testResponse.response.status || 200);
          setResponseData(testResponse.response.data || testResponse.response);
        } else {
          // If response is directly the data
          setResponseData(testResponse);
        }
      }
      
      setIsTestingApi(false);
    } catch (error) {
      console.error('Error executing API test:', error);
      setNotification({
        open: true,
        message: `API test failed: ${error.message}`,
        severity: 'error'
      });
      setResponseStatus(error.status || 500);
      setResponseData({
        error: error.message,
        timestamp: new Date().toISOString()
      });
      setIsTestingApi(false);
    }
  };
  
  // Show loading spinner if data is loading
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  // Show error if there's an error
  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
        <Button 
          variant="outlined" 
          startIcon={<ArrowBackIcon />} 
          onClick={() => navigate('/agents')}
        >
          Back to My Agents
        </Button>
      </Box>
    );
  }
  
  return (
    <Box>
      <Fade in={true} timeout={800}>
        <Box sx={{ mb: 4 }}>
          {/* Header */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 3
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Button 
                variant="outlined" 
                startIcon={<ArrowBackIcon />} 
                onClick={() => navigate(-1)}
                sx={{ mr: 2 }}
              >
                Back
              </Button>
              <Typography variant="h4" component="h1" fontWeight="bold">
                API Integration
              </Typography>
              {agent && (
                <Chip 
                  label={agent.name} 
                  sx={{ ml: 2, bgcolor: alpha(theme.palette.primary.main, 0.1) }}
                />
              )}
            </Box>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<UploadIcon />}
                onClick={handleFileUploadClick}
                disabled={isUploading}
              >
                Upload API Configuration
              </Button>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                Accepted files: OpenAPI specifications (.yaml, .yml) or MCP config files
              </Typography>
            </Box>
            
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".yaml,.yml,.json"
              onChange={handleFileSelected}
            />
          </Box>
          
          {/* Upload Progress */}
          {isUploading && (
            <Box sx={{ width: '100%', mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Uploading and processing API specification...</Typography>
                <Typography variant="body2">{uploadProgress}%</Typography>
              </Box>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}
          
          {/* Main Content */}
          <Paper elevation={2} sx={{ borderRadius: 2, overflow: 'hidden' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={handleTabChange} aria-label="api integration tabs">
                <Tab icon={<InfoIcon />} iconPosition="start" label="Overview" />
                <Tab icon={<CodeIcon />} iconPosition="start" label="API Spec" />
                <Tab icon={<PlayArrowIcon />} iconPosition="start" label="API Testing" />
                <Tab icon={<InfoIcon />} iconPosition="start" label="Usage Guide" />
              </Tabs>
            </Box>
            
            {/* Overview Tab */}
            <TabPanel value={tabValue} index={0}>
              <Box>
                <Typography variant="h6" sx={{ mb: 2 }} color="primary">
                  Enhance Your Agent with API Integrations
                </Typography>
                <Typography paragraph>
                  Upload OpenAPI specification files (YAML or JSON) to give your agent the ability to interact with external APIs.
                  Once integrated, your agent can use these APIs to fetch data, perform actions, and more.
                </Typography>
                
                <Grid container spacing={3} sx={{ mt: 2 }}>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <UploadIcon color="primary" sx={{ mr: 1 }} />
                          <Typography variant="h6">How to Integrate APIs</Typography>
                        </Box>
                        <Divider sx={{ mb: 2 }} />
                        <Typography variant="body2" paragraph>
                          1. Prepare your OpenAPI specification file (YAML or JSON format)
                        </Typography>
                        <Typography variant="body2" paragraph>
                          2. Click the "Upload OpenAPI Spec" button at the top right
                        </Typography>
                        <Typography variant="body2" paragraph>
                          3. Select your specification file
                        </Typography>
                        <Typography variant="body2">
                          4. Your agent will now have access to the API endpoints defined in the specification
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <ApiIcon color="primary" sx={{ mr: 1 }} />
                          <Typography variant="h6">API Statistics</Typography>
                        </Box>
                        <Divider sx={{ mb: 2 }} />
                        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', height: '150px' }}>
                          <Typography variant="h3" color="primary" gutterBottom>
                            {uploadedApis.length}
                          </Typography>
                          <Typography variant="body1">
                            {uploadedApis.length === 1 ? 'API Integrated' : 'APIs Integrated'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                            {uploadedApis.length === 0 
                              ? 'Upload your first API specification to get started'
                              : `${(Array.isArray(uploadedApis) ? uploadedApis : []).reduce((total, api) => total + ((api && api.endpoints) ? api.endpoints : 0), 0)} endpoints available to your agent`
                            }
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
                
                {uploadedApis.length === 0 && (
                  <Box sx={{ 
                    mt: 4, 
                    p: 3, 
                    textAlign: 'center',
                    border: `1px dashed ${alpha(theme.palette.primary.main, 0.3)}`,
                    borderRadius: 2,
                    bgcolor: alpha(theme.palette.primary.main, 0.05)
                  }}>
                    <UploadIcon sx={{ fontSize: 48, color: alpha(theme.palette.primary.main, 0.5), mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      No API Specifications Uploaded Yet
                    </Typography>
                    <Typography variant="body1" paragraph>
                      Upload an OpenAPI specification file to enhance your agent's capabilities.
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={handleFileUploadClick}
                    >
                      Upload Specification
                    </Button>
                  </Box>
                )}
              </Box>
            </TabPanel>
            
            {/* API Spec Tab */}
            <TabPanel value={tabValue} index={1}>
              <Typography variant="h6" sx={{ mb: 2 }}>API Specification</Typography>
              
              {isLoading ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
                  <CircularProgress size={40} sx={{ mb: 2 }} />
                  <Typography variant="body1">Loading API specification...</Typography>
                </Box>
              ) : (
                <Grid container spacing={3}>
                  {/* API Files List */}
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, height: '100%' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Available API Files
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      
                      {apiFiles.length === 0 ? (
                        <Box sx={{ p: 2 }}>
                          <Typography variant="body2" color="text.secondary">
                            No API specification files found.
                          </Typography>
                          <Button
                            variant="contained"
                            startIcon={<UploadIcon />}
                            onClick={handleFileUploadClick}
                            sx={{ mt: 2 }}
                          >
                            Upload API Specification
                          </Button>
                        </Box>
                      ) : (
                        <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                          {apiFiles.map((file, index) => {
                            const fileId = file.file_id || file.api_id || index;
                            const isSelected = selectedApiFile && 
                              (selectedApiFile.file_id === file.file_id || 
                               selectedApiFile.api_id === file.api_id);
                            
                            return (
                              <Button
                                key={fileId}
                                variant={isSelected ? "contained" : "outlined"}
                                sx={{
                                  mb: 1,
                                  display: 'flex',
                                  justifyContent: 'flex-start',
                                  textAlign: 'left',
                                  textTransform: 'none',
                                  width: '100%',
                                  padding: '8px 12px'
                                }}
                                onClick={() => handleApiFileSelect(file)}
                              >
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%' }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                    <CodeIcon sx={{ mr: 1 }} />
                                    <Typography variant="body2" noWrap sx={{ fontWeight: 'bold' }}>
                                      {file.api_name || file.file_name || `API Spec ${index + 1}`}
                                    </Typography>
                                    {file.api_key_present && (
                                      <Chip 
                                        label="API Key" 
                                        size="small" 
                                        color="success" 
                                        sx={{ ml: 1, height: '20px' }} 
                                      />
                                    )}
                                  </Box>
                                  {file.file_type && (
                                    <Typography variant="caption" color="text.secondary" sx={{ ml: 4 }}>
                                      {file.file_type}
                                    </Typography>
                                  )}
                                  {file.created_at && (
                                    <Typography variant="caption" color="text.secondary" sx={{ ml: 4 }}>
                                      Added: {convertTimestamp(file.created_at)?.toLocaleDateString() || 'Unknown date'}
                                    </Typography>
                                  )}
                                  {file.file_size && (
                                    <Typography variant="caption" color="text.secondary" sx={{ ml: 4 }}>
                                      Size: {(file.file_size / 1024).toFixed(2)} KB
                                    </Typography>
                                  )}
                                </Box>
                              </Button>
                            );
                          })}
                        </Box>
                      )}
                      
                      <Divider sx={{ my: 2 }} />
                      <Button
                        variant="outlined"
                        startIcon={<UploadIcon />}
                        onClick={handleFileUploadClick}
                        fullWidth
                      >
                        Upload New Spec
                      </Button>
                    </Paper>
                  </Grid>
                  
                  {/* API Spec Content */}
                  <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 2 }}>
                      {!apiSpecPreview ? (
                        <Box sx={{ 
                          p: 4, 
                          textAlign: 'center',
                          border: `1px dashed ${alpha(theme.palette.primary.main, 0.3)}`,
                          borderRadius: 2,
                          bgcolor: alpha(theme.palette.primary.main, 0.05)
                        }}>
                          <Typography variant="body1">
                            Select an API specification from the list to view its content.
                          </Typography>
                        </Box>
                      ) : (
                        <>
                          {selectedApiFile && (
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                                {selectedApiFile.api_name || selectedApiFile.file_name}
                              </Typography>
                              
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 1 }}>
                                {selectedApiFile.file_type && (
                                  <Chip 
                                    label={selectedApiFile.file_type} 
                                    size="small" 
                                    color="primary" 
                                    variant="outlined"
                                  />
                                )}
                                
                                {selectedApiFile.file_extension && (
                                  <Chip 
                                    label={selectedApiFile.file_extension.toUpperCase()} 
                                    size="small" 
                                    color="info" 
                                  />
                                )}
                                
                                {selectedApiFile.api_key_present && (
                                  <Chip 
                                    label="API Key Present" 
                                    size="small" 
                                    color="success" 
                                  />
                                )}
                              </Box>
                              
                              {selectedApiFile.download_url && (
                                <Button
                                  variant="outlined"
                                  size="small"
                                  startIcon={<DownloadIcon />}
                                  href={selectedApiFile.download_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  sx={{ mt: 1, mr: 1 }}
                                >
                                  Download
                                </Button>
                              )}
                              
                              <Divider sx={{ my: 2 }} />
                            </Box>
                          )}
                          
                          <Box sx={{ position: 'relative' }}>
                            <SyntaxHighlighter 
                              language={
                                selectedApiFile?.file_extension === 'json' || 
                                selectedApiFile?.file_type?.includes('json') || 
                                selectedApiFile?.file_content_type?.includes('json') ? 
                                  'json' : 'yaml'
                              }
                              style={atomOneDark}
                              customStyle={{
                                padding: '16px',
                                borderRadius: '4px',
                                fontSize: '14px',
                                maxHeight: '500px',
                                overflow: 'auto'
                              }}
                            >
                              {apiSpecPreview}
                            </SyntaxHighlighter>
                            <Button 
                              variant="contained" 
                              size="small" 
                              startIcon={<CopyAllIcon />}
                              onClick={() => handleCopy(apiSpecPreview)}
                              sx={{ 
                                position: 'absolute', 
                                top: 8, 
                                right: 8,
                                bgcolor: alpha(theme.palette.background.paper, 0.8),
                                '&:hover': {
                                  bgcolor: alpha(theme.palette.background.paper, 0.9),
                                }
                              }}
                            >
                              Copy
                            </Button>
                          </Box>
                        </>
                      )}
                    </Paper>
                  </Grid>
                </Grid>
              )}
            </TabPanel>
            
            {/* API Testing Tab */}
            <TabPanel value={tabValue} index={2}>
              <Typography variant="h6" sx={{ mb: 3 }}>API Testing</Typography>
              
              {isLoading ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
                  <CircularProgress size={40} sx={{ mb: 2 }} />
                  <Typography variant="body1">Loading API endpoints...</Typography>
                </Box>
              ) : (
                <Grid container spacing={3}>
                  {/* Endpoint Selector */}
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, height: '100%' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Available Endpoints
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      
                      {endpoints.length === 0 ? (
                        <Typography variant="body2" color="text.secondary">
                          No endpoints found in this API specification.
                        </Typography>
                      ) : (
                        <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                          {endpoints.map((endpoint) => (
                            <Button
                              key={endpoint.id}
                              variant={selectedEndpoint === endpoint.id ? "contained" : "outlined"}
                              sx={{
                                mb: 1,
                                display: 'flex',
                                justifyContent: 'flex-start',
                                textAlign: 'left',
                                textTransform: 'none',
                                width: '100%'
                              }}
                              onClick={() => handleEndpointSelect(endpoint.id)}
                            >
                              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                <Chip 
                                  label={endpoint.method} 
                                  size="small" 
                                  color={
                                    endpoint.method === 'GET' ? 'success' :
                                    endpoint.method === 'POST' ? 'primary' :
                                    endpoint.method === 'PUT' ? 'warning' :
                                    endpoint.method === 'DELETE' ? 'error' : 'default'
                                  }
                                  sx={{ mr: 1, minWidth: '60px', justifyContent: 'center' }}
                                />
                                <Typography variant="body2" noWrap sx={{ maxWidth: '180px' }}>
                                  {endpoint.path}
                                </Typography>
                              </Box>
                            </Button>
                          ))}
                        </Box>
                      )}
                    </Paper>
                  </Grid>
                  
                  {/* Request Builder */}
                  <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 2 }}>
                      {isTestingApi ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
                          <CircularProgress size={40} sx={{ mb: 2 }} />
                          <Typography variant="body1">Testing API endpoint...</Typography>
                        </Box>
                      ) : selectedEndpoint ? (
                        <>
                          <Typography variant="subtitle1" gutterBottom>
                            Request Builder
                          </Typography>
                          <Divider sx={{ mb: 2 }} />
                          
                          {/* Endpoint Info */}
                          {(() => {
                            const endpoint = endpoints.find(e => e.id === selectedEndpoint);
                            return endpoint ? (
                              <Box sx={{ mb: 3 }}>
                                <Typography variant="subtitle2" color="primary">
                                  {endpoint.method} {endpoint.path}
                                </Typography>
                                {endpoint.summary && (
                                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                                    {endpoint.summary}
                                  </Typography>
                                )}
                              </Box>
                            ) : null;
                          })()}
                          
                          {/* Path Parameters */}
                          {Object.keys(pathParams).length > 0 && (
                            <Accordion defaultExpanded sx={{ mb: 2 }}>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography>Path Parameters</Typography>
                                {Object.keys(paramErrors).some(key => key.startsWith('path_')) && (
                                  <Chip 
                                    label="Required fields missing" 
                                    size="small" 
                                    color="error" 
                                    sx={{ ml: 2 }}
                                  />
                                )}
                              </AccordionSummary>
                              <AccordionDetails>
                                <Grid container spacing={2}>
                                  {Object.entries(pathParams).map(([paramName, paramValue]) => {
                                    // Find parameter definition to check if required
                                    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
                                    const param = endpoint?.parameters?.find(p => p.name === paramName && p.in === 'path');
                                    const isRequired = param?.required || false;
                                    const hasError = paramErrors[`path_${paramName}`] && paramFieldsTouched[`path_${paramName}`];
                                    
                                    return (
                                      <Grid item xs={12} sm={6} key={paramName}>
                                        <TextField
                                          fullWidth
                                          label={paramName}
                                          value={paramValue}
                                          onChange={(e) => handlePathParamChange(paramName, e.target.value)}
                                          size="small"
                                          required={isRequired}
                                          error={hasError}
                                          helperText={hasError ? "This field is required" : param?.description || ''}
                                          InputLabelProps={{
                                            shrink: true,
                                          }}
                                          InputProps={{
                                            endAdornment: isRequired ? (
                                              <InputAdornment position="end">
                                                <Typography 
                                                  color="error" 
                                                  variant="caption" 
                                                  sx={{ fontWeight: 'bold' }}
                                                >
                                                  *
                                                </Typography>
                                              </InputAdornment>
                                            ) : null
                                          }}
                                          onBlur={() => {
                                            setParamFieldsTouched(prev => ({
                                              ...prev,
                                              [`path_${paramName}`]: true
                                            }));
                                            validateAllRequiredParams();
                                          }}
                                          placeholder={param?.example || ''}
                                        />
                                      </Grid>
                                    );
                                  })}
                                </Grid>
                              </AccordionDetails>
                            </Accordion>
                          )}
                          
                          {/* Query Parameters */}
                          {Object.keys(queryParams).length > 0 && (
                            <Accordion defaultExpanded sx={{ mb: 2 }}>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography>Query Parameters</Typography>
                                {Object.keys(paramErrors).some(key => key.startsWith('query_')) && (
                                  <Chip 
                                    label="Required fields missing" 
                                    size="small" 
                                    color="error" 
                                    sx={{ ml: 2 }}
                                  />
                                )}
                              </AccordionSummary>
                              <AccordionDetails>
                                <Grid container spacing={2}>
                                  {Object.entries(queryParams).map(([paramName, paramValue]) => {
                                    // Find parameter definition to check if required
                                    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
                                    const param = endpoint?.parameters?.find(p => p.name === paramName && p.in === 'query');
                                    const isRequired = param?.required || false;
                                    const hasError = paramErrors[`query_${paramName}`] && paramFieldsTouched[`query_${paramName}`];
                                    const paramType = param?.type || 'string';
                                    
                                    return (
                                      <Grid item xs={12} sm={6} key={paramName}>
                                        <TextField
                                          fullWidth
                                          label={`${paramName}${param?.type ? ` (${param.type})` : ''}`}
                                          value={paramValue}
                                          onChange={(e) => handleQueryParamChange(paramName, e.target.value)}
                                          size="small"
                                          required={isRequired}
                                          error={hasError}
                                          helperText={hasError ? "This field is required" : param?.description || ''}
                                          InputLabelProps={{
                                            shrink: true,
                                          }}
                                          InputProps={{
                                            endAdornment: isRequired ? (
                                              <InputAdornment position="end">
                                                <Typography 
                                                  color="error" 
                                                  variant="caption" 
                                                  sx={{ fontWeight: 'bold' }}
                                                >
                                                  *
                                                </Typography>
                                              </InputAdornment>
                                            ) : null,
                                            // Special input for boolean parameters
                                            ...(paramType === 'boolean' && {
                                              inputComponent: ({ inputRef, ...otherProps }) => (
                                                <Select
                                                  {...otherProps}
                                                  inputRef={inputRef}
                                                  fullWidth
                                                >
                                                  <MenuItem value="true">true</MenuItem>
                                                  <MenuItem value="false">false</MenuItem>
                                                  <MenuItem value="">Not specified</MenuItem>
                                                </Select>
                                              )
                                            })
                                          }}
                                          onBlur={() => {
                                            setParamFieldsTouched(prev => ({
                                              ...prev,
                                              [`query_${paramName}`]: true
                                            }));
                                            validateAllRequiredParams();
                                          }}
                                          placeholder={param?.example !== undefined ? `${param.example}` : ''}
                                          type={paramType === 'integer' || paramType === 'number' ? 'number' : 'text'}
                                        />
                                      </Grid>
                                    );
                                  })}
                                </Grid>
                              </AccordionDetails>
                            </Accordion>
                          )}
                          
                          {/* Header Parameters */}
                          {Object.keys(headerParams).length > 0 && (
                            <Accordion defaultExpanded sx={{ mb: 2 }}>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography>Header Parameters</Typography>
                                {Object.keys(paramErrors).some(key => key.startsWith('header_')) && (
                                  <Chip 
                                    label="Required fields missing" 
                                    size="small" 
                                    color="error" 
                                    sx={{ ml: 2 }}
                                  />
                                )}
                              </AccordionSummary>
                              <AccordionDetails>
                                <Grid container spacing={2}>
                                  {Object.entries(headerParams).map(([paramName, paramValue]) => {
                                    // Find parameter definition to check if required
                                    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
                                    let isRequired = false;
                                    let description = '';
                                    let paramType = 'string';
                                    let isApiKey = false;
                                    
                                    // Check if this is a required header parameter
                                    if (endpoint?.header_params) {
                                      endpoint.header_params.forEach(paramStr => {
                                        try {
                                          const param = typeof paramStr === 'string' ? JSON.parse(paramStr) : paramStr;
                                          if (param.name === paramName) {
                                            isRequired = param.required || false;
                                            description = param.description || '';
                                            paramType = param.type || 'string';
                                            isApiKey = param.is_api_key || false;
                                          }
                                        } catch (e) {
                                          console.error('Error parsing header parameter:', e);
                                        }
                                      });
                                    }
                                    
                                    // Also check if this is the API key header
                                    if (endpoint?.api_key_name === paramName && endpoint?.api_key_location === 'header') {
                                      isRequired = true;
                                      description = 'API key for authentication';
                                      isApiKey = true;
                                    }
                                    
                                    const hasError = paramErrors[`header_${paramName}`] && paramFieldsTouched[`header_${paramName}`];
                                    
                                    return (
                                      <Grid item xs={12} sm={6} key={paramName}>
                                        <TextField
                                          fullWidth
                                          label={`${paramName}${isApiKey ? ' (API Key)' : ''}`}
                                          value={paramValue}
                                          onChange={(e) => handleHeaderParamChange(paramName, e.target.value)}
                                          size="small"
                                          required={isRequired}
                                          error={hasError}
                                          helperText={hasError ? "This field is required" : description}
                                          InputLabelProps={{
                                            shrink: true,
                                          }}
                                          type={isApiKey ? "password" : "text"}
                                          InputProps={{
                                            endAdornment: isRequired ? (
                                              <InputAdornment position="end">
                                                <Typography 
                                                  color="error" 
                                                  variant="caption" 
                                                  sx={{ fontWeight: 'bold' }}
                                                >
                                                  *
                                                </Typography>
                                              </InputAdornment>
                                            ) : null
                                          }}
                                          onBlur={() => {
                                            setParamFieldsTouched(prev => ({
                                              ...prev,
                                              [`header_${paramName}`]: true
                                            }));
                                            validateAllRequiredParams();
                                          }}
                                        />
                                      </Grid>
                                    );
                                  })}
                                </Grid>
                              </AccordionDetails>
                            </Accordion>
                          )}
                          
                          {/* Request Body */}
                          {requestMethod !== 'GET' && (
                            <Accordion defaultExpanded sx={{ mb: 2 }}>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography>Request Body</Typography>
                                {paramErrors.requestBody && (
                                  <Chip 
                                    label="Invalid JSON" 
                                    size="small" 
                                    color="error" 
                                    sx={{ ml: 2 }}
                                  />
                                )}
                              </AccordionSummary>
                              <AccordionDetails>
                                <TextField
                                  fullWidth
                                  multiline
                                  rows={6}
                                  value={requestBody}
                                  onChange={(e) => {
                                    setRequestBody(e.target.value);
                                    
                                    // Validate JSON format for request body
                                    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
                                    if (endpoint?.requestBody?.required && !isValidJson(e.target.value)) {
                                      setParamErrors(prev => ({
                                        ...prev,
                                        requestBody: true
                                      }));
                                    } else {
                                      setParamErrors(prev => {
                                        const updated = { ...prev };
                                        delete updated.requestBody;
                                        return updated;
                                      });
                                    }
                                    
                                    // Validate all parameters
                                    setTimeout(validateAllRequiredParams, 50);
                                  }}
                                  placeholder="{}"
                                  variant="outlined"
                                  sx={{ fontFamily: 'monospace' }}
                                  error={paramErrors.requestBody}
                                  helperText={paramErrors.requestBody ? "Please enter valid JSON" : ""}
                                  onBlur={() => validateAllRequiredParams()}
                                />
                              </AccordionDetails>
                            </Accordion>
                          )}
                          
                          {/* Missing Parameters Warning */}
                          {missingRequiredParams.length > 0 && (
                            <Alert severity="warning" sx={{ mb: 2 }}>
                              <Typography variant="subtitle2">Missing Required Parameters:</Typography>
                              <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                                {missingRequiredParams.map((param, index) => (
                                  <li key={index}>{param}</li>
                                ))}
                              </ul>
                              <Typography variant="body2">
                                Please fill in all required parameters before sending the request.
                              </Typography>
                            </Alert>
                          )}
                          
                          {/* Execute Button */}
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                            <Button
                              variant="contained"
                              color="primary"
                              onClick={executeApiTest}
                              disabled={isTestingApi || !isRequestValid}
                              startIcon={isTestingApi ? <CircularProgress size={20} /> : <SendIcon />}
                            >
                              {isTestingApi ? 'Sending...' : 'Send Request'}
                            </Button>
                          </Box>
                          
                          {/* Response */}
                          {(responseData || responseStatus) && (
                            <Box sx={{ mt: 3 }}>
                              <Divider sx={{ mb: 2 }} />
                              <Typography variant="subtitle1" gutterBottom>
                                Response
                                {responseStatus && (
                                  <Chip
                                    label={`Status: ${responseStatus}`}
                                    color={responseStatus >= 200 && responseStatus < 300 ? 'success' : 'error'}
                                    size="small"
                                    sx={{ ml: 1 }}
                                  />
                                )}
                              </Typography>
                              
                              {responseData && (
                                <Box sx={{ position: 'relative' }}>
                                  <SyntaxHighlighter 
                                    language="json" 
                                    style={atomOneDark}
                                    customStyle={{
                                      padding: '16px',
                                      borderRadius: '4px',
                                      fontSize: '14px',
                                      maxHeight: '300px',
                                      overflow: 'auto'
                                    }}
                                  >
                                    {JSON.stringify(responseData, null, 2)}
                                  </SyntaxHighlighter>
                                  <Button 
                                    variant="contained" 
                                    size="small" 
                                    startIcon={<CopyAllIcon />}
                                    onClick={() => handleCopy(JSON.stringify(responseData, null, 2))}
                                    sx={{ 
                                      position: 'absolute', 
                                      top: 8, 
                                      right: 8,
                                      bgcolor: alpha(theme.palette.background.paper, 0.8),
                                      '&:hover': {
                                        bgcolor: alpha(theme.palette.background.paper, 0.9),
                                      }
                                    }}
                                  >
                                    Copy
                                  </Button>
                                </Box>
                              )}
                            </Box>
                          )}
                        </>
                      ) : (
                        <Box sx={{ p: 4, textAlign: 'center' }}>
                          <Typography variant="body1">
                            Select an endpoint from the list to start building your request.
                          </Typography>
                        </Box>
                      )}
                    </Paper>
                  </Grid>
                </Grid>
              )}
            </TabPanel>
            
            {/* Usage Guide Tab */}
            <TabPanel value={tabValue} index={3}>
              <Typography variant="h6" sx={{ mb: 3 }}>How to Use API Integrations with Your Agent</Typography>
              
              <Box sx={{ mb: 4 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}>
                  1. Upload API Specifications
                </Typography>
                <Typography paragraph>
                  Start by uploading OpenAPI specifications (YAML or JSON format) using the "Upload OpenAPI Spec" button.
                  Each specification defines endpoints, parameters, authentication methods, and response formats.
                </Typography>
                
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: theme.palette.primary.main, mt: 3 }}>
                  2. Agent Capabilities
                </Typography>
                <Typography paragraph>
                  Once uploaded, your agent automatically gains the ability to:
                </Typography>
                <ul>
                  <li>
                    <Typography>Understand and use the API endpoints in conversations</Typography>
                  </li>
                  <li>
                    <Typography>Make API calls when needed to fulfill user requests</Typography>
                  </li>
                  <li>
                    <Typography>Parse API responses and present information to users</Typography>
                  </li>
                </ul>
                
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: theme.palette.primary.main, mt: 3 }}>
                  3. Example Usage in Conversations
                </Typography>
                <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05), p: 2, borderRadius: 2, border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}` }}>
                  <Typography sx={{ fontWeight: 'bold' }}>User:</Typography>
                  <Typography paragraph>
                    Can you check the weather in San Francisco?
                  </Typography>
                  <Typography sx={{ fontWeight: 'bold' }}>Agent:</Typography>
                  <Typography paragraph>
                    I'll check that for you. Let me call the weather API...
                  </Typography>
                  <Typography sx={{ fontStyle: 'italic', color: 'text.secondary', fontSize: '0.85rem' }}>
                    [Agent calls the integrated weather API endpoint]
                  </Typography>
                  <Typography paragraph sx={{ mt: 1 }}>
                    The current temperature in San Francisco is 68°F with partly cloudy skies. The forecast shows a high of 72°F and a low of 58°F today.
                  </Typography>
                </Box>
                
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: theme.palette.primary.main, mt: 3 }}>
                  4. Authentication
                </Typography>
                <Typography paragraph>
                  If your APIs require authentication, you'll need to:
                </Typography>
                <ol>
                  <li>
                    <Typography>Ensure authentication details are included in your OpenAPI specification</Typography>
                  </li>
                  <li>
                    <Typography>Provide your API key when uploading the specification (you can input it in the dialog that appears after selecting a file)</Typography>
                  </li>
                  <li>
                    <Typography>For sensitive APIs, consider using environment variables or secure credential storage</Typography>
                  </li>
                </ol>
                
                <Alert severity="info" sx={{ mt: 3 }}>
                  <Typography variant="body2">
                    Note: Your agent will automatically manage API rate limits, handle errors, and retry failed requests when appropriate.
                  </Typography>
                </Alert>
              </Box>
            </TabPanel>
          </Paper>
        </Box>
      </Fade>
      
      {/* API Name Dialog */}
      <Dialog open={showNameDialog} onClose={handleUploadCancel}>
        <DialogTitle>API Integration Name</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Please provide a name for this API integration.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="name"
            label="API Name"
            type="text"
            fullWidth
            variant="outlined"
            value={apiName}
            onChange={(e) => setApiName(e.target.value)}
          />
          <TextField
            margin="dense"
            id="apiKey"
            label="API Key (Optional)"
            type="password"
            fullWidth
            variant="outlined"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            helperText="If your API requires authentication, you can provide the API key here"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleUploadCancel}>Cancel</Button>
          <Button onClick={handleUploadConfirm} variant="contained" color="primary">
            Upload
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog
        open={showConfirmDelete}
        onClose={() => setShowConfirmDelete(false)}
      >
        <DialogTitle>
          Delete API Specification
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the API specification "{apiToDelete?.name}"? 
            This will remove the API integration from your agent.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConfirmDelete(false)}>
            Cancel
          </Button>
          <Button onClick={confirmDeleteApiSpec} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Notification */}
      <Snackbar
        open={notification.open}
        autoHideDuration={3000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ApiIntegration; 