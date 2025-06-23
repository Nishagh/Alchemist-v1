/**
 * Billing API Routes
 * 
 * All billing-related API endpoints
 */

const express = require('express');
const { billingService } = require('../services/billingService.js');

const router = express.Router();

// ========== BILLING PROFILE ROUTES ==========

/**
 * GET /api/billing/profile
 * Get user billing profile
 */
router.get('/profile', async (req, res) => {
  try {
    const userId = req.user.uid;
    const profile = await billingService.getUserBillingProfile(userId);
    
    res.status(200).json({
      success: true,
      data: profile
    });
  } catch (error) {
    console.error('Error getting billing profile:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get billing profile'
    });
  }
});

/**
 * PUT /api/billing/profile
 * Update user billing profile
 */
router.put('/profile', async (req, res) => {
  try {
    const userId = req.user.uid;
    const updates = req.body;
    
    const profile = await billingService.updateUserBillingProfile(userId, updates);
    
    res.status(200).json({
      success: true,
      data: profile
    });
  } catch (error) {
    console.error('Error updating billing profile:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update billing profile'
    });
  }
});

// ========== SUBSCRIPTION ROUTES ==========

/**
 * GET /api/billing/subscription
 * Get user subscription
 */
router.get('/subscription', async (req, res) => {
  try {
    const userId = req.user.uid;
    const subscription = await billingService.getUserSubscription(userId);
    
    res.status(200).json({
      success: true,
      data: subscription
    });
  } catch (error) {
    console.error('Error getting subscription:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get subscription'
    });
  }
});

/**
 * PUT /api/billing/subscription/plan
 * Update subscription plan
 */
router.put('/subscription/plan', async (req, res) => {
  try {
    const userId = req.user.uid;
    const { planId } = req.body;
    
    if (!planId) {
      return res.status(400).json({
        success: false,
        error: 'Plan ID is required'
      });
    }
    
    const subscription = await billingService.updateSubscriptionPlan(userId, planId);
    
    res.status(200).json({
      success: true,
      data: subscription
    });
  } catch (error) {
    console.error('Error updating subscription plan:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to update subscription plan'
    });
  }
});

// ========== USAGE ROUTES ==========

/**
 * GET /api/billing/usage/current
 * Get current month usage
 */
router.get('/usage/current', async (req, res) => {
  try {
    const userId = req.user.uid;
    const usage = await billingService.getCurrentUsage(userId);
    const subscription = await billingService.getUserSubscription(userId);
    
    // Calculate usage percentages
    const charactersUsed = usage.metrics?.characters_used || 0;
    const charactersLimit = subscription.limits?.characters_per_month || 1000000;
    const usagePercentage = charactersLimit > 0 ? (charactersUsed / charactersLimit) * 100 : 0;
    
    // Calculate cost
    const totalCost = usage.costs?.total_cost || 0;
    const costLimit = 1000; // Default monthly limit in INR
    const costPercentage = (totalCost / costLimit) * 100;
    
    res.status(200).json({
      success: true,
      data: {
        current_usage: {
          characters_used: charactersUsed,
          characters_limit: charactersLimit,
          usage_percentage: Math.round(usagePercentage * 10) / 10,
          cost: totalCost,
          cost_limit: costLimit,
          cost_percentage: Math.round(costPercentage * 10) / 10
        },
        subscription: {
          plan: subscription.plan?.name || 'Production',
          status: subscription.plan?.status || 'active',
          next_billing: subscription.billing?.next_billing_date,
          rate_per_1k_characters: 1.0 // INR
        },
        raw_usage: usage
      }
    });
  } catch (error) {
    console.error('Error getting current usage:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get usage data'
    });
  }
});

/**
 * GET /api/billing/usage/history
 * Get usage history
 */
router.get('/usage/history', async (req, res) => {
  try {
    const userId = req.user.uid;
    const limit = parseInt(req.query.limit) || 12;
    
    const history = await billingService.getUsageHistory(userId, limit);
    
    res.status(200).json({
      success: true,
      data: history
    });
  } catch (error) {
    console.error('Error getting usage history:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get usage history'
    });
  }
});

/**
 * POST /api/billing/usage/track
 * Track usage (internal API)
 */
router.post('/usage/track', async (req, res) => {
  try {
    const userId = req.user.uid;
    const { characters, agentId } = req.body;
    
    if (!characters || characters <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Valid character count is required'
      });
    }
    
    const result = await billingService.trackCharacterUsage(userId, characters, agentId);
    
    res.status(200).json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('Error tracking usage:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to track usage'
    });
  }
});

// ========== INVOICE ROUTES ==========

/**
 * GET /api/billing/invoices
 * Get user invoices
 */
router.get('/invoices', async (req, res) => {
  try {
    const userId = req.user.uid;
    const limit = parseInt(req.query.limit) || 10;
    
    const invoices = await billingService.getUserInvoices(userId, limit);
    
    // Format invoices for frontend
    const formattedInvoices = invoices.map(invoice => ({
      id: invoice.invoice_number,
      date: invoice.invoice_date,
      amount: invoice.amounts?.total_amount || 0,
      status: invoice.payment?.status || 'pending',
      description: `API Usage - ${invoice.billing_period?.start ? new Date(invoice.billing_period.start).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : 'Current Period'}`,
      downloadUrl: invoice.files?.pdf_url || '#'
    }));
    
    res.status(200).json({
      success: true,
      data: formattedInvoices
    });
  } catch (error) {
    console.error('Error getting invoices:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get invoices'
    });
  }
});

