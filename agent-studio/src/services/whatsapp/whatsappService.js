/**
 * Legacy WhatsApp Service - DEPRECATED
 * 
 * This service is deprecated in favor of the simplified webhook service.
 * Use whatsappWebhookService.js for new integrations.
 * 
 * @deprecated Use whatsappWebhookService.js instead
 */

import { api } from '../config/apiConfig';
import { db } from '../../utils/firebase';
import { 
  collection, 
  doc, 
  addDoc, 
  updateDoc, 
  deleteDoc, 
  getDocs, 
  getDoc, 
  query, 
  where, 
  orderBy,
  onSnapshot
} from 'firebase/firestore';

class WhatsAppService {
  constructor() {
    this.baseURL = process.env.REACT_APP_WHATSAPP_SERVICE_URL || 'http://localhost:8081';
  }

  /**
   * Create a new WhatsApp integration for a deployed agent
   */
  async createWhatsAppIntegration(deploymentId, config) {
    try {
      const integrationData = {
        deployment_id: deploymentId,
        phone_number: config.phoneNumber,
        business_account_id: config.businessAccountId,
        access_token: config.accessToken,
        webhook_verify_token: config.webhookVerifyToken,
        webhook_url: `${config.serviceUrl}/webhook/whatsapp`,
        status: 'pending',
        created_at: new Date(),
        updated_at: new Date()
      };

      // Store integration in Firestore
      const integrationsRef = collection(db, 'whatsapp_integrations');
      const docRef = await addDoc(integrationsRef, integrationData);

      // Call backend service to set up WhatsApp webhook
      const response = await fetch(`${this.baseURL}/api/whatsapp/setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          integration_id: docRef.id,
          ...integrationData
        })
      });

      if (!response.ok) {
        // If backend setup fails, delete the Firestore document
        await deleteDoc(docRef);
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `WhatsApp setup failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Update the integration with webhook setup results
      await updateDoc(docRef, {
        status: 'connected',
        webhook_url: result.webhook_url,
        updated_at: new Date()
      });

      return {
        id: docRef.id,
        ...integrationData,
        status: 'connected',
        webhook_url: result.webhook_url
      };
    } catch (error) {
      console.error('Error creating WhatsApp integration:', error);
      throw error;
    }
  }

  /**
   * Get all WhatsApp integrations for an agent
   */
  async getWhatsAppIntegrations(agentId) {
    try {
      const integrationsRef = collection(db, 'whatsapp_integrations');
      const q = query(
        integrationsRef,
        where('agent_id', '==', agentId),
        orderBy('created_at', 'desc')
      );
      
      const querySnapshot = await getDocs(q);
      const integrations = [];
      
      querySnapshot.forEach((doc) => {
        const data = doc.data();
        integrations.push({
          id: doc.id,
          ...data,
          created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
          updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
        });
      });
      
      return integrations;
    } catch (error) {
      console.error('Error getting WhatsApp integrations:', error);
      throw error;
    }
  }

  /**
   * Get a specific WhatsApp integration by deployment ID
   */
  async getWhatsAppIntegrationByDeployment(deploymentId) {
    try {
      const integrationsRef = collection(db, 'whatsapp_integrations');
      const q = query(integrationsRef, where('deployment_id', '==', deploymentId));
      
      const querySnapshot = await getDocs(q);
      
      if (querySnapshot.empty) {
        return null;
      }
      
      const doc = querySnapshot.docs[0];
      const data = doc.data();
      
      return {
        id: doc.id,
        ...data,
        created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
        updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
      };
    } catch (error) {
      console.error('Error getting WhatsApp integration by deployment:', error);
      throw error;
    }
  }

  /**
   * Update WhatsApp integration configuration
   */
  async updateWhatsAppIntegration(integrationId, updates) {
    try {
      const integrationRef = doc(db, 'whatsapp_integrations', integrationId);
      
      const updateData = {
        ...updates,
        updated_at: new Date()
      };
      
      await updateDoc(integrationRef, updateData);
      
      // Get updated document
      const updatedDoc = await getDoc(integrationRef);
      if (!updatedDoc.exists()) {
        throw new Error('Integration not found after update');
      }
      
      const data = updatedDoc.data();
      return {
        id: integrationId,
        ...data,
        created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
        updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
      };
    } catch (error) {
      console.error('Error updating WhatsApp integration:', error);
      throw error;
    }
  }

  /**
   * Delete WhatsApp integration
   */
  async deleteWhatsAppIntegration(integrationId) {
    try {
      // First get the integration to clean up backend
      const integrationRef = doc(db, 'whatsapp_integrations', integrationId);
      const integrationDoc = await getDoc(integrationRef);
      
      if (integrationDoc.exists()) {
        const integrationData = integrationDoc.data();
        
        // Call backend to clean up webhook
        try {
          await fetch(`${this.baseURL}/api/whatsapp/cleanup`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              integration_id: integrationId,
              phone_number: integrationData.phone_number,
              business_account_id: integrationData.business_account_id
            })
          });
        } catch (backendError) {
          console.warn('Backend cleanup failed:', backendError);
          // Continue with Firestore deletion even if backend cleanup fails
        }
      }
      
