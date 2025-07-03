/**
 * Billing Service V2
 * 
 * New service layer for billing operations using the dedicated billing microservice
 */

import { billingApi } from '../config/apiConfig';
import { ENDPOINTS } from '../config/apiConfig';
import { getAuthToken } from '../auth/authService';

class BillingServiceV2 {
  constructor() {
    this.baseURL = '/api/v1';
  }

  /**
   * Get authenticated headers
   */
  async getHeaders() {
    const token = await getAuthToken();
    if (!token) {
      throw new Error('Authentication failed. Please sign out and sign back in.');
    }
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // ========== CREDITS BALANCE ==========

  /**
   * Get user credit balance
   */
  async getBalance() {
    try {
      const headers = await this.getHeaders();
      const response = await billingApi.get(ENDPOINTS.BILLING_CREDITS_BALANCE, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting credit balance:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get complete credits account
   */
  async getAccount() {
    try {
      const headers = await this.getHeaders();
      const response = await billingApi.get(ENDPOINTS.BILLING_CREDITS_ACCOUNT, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting credits account:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get comprehensive credit status
   */
  async getStatus() {
    try {
      const headers = await this.getHeaders();
      const response = await billingApi.get(ENDPOINTS.BILLING_CREDITS_STATUS, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting credit status:', error);
      throw this.handleError(error);
    }
  }

  // ========== CREDIT PACKAGES ==========

  /**
   * Get available credit packages
   */
  async getPackages() {
    try {
      const headers = await this.getHeaders();
      const response = await billingApi.get(ENDPOINTS.BILLING_CREDITS_PACKAGES, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting credit packages:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get specific credit package
   */
  async getPackage(packageId) {
    try {
      const headers = await this.getHeaders();
      const response = await billingApi.get(`${ENDPOINTS.BILLING_CREDITS_PACKAGES}/${packageId}`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting credit package:', error);
      throw this.handleError(error);
    }
  }

  // ========== CREDIT PURCHASE ==========

  /**
   * Create credit purchase order
   */
  async purchaseCredits(packageId, quantity = 1, customAmount = null) {
    try {
      const headers = await this.getHeaders();
      const requestData = { 
        package_id: packageId, 
        quantity 
      };
      
      if (customAmount) {
        requestData.custom_amount = customAmount;
      }
      
      const response = await billingApi.post(ENDPOINTS.BILLING_CREDITS_PURCHASE, requestData, { headers });
      return response.data;
    } catch (error) {
      console.error('Error purchasing credits:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Verify payment and complete purchase
   */
  async verifyPurchase(orderId, paymentId, signature) {
    try {
      const headers = await this.getHeaders();
      const response = await billingApi.post(ENDPOINTS.BILLING_PAYMENTS_VERIFY, {
        order_id: orderId,
        payment_id: paymentId,
        signature
      }, { headers });
      return response.data;
    } catch (error) {
      console.error('Error verifying purchase:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get purchase orders
   */
  async getOrders(limit = 10, status = null) {
    try {
      const headers = await this.getHeaders();
      let url = `${ENDPOINTS.BILLING_CREDITS_ORDERS}?limit=${limit}`;
      if (status) url += `&status=${status}`;
      
      const response = await billingApi.get(url, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting orders:', error);
      throw this.handleError(error);
    }
  }

  // ========== TRANSACTION HISTORY ==========

  /**
   * Get transaction history
   */
  async getTransactions(limit = 20, type = null) {
    try {
      const headers = await this.getHeaders();
      let url = `${ENDPOINTS.BILLING_TRANSACTIONS}?limit=${limit}`;
      if (type) url += `&transaction_type=${type}`;
      
      const response = await billingApi.get(url, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting transactions:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get usage summary
   */
  async getUsageSummary(period = 'current_month') {
    try {
      const headers = await this.getHeaders();
      const response = await billingApi.get(`${ENDPOINTS.BILLING_TRANSACTIONS}/usage?period=${period}`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting usage summary:', error);
      throw this.handleError(error);
    }
  }

  // ========== UTILITY METHODS ==========

  /**
   * Handle API errors with improved error messages
   */
  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      // Handle authentication errors
      if (status === 401) {
        return {
          status,
          message: 'Authentication failed. Please sign out and sign back in.',
          error_code: 'UNAUTHENTICATED',
          type: 'authentication_error',
          actions: ['Sign out', 'Sign back in', 'Refresh page']
        };
      }
      
      // Handle specific billing errors
      if (status === 402 && data.error_code === 'INSUFFICIENT_CREDITS') {
        return {
          status,
          message: data.error || 'Insufficient credits',
          error_code: data.error_code,
          details: data.details,
          actions: data.actions || ['Purchase more credits'],
          type: 'insufficient_credits'
        };
      }
      
      // Handle validation errors
      if (status === 400) {
        return {
          status,
          message: data.error || data.detail?.error || 'Invalid request',
          error_code: data.error_code || data.detail?.error_code || 'VALIDATION_ERROR',
          details: data.details || data.detail?.details
        };
      }
      
      return {
        status,
        message: data.error || data.detail?.error || data.message || 'An error occurred',
        error_code: data.error_code || data.detail?.error_code,
        details: data.details || data.detail?.details
      };
    } else if (error.request) {
      return {
        status: 0,
        message: 'Network error - please check your connection',
        error_code: 'NETWORK_ERROR',
        details: null
      };
    } else {
      return {
        status: 0,
        message: error.message || 'Unknown error occurred',
        error_code: 'UNKNOWN_ERROR',
        details: null
      };
    }
  }

  /**
   * Open Razorpay payment checkout
   */
  async openPaymentCheckout(order, onSuccess, onFailure) {
    try {
      // Load Razorpay script if not already loaded
      if (!window.Razorpay) {
        await this.loadRazorpayScript();
      }

      const options = {
        key: process.env.REACT_APP_RAZORPAY_KEY_ID,
        amount: order.total_amount * 100, // Amount in paisa
        currency: 'INR',
        name: 'Alchemist Credits',
        description: `Purchase ${order.total_credits} credits`,
        order_id: order.payment.gateway_order_id,
        handler: async (response) => {
          try {
            // Verify payment using the new API
            const result = await this.verifyPurchase(
              order.id,
              response.razorpay_payment_id,
              response.razorpay_signature
            );
            
            if (result.success) {
              onSuccess(result.data);
            } else {
              onFailure({ message: 'Payment verification failed' });
            }
          } catch (error) {
            onFailure(this.handleError(error));
          }
        },
        prefill: {
          name: order.customer?.name || '',
          email: order.customer?.email || '',
          contact: order.customer?.phone || ''
        },
        theme: {
          color: '#6366f1'
        },
        modal: {
          ondismiss: () => {
            onFailure({ message: 'Payment cancelled by user' });
          }
        }
      };

      const paymentObject = new window.Razorpay(options);
      paymentObject.open();
    } catch (error) {
      console.error('Error opening payment checkout:', error);
      onFailure(this.handleError(error));
    }
  }

  /**
   * Load Razorpay script dynamically
   */
  loadRazorpayScript() {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  /**
   * Check service health
   */
  async checkHealth() {
    try {
      const response = await billingApi.get(ENDPOINTS.BILLING_HEALTH);
      return response.data;
    } catch (error) {
      console.error('Billing service health check failed:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Format credits for display
   */
  formatCredits(credits) {
    // Handle null, undefined, or NaN values
    const safeCredits = (credits == null || isNaN(credits)) ? 0 : Number(credits);
    
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(safeCredits);
  }

  /**
   * Format large numbers
   */
  formatNumber(number) {
    // Handle null, undefined, or NaN values
    const safeNumber = (number == null || isNaN(number)) ? 0 : Number(number);
    
    return new Intl.NumberFormat('en-IN').format(safeNumber);
  }

  /**
   * Calculate usage in characters from credits
   */
  creditsToCharacters(credits) {
    return credits * 1000; // 1 credit = 1000 characters
  }

  /**
   * Calculate credits from characters
   */
  charactersToCredits(characters) {
    return characters / 1000; // 1000 characters = 1 credit
  }

  /**
   * Get credit status color
   */
  getBalanceStatusColor(balance, threshold = 50) {
    if (balance <= 0) return 'error';
    if (balance <= threshold) return 'warning';
    return 'success';
  }

  /**
   * Check if user needs to purchase credits
   */
  needsCreditPurchase(balance, threshold = 10) {
    return balance <= threshold;
  }
}

// Export singleton instance
export const billingServiceV2 = new BillingServiceV2();
export default billingServiceV2;