/**
 * POST /api/billing/invoices/generate
 * Generate invoice for current period
 */
router.post('/invoices/generate', async (req, res) => {
  try {
    const userId = req.user.uid;
    const { billingPeriod } = req.body;
    
    const invoice = await billingService.generateInvoice(userId, billingPeriod);
    
    res.status(201).json({
      success: true,
      data: invoice
    });
  } catch (error) {
    console.error('Error generating invoice:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to generate invoice'
    });
  }
});

/**
 * GET /api/billing/invoices/:invoiceId/download
 * Download invoice PDF
 */
router.get('/invoices/:invoiceId/download', async (req, res) => {
  try {
    const userId = req.user.uid;
    const invoiceId = req.params.invoiceId;
    
    // TODO: Implement PDF generation and download
    // For now, return a placeholder response
    res.status(200).json({
      success: true,
      message: 'PDF download functionality coming soon',
      download_url: '#'
    });
  } catch (error) {
    console.error('Error downloading invoice:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to download invoice'
    });
  }
});

// ========== PAYMENT METHOD ROUTES ==========

/**
 * GET /api/billing/payment-methods
 * Get user payment methods
 */
router.get('/payment-methods', async (req, res) => {
  try {
    const userId = req.user.uid;
    const paymentMethods = await billingService.getUserPaymentMethods(userId);
    
    // Format for frontend (hide sensitive data)
    const formattedMethods = paymentMethods.map(method => ({
      id: method.id,
      type: method.type,
      last4: method.card?.last4 || method.upi?.vpa?.split('@')[0] || '****',
      expiryMonth: method.card?.exp_month,
      expiryYear: method.card?.exp_year,
      brand: method.card?.brand,
      isDefault: method.is_default,
      status: method.status
    }));
    
    res.status(200).json({
      success: true,
      data: formattedMethods
    });
  } catch (error) {
    console.error('Error getting payment methods:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get payment methods'
    });
  }
});

/**
 * POST /api/billing/payment-methods
 * Add new payment method
 */
router.post('/payment-methods', async (req, res) => {
  try {
    const userId = req.user.uid;
    const paymentMethodData = req.body;
    
    // Validate required fields
    if (!paymentMethodData.type) {
      return res.status(400).json({
        success: false,
        error: 'Payment method type is required'
      });
    }
    
    const paymentMethod = await billingService.addPaymentMethod(userId, paymentMethodData);
    
    // Return formatted response (hide sensitive data)
    const formattedMethod = {
      id: paymentMethod.id,
      type: paymentMethod.type,
      last4: paymentMethod.card?.last4,
      brand: paymentMethod.card?.brand,
      isDefault: paymentMethod.is_default,
      status: paymentMethod.status
    };
    
    res.status(201).json({
      success: true,
      data: formattedMethod
    });
  } catch (error) {
    console.error('Error adding payment method:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to add payment method'
    });
  }
});

/**
 * DELETE /api/billing/payment-methods/:methodId
 * Delete payment method
 */
router.delete('/payment-methods/:methodId', async (req, res) => {
  try {
    const userId = req.user.uid;
    const methodId = req.params.methodId;
    
    // TODO: Implement payment method deletion
    // For now, return placeholder
    res.status(200).json({
      success: true,
      message: 'Payment method deletion functionality coming soon'
    });
  } catch (error) {
    console.error('Error deleting payment method:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete payment method'
    });
  }
});

// ========== SETTINGS ROUTES ==========

/**
 * GET /api/billing/settings
 * Get billing settings
 */
router.get('/settings', async (req, res) => {
  try {
    const userId = req.user.uid;
    const profile = await billingService.getUserBillingProfile(userId);
    
    res.status(200).json({
      success: true,
      data: {
        preferences: profile.preferences || {},
        limits: profile.limits || {},
        notifications: {
          email_notifications: profile.preferences?.email_notifications || true,
          usage_alerts: profile.preferences?.usage_alerts || true,
          spending_alerts: profile.preferences?.spending_alerts || true
        }
      }
    });
  } catch (error) {
    console.error('Error getting billing settings:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get billing settings'
    });
  }
});

/**
 * PUT /api/billing/settings
 * Update billing settings
 */
router.put('/settings', async (req, res) => {
  try {
    const userId = req.user.uid;
    const settings = req.body;
    
    const updates = {};
    if (settings.preferences) updates.preferences = settings.preferences;
    if (settings.limits) updates.limits = settings.limits;
    
    const profile = await billingService.updateUserBillingProfile(userId, updates);
    
    res.status(200).json({
      success: true,
      data: {
        preferences: profile.preferences || {},
        limits: profile.limits || {}
      }
    });
  } catch (error) {
    console.error('Error updating billing settings:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update billing settings'
    });
  }
});

module.exports = router;