      // Delete from Firestore
      await deleteDoc(integrationRef);
      
      return { success: true };
    } catch (error) {
      console.error('Error deleting WhatsApp integration:', error);
      throw error;
    }
  }

  /**
   * Test WhatsApp integration by sending a test message
   */
  async testWhatsAppIntegration(integrationId, testPhoneNumber) {
    try {
      const response = await fetch(`${this.baseURL}/api/whatsapp/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          integration_id: integrationId,
          test_phone_number: testPhoneNumber,
          message: 'Hello! This is a test message from your AI agent. WhatsApp integration is working correctly.'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Test failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error testing WhatsApp integration:', error);
      throw error;
    }
  }

  /**
   * Get WhatsApp integration status
   */
  async getWhatsAppStatus(integrationId) {
    try {
      const response = await fetch(`${this.baseURL}/api/whatsapp/status/${integrationId}`);
      
      if (!response.ok) {
        throw new Error(`Status check failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error getting WhatsApp status:', error);
      throw error;
    }
  }

  /**
   * Subscribe to WhatsApp integration updates in real-time
   */
  subscribeToWhatsAppUpdates(agentId, onUpdate, onError = null) {
    try {
      const integrationsRef = collection(db, 'whatsapp_integrations');
      const q = query(
        integrationsRef,
        where('agent_id', '==', agentId),
        orderBy('created_at', 'desc')
      );
      
      const unsubscribe = onSnapshot(q, (querySnapshot) => {
        const integrations = [];
        querySnapshot.forEach((doc) => {
          const data = doc.data();
          integrations.push({
            id: doc.id,
            ...data,
            created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
            updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at
          });
        });
        
        onUpdate(integrations);
      }, (error) => {
        console.error('WhatsApp subscription error:', error);
        if (onError) {
          onError(error);
        }
      });
      
      return unsubscribe;
    } catch (error) {
      console.error('Error setting up WhatsApp subscription:', error);
      if (onError) {
        onError(error);
      }
      return () => {}; // Return empty function as fallback
    }
  }

  /**
   * Validate WhatsApp Business API credentials
   */
  async validateCredentials(config) {
    try {
      const response = await fetch(`${this.baseURL}/api/whatsapp/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          business_account_id: config.businessAccountId,
          access_token: config.accessToken,
          phone_number: config.phoneNumber
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Validation failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error validating WhatsApp credentials:', error);
      throw error;
    }
  }
}

// Create singleton instance
const whatsappService = new WhatsAppService();

export default whatsappService;

// Named exports for convenience
export const createWhatsAppIntegration = whatsappService.createWhatsAppIntegration.bind(whatsappService);
export const getWhatsAppIntegrations = whatsappService.getWhatsAppIntegrations.bind(whatsappService);
export const getWhatsAppIntegrationByDeployment = whatsappService.getWhatsAppIntegrationByDeployment.bind(whatsappService);
export const updateWhatsAppIntegration = whatsappService.updateWhatsAppIntegration.bind(whatsappService);
export const deleteWhatsAppIntegration = whatsappService.deleteWhatsAppIntegration.bind(whatsappService);
export const testWhatsAppIntegration = whatsappService.testWhatsAppIntegration.bind(whatsappService);
export const getWhatsAppStatus = whatsappService.getWhatsAppStatus.bind(whatsappService);
export const subscribeToWhatsAppUpdates = whatsappService.subscribeToWhatsAppUpdates.bind(whatsappService);
export const validateCredentials = whatsappService.validateCredentials.bind(whatsappService);