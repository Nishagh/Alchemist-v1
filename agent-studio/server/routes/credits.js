/**
 * Credits API Routes
 * 
 * All credit-related API endpoints for prepaid billing system
 */

const express = require('express');
const { creditsService } = require('../services/creditsService');
const { paymentService } = require('../services/paymentService');

const router = express.Router();

// ========== CREDITS BALANCE ROUTES ==========

/**
 * GET /api/credits/balance
 * Get user credit balance
 */
router.get('/balance', async (req, res) => {
  try {
    const userId = req.user.uid;
    const balance = await creditsService.getUserBalance(userId);
    
    res.status(200).json({
      success: true,
      data: balance
    });
  } catch (error) {
    console.error('Error getting credit balance:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get credit balance'
    });
  }
});

/**
 * GET /api/credits/account
 * Get complete user credits account
 */
router.get('/account', async (req, res) => {
  try {
    const userId = req.user.uid;
    const account = await creditsService.getUserCreditsAccount(userId);
    
    res.status(200).json({
      success: true,
      data: account
    });
  } catch (error) {
    console.error('Error getting credits account:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get credits account'
    });
  }
});

// ========== CREDIT PACKAGES ROUTES ==========

/**
 * GET /api/credits/packages
 * Get available credit packages
 */
router.get('/packages', async (req, res) => {
  try {
    const packages = await creditsService.getCreditPackages();
    
    res.status(200).json({
      success: true,
      data: packages
    });
  } catch (error) {
    console.error('Error getting credit packages:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get credit packages'
    });
  }
});

/**
 * GET /api/credits/packages/:packageId
 * Get specific credit package
 */
router.get('/packages/:packageId', async (req, res) => {
  try {
    const packages = await creditsService.getCreditPackages();
    const package = packages.find(p => p.id === req.params.packageId);
    
    if (!package) {
      return res.status(404).json({
        success: false,
        error: 'Package not found'
      });
    }
    
    res.status(200).json({
      success: true,
      data: package
    });
  } catch (error) {
    console.error('Error getting credit package:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get credit package'
    });
  }
});

// ========== CREDIT PURCHASE ROUTES ==========

/**
 * POST /api/credits/purchase
 * Create credit purchase order
 */
router.post('/purchase', async (req, res) => {
  try {
    const userId = req.user.uid;
    const { packageId, quantity = 1, customAmount } = req.body;
    
    if (!packageId) {
      return res.status(400).json({
        success: false,
        error: 'Package ID is required'
      });
    }
    
    // Validate custom amount if provided
    if (packageId === 'custom_amount') {
      if (!customAmount || customAmount < creditsService.constants.MIN_PURCHASE) {
        return res.status(400).json({
          success: false,
          error: `Minimum purchase amount is ₹${creditsService.constants.MIN_PURCHASE}`
        });
      }
      
      if (customAmount > creditsService.constants.MAX_PURCHASE) {
        return res.status(400).json({
          success: false,
          error: `Maximum purchase amount is ₹${creditsService.constants.MAX_PURCHASE}`
        });
      }
    }
    
    // Create credit order
    const order = await creditsService.createCreditOrder(userId, packageId, quantity, customAmount);
    
    // Create payment with Razorpay
    const payment = await paymentService.createInvoicePayment(
      userId, 
      order.id, 
      order.total_amount
    );
    
    // Update order with payment details
    await creditsService.db.collection(creditsService.collections.CREDIT_ORDERS).doc(order.id).update({
      'payment.gateway_order_id': payment.id,
      'payment.payment_link': `https://rzp.io/i/${payment.id}`,
      updated_at: new Date().toISOString()
    });
    
    res.status(201).json({
      success: true,
      data: {
        order: {
          ...order,
          payment: {
            ...order.payment,
            gateway_order_id: payment.id,
            payment_link: `https://rzp.io/i/${payment.id}`
          }
        },
        payment_details: payment
      }
    });
  } catch (error) {
    console.error('Error creating credit purchase:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to create credit purchase'
    });
  }
});

/**
 * POST /api/credits/purchase/verify
 * Verify payment and complete credit purchase
 */
router.post('/purchase/verify', async (req, res) => {
  try {
    const userId = req.user.uid;
    const { orderId, paymentId, signature } = req.body;
    
    if (!orderId || !paymentId || !signature) {
      return res.status(400).json({
        success: false,
        error: 'Order ID, payment ID, and signature are required'
      });
    }
    
    // Verify payment signature
    const isValidSignature = paymentService.verifyPaymentSignature(orderId, paymentId, signature);
    
    if (!isValidSignature) {
      return res.status(400).json({
        success: false,
        error: 'Invalid payment signature'
      });
    }
    
    // Complete the credit order
    const result = await creditsService.completeCreditOrder(orderId, {
      payment_id: paymentId,
      verified: true
    });
    
    res.status(200).json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('Error verifying credit purchase:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to verify payment'
    });
  }
});

/**
 * GET /api/credits/orders
 * Get user's credit purchase orders
 */
