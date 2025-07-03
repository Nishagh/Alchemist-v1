/**
 * Deployment Service
 * 
 * Service for managing optimized agent deployments via the deployment service API
 * and Firestore for deployment history
 */

import { apiConfig } from '../config/apiConfig';
import { db, Collections, DocumentFields, StatusValues, serverTimestamp } from '../../utils/firebase';
import { collection, query, where, orderBy, getDocs, doc, getDoc, onSnapshot, updateDoc, addDoc } from 'firebase/firestore';
import { auth } from '../../utils/firebase';

const AGENT_LAUNCHER_URL = process.env.REACT_APP_AGENT_LAUNCHER_URL || 'http://0.0.0.0:8080';

class DeploymentService {
  constructor() {
    this.baseURL = AGENT_LAUNCHER_URL;
  }

  /**
   * Deploy an agent using optimized deployment
   */
  async deployAgent(agentId, options = {}) {
    try {
      // First, create the deployment document in Firestore following deploy-job.py structure
      const deploymentId = await this.createDeploymentDocument(agentId, options);
      
      const deploymentRequest = {
        agent_id: agentId,
        deployment_id: deploymentId, // Pass the deployment ID
        project_id: 'alchemist-e69bb',
        region: options.region || 'us-central1',
        webhook_url: options.webhookUrl,
        priority: options.priority || 5
      };

      const response = await fetch(`${AGENT_LAUNCHER_URL}/api/deploy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deploymentRequest)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Update deployment document with failure
        await this.updateDeploymentDocument(deploymentId, {
          status: 'failed',
          error_message: errorData.detail || `Deployment failed: ${response.status}`,
          progress: 0,
          current_step: 'Failed to initiate deployment',
          completed_at: serverTimestamp()
        });
        
        throw new Error(errorData.detail || `Deployment failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Update deployment document with successful initiation
      await this.updateDeploymentDocument(deploymentId, {
        status: 'queued',
        progress: 10,
        current_step: 'Deployment queued successfully'
      });
      
      return {
        ...result,
        deployment_id: deploymentId
      };
    } catch (error) {
      console.error('Error deploying agent:', error);
      throw error;
    }
  }

  /**
   * Create deployment document in Firestore following deploy-job.py structure
   */
  async createDeploymentDocument(agentId, options = {}) {
    try {
      const currentUser = auth.currentUser;
      const userId = currentUser?.uid;
      
      if (!userId) {
        throw new Error('User not authenticated');
      }

      const deploymentData = {
        agent_id: agentId,
        user_id: userId,
        status: 'queued',
        progress: 0,
        current_step: 'Deployment request created',
        deployment_config: {
          region: options.region || 'us-central1',
          priority: options.priority || 5,
          webhook_url: options.webhookUrl || null
        },
        progress_steps: [
          { step: 'queued', status: 'completed', message: 'Deployment request created' },
          { step: 'validating', status: 'pending', message: 'Validating deployment configuration' },
          { step: 'building', status: 'pending', message: 'Building agent container' },
          { step: 'deploying', status: 'pending', message: 'Deploying to cloud infrastructure' },
          { step: 'testing', status: 'pending', message: 'Testing deployment connectivity' }
        ],
        created_at: serverTimestamp(),
        updated_at: serverTimestamp()
      };

      const deploymentsRef = collection(db, Collections.AGENT_DEPLOYMENTS);
      const deploymentRef = await addDoc(deploymentsRef, deploymentData);
      
      console.log('Created deployment document:', deploymentRef.id);
      return deploymentRef.id;
    } catch (error) {
      console.error('Error creating deployment document:', error);
      throw error;
    }
  }

  /**
   * Update deployment document in Firestore
   */
  async updateDeploymentDocument(deploymentId, updateData) {
    try {
      const deploymentRef = doc(db, Collections.AGENT_DEPLOYMENTS, deploymentId);
      const updates = {
        ...updateData,
        updated_at: serverTimestamp()
      };
      
      await updateDoc(deploymentRef, updates);
      console.log('Updated deployment document:', deploymentId, updates);
    } catch (error) {
      console.error('Error updating deployment document:', error);
      throw error;
    }
  }

  /**
   * Update specific progress step in deployment document
   */
  async updateProgressStep(deploymentId, stepName, stepStatus, stepMessage = null) {
    try {
      const deploymentRef = doc(db, Collections.AGENT_DEPLOYMENTS, deploymentId);
      const deploymentDoc = await getDoc(deploymentRef);
      
      if (!deploymentDoc.exists()) {
        throw new Error('Deployment document not found');
      }
      
      const data = deploymentDoc.data();
      const progressSteps = [...(data.progress_steps || [])];
      
      // Find and update the specific step
      const stepIndex = progressSteps.findIndex(step => step.step === stepName);
      if (stepIndex >= 0) {
        progressSteps[stepIndex] = {
          ...progressSteps[stepIndex],
          status: stepStatus,
          message: stepMessage || progressSteps[stepIndex].message,
          updated_at: new Date().toISOString()
        };
        
        // Calculate overall progress based on completed steps
        const completedSteps = progressSteps.filter(step => step.status === 'completed').length;
        const progress = Math.round((completedSteps / progressSteps.length) * 100);
        
        await updateDoc(deploymentRef, {
          progress_steps: progressSteps,
          progress: progress,
          current_step: stepMessage || progressSteps[stepIndex].message,
          updated_at: serverTimestamp()
        });
        
        console.log(`Updated progress step ${stepName} to ${stepStatus}:`, progressSteps[stepIndex]);
      }
    } catch (error) {
      console.error('Error updating progress step:', error);
      throw error;
    }
  }

  /**
   * Get deployment status and progress - checks Firestore first, falls back to API
   */
  async getDeploymentStatus(deploymentId) {
    try {
      // First try to get from Firestore
      const deploymentDoc = doc(db, Collections.AGENT_DEPLOYMENTS, deploymentId);
      const docSnapshot = await getDoc(deploymentDoc);
      
      if (docSnapshot.exists()) {
        const data = docSnapshot.data();
        return {
          [DocumentFields.DEPLOYMENT_ID]: deploymentId,
          ...data,
          // Convert Firestore timestamps to ISO strings for consistency
          [DocumentFields.CREATED_AT]: data[DocumentFields.CREATED_AT]?.toDate?.()?.toISOString() || data[DocumentFields.CREATED_AT],
          [DocumentFields.UPDATED_AT]: data[DocumentFields.UPDATED_AT]?.toDate?.()?.toISOString() || data[DocumentFields.UPDATED_AT]
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
          if (status.status === 'completed' || status.status === 'deployed') {
            unsubscribe();
            
            // Update agent deployment status if deployment was successful
            this.updateAgentDeploymentStatus(status.agent_id, status)
              .then(() => {
                console.log('Agent deployment status updated successfully');
              })
              .catch((updateError) => {
                console.error('Failed to update agent deployment status:', updateError);
                // Don't reject the promise - deployment still succeeded
              });
            
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

  /**
   * Update agent deployment status when deployment completes successfully
   * Implements Google Cloud Run-like behavior where agent is "deployed" if any deployment succeeds
   */
  async updateAgentDeploymentStatus(agentId, deploymentData) {
    try {
      const agentDoc = doc(db, 'agents', agentId);
      
      // Check if this is the first successful deployment
      const currentDeployments = await this.listDeployments({ 
        agentId: agentId,
        status: 'completed'
      });
      
      // Also check for 'deployed' status deployments
      const deployedDeployments = await this.listDeployments({ 
        agentId: agentId,
        status: 'deployed'
      });
      
      const totalSuccessful = (currentDeployments.deployments || []).length + 
                             (deployedDeployments.deployments || []).length;
      
      // Prepare agent update data
      const agentUpdates = {
        deployment_status: 'completed',
        active_deployment_id: deploymentData.deployment_id,
        last_deployment_at: serverTimestamp(),
        updated_at: serverTimestamp()
      };
      
      // Add service URL if available
      if (deploymentData.service_url) {
        agentUpdates.service_url = deploymentData.service_url;
      }
      
      // Update agent document
      await updateDoc(agentDoc, agentUpdates);
      
      console.log(`Agent ${agentId} deployment status updated to completed with active deployment ${deploymentData.deployment_id}`);
      
      return {
        success: true,
        isFirstDeployment: totalSuccessful === 0,
        agentUpdates
      };
      
    } catch (error) {
      console.error('Error updating agent deployment status:', error);
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
export const updateAgentDeploymentStatus = deploymentService.updateAgentDeploymentStatus.bind(deploymentService);
export const createDeploymentDocument = deploymentService.createDeploymentDocument.bind(deploymentService);
export const updateDeploymentDocument = deploymentService.updateDeploymentDocument.bind(deploymentService);
export const updateProgressStep = deploymentService.updateProgressStep.bind(deploymentService);