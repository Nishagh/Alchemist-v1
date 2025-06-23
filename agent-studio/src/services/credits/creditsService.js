/**
 * Frontend Credits Service
 * 
 * Service layer for credits-related API calls
 */

import { api } from '../config/apiConfig';
import { getAuthToken } from '../auth/authService';

class CreditsService {
  constructor() {
    this.baseURL = '/api/credits';
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

  // ========== CREDITS BALANCE ==========

  /**
   * Get user credit balance
   */
  async getBalance() {
    try {
      const headers = await this.getHeaders();
      const response = await api.get(`${this.baseURL}/balance`, { headers });
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
      const response = await api.get(`${this.baseURL}/account`, { headers });
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
      const response = await api.get(`${this.baseURL}/status`, { headers });
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
      const response = await api.get(`${this.baseURL}/packages`, { headers });
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
      const response = await api.get(`${this.baseURL}/packages/${packageId}`, { headers });
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
      const requestData = { packageId, quantity };
      
      if (customAmount) {
        requestData.customAmount = customAmount;
      }
      
      const response = await api.post(`${this.baseURL}/purchase`, requestData, { headers });
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
      const response = await api.post(`${this.baseURL}/purchase/verify`, {
        orderId,
        paymentId,
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
      let url = `${this.baseURL}/orders?limit=${limit}`;
      if (status) url += `&status=${status}`;
      
      const response = await api.get(url, { headers });
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
      let url = `${this.baseURL}/transactions?limit=${limit}`;
      if (type) url += `&type=${type}`;
      
      const response = await api.get(url, { headers });
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
      const response = await api.get(`${this.baseURL}/usage?period=${period}`, { headers });
      return response.data;
    } catch (error) {
      console.error('Error getting usage summary:', error);
      throw this.handleError(error);
    }
  }

  // ========== SETTINGS ==========

  /**
   * Update credit settings
   */
  async updateSettings(settings) {
    try {
      const headers = await this.getHeaders();
      const response = await api.put(`${this.baseURL}/settings`, settings, { headers });
      return response.data;
    } catch (error) {
      console.error('Error updating settings:', error);
      throw this.handleError(error);
    }
  }

  // ========== UTILITY METHODS ==========

  /**
   * Handle API errors
   */
  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      // Handle specific credit errors
      if (status === 402 && data.error_code === 'INSUFFICIENT_CREDITS') {
        return {
          status,
          message: data.error,
          error_code: data.error_code,
          details: data.details,
          actions: data.actions,
          type: 'insufficient_credits'
        };
      }
      
      return {
        status,
        message: data.error || data.message || 'An error occurred',
        details: data.details || null
      };
    } else if (error.request) {
      return {
        status: 0,
        message: 'Network error - please check your connection',
        details: null
      };
    } else {
      return {
        status: 0,
        message: error.message || 'Unknown error occurred',
        details: null
      };
    }
  }

  /**
   * Format credits for display
   */
  formatCredits(credits) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(credits);
  }

  /**
   * Format large numbers
   */
  formatNumber(number) {
    return new Intl.NumberFormat('en-IN').format(number);
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
   * Get package display information
   */
  getPackageDisplayInfo(pkg) {
    const savings = pkg.bonus_credits > 0 ? 
      Math.round((pkg.bonus_credits / pkg.base_credits) * 100) : 0;
    
    return {
      ...pkg,
      savings_percentage: savings,
      effective_rate: pkg.price / pkg.total_credits,
      character_equivalent: this.creditsToCharacters(pkg.total_credits),
      display_price: this.formatCredits(pkg.price),
      display_credits: this.formatCredits(pkg.total_credits)
    };
  }

  /**
   * Check if user needs to purchase credits
   */
  needsCreditPurchase(balance, threshold = 10) {
    return balance <= threshold;
  }

  /**
   * Get recommended package based on usage
   */
  getRecommendedPackage(packages, monthlyUsage = 0) {
    if (monthlyUsage === 0) {
      // First time user - recommend starter pack
      return packages.find(p => p.category === 'starter') || packages[0];
    }
    
    // Recommend based on usage with some buffer
    const recommendedCredits = monthlyUsage * 1.2; // 20% buffer
    
    return packages.find(p => p.total_credits >= recommendedCredits) || 
           packages[packages.length - 1]; // Return largest if usage is very high
  }

  /**
   * Calculate days until credits run out
   */
  calculateDaysRemaining(currentBalance, dailyUsage) {
    if (dailyUsage <= 0) return Infinity;
    return Math.floor(currentBalance / dailyUsage);
  }

  /**
   * Get usage trend (increasing/decreasing/stable)
   */
  getUsageTrend(transactions) {
    if (transactions.length < 2) return 'stable';
    
    const recentUsage = transactions.slice(0, 7); // Last 7 transactions
    const olderUsage = transactions.slice(7, 14); // Previous 7 transactions
    
    const recentAvg = recentUsage.reduce((sum, t) => sum + Math.abs(t.amount), 0) / recentUsage.length;
    const olderAvg = olderUsage.reduce((sum, t) => sum + Math.abs(t.amount), 0) / olderUsage.length;
    
    const changePercent = ((recentAvg - olderAvg) / olderAvg) * 100;
    
    if (changePercent > 20) return 'increasing';
    if (changePercent < -20) return 'decreasing';
    return 'stable';
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
        key: process.env.REACT_APP_RAZORPAY_KEY_ID, // Your Razorpay key
        amount: order.total_amount * 100, // Amount in paisa
        currency: 'INR',
        name: 'Alchemist Credits',
        description: `Purchase ${order.total_credits} credits`,
        order_id: order.payment.gateway_order_id,
        handler: async (response) => {
          try {
            // Verify payment
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
            onFailure(error);
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
      onFailure(error);
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
}

// Export singleton instance
export const creditsService = new CreditsService();
export default creditsService;