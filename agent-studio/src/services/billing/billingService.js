/**
 * Frontend Billing Service
 * 
 * Service layer for billing-related API calls
 */

import { api } from '../config/apiConfig';
import { getAuthToken } from '../auth/authService';

class BillingService {
  constructor() {
    this.baseURL = '/api/billing';
  }

  /**
   * Get authenticated headers
   */
  async getHeaders() {
    const token = await getAuthToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // ========== BILLING PROFILE ==========

  /**
   * Get user billing profile
   */
  async getBillingProfile() {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/profile`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting billing profile:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Update billing profile
   */
  async updateBillingProfile(profileData) {
    try {
      const headers = await this.getHeaders();
      const response = await api.put(`${this.baseURL}/profile`, profileData, { headers });
      return response.data;
    } catch (error) {
      console.error('Error updating billing profile:', error);
      throw this.handleError(error);
    }
  }

  // ========== SUBSCRIPTION ==========

  /**
   * Get user subscription
   */
  async getSubscription() {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/subscription`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting subscription:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Update subscription plan
   */
  async updateSubscriptionPlan(planId) {
    try {
      const headers = await this.getHeaders();
      const response = await api.put(`${this.baseURL}/subscription/plan`, { planId }, { headers });
      return response.data;
    } catch (error) {
      console.error('Error updating subscription plan:', error);
      throw this.handleError(error);
    }
  }

  // ========== USAGE ==========

  /**
   * Get current usage data
   */
  async getCurrentUsage() {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/usage/current`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting current usage:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get usage history
   */
  async getUsageHistory(limit = 12) {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/usage/history?limit=${limit}`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting usage history:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Track usage manually (for testing)
   */
  async trackUsage(characters, agentId = null) {
    try {
      const headers = await this.getHeaders();
      const response = await api.post(`${this.baseURL}/usage/track`, { characters, agentId }, { headers });
      return response.data;
    } catch (error) {
      console.error('Error tracking usage:', error);
      throw this.handleError(error);
    }
  }

  // ========== INVOICES ==========

  /**
   * Get user invoices
   */
  async getInvoices(limit = 10) {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/invoices?limit=${limit}`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting invoices:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Generate invoice for current period
   */
  async generateInvoice(billingPeriod = null) {
    try {
      const headers = await this.getHeaders();
      const response = await api.post(`${this.baseURL}/invoices/generate`, { billingPeriod }, { headers });
      return response.data;
    } catch (error) {
      console.error('Error generating invoice:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Download invoice
   */
  async downloadInvoice(invoiceId) {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/invoices/${invoiceId}/download`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error downloading invoice:', error);
      throw this.handleError(error);
    }
  }

  // ========== PAYMENT METHODS ==========

  /**
   * Get user payment methods
   */
  async getPaymentMethods() {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/payment-methods`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting payment methods:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Add payment method
   */
  async addPaymentMethod(paymentMethodData) {
    try {
      const headers = await this.getHeaders();
      const response = await api.post(`${this.baseURL}/payment-methods`, paymentMethodData, { headers });
      return response.data;
    } catch (error) {
      console.error('Error adding payment method:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Delete payment method
   */
  async deletePaymentMethod(methodId) {
    try {
      const headers = await this.getHeaders();
      const response = await api.delete(`${this.baseURL}/payment-methods/${methodId}`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error deleting payment method:', error);
      throw this.handleError(error);
    }
  }

  // ========== SETTINGS ==========

  /**
   * Get billing settings
   */
  async getBillingSettings() {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/settings`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting billing settings:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Update billing settings
   */
  async updateBillingSettings(settings) {
    try {
      const headers = await this.getHeaders();
      const response = await api.put(`${this.baseURL}/settings`, settings, { headers });
      return response.data;
    } catch (error) {
      console.error('Error updating billing settings:', error);
      throw this.handleError(error);
    }
  }

  // ========== UTILITY METHODS ==========

  /**
   * Handle API errors
   */
  handleError(error) {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      return {
        status,
        message: data.error || data.message || 'An error occurred',
        details: data.details || null
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        status: 0,
        message: 'Network error - please check your connection',
        details: null
      };
    } else {
      // Something else happened
      return {
        status: 0,
        message: error.message || 'Unknown error occurred',
        details: null
      };
    }
  }

  /**
   * Format currency for display
   */
  formatCurrency(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency
    }).format(amount);
  }

  /**
   * Format number for display
   */
  formatNumber(number) {
    return new Intl.NumberFormat('en-IN').format(number);
  }

  /**
   * Calculate usage percentage
   */
  calculateUsagePercentage(used, limit) {
    if (limit <= 0) return 0;
    return Math.min((used / limit) * 100, 100);
  }

  /**
   * Get status color based on usage percentage
   */
  getUsageStatusColor(percentage) {
    if (percentage >= 90) return 'error';
    if (percentage >= 75) return 'warning';
    return 'success';
  }

  /**
   * Get next billing date
   */
  getNextBillingDate() {
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return nextMonth.toISOString();
  }

  /**
   * Check if usage is over limit
   */
  isOverLimit(used, limit) {
    return limit > 0 && used >= limit;
  }

  /**
   * Get plan features
   */
  getPlanFeatures(planId) {
    const plans = {
      development: {
        name: 'Development',
        features: ['Basic Analytics', 'API Access', '10K Characters/Month'],
        price: 'Free',
        color: 'success'
      },
      production: {
        name: 'Production',
        features: ['Full Analytics', 'WhatsApp Integration', 'API Access', '1M Characters/Month'],
        price: '₹1 per 1K characters',
        color: 'primary'
      },
      enterprise: {
        name: 'Enterprise',
        features: ['Custom Models', 'Priority Support', 'Unlimited Usage', 'Webhook Support'],
        price: 'Custom Pricing',
        color: 'secondary'
      }
    };

    return plans[planId] || plans.production;
  }
}

// Export singleton instance
export const billingService = new BillingService();
export default billingService;