/**
 * WhatsApp Webhook Service
 * 
 * Simplified service for existing WhatsApp Business users.
 * Only handles webhook configuration - no complex Business API setup.
 */

import { db, serverTimestamp } from '../../utils/firebase';
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
  orderBy
} from 'firebase/firestore';

class WhatsAppWebhookService {
  constructor() {
    this.collectionName = 'whatsapp_webhooks';
  }

  /**
   * Save webhook configuration for existing WhatsApp Business users
   */
  async saveWebhookConfig(agentId, config) {
    try {
      const configData = {
        agentId,
        phone_id: config.phone_id,
        access_token: config.access_token,
        verify_token: config.verify_token || 'default_verify_token',
        app_secret: config.app_secret || null, // Optional for existing users
        webhook_url: config.webhook_url,
        status: 'configured',
        created_at: serverTimestamp(),
        updated_at: serverTimestamp()
      };

      // Save to webhook configs collection
      const docRef = await addDoc(collection(db, this.collectionName), configData);
      
      // Also update the agent configuration so the deployed agent can access it
      await this.updateAgentWhatsAppConfig(agentId, {
        phone_id: config.phone_id,
        access_token: config.access_token,
        verify_token: config.verify_token || 'default_verify_token',
        app_secret: config.app_secret || null,
        enabled: true
      });
      
      return {
        id: docRef.id,
        ...configData
      };
    } catch (error) {
      console.error('Error saving WhatsApp webhook config:', error);
      throw new Error('Failed to save webhook configuration');
    }
  }

  /**
   * Update agent configuration with WhatsApp webhook settings
   */
  async updateAgentWhatsAppConfig(agentId, whatsappConfig) {
    try {
      const agentRef = doc(db, 'agents', agentId);
      
      // Update the agent configuration with WhatsApp webhook settings
      await updateDoc(agentRef, {
        'whatsapp_webhook': whatsappConfig,
        'updated_at': serverTimestamp()
      });
      
      console.log('Agent WhatsApp configuration updated');
    } catch (error) {
      console.error('Error updating agent WhatsApp config:', error);
      // Don't throw here - webhook config is still saved
    }
  }

  /**
   * Get webhook configuration for an agent
   */
  async getWebhookConfig(agentId) {
    try {
      const q = query(
        collection(db, this.collectionName),
        where('agentId', '==', agentId),
        orderBy('created_at', 'desc')
      );
      
      const querySnapshot = await getDocs(q);
      
      if (querySnapshot.empty) {
        return null;
      }
      
      const doc = querySnapshot.docs[0];
      return {
        id: doc.id,
        ...doc.data()
      };
    } catch (error) {
      console.error('Error getting WhatsApp webhook config:', error);
      throw new Error('Failed to get webhook configuration');
    }
  }

  /**
   * Update webhook configuration
   */
  async updateWebhookConfig(configId, updates) {
    try {
      const docRef = doc(db, this.collectionName, configId);
      await updateDoc(docRef, {
        ...updates,
        updated_at: serverTimestamp()
      });
      
      return true;
    } catch (error) {
      console.error('Error updating WhatsApp webhook config:', error);
      throw new Error('Failed to update webhook configuration');
    }
  }

  /**
   * Delete webhook configuration
   */
  async deleteWebhookConfig(configId) {
    try {
      // Get the config first to know which agent to update
      const configDoc = await getDoc(doc(db, this.collectionName, configId));
      if (configDoc.exists()) {
        const configData = configDoc.data();
        
        // Remove from agent configuration
        await this.updateAgentWhatsAppConfig(configData.agentId, {
          enabled: false
        });
      }
      
      // Delete the webhook config
      await deleteDoc(doc(db, this.collectionName, configId));
      return true;
    } catch (error) {
      console.error('Error deleting WhatsApp webhook config:', error);
      throw new Error('Failed to delete webhook configuration');
    }
  }

  /**
   * Generate webhook URL for deployed agent
   */
  generateWebhookUrl(agentId, deploymentUrl) {
    if (!deploymentUrl) {
      throw new Error('Deployment URL is required');
    }
    
    // Remove trailing slash if present
    const baseUrl = deploymentUrl.replace(/\/$/, '');
    return `${baseUrl}/webhook/whatsapp`;
  }

  /**
   * Test webhook configuration
   */
  async testWebhookConfig(agentId) {
    try {
      const config = await this.getWebhookConfig(agentId);
      if (!config) {
        throw new Error('No webhook configuration found');
      }

      // Simple validation
      const errors = [];
      
      if (!config.phone_id) {
        errors.push('Phone ID is required');
      }
      
      if (!config.access_token) {
        errors.push('Access Token is required');
      }
      
      if (!config.webhook_url) {
        errors.push('Webhook URL is required');
      }

      if (errors.length > 0) {
        throw new Error(`Configuration errors: ${errors.join(', ')}`);
      }

      // Test webhook URL accessibility (basic check)
      try {
        const response = await fetch(config.webhook_url, {
          method: 'GET',
          headers: {
            'User-Agent': 'WhatsApp-Webhook-Test'
          }
        });
        
        // Any response (even 404) means the endpoint is reachable
        return {
          success: true,
          message: 'Webhook configuration is valid',
          webhook_url: config.webhook_url,
          status: response.status
        };
      } catch (fetchError) {
        return {
          success: false,
          message: 'Webhook URL is not accessible',
          error: fetchError.message
        };
      }

    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.message
      };
    }
  }

  /**
   * Get setup instructions for existing WhatsApp Business users
   */
  getSetupInstructions(webhookUrl) {
    return {
      title: "Setup Instructions for Existing WhatsApp Business Users",
      steps: [
        {
          step: 1,
          title: "Get Your Credentials",
          description: "Log into your WhatsApp Business Platform account and note:",
          details: [
            "Phone Number ID (from your WhatsApp Business account)",
            "Access Token (permanent access token for your app)",
            "Verify Token (create a secure random string)"
          ]
        },
        {
          step: 2,
          title: "Configure Webhook in WhatsApp",
          description: "In your WhatsApp Business Platform:",
          details: [
            `Set Webhook URL to: ${webhookUrl}`,
            "Set Verify Token to the same value you'll enter below",
            "Subscribe to 'messages' webhook field"
          ]
        },
        {
          step: 3,
          title: "Enter Configuration",
          description: "Enter your credentials in the form below and save"
        },
        {
          step: 4,
          title: "Test Integration",
          description: "Send a test message to verify the setup is working"
        }
      ],
      notes: [
        "This setup works with your existing WhatsApp Business number",
        "No need to create new accounts or verify phone numbers",
        "Your existing WhatsApp Business features remain unchanged",
        "App Secret is optional but recommended for production use"
      ]
    };
  }
}

export default new WhatsAppWebhookService();