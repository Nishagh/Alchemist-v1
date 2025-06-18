/**
 * WhatsApp Business API Service
 * 
 * Service for managing WhatsApp Business accounts through direct WhatsApp Business API
 * Handles automated account creation, phone number provisioning, and verification
 */

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
    // WhatsApp Business API configuration
    this.baseURL = process.env.REACT_APP_WHATSAPP_SERVICE_URL || 'http://localhost:8000';
    this.apiKey = process.env.REACT_APP_WHATSAPP_API_KEY;
  }

  /**
   * Initiate WhatsApp Business account creation with just a phone number
   */
  async createManagedWhatsAppAccount(deploymentId, phoneNumber, userDetails = {}) {
    try {
      const accountRequest = {
        deployment_id: deploymentId,
        phone_number: phoneNumber,
        business_name: userDetails.businessName || 'AI Agent Business',
        business_industry: userDetails.industry || 'Technology',
        business_description: userDetails.description || 'AI-powered customer service',
        webhook_url: `${this.baseURL}/api/webhook/whatsapp`,
        agent_webhook_url: userDetails.agentWebhookUrl || `${userDetails.serviceUrl}/api/webhook/whatsapp`,
        provider: 'whatsapp',
        created_at: new Date(),
        status: 'initializing'
      };

      // Store initial account request in Firestore
      const accountsRef = collection(db, 'whatsapp_managed_accounts');
      const docRef = await addDoc(accountsRef, accountRequest);

      // Call WhatsApp Business API service to create account
      const response = await fetch(`${this.baseURL}/api/bsp/create-account`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        },
        body: JSON.stringify({
          account_id: docRef.id,
          phone_number: phoneNumber,
          business_profile: {
            name: accountRequest.business_name,
            industry: accountRequest.business_industry,
            description: accountRequest.business_description
          },
          webhook_config: {
            url: accountRequest.webhook_url,
            events: ['messages', 'message_deliveries', 'message_reads']
          },
          agent_webhook_url: accountRequest.agent_webhook_url
        })
      });

      if (!response.ok) {
        // If BSP creation fails, clean up Firestore
        await deleteDoc(docRef);
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Account creation failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Update Firestore with BSP response
      await updateDoc(docRef, {
        bsp_account_id: result.account_id,
        bsp_sender_id: result.sender_id,
        verification_required: result.verification_required,
        verification_methods: result.verification_methods || ['sms', 'voice'],
        status: result.verification_required ? 'verification_pending' : 'active',
        updated_at: new Date()
      });

      return {
        account_id: docRef.id,
        bsp_account_id: result.account_id,
        sender_id: result.sender_id,
        phone_number: phoneNumber,
        verification_required: result.verification_required,
        verification_methods: result.verification_methods,
        status: result.verification_required ? 'verification_pending' : 'active'
      };
    } catch (error) {
      console.error('Error creating managed WhatsApp account:', error);
      throw error;
    }
  }

  /**
   * Verify phone number ownership
   */
  async verifyPhoneNumber(accountId, verificationCode, method = 'sms') {
    try {
      const response = await fetch(`${this.baseURL}/api/bsp/verify-phone`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        },
        body: JSON.stringify({
          account_id: accountId,
          verification_code: verificationCode,
          verification_method: method
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Verification failed: ${response.status}`);
      }

      const result = await response.json();

      // Update Firestore account status
      const accountRef = doc(db, 'whatsapp_managed_accounts', accountId);
      await updateDoc(accountRef, {
        status: result.verified ? 'active' : 'verification_failed',
        verified_at: result.verified ? new Date() : null,
        verification_attempts: result.attempts || 1,
        updated_at: new Date()
      });

      return {
        verified: result.verified,
        account_id: accountId,
        status: result.verified ? 'active' : 'verification_failed',
        message: result.message
      };
    } catch (error) {
      console.error('Error verifying phone number:', error);
      throw error;
    }
  }

  /**
   * Request new verification code
   */
  async requestVerificationCode(accountId, method = 'sms') {
    try {
      const response = await fetch(`${this.baseURL}/api/bsp/request-verification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        },
        body: JSON.stringify({
          account_id: accountId,
          verification_method: method
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Verification request failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Update Firestore with verification attempt
      const accountRef = doc(db, 'whatsapp_managed_accounts', accountId);
      await updateDoc(accountRef, {
        last_verification_request: new Date(),
        verification_method_used: method,
        updated_at: new Date()
      });

      return {
        success: true,
        method: method,
        expires_in: result.expires_in || 300, // 5 minutes default
        attempts_remaining: result.attempts_remaining
      };
    } catch (error) {
      console.error('Error requesting verification code:', error);
      throw error;
    }
  }

  /**
   * Get managed account details
   */
  async getManagedAccount(accountId) {
    try {
      const accountRef = doc(db, 'whatsapp_managed_accounts', accountId);
      const accountDoc = await getDoc(accountRef);
      
      if (!accountDoc.exists()) {
        throw new Error('Managed account not found');
      }
      
      const data = accountDoc.data();
      return {
        id: accountId,
        ...data,
        created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
        updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at,
        verified_at: data.verified_at?.toDate?.()?.toISOString() || data.verified_at
      };
    } catch (error) {
      console.error('Error getting managed account:', error);
      throw error;
    }
  }

  /**
   * Get managed account by deployment ID
   */
  async getManagedAccountByDeployment(deploymentId) {
    try {
      const accountsRef = collection(db, 'whatsapp_managed_accounts');
      const q = query(accountsRef, where('deployment_id', '==', deploymentId));
      
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
        updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at,
        verified_at: data.verified_at?.toDate?.()?.toISOString() || data.verified_at
      };
    } catch (error) {
      console.error('Error getting managed account by deployment:', error);
      throw error;
    }
  }

  /**
   * Test managed account messaging
   */
  async testManagedAccount(accountId, testPhoneNumber, message = null) {
    try {
      const defaultMessage = "Hello! This is a test message from your AI agent's WhatsApp integration. Everything is working correctly! 🤖";
      
      const response = await fetch(`${this.baseURL}/api/bsp/send-test-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        },
        body: JSON.stringify({
          account_id: accountId,
          to: testPhoneNumber,
          message: message || defaultMessage
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Test message failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Update Firestore with test info
      const accountRef = doc(db, 'whatsapp_managed_accounts', accountId);
      await updateDoc(accountRef, {
        last_test_sent: new Date(),
        last_test_recipient: testPhoneNumber,
        updated_at: new Date()
      });

      return {
        success: true,
        message_id: result.message_id,
        status: result.status,
        sent_to: testPhoneNumber
      };
    } catch (error) {
      console.error('Error testing managed account:', error);
      throw error;
    }
  }

  /**
   * Delete managed account
   */
  async deleteManagedAccount(accountId) {
    try {
      // Get account details first
      const account = await this.getManagedAccount(accountId);
      
      // Call BSP service to clean up
      try {
        await fetch(`${this.baseURL}/api/bsp/delete-account`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`,
            'X-Account-SID': this.accountSid
          },
          body: JSON.stringify({
            account_id: accountId,
            bsp_account_id: account.bsp_account_id,
            sender_id: account.bsp_sender_id
          })
        });
      } catch (bspError) {
        console.warn('BSP cleanup failed:', bspError);
        // Continue with Firestore deletion even if BSP cleanup fails
      }
      
      // Delete from Firestore
      const accountRef = doc(db, 'whatsapp_managed_accounts', accountId);
      await deleteDoc(accountRef);
      
      return { success: true };
    } catch (error) {
      console.error('Error deleting managed account:', error);
      throw error;
    }
  }

  /**
   * Get account status and health
   */
  async getAccountHealth(accountId) {
    try {
      const response = await fetch(`${this.baseURL}/api/bsp/account-health/${accountId}`, {
        headers: {
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        }
      });

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error checking account health:', error);
      throw error;
    }
  }

  /**
   * Subscribe to managed account updates
   */
  subscribeManagedAccountUpdates(deploymentId, onUpdate, onError = null) {
    try {
      const accountsRef = collection(db, 'whatsapp_managed_accounts');
      const q = query(
        accountsRef,
        where('deployment_id', '==', deploymentId),
        orderBy('created_at', 'desc')
      );
      
      const unsubscribe = onSnapshot(q, (querySnapshot) => {
        const accounts = [];
        querySnapshot.forEach((doc) => {
          const data = doc.data();
          accounts.push({
            id: doc.id,
            ...data,
            created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
            updated_at: data.updated_at?.toDate?.()?.toISOString() || data.updated_at,
            verified_at: data.verified_at?.toDate?.()?.toISOString() || data.verified_at
          });
        });
        
        onUpdate(accounts[0] || null); // Return the most recent account or null
      }, (error) => {
        console.error('Managed account subscription error:', error);
        if (onError) {
          onError(error);
        }
      });
      
      return unsubscribe;
    } catch (error) {
      console.error('Error setting up managed account subscription:', error);
      if (onError) {
        onError(error);
      }
      return () => {}; // Return empty function as fallback
    }
  }
}

// Create singleton instance and export
const whatsappService = new WhatsAppService();
export default whatsappService;