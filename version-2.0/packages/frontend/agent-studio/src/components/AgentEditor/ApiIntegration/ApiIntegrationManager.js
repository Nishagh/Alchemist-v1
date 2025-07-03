/**
 * API Integration Manager
 * 
 * Main component for managing API integrations and MCP server deployments
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  Fade
} from '@mui/material';
import {
  Api as ApiIcon
} from '@mui/icons-material';
import { 
  uploadApiSpecification,
  deleteApiIntegration
} from '../../../services';
import { 
  deployMcpServer,
  subscribeToDeploymentStatus
} from '../../../services/mcpServer/mcpServerService';
import { createNotification } from '../../shared/NotificationSystem';
import ApiUploadPanel from './ApiUploadPanel';
import McpDeploymentStatus from './McpDeploymentStatus';
import { useAgentState } from '../../../hooks/useAgentState';
import { collection, query, where, orderBy, onSnapshot } from 'firebase/firestore';
import { db } from '../../../utils/firebase';
import { useAuth } from '../../../utils/AuthContext';

const ApiIntegrationManager = ({ 
  onNotification,
  disabled = false 
}) => {
  const { agent, agentId } = useAgentState();
  const { currentUser } = useAuth();
  const [apiFiles, setApiFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [error, setError] = useState('');
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  const [integrationSummary, setIntegrationSummary] = useState(null);
  const [deploymentHistory, setDeploymentHistory] = useState([]);
  const [currentDeploymentId, setCurrentDeploymentId] = useState(null);
  const [deploymentUnsubscribe, setDeploymentUnsubscribe] = useState(null);

  // Load API integrations from Firestore agent document
  useEffect(() => {
    const loadApiDataFromFirestore = () => {
    try {
      setLoading(true);
      setError('');
      
      console.log('Loading API integration data from Firestore:', agent);
      
      // Extract API files from Firestore agent document
      const firestoreApiFiles = [];
      
      // Add OpenAPI spec if exists
      if (agent.openapi_spec) {
        firestoreApiFiles.push({
          id: 'openapi_spec',
          filename: agent.openapi_spec.filename || 'OpenAPI Specification',
          name: agent.openapi_spec.filename || 'OpenAPI Specification',
          type: 'OpenAPI',
          size: agent.openapi_spec.file_size || 0,
          uploaded_at: agent.openapi_spec.uploaded_at,
          created_at: agent.openapi_spec.uploaded_at,
          status: agent.openapi_spec.status || 'uploaded',
          description: 'OpenAPI 3.0+ specification',
          public_url: agent.openapi_spec.public_url
        });
      }
      
      // Add MCP config if exists
      if (agent.mcp_config) {
        firestoreApiFiles.push({
          id: 'mcp_config',
          filename: agent.mcp_config.filename || 'MCP Configuration',
          name: agent.mcp_config.filename || 'MCP Configuration',
          type: 'MCP',
          size: agent.mcp_config.file_size || 0,
          uploaded_at: agent.mcp_config.uploaded_at,
          created_at: agent.mcp_config.uploaded_at,
          status: agent.mcp_config.status || 'uploaded',
          description: 'Model Context Protocol configuration',
          public_url: agent.mcp_config.public_url
        });
      }
      
      console.log('Extracted API files from Firestore:', firestoreApiFiles);
      setApiFiles(firestoreApiFiles);
      
      // Set integration summary from agent document
      if (agent.api_integration) {
        console.log('Loaded integration summary from Firestore:', agent.api_integration);
        setIntegrationSummary(agent.api_integration);
      } else {
        setIntegrationSummary(null);
      }
      
    } catch (err) {
      console.error('Error loading API data from Firestore:', err);
      setError('Failed to load API integration data');
      setApiFiles([]);
      setIntegrationSummary(null);
    } finally {
      setLoading(false);
    }
    };

    if (agent) {
      loadApiDataFromFirestore();
    } else if (!agentId) {
      setLoading(false);
    }
  }, [agent, agentId]);

  // Listen to MCP deployment requests from the new mcp_deployments collection
  useEffect(() => {
    if (agentId && currentUser) {
      console.log('Setting up MCP deployment listener for agent:', agentId);
      
      // Listen to mcp_deployments collection for this specific agent
      const deploymentsRef = collection(db, 'mcp_deployments');
      const deploymentsQuery = query(
        deploymentsRef,
        where('agent_id', '==', agentId),
        orderBy('created_at', 'desc')
      );
      
      const unsubscribe = onSnapshot(deploymentsQuery, (snapshot) => {
        const agentDeployments = [];
        
        snapshot.forEach((doc) => {
          const deploymentData = { id: doc.id, ...doc.data() };
          agentDeployments.push(deploymentData);
        });
        
        console.log('MCP deployment history updated for agent:', agentId, agentDeployments);
        setDeploymentHistory(agentDeployments);
        
        // Update deployment status based on latest deployment for this agent
        if (agentDeployments.length > 0) {
          const latestDeployment = agentDeployments[0];
          console.log('Latest MCP deployment:', latestDeployment);
          
          // Set current deployment ID for real-time tracking
          if (latestDeployment.status === 'queued' || latestDeployment.status === 'processing') {
            setCurrentDeploymentId(latestDeployment.id);
            setDeploying(true);
          } else {
            setDeploying(false);
            // Keep the deployment ID if recently completed for status display
            if (latestDeployment.status === 'deployed' || latestDeployment.status === 'failed') {
              setCurrentDeploymentId(latestDeployment.id);
            }
          }
          
          setDeploymentStatus({
            status: latestDeployment.status,
            deployment_id: latestDeployment.id,
            progress: latestDeployment.progress || 0,
            current_step: latestDeployment.current_step,
            error_message: latestDeployment.error_message,
            service_url: latestDeployment.service_url
          });
        }
      }, (error) => {
        console.error('Error listening to MCP deployment history:', error);
      });
      
      // Return cleanup function
      return () => {
        console.log('Cleaning up MCP deployment listener');
        unsubscribe();
      };
    }
  }, [agentId, currentUser]);

  // Cleanup deployment listeners on unmount
  useEffect(() => {
    return () => {
      if (deploymentUnsubscribe) {
        console.log('Cleaning up deployment status listener on unmount');
        deploymentUnsubscribe();
      }
    };
  }, [deploymentUnsubscribe]);

  const handleApiUpload = async (file, apiName) => {
    if (!file) return;

    setUploading(true);

    try {
      console.log(`Uploading API specification: ${file.name}`);
      const response = await uploadApiSpecification(agentId, file);
      
      if (response) {
        // Reload API files to get the updated list from Firestore
        // The useAgentState hook will automatically update when Firestore changes
        
        onNotification?.(createNotification(
          `Successfully uploaded ${apiName || file.name}`,
          'success'
        ));
      }

    } catch (error) {
      console.error('Error uploading API specification:', error);
      onNotification?.(createNotification(
        `Failed to upload ${file.name}. Please try again.`,
        'error'
      ));
    } finally {
      setUploading(false);
    }
  };

  const handleApiDelete = async (integrationId, fileName) => {
    try {
      console.log(`Deleting API integration: ${fileName} (ID: ${integrationId})`);
      await deleteApiIntegration(agentId, integrationId);
      
      // Remove the integration from the local state
      setApiFiles(prev => prev.filter(file => file.id !== integrationId));
      
      onNotification?.(createNotification(
        `Successfully deleted ${fileName}`,
        'success'
      ));
    } catch (error) {
      console.error('Error deleting API integration:', error);
      onNotification?.(createNotification(
        `Failed to delete ${fileName}. Please try again.`,
        'error'
      ));
    }
  };

  const handleDeploy = async () => {
    setDeploying(true);

    try {
      console.log(`Creating MCP deployment request for agent ${agentId}`);
      
      // Use the new Firestore-based deployment service
      const response = await deployMcpServer(agentId);
      
      if (response && response.deployment_id) {
        // Set the current deployment ID for real-time tracking
        setCurrentDeploymentId(response.deployment_id);
        
        // Initial status will be updated by the Firestore listener
        setDeploymentStatus({
          status: 'queued',
          deployment_id: response.deployment_id,
          progress: 0,
          current_step: 'Deployment request created'
        });
        
        onNotification?.(createNotification(
          'MCP deployment request created successfully',
          'success'
        ));
        
        // Note: No polling needed - real-time updates via Firestore listeners
        console.log('MCP deployment request created, listening for real-time updates...');
      }

    } catch (error) {
      console.error('Error creating MCP deployment request:', error);
      onNotification?.(createNotification(
        'Failed to create deployment request. Please try again.',
        'error'
      ));
      setDeploying(false);
    }
  };

  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 8 
        }}
      >
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          Loading API integrations...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Sticky Header */}
      <Box sx={{ 
        position: 'sticky',
        top: 0,
        zIndex: 100,
        p: 3,
        borderBottom: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        backdropFilter: 'blur(8px)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <ApiIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
            API Integration
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Upload API specifications and deploy MCP servers to extend your agent's capabilities
        </Typography>
      </Box>

      {/* Error Display */}
      {error && (
        <Fade in={true}>
          <Alert severity="error" sx={{ m: 3, mb: 0 }} onClose={() => setError('')}>
            {error}
          </Alert>
        </Fade>
      )}

      {/* Two Panel Layout */}
      <Box sx={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: { xs: 'column', md: 'row' },
        gap: 3, 
        p: 3, 
        overflow: 'hidden', 
        minHeight: 0 
      }}>
        {/* Left Panel - API Upload and Management */}
        <Box sx={{ flex: 1, minHeight: { xs: '300px', md: 0 } }}>
          <ApiUploadPanel
            agentId={agentId}
            apiFiles={apiFiles}
            onApiUpload={handleApiUpload}
            onApiDelete={handleApiDelete}
            uploading={uploading}
            disabled={disabled}
          />
        </Box>

        {/* Right Panel - Deployment Status */}
        <Box sx={{ flex: 1, minHeight: { xs: '300px', md: 0 } }}>
          <McpDeploymentStatus
            agentId={agentId}
            deploymentStatus={deploymentStatus}
            integrationSummary={integrationSummary}
            deploymentHistory={deploymentHistory}
            currentDeploymentId={currentDeploymentId}
            onDeploy={handleDeploy}
            deploying={deploying}
            disabled={disabled}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default ApiIntegrationManager;