router.get('/orders', async (req, res) => {
  try {
    const userId = req.user.uid;
    const limit = parseInt(req.query.limit) || 10;
    const status = req.query.status;
    
    let query = creditsService.db
      .collection(creditsService.collections.CREDIT_ORDERS)
      .where('userId', '==', userId)
      .orderBy('created_at', 'desc')
      .limit(limit);
    
    if (status) {
      query = query.where('status', '==', status);
    }
    
    const snapshot = await query.get();
    
    const orders = [];
    snapshot.forEach(doc => {
      orders.push({ id: doc.id, ...doc.data() });
    });
    
    res.status(200).json({
      success: true,
      data: orders
    });
  } catch (error) {
    console.error('Error getting credit orders:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get credit orders'
    });
  }
});

// ========== TRANSACTION HISTORY ROUTES ==========

/**
 * GET /api/credits/transactions
 * Get user transaction history
 */
router.get('/transactions', async (req, res) => {
  try {
    const userId = req.user.uid;
    const limit = parseInt(req.query.limit) || 20;
    const type = req.query.type; // purchase, usage, refund, bonus
    
    const transactions = await creditsService.getUserTransactions(userId, limit, type);
    
    res.status(200).json({
      success: true,
      data: transactions
    });
  } catch (error) {
    console.error('Error getting transactions:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get transactions'
    });
  }
});

/**
 * GET /api/credits/usage
 * Get usage summary for current period
 */
router.get('/usage', async (req, res) => {
  try {
    const userId = req.user.uid;
    const period = req.query.period || 'current_month';
    
    // Get usage transactions for the period
    const usageTransactions = await creditsService.getUserTransactions(userId, 100, 'usage');
    
    // Calculate usage summary
    let totalCreditsUsed = 0;
    let totalCharacters = 0;
    let totalApiCalls = 0;
    let agentUsage = {};
    
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    
    usageTransactions.forEach(transaction => {
      const transactionDate = new Date(transaction.timestamp);
      
      // Filter by period (for now, just current month)
      if (transactionDate >= startOfMonth) {
        totalCreditsUsed += Math.abs(transaction.amount);
        
        if (transaction.usage_details) {
          totalCharacters += transaction.usage_details.characters || 0;
          totalApiCalls += transaction.usage_details.api_calls || 0;
          
          const agentId = transaction.usage_details.agent_id;
          if (agentId) {
            if (!agentUsage[agentId]) {
              agentUsage[agentId] = {
                credits: 0,
                characters: 0,
                api_calls: 0
              };
            }
            agentUsage[agentId].credits += Math.abs(transaction.amount);
            agentUsage[agentId].characters += transaction.usage_details.characters || 0;
            agentUsage[agentId].api_calls += transaction.usage_details.api_calls || 0;
          }
        }
      }
    });
    
    res.status(200).json({
      success: true,
      data: {
        period,
        summary: {
          total_credits_used: totalCreditsUsed,
          total_characters: totalCharacters,
          total_api_calls: totalApiCalls,
          average_cost_per_character: totalCharacters > 0 ? totalCreditsUsed / totalCharacters : 0
        },
        agent_usage: agentUsage,
        period_start: startOfMonth.toISOString(),
        period_end: now.toISOString()
      }
    });
  } catch (error) {
    console.error('Error getting usage summary:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get usage summary'
    });
  }
});

// ========== CREDIT MANAGEMENT ROUTES ==========

/**
 * POST /api/credits/add
 * Add credits (admin only or promotional)
 */
router.post('/add', async (req, res) => {
  try {
    const { targetUserId, amount, bonusAmount = 0, reason } = req.body;
    const adminUserId = req.user.uid;
    
    if (!targetUserId || !amount || amount <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Target user ID and valid amount are required'
      });
    }
    
    // TODO: Add admin permission check here
    
    const result = await creditsService.addCredits(
      targetUserId,
      amount,
      bonusAmount,
      {
        package_name: 'Admin Credit Addition',
        admin_action: true,
        admin_user_id: adminUserId,
        reason: reason || 'Manual credit addition'
      }
    );
    
    res.status(200).json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('Error adding credits:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to add credits'
    });
  }
});

/**
 * GET /api/credits/status
 * Get comprehensive credit status for user
 */
router.get('/status', async (req, res) => {
  try {
    const userId = req.user.uid;
    
    const [account, lowBalanceCheck] = await Promise.all([
      creditsService.getUserCreditsAccount(userId),
      creditsService.checkLowBalanceAlert(userId)
    ]);
    
    res.status(200).json({
      success: true,
      data: {
        balance: account.balance,
        settings: account.settings,
        status: account.status,
        alerts: {
          low_balance: lowBalanceCheck.is_low_balance,
          threshold: lowBalanceCheck.threshold,
          should_alert: lowBalanceCheck.should_alert
        },
        can_use_services: account.balance?.total_credits > 0
      }
    });
  } catch (error) {
    console.error('Error getting credit status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get credit status'
    });
  }
});

/**
 * PUT /api/credits/settings
 * Update credit account settings
 */
router.put('/settings', async (req, res) => {
  try {
    const userId = req.user.uid;
    const settings = req.body;
    
    // Update account settings
    await creditsService.db.collection(creditsService.collections.USER_CREDITS).doc(userId).update({
      settings: settings,
      updated_at: new Date().toISOString()
    });
    
    const updatedAccount = await creditsService.getUserCreditsAccount(userId);
    
    res.status(200).json({
      success: true,
      data: updatedAccount.settings
    });
  } catch (error) {
    console.error('Error updating credit settings:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update settings'
    });
  }
});

module.exports = router;