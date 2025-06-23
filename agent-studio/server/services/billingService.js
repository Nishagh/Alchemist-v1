/**
 * Billing Service
 * 
 * Core business logic for billing operations
 */

const { db } = require('../firebase-admin');
const { 
  COLLECTIONS, 
  BILLING_CONSTANTS, 
  USER_BILLING_SCHEMA,
  USAGE_TRACKING_SCHEMA,
  SUBSCRIPTION_SCHEMA,
  INVOICE_SCHEMA,
  TRANSACTION_SCHEMA
} = require('../schemas/billingSchema');

class BillingService {
  constructor() {
    this.db = db;
    this.collections = COLLECTIONS;
    this.constants = BILLING_CONSTANTS;
  }

  // ========== USER BILLING PROFILE ==========
  
  /**
   * Get or create user billing profile
   */
  async getUserBillingProfile(userId) {
    try {
      const docRef = this.db.collection(this.collections.USER_BILLING).doc(userId);
      const doc = await docRef.get();
      
      if (!doc.exists) {
        // Create default profile
        const defaultProfile = {
          ...USER_BILLING_SCHEMA,
          userId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        await docRef.set(defaultProfile);
        return defaultProfile;
      }
      
      return { id: doc.id, ...doc.data() };
    } catch (error) {
      console.error('Error getting user billing profile:', error);
      throw new Error('Failed to get billing profile');
    }
  }
  
  /**
   * Update user billing profile
   */
  async updateUserBillingProfile(userId, updates) {
    try {
      const docRef = this.db.collection(this.collections.USER_BILLING).doc(userId);
      const updateData = {
        ...updates,
        updated_at: new Date().toISOString()
      };
      
      await docRef.update(updateData);
      return await this.getUserBillingProfile(userId);
    } catch (error) {
      console.error('Error updating user billing profile:', error);
      throw new Error('Failed to update billing profile');
    }
  }

  // ========== SUBSCRIPTION MANAGEMENT ==========
  
  /**
   * Get user subscription
   */
  async getUserSubscription(userId) {
    try {
      const snapshot = await this.db
        .collection(this.collections.SUBSCRIPTIONS)
        .where('userId', '==', userId)
        .where('plan.status', '==', 'active')
        .limit(1)
        .get();
      
      if (snapshot.empty) {
        // Create default subscription
        return await this.createDefaultSubscription(userId);
      }
      
      const doc = snapshot.docs[0];
      return { id: doc.id, ...doc.data() };
    } catch (error) {
      console.error('Error getting user subscription:', error);
      throw new Error('Failed to get subscription');
    }
  }
  
  /**
   * Create default subscription for new user
   */
  async createDefaultSubscription(userId) {
    try {
      const defaultSubscription = {
        ...SUBSCRIPTION_SCHEMA,
        userId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        plan: {
          ...SUBSCRIPTION_SCHEMA.plan,
          ...this.constants.PLANS.PRODUCTION
        },
        billing: {
          ...SUBSCRIPTION_SCHEMA.billing,
          next_billing_date: this.getNextBillingDate(),
          last_billing_date: new Date().toISOString()
        }
      };
      
      const docRef = await this.db.collection(this.collections.SUBSCRIPTIONS).add(defaultSubscription);
      return { id: docRef.id, ...defaultSubscription };
    } catch (error) {
      console.error('Error creating default subscription:', error);
      throw new Error('Failed to create subscription');
    }
  }
  
  /**
   * Update subscription plan
   */
  async updateSubscriptionPlan(userId, planId) {
    try {
      const subscription = await this.getUserSubscription(userId);
      const plan = this.constants.PLANS[planId.toUpperCase()];
      
      if (!plan) {
        throw new Error('Invalid plan ID');
      }
      
      const updateData = {
        'plan.id': plan.id,
        'plan.name': plan.name,
        'pricing.character_rate': plan.character_rate,
        'limits.characters_per_month': plan.monthly_limit,
        'features': plan.features,
        updated_at: new Date().toISOString()
      };
      
      await this.db.collection(this.collections.SUBSCRIPTIONS).doc(subscription.id).update(updateData);
      return await this.getUserSubscription(userId);
    } catch (error) {
      console.error('Error updating subscription plan:', error);
      throw new Error('Failed to update subscription plan');
    }
  }

  // ========== USAGE TRACKING ==========
  
  /**
   * Track character usage
   */
  async trackCharacterUsage(userId, characters, agentId = null) {
    try {
      const currentPeriod = this.getCurrentBillingPeriod();
      const cost = this.calculateCharacterCost(userId, characters);
      
      // Get or create usage document for current period
      const usageDocId = `${userId}_${currentPeriod}`;
      const usageRef = this.db.collection(this.collections.USAGE_TRACKING).doc(usageDocId);
      
      const doc = await usageRef.get();
      
      if (!doc.exists) {
        // Create new usage document
        const newUsage = {
          ...USAGE_TRACKING_SCHEMA,
          id: usageDocId,
          userId,
          timestamp: new Date().toISOString(),
          period: currentPeriod,
          metrics: {
            ...USAGE_TRACKING_SCHEMA.metrics,
            characters_used: characters,
            api_calls: 1
          },
          costs: {
            ...USAGE_TRACKING_SCHEMA.costs,
            character_cost: cost,
            total_cost: cost
          },
          billing_cycle: {
            start_date: this.getBillingCycleStart(),
            end_date: this.getBillingCycleEnd(),
            cycle_id: currentPeriod
          }
        };
        
        if (agentId) {
          newUsage.agent_usage[agentId] = {
            characters: characters,
            tokens: 0,
            calls: 1,
            cost: cost
          };
        }
        
        await usageRef.set(newUsage);
      } else {
        // Update existing usage document
        const currentData = doc.data();
        const updateData = {
          'metrics.characters_used': (currentData.metrics?.characters_used || 0) + characters,
          'metrics.api_calls': (currentData.metrics?.api_calls || 0) + 1,
          'costs.character_cost': (currentData.costs?.character_cost || 0) + cost,
          'costs.total_cost': (currentData.costs?.total_cost || 0) + cost,
          timestamp: new Date().toISOString()
        };
        
        if (agentId) {
          const agentUsage = currentData.agent_usage?.[agentId] || { characters: 0, tokens: 0, calls: 0, cost: 0 };
          updateData[`agent_usage.${agentId}`] = {
            characters: agentUsage.characters + characters,
            tokens: agentUsage.tokens,
            calls: agentUsage.calls + 1,
            cost: agentUsage.cost + cost
          };
        }
        
        await usageRef.update(updateData);
      }
      
      return { success: true, cost, characters };
    } catch (error) {
      console.error('Error tracking character usage:', error);
      throw new Error('Failed to track usage');
    }
  }
  
  /**
   * Get current month usage for user
   */
  async getCurrentUsage(userId) {
    try {
      const currentPeriod = this.getCurrentBillingPeriod();
      const usageDocId = `${userId}_${currentPeriod}`;
      
      const doc = await this.db.collection(this.collections.USAGE_TRACKING).doc(usageDocId).get();
      
      if (!doc.exists) {
        return {
          period: currentPeriod,
          metrics: { characters_used: 0, tokens_used: 0, api_calls: 0 },
          costs: { total_cost: 0 }
        };
      }
      
      return { id: doc.id, ...doc.data() };
    } catch (error) {
      console.error('Error getting current usage:', error);
      throw new Error('Failed to get usage data');
    }
  }
  
  /**
   * Get usage history for user
   */
  async getUsageHistory(userId, limit = 12) {
    try {
      const snapshot = await this.db
        .collection(this.collections.USAGE_TRACKING)
        .where('userId', '==', userId)
        .orderBy('period', 'desc')
        .limit(limit)
        .get();
      
      const history = [];
      snapshot.forEach(doc => {
        history.push({ id: doc.id, ...doc.data() });
      });
      
      return history;
    } catch (error) {
      console.error('Error getting usage history:', error);
      throw new Error('Failed to get usage history');
    }
  }

  // ========== INVOICE MANAGEMENT ==========
  
  /**
   * Generate invoice for billing period
   */
  async generateInvoice(userId, billingPeriod = null) {
    try {
      const period = billingPeriod || this.getCurrentBillingPeriod();
      const usage = await this.getCurrentUsage(userId);
      const subscription = await this.getUserSubscription(userId);
      const billingProfile = await this.getUserBillingProfile(userId);
      
      // Calculate amounts
      const subtotal = usage.costs?.total_cost || 0;
      const taxRate = this.constants.DEFAULT_TAX_RATE;
      const taxAmount = (subtotal * taxRate) / 100;
      const totalAmount = subtotal + taxAmount;
      
      // Generate invoice number
      const invoiceNumber = await this.generateInvoiceNumber();
      
      const invoice = {
        ...INVOICE_SCHEMA,
        userId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        invoice_number: invoiceNumber,
        invoice_date: new Date().toISOString(),
        due_date: this.getDueDate(),
        billing_period: {
          start: this.getBillingCycleStart(),
          end: this.getBillingCycleEnd()
        },
        amounts: {
          subtotal,
          tax_amount: taxAmount,
          tax_rate: taxRate,
          discount_amount: 0,
          total_amount: totalAmount,
          currency: this.constants.DEFAULT_CURRENCY
        },
        line_items: this.generateLineItems(usage),
        customer: {
          name: billingProfile.profile?.name || 'User',
          email: billingProfile.profile?.email || '',
          address: billingProfile.profile?.address || {},
          tax_info: billingProfile.profile?.tax_info || {}
        },
        metadata: {
          subscription_id: subscription.id,
          billing_cycle_id: period,
          auto_generated: true
        }
      };
      
      const docRef = await this.db.collection(this.collections.INVOICES).add(invoice);
      return { id: docRef.id, ...invoice };
    } catch (error) {
      console.error('Error generating invoice:', error);
      throw new Error('Failed to generate invoice');
    }
  }
  
  /**
   * Get user invoices
   */
  async getUserInvoices(userId, limit = 10) {
    try {
      const snapshot = await this.db
        .collection(this.collections.INVOICES)
        .where('userId', '==', userId)
        .orderBy('invoice_date', 'desc')
        .limit(limit)
        .get();
      
      const invoices = [];
      snapshot.forEach(doc => {
        invoices.push({ id: doc.id, ...doc.data() });
      });
      
      return invoices;
    } catch (error) {
      console.error('Error getting user invoices:', error);
      throw new Error('Failed to get invoices');
    }
  }

  // ========== PAYMENT METHODS ==========
  
  /**
   * Add payment method
   */
  async addPaymentMethod(userId, paymentMethodData) {
    try {
      const paymentMethod = {
        ...paymentMethodData,
        userId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'active'
      };
      
      // If this is the first payment method, make it default
      const existingMethods = await this.getUserPaymentMethods(userId);
      if (existingMethods.length === 0) {
        paymentMethod.is_default = true;
      }
      
      const docRef = await this.db.collection(this.collections.PAYMENT_METHODS).add(paymentMethod);
      return { id: docRef.id, ...paymentMethod };
    } catch (error) {
      console.error('Error adding payment method:', error);
      throw new Error('Failed to add payment method');
    }
  }
  
  /**
   * Get user payment methods
   */
  async getUserPaymentMethods(userId) {
    try {
      const snapshot = await this.db
        .collection(this.collections.PAYMENT_METHODS)
        .where('userId', '==', userId)
        .where('status', '==', 'active')
        .orderBy('created_at', 'desc')
        .get();
      
      const methods = [];
      snapshot.forEach(doc => {
        methods.push({ id: doc.id, ...doc.data() });
      });
      
      return methods;
    } catch (error) {
      console.error('Error getting payment methods:', error);
      throw new Error('Failed to get payment methods');
    }
  }

  // ========== UTILITY METHODS ==========
  
  calculateCharacterCost(userId, characters) {
    return characters * this.constants.PRICING.CHARACTERS_PER_INR;
  }
  
  getCurrentBillingPeriod() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }
  
