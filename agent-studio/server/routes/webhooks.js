/**
 * Webhook Routes
 * 
 * Handle payment gateway webhooks
 */

const express = require('express');
const { paymentService } = require('../services/paymentService');

const router = express.Router();

// Raw body parser for webhook verification
const rawBodyParser = express.raw({ type: 'application/json' });

/**
 * POST /webhooks/razorpay
 * Handle Razorpay webhooks
 */
router.post('/razorpay', rawBodyParser, async (req, res) => {
  try {
    const signature = req.headers['x-razorpay-signature'];
    const payload = req.body;

    // Verify webhook signature
    if (!paymentService.verifyWebhookSignature(payload, signature)) {
      console.error('Invalid webhook signature');
      return res.status(400).json({ 
        success: false, 
        error: 'Invalid signature' 
      });
    }

    // Parse the payload
    const event = JSON.parse(payload);
    
    // Process the webhook event
    await paymentService.processWebhook(event);

    res.status(200).json({ 
      success: true, 
      message: 'Webhook processed successfully' 
    });
  } catch (error) {
    console.error('Error processing Razorpay webhook:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to process webhook' 
    });
  }
});

/**
 * POST /webhooks/stripe (for future use)
 * Handle Stripe webhooks
 */
router.post('/stripe', rawBodyParser, async (req, res) => {
  try {
    // TODO: Implement Stripe webhook handling
    res.status(200).json({ 
      success: true, 
      message: 'Stripe webhook endpoint - coming soon' 
    });
  } catch (error) {
    console.error('Error processing Stripe webhook:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to process webhook' 
    });
  }
});

/**
 * GET /webhooks/health
 * Health check for webhook endpoints
 */
router.get('/health', (req, res) => {
  res.status(200).json({
    success: true,
    message: 'Webhook endpoints are healthy',
    timestamp: new Date().toISOString(),
    endpoints: {
      razorpay: '/webhooks/razorpay',
      stripe: '/webhooks/stripe'
    }
  });
});

module.exports = router;