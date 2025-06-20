/**
 * Deployment Service
 * 
 * Service for managing optimized agent deployments via the deployment service API
 * and Firestore for deployment history
 */

import { apiConfig } from '../config/apiConfig';
import { db } from '../../utils/firebase';
import { collection, query, where, orderBy, getDocs, doc, getDoc, onSnapshot } from 'firebase/firestore';

const DEPLOYMENT_SERVICE_URL = process.env.REACT_APP_DEPLOYMENT_SERVICE_URL || 'http://0.0.0.0:8080';

class DeploymentService {
  constructor() {
    this.baseURL = DEPLOYMENT_SERVICE_URL;
  }

  /**
   * Deploy an agent using optimized deployment
   */
  async deployAgent(agentId, options = {}) {
    try {
      const deploymentRequest = {
        agent_id: agentId,
        project_id: process.env.REACT_APP_GCP_PROJECT_ID || 'alchemist-e69bb',
        region: options.region || 'us-central1',
        webhook_url: options.webhookUrl,
        priority: options.priority || 5
      };

      const response = await fetch(`${DEPLOYMENT_SERVICE_URL}/api/deploy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deploymentRequest)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Deployment failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error deploying agent:', error);
      throw error;
    }
  }

  /**
   * Get deployment status and progress - checks Firestore first, falls back to API
   */
  async getDeploymentStatus(deploymentId) {
    try {
      // First try to get from Firestore
      const deploymentDoc = doc(db, 'agent_deployments', deploymentId);
      const docSnapshot = await getDoc(deploymentDoc);
      
      if (docSnapshot.exists()) {
        const data = docSnapshot.data();
        return {
          deployment_id: deploymentId,
          ...data,
          // Convert Firestore timestamps to ISO strings for consistency
          created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
          updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
        };
      }
    } catch (error) {
      console.error('Error getting deployment status:', error);
      throw error;
    }
  }

  /**
   * List all deployments with optional filtering - uses Firestore directly
   */
  async listDeployments(options = {}) {
    try {
      const deploymentsRef = collection(db, 'agent_deployments');
      let q = query(deploymentsRef, orderBy('created_at', 'desc'));
      
      // Apply filters
      if (options.agentId) {
        q = query(deploymentsRef, where('agent_id', '==', options.agentId), orderBy('created_at', 'desc'));
      }
      
      if (options.status) {
        // If both agentId and status are specified, we need to use a compound query
        if (options.agentId) {
          q = query(
            deploymentsRef, 
            where('agent_id', '==', options.agentId),
            where('status', '==', options.status),
            orderBy('created_at', 'desc')
          );
        } else {
          q = query(deploymentsRef, where('status', '==', options.status), orderBy('created_at', 'desc'));
        }
      }
      
      const querySnapshot = await getDocs(q);
      const deployments = [];
      
      querySnapshot.forEach((doc) => {
        const data = doc.data();
        deployments.push({
          deployment_id: doc.id,
          ...data,
          // Convert Firestore timestamps to ISO strings for consistency
          created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
          updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
        });
      });
      
      // Apply limit after fetching (since Firestore limit() doesn't work well with where clauses)
      const limitedDeployments = options.limit ? deployments.slice(0, options.limit) : deployments;
      
      return {
        deployments: limitedDeployments,
        total: deployments.length
      };
    } catch (error) {
      console.error('Error listing deployments from Firestore:', error);
      throw error;
    }
  }

  /**
   * Cancel a deployment
   */
  async cancelDeployment(deploymentId) {
    try {
      const response = await fetch(`${this.baseURL}/api/deployment/${deploymentId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`Failed to cancel deployment: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error canceling deployment:', error);
      throw error;
    }
  }

  /**
   * Get deployment queue status
   */
  async getQueueStatus() {
    try {
      const response = await fetch(`${this.baseURL}/api/queue`);
      
      if (!response.ok) {
        throw new Error(`Failed to get queue status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error getting queue status:', error);
      throw error;
    }
  }

  /**
   * Get deployment service health
   */
  async getServiceHealth() {
    try {
      const response = await fetch(`${this.baseURL}/`);
      
      if (!response.ok) {
        throw new Error(`Service health check failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error checking service health:', error);
      throw error;
    }
  }

  /**
   * Poll deployment status until completion using Firestore real-time listener
   */
  async pollDeploymentStatus(deploymentId, onProgress = null, options = {}) {
    const { 
      timeoutMs = 600000  // 10 minutes
    } = options;

    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      const deploymentDoc = doc(db, 'agent_deployments', deploymentId);
      
      // Set up real-time listener
      const unsubscribe = onSnapshot(deploymentDoc, (docSnapshot) => {
        try {
          // Check timeout
          if (Date.now() - startTime > timeoutMs) {
            unsubscribe();
            reject(new Error('Deployment polling timed out'));
            return;
          }

          if (!docSnapshot.exists()) {
            // Document doesn't exist yet, continue listening
            return;
          }

          const data = docSnapshot.data();
          const status = {
            deployment_id: deploymentId,
            ...data,
            // Convert Firestore timestamps to ISO strings for consistency
            created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
            updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
          };
          console.log(status)
          
          // Call progress callback if provided
          if (onProgress) {
            onProgress(JSON.parse(JSON.stringify(status)));
          }

          // Check if deployment is complete
          if (status.status === 'completed') {
            unsubscribe();
            resolve(status);
            return;
          }

          // Check if deployment failed
          if (status.status === 'failed' || status.status === 'cancelled') {
            unsubscribe();
            reject(new Error(String(status.error_message || `Deployment ${status.status}`)));
            return;
          }

          // Continue listening for other statuses

        } catch (error) {
          unsubscribe();
          reject(error);
        }
      }, (error) => {
        console.error('Firestore listener error:', error);
        reject(error);
      });

      // Set up timeout to clean up listener
      setTimeout(() => {
        unsubscribe();
        reject(new Error('Deployment polling timed out'));
      }, timeoutMs);
    });
  }
  /**
   * Subscribe to deployment updates in real-time
   */
  subscribeToDeploymentUpdates(agentId, onUpdate, onError = null) {
    try {
      const deploymentsRef = collection(db, 'agent_deployments');
      const q = query(
        deploymentsRef, 
        where('agent_id', '==', agentId),
        orderBy('created_at', 'desc')
      );
      
      const unsubscribe = onSnapshot(q, (querySnapshot) => {
        const deployments = [];
        querySnapshot.forEach((doc) => {
          const data = doc.data();
          deployments.push({
            deployment_id: doc.id,
            ...data,
            // Convert Firestore timestamps to ISO strings for consistency
            created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
            updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
          });
        });
        
        onUpdate(deployments);
      }, (error) => {
        console.error('Deployment subscription error:', error);
        if (onError) {
          onError(error);
        }
      });
      
      return unsubscribe;
    } catch (error) {
      console.error('Error setting up deployment subscription:', error);
      if (onError) {
        onError(error);
      }
      return () => {}; // Return empty function as fallback
    }
  }

  /**
   * Get a single deployment by ID from Firestore
   */
  async getDeployment(deploymentId) {
    try {
      const deploymentDoc = doc(db, 'agent_deployments', deploymentId);
      const docSnapshot = await getDoc(deploymentDoc);
      
      if (!docSnapshot.exists()) {
        throw new Error('Deployment not found');
      }
      
      const data = docSnapshot.data();
      return {
        deployment_id: deploymentId,
        ...data,
        // Convert Firestore timestamps to ISO strings for consistency
        created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
        updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
      };
    } catch (error) {
      console.error('Error getting deployment:', error);
      throw error;
    }
  }
}

// Create singleton instance
const deploymentService = new DeploymentService();

export default deploymentService;

// Named exports for convenience - bind methods to maintain context
export const deployAgent = deploymentService.deployAgent.bind(deploymentService);
export const getDeploymentStatus = deploymentService.getDeploymentStatus.bind(deploymentService);
export const listDeployments = deploymentService.listDeployments.bind(deploymentService);
export const cancelDeployment = deploymentService.cancelDeployment.bind(deploymentService);
export const getQueueStatus = deploymentService.getQueueStatus.bind(deploymentService);
export const getServiceHealth = deploymentService.getServiceHealth.bind(deploymentService);
export const pollDeploymentStatus = deploymentService.pollDeploymentStatus.bind(deploymentService);
export const subscribeToDeploymentUpdates = deploymentService.subscribeToDeploymentUpdates.bind(deploymentService);
export const getDeployment = deploymentService.getDeployment.bind(deploymentService);