  getBillingCycleStart() {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
  }
  
  getBillingCycleEnd() {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59).toISOString();
  }
  
  getNextBillingDate() {
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return nextMonth.toISOString();
  }
  
  getDueDate(daysFromNow = 7) {
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + daysFromNow);
    return dueDate.toISOString();
  }
  
  async generateInvoiceNumber() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    
    // Get count of invoices this month
    const startOfMonth = new Date(year, now.getMonth(), 1);
    const endOfMonth = new Date(year, now.getMonth() + 1, 0);
    
    const snapshot = await this.db
      .collection(this.collections.INVOICES)
      .where('invoice_date', '>=', startOfMonth.toISOString())
      .where('invoice_date', '<=', endOfMonth.toISOString())
      .get();
    
    const count = snapshot.size + 1;
    return `INV-${year}-${month}-${String(count).padStart(3, '0')}`;
  }
  
  generateLineItems(usage) {
    const lineItems = [];
    
    if (usage.metrics?.characters_used > 0) {
      lineItems.push({
        description: 'API Usage - Characters',
        quantity: usage.metrics.characters_used,
        unit: 'characters',
        unit_price: this.constants.PRICING.CHARACTERS_PER_INR,
        amount: usage.costs?.character_cost || 0
      });
    }
    
    if (usage.metrics?.tokens_used > 0) {
      lineItems.push({
        description: 'API Usage - Tokens',
        quantity: usage.metrics.tokens_used,
        unit: 'tokens',
        unit_price: this.constants.PRICING.TOKENS_PER_INR,
        amount: usage.costs?.token_cost || 0
      });
    }
    
    return lineItems;
  }
}

// Export singleton instance
const billingService = new BillingService();
module.exports = { billingService, BillingService };
module.exports.default = billingService;