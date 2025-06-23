/**
 * Credits Service
 * 
 * Handles all credit-based billing operations for prepaid system
 */

const { db } = require('../firebase-admin');
const { 
  COLLECTIONS, 
  CREDITS_CONSTANTS,
  DEFAULT_CREDIT_PACKAGES,
  USER_CREDITS_SCHEMA,
  CREDIT_TRANSACTION_SCHEMA,
  CREDIT_ORDER_SCHEMA
} = require('../schemas/creditsSchema');

class CreditsService {
  constructor() {
    this.db = db;
    this.collections = COLLECTIONS;
    this.constants = CREDITS_CONSTANTS;
  }

  // ========== USER CREDITS ACCOUNT ==========
  
  /**
   * Get or create user credits account
   */
  async getUserCreditsAccount(userId) {
    try {
      const docRef = this.db.collection(this.collections.USER_CREDITS).doc(userId);
      const doc = await docRef.get();
      
      if (!doc.exists) {
        // Create default credits account
        const defaultAccount = {
          ...USER_CREDITS_SCHEMA,
          userId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          balance: {
            available_credits: 0,
            bonus_credits: 0,
            total_credits: 0,
            reserved_credits: 0,
            lifetime_purchased: 0,
            lifetime_used: 0,
            last_purchase_date: '',
            last_usage_date: ''
          }
        };
        
        await docRef.set(defaultAccount);
        return defaultAccount;
      }
      
      return { id: doc.id, ...doc.data() };
    } catch (error) {
      console.error('Error getting user credits account:', error);
      throw new Error('Failed to get credits account');
    }
  }
  
  /**
   * Get user balance
   */
  async getUserBalance(userId) {
    try {
      const account = await this.getUserCreditsAccount(userId);
      return {
        available_credits: account.balance?.available_credits || 0,
        bonus_credits: account.balance?.bonus_credits || 0,
        total_credits: account.balance?.total_credits || 0,
        reserved_credits: account.balance?.reserved_credits || 0
      };
    } catch (error) {
      console.error('Error getting user balance:', error);
      throw new Error('Failed to get balance');
    }
  }

  // ========== CREDIT TRANSACTIONS ==========
  
  /**
   * Deduct credits for usage
   */
  async deductCredits(userId, amount, usageDetails) {
    try {
      // Use Firestore transaction to ensure atomicity
      return await this.db.runTransaction(async (transaction) => {
        const accountRef = this.db.collection(this.collections.USER_CREDITS).doc(userId);
        const accountDoc = await transaction.get(accountRef);
        
        if (!accountDoc.exists) {
          throw new Error('Credits account not found');
        }
        
        const account = accountDoc.data();
        const currentBalance = account.balance?.total_credits || 0;
        
        // Check if user has sufficient balance
        if (currentBalance < amount) {
          throw new Error(`Insufficient credits. Required: ${amount}, Available: ${currentBalance}`);
        }
        
        // Calculate new balance (deduct from available first, then bonus)
        let newAvailableCredits = account.balance?.available_credits || 0;
        let newBonusCredits = account.balance?.bonus_credits || 0;
        
        let remainingDeduction = amount;
        
        // First deduct from available credits
        if (remainingDeduction > 0 && newAvailableCredits > 0) {
          const deductFromAvailable = Math.min(remainingDeduction, newAvailableCredits);
          newAvailableCredits -= deductFromAvailable;
          remainingDeduction -= deductFromAvailable;
        }
        
        // Then deduct from bonus credits if needed
        if (remainingDeduction > 0 && newBonusCredits > 0) {
          const deductFromBonus = Math.min(remainingDeduction, newBonusCredits);
          newBonusCredits -= deductFromBonus;
          remainingDeduction -= deductFromBonus;
        }
        
        const newTotalCredits = newAvailableCredits + newBonusCredits;
        
        // Update account balance
        const updatedBalance = {
          ...account.balance,
          available_credits: newAvailableCredits,
          bonus_credits: newBonusCredits,
          total_credits: newTotalCredits,
          lifetime_used: (account.balance?.lifetime_used || 0) + amount,
          last_usage_date: new Date().toISOString()
        };
        
        transaction.update(accountRef, {
          balance: updatedBalance,
          updated_at: new Date().toISOString()
        });
        
        // Create transaction record
        const transactionData = {
          ...CREDIT_TRANSACTION_SCHEMA,
          userId,
          timestamp: new Date().toISOString(),
          type: 'usage',
          category: 'api_usage',
          amount: -amount, // Negative for deduction
          balance_before: currentBalance,
          balance_after: newTotalCredits,
          description: usageDetails.description || 'API usage',
          usage_details: usageDetails
        };
        
        const transactionRef = this.db.collection(this.collections.CREDIT_TRANSACTIONS).doc();
        transaction.set(transactionRef, transactionData);
        
        return {
          success: true,
          amount_deducted: amount,
          new_balance: newTotalCredits,
          transaction_id: transactionRef.id
        };
      });
    } catch (error) {
      console.error('Error deducting credits:', error);
      throw error;
    }
  }
  
  /**
   * Add credits to user account
   */
  async addCredits(userId, amount, bonusAmount = 0, purchaseDetails = null) {
    try {
      return await this.db.runTransaction(async (transaction) => {
        const accountRef = this.db.collection(this.collections.USER_CREDITS).doc(userId);
        const accountDoc = await transaction.get(accountRef);
        
        let account;
        if (!accountDoc.exists) {
          // Create new account if doesn't exist
          account = await this.getUserCreditsAccount(userId);
        } else {
          account = accountDoc.data();
        }
        
        const currentBalance = account.balance?.total_credits || 0;
        
        // Calculate new balance
        const newAvailableCredits = (account.balance?.available_credits || 0) + amount;
        const newBonusCredits = (account.balance?.bonus_credits || 0) + bonusAmount;
        const newTotalCredits = newAvailableCredits + newBonusCredits;
        
        // Update account balance
        const updatedBalance = {
          ...account.balance,
          available_credits: newAvailableCredits,
          bonus_credits: newBonusCredits,
          total_credits: newTotalCredits,
          lifetime_purchased: (account.balance?.lifetime_purchased || 0) + amount + bonusAmount,
          last_purchase_date: new Date().toISOString()
        };
        
        transaction.update(accountRef, {
          balance: updatedBalance,
          updated_at: new Date().toISOString()
        });
        
        // Create transaction record
        const transactionData = {
          ...CREDIT_TRANSACTION_SCHEMA,
          userId,
          timestamp: new Date().toISOString(),
          type: 'purchase',
          category: 'credit_purchase',
          amount: amount + bonusAmount, // Positive for addition
          balance_before: currentBalance,
          balance_after: newTotalCredits,
          description: purchaseDetails ? `Credit purchase: ${purchaseDetails.package_name}` : 'Credit purchase',
          purchase_details: purchaseDetails
        };
        
        const transactionRef = this.db.collection(this.collections.CREDIT_TRANSACTIONS).doc();
        transaction.set(transactionRef, transactionData);
        
        return {
          success: true,
          amount_added: amount,
          bonus_added: bonusAmount,
          total_added: amount + bonusAmount,
          new_balance: newTotalCredits,
          transaction_id: transactionRef.id
        };
      });
    } catch (error) {
      console.error('Error adding credits:', error);
      throw error;
    }
  }

  // ========== CREDIT PACKAGES ==========
  
  /**
   * Get available credit packages
   */
  async getCreditPackages() {
    try {
      const snapshot = await this.db
        .collection(this.collections.CREDIT_PACKAGES)
        .where('status', '==', 'active')
        .orderBy('sort_order')
        .get();
      
      if (snapshot.empty) {
        // Initialize default packages if none exist
        await this.initializeDefaultPackages();
        return DEFAULT_CREDIT_PACKAGES;
      }
      
      const packages = [];
      snapshot.forEach(doc => {
        packages.push({ id: doc.id, ...doc.data() });
      });
      
      return packages;
    } catch (error) {
      console.error('Error getting credit packages:', error);
      throw new Error('Failed to get credit packages');
    }
  }
  
  /**
   * Initialize default credit packages
   */
  async initializeDefaultPackages() {
    try {
      const batch = this.db.batch();
      
      DEFAULT_CREDIT_PACKAGES.forEach(pkg => {
        const docRef = this.db.collection(this.collections.CREDIT_PACKAGES).doc(pkg.id);
        batch.set(docRef, {
          ...pkg,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
      });
      
      await batch.commit();
      console.log('Default credit packages initialized');
    } catch (error) {
      console.error('Error initializing default packages:', error);
      throw error;
    }
  }

  // ========== CREDIT ORDERS ==========
  
  /**
   * Create credit purchase order
   */
  async createCreditOrder(userId, packageId, quantity = 1, customAmount = null) {
    try {
      // Get package details
      let packageData;
      if (packageId === 'custom_amount' && customAmount) {
        packageData = {
          id: 'custom_amount',
          name: 'Custom Amount',
          base_credits: customAmount,
          bonus_credits: this.calculateBonusCredits(customAmount),
          price: customAmount
        };
      } else {
        const packageDoc = await this.db.collection(this.collections.CREDIT_PACKAGES).doc(packageId).get();
        if (!packageDoc.exists) {
          throw new Error('Package not found');
        }
        packageData = { id: packageDoc.id, ...packageDoc.data() };
      }
      
      // Calculate order totals
      const unitPrice = packageData.price;
      const subtotal = unitPrice * quantity;
      const taxRate = 18; // GST
      const taxAmount = (subtotal * taxRate) / 100;
      const totalAmount = subtotal + taxAmount;
      
      const baseCredits = packageData.base_credits * quantity;
      const bonusCredits = packageData.bonus_credits * quantity;
      const totalCredits = baseCredits + bonusCredits;
      
      // Generate order number
      const orderNumber = await this.generateOrderNumber();
      
      // Create order
      const orderData = {
        ...CREDIT_ORDER_SCHEMA,
        userId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        order_number: orderNumber,
        status: 'pending',
        package_id: packageId,
        package_name: packageData.name,
        quantity,
        unit_price: unitPrice,
        subtotal,
        tax_amount: taxAmount,
        tax_rate: taxRate,
        total_amount: totalAmount,
        base_credits: baseCredits,
        bonus_credits: bonusCredits,
        total_credits: totalCredits
      };
      
      const orderRef = await this.db.collection(this.collections.CREDIT_ORDERS).add(orderData);
      
      return { id: orderRef.id, ...orderData };
    } catch (error) {
      console.error('Error creating credit order:', error);
      throw error;
    }
  }
  
  /**
   * Complete credit order (called after successful payment)
   */
  async completeCreditOrder(orderId, paymentDetails) {
    try {
      return await this.db.runTransaction(async (transaction) => {
        const orderRef = this.db.collection(this.collections.CREDIT_ORDERS).doc(orderId);
        const orderDoc = await transaction.get(orderRef);
        
        if (!orderDoc.exists) {
          throw new Error('Order not found');
        }
        
        const order = orderDoc.data();
        
        if (order.status !== 'pending') {
          throw new Error('Order is not in pending status');
        }
        
        // Update order status
        transaction.update(orderRef, {
          status: 'paid',
          'payment.gateway_payment_id': paymentDetails.payment_id,
          'payment.paid_at': new Date().toISOString(),
          'fulfillment.fulfilled': true,
          'fulfillment.fulfilled_at': new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
        
        // Add credits to user account
        const addResult = await this.addCredits(
          order.userId,
          order.base_credits,
          order.bonus_credits,
          {
            package_id: order.package_id,
            package_name: order.package_name,
            base_amount: order.base_credits,
            bonus_amount: order.bonus_credits,
            payment_method: 'razorpay',
            payment_id: paymentDetails.payment_id,
            order_id: orderId
          }
        );
        
        // Update fulfillment details
        transaction.update(orderRef, {
          'fulfillment.transaction_id': addResult.transaction_id,
          'fulfillment.notes': `Added ${addResult.total_added} credits to account`
        });
        
        return {
          success: true,
          order_id: orderId,
          credits_added: addResult.total_added,
          new_balance: addResult.new_balance
        };
      });
    } catch (error) {
      console.error('Error completing credit order:', error);
      throw error;
    }
  }

  // ========== TRANSACTION HISTORY ==========
  
  /**
   * Get user transaction history
   */
  async getUserTransactions(userId, limit = 20, type = null) {
    try {
      let query = this.db
        .collection(this.collections.CREDIT_TRANSACTIONS)
        .where('userId', '==', userId)
        .orderBy('timestamp', 'desc')
        .limit(limit);
      
      if (type) {
        query = query.where('type', '==', type);
      }
      
      const snapshot = await query.get();
      
      const transactions = [];
      snapshot.forEach(doc => {
        transactions.push({ id: doc.id, ...doc.data() });
      });
      
      return transactions;
    } catch (error) {
      console.error('Error getting user transactions:', error);
      throw new Error('Failed to get transactions');
    }
  }

  // ========== UTILITY METHODS ==========
  
  /**
   * Calculate cost in credits for character usage
   */
  calculateCharacterCost(characters) {
    return characters / this.constants.CHARACTERS_PER_CREDIT;
  }
  
  /**
   * Calculate bonus credits based on purchase amount
   */
  calculateBonusCredits(amount) {
    let bonusPercentage = 0;
    
    for (const threshold of this.constants.BONUS_THRESHOLDS) {
      if (amount >= threshold.min_amount) {
        bonusPercentage = threshold.bonus_percentage;
      }
    }
    
    return Math.floor((amount * bonusPercentage) / 100);
  }
  
  /**
   * Check if user has sufficient credits
   */
  async hasSufficientCredits(userId, requiredAmount) {
    try {
      const balance = await this.getUserBalance(userId);
      return balance.total_credits >= requiredAmount;
    } catch (error) {
      console.error('Error checking sufficient credits:', error);
      return false;
    }
  }
  
  /**
   * Generate order number
   */
  async generateOrderNumber() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    
    // Get count of orders this month
    const startOfMonth = new Date(year, now.getMonth(), 1);
    const endOfMonth = new Date(year, now.getMonth() + 1, 0);
    
    const snapshot = await this.db
      .collection(this.collections.CREDIT_ORDERS)
      .where('created_at', '>=', startOfMonth.toISOString())
      .where('created_at', '<=', endOfMonth.toISOString())
      .get();
    
    const count = snapshot.size + 1;
    return `ORD-${year}-${month}-${String(count).padStart(4, '0')}`;
  }
  
  /**
   * Get user's low balance status
   */
  async checkLowBalanceAlert(userId) {
    try {
      const account = await this.getUserCreditsAccount(userId);
      const balance = account.balance?.total_credits || 0;
      const threshold = account.settings?.low_balance_threshold || this.constants.DEFAULT_LOW_BALANCE_THRESHOLD;
      
      return {
        is_low_balance: balance <= threshold,
        current_balance: balance,
        threshold,
        should_alert: balance <= threshold && account.settings?.balance_alerts !== false
      };
    } catch (error) {
      console.error('Error checking low balance:', error);
      return { is_low_balance: false, current_balance: 0 };
    }
  }
  
  /**
   * Format credits for display
   */
  formatCredits(credits) {
    return `₹${credits.toFixed(2)}`;
  }
}

// Export singleton instance
const creditsService = new CreditsService();
module.exports = { creditsService, CreditsService };
module.exports.default = creditsService;