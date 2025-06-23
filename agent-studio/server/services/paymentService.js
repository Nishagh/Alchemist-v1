/**
 * Payment Service
 * 
 * Handles payment processing with Razorpay
 */

let Razorpay;
try {
  Razorpay = require('razorpay');
} catch (error) {
  console.warn('Razorpay not available, payment features will be disabled');
  Razorpay = null;
}
const crypto = require('crypto');
const { billingService } = require('./billingService');

class PaymentService {
  constructor() {
    // Initialize Razorpay with environment variables
    if (Razorpay) {
      this.razorpay = new Razorpay({
        key_id: process.env.RAZORPAY_KEY_ID || 'your_razorpay_key_id',
        key_secret: process.env.RAZORPAY_KEY_SECRET || 'your_razorpay_key_secret'
      });
    } else {
      this.razorpay = null;
    }
    
    this.webhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET || 'your_webhook_secret';
  }

  // Check if payment service is available
  _checkAvailability() {
    if (!this.razorpay) {
      throw new Error('Payment service not available - Razorpay not installed');
    }
  }

  // ========== CUSTOMER MANAGEMENT ==========

  /**
   * Create or update Razorpay customer
   */
  async createCustomer(userId, customerData) {
    try {
      this._checkAvailability();
      const customer = await this.razorpay.customers.create({
        name: customerData.name,
        email: customerData.email,
        contact: customerData.phone,
        notes: {
          userId: userId,
          source: 'alchemist_agent_studio'
        }
      });

      return customer;
    } catch (error) {
      console.error('Error creating Razorpay customer:', error);
      throw new Error('Failed to create customer');
    }
  }

  /**
   * Get customer by ID
   */
  async getCustomer(customerId) {
    try {
      return await this.razorpay.customers.fetch(customerId);
    } catch (error) {
      console.error('Error fetching customer:', error);
      throw new Error('Failed to fetch customer');
    }
  }

  // ========== PAYMENT METHOD MANAGEMENT ==========

  /**
   * Create payment link for adding payment method
   */
  async createPaymentMethodSetup(userId, amount = 100) { // 100 paisa = ₹1 for setup
    try {
      const billingProfile = await billingService.getUserBillingProfile(userId);
      
      const paymentLink = await this.razorpay.paymentLinks.create({
        amount: amount, // Amount in paisa
        currency: 'INR',
        description: 'Setup Payment Method',
        customer: {
          name: billingProfile.profile?.name || 'User',
          email: billingProfile.profile?.email || '',
          contact: billingProfile.profile?.phone || ''
        },
        notify: {
          sms: true,
          email: true
        },
        reminder_enable: false,
        options: {
          checkout: {
            method: {
              netbanking: 1,
              card: 1,
              upi: 1,
              wallet: 1
            }
          }
        },
        notes: {
          userId: userId,
          purpose: 'payment_method_setup'
        }
      });

      return paymentLink;
    } catch (error) {
      console.error('Error creating payment method setup:', error);
      throw new Error('Failed to create payment method setup');
    }
  }

  // ========== INVOICE PAYMENT ==========

  /**
   * Create payment for invoice
   */
  async createInvoicePayment(userId, invoiceId, amount) {
    try {
      const billingProfile = await billingService.getUserBillingProfile(userId);
      
      const order = await this.razorpay.orders.create({
        amount: Math.round(amount * 100), // Convert to paisa
        currency: 'INR',
        receipt: `invoice_${invoiceId}`,
        notes: {
          userId: userId,
          invoiceId: invoiceId,
          purpose: 'invoice_payment'
        }
      });

      return order;
    } catch (error) {
      console.error('Error creating invoice payment:', error);
      throw new Error('Failed to create payment');
    }
  }

  /**
   * Verify payment signature
   */
  verifyPaymentSignature(orderId, paymentId, signature) {
    try {
      const body = orderId + '|' + paymentId;
      const expectedSignature = crypto
        .createHmac('sha256', this.razorpay.key_secret)
        .update(body.toString())
        .digest('hex');

      return expectedSignature === signature;
    } catch (error) {
      console.error('Error verifying payment signature:', error);
      return false;
    }
  }

  // ========== SUBSCRIPTION MANAGEMENT ==========

  /**
   * Create subscription plan
   */
  async createSubscriptionPlan(planData) {
    try {
      const plan = await this.razorpay.plans.create({
        period: planData.period || 'monthly',
        interval: planData.interval || 1,
        item: {
          name: planData.name,
          description: planData.description,
          amount: Math.round(planData.amount * 100), // Convert to paisa
          currency: 'INR'
        },
        notes: planData.notes || {}
      });

      return plan;
    } catch (error) {
      console.error('Error creating subscription plan:', error);
      throw new Error('Failed to create subscription plan');
    }
  }

  /**
   * Create subscription
   */
  async createSubscription(customerId, planId, startAt = null) {
    try {
      const subscriptionData = {
        plan_id: planId,
        customer_id: customerId,
        quantity: 1,
        total_count: 12, // 12 months
        addons: [],
        notes: {
          source: 'alchemist_agent_studio'
        }
      };

      if (startAt) {
        subscriptionData.start_at = startAt;
      }

      const subscription = await this.razorpay.subscriptions.create(subscriptionData);
      return subscription;
    } catch (error) {
      console.error('Error creating subscription:', error);
      throw new Error('Failed to create subscription');
    }
  }

  // ========== WEBHOOK HANDLING ==========

  /**
   * Verify webhook signature
   */
  verifyWebhookSignature(payload, signature) {
    try {
      const expectedSignature = crypto
        .createHmac('sha256', this.webhookSecret)
        .update(payload)
        .digest('hex');

      return crypto.timingSafeEqual(
        Buffer.from(signature, 'hex'),
        Buffer.from(expectedSignature, 'hex')
      );
    } catch (error) {
      console.error('Error verifying webhook signature:', error);
      return false;
    }
  }

  /**
   * Process webhook event
   */
  async processWebhook(event) {
    try {
      const { entity, event: eventType } = event;

      switch (eventType) {
        case 'payment.captured':
          await this.handlePaymentCaptured(entity);
          break;
        
        case 'payment.failed':
          await this.handlePaymentFailed(entity);
          break;
        
        case 'subscription.charged':
          await this.handleSubscriptionCharged(entity);
          break;
        
        case 'subscription.cancelled':
          await this.handleSubscriptionCancelled(entity);
          break;
        
        default:
          console.log(`Unhandled webhook event: ${eventType}`);
      }

      return { success: true };
    } catch (error) {
      console.error('Error processing webhook:', error);
      throw error;
    }
  }

  /**
   * Handle payment captured event
   */
  async handlePaymentCaptured(payment) {
    try {
      const { notes, amount, id: paymentId, order_id: orderId } = payment;
      const userId = notes?.userId;
      const invoiceId = notes?.invoiceId;
      const purpose = notes?.purpose;

      // Handle credit purchase
      if (purpose === 'credit_purchase' || orderId) {
        const { creditsService } = require('./creditsService');
        
        try {
          // Complete the credit order
          await creditsService.completeCreditOrder(orderId, {
            payment_id: paymentId,
            amount: amount / 100 // Convert from paisa
          });
          
          console.log(`Credit purchase completed: Order ${orderId}, Payment ${paymentId}, Amount: ₹${amount / 100}`);
        } catch (error) {
          console.error('Error completing credit order:', error);
        }
      }
      
      // Handle invoice payment (legacy postpaid)
      if (invoiceId && userId) {
        const { billingService } = require('./billingService');
        
        try {
          await billingService.updateInvoicePaymentStatus(invoiceId, {
            status: 'paid',
            payment_id: paymentId,
            amount: amount / 100, // Convert from paisa
            paid_at: new Date().toISOString()
          });
        } catch (error) {
          console.error('Error updating invoice payment:', error);
        }
      }

      console.log(`Payment captured: ${paymentId}, Amount: ₹${amount / 100}`);
    } catch (error) {
      console.error('Error handling payment captured:', error);
      throw error;
    }
  }

  /**
   * Handle payment failed event
   */
  async handlePaymentFailed(payment) {
    try {
      const { notes, id: paymentId, error_description } = payment;
      const userId = notes?.userId;
      const invoiceId = notes?.invoiceId;

      if (invoiceId && userId) {
        // Update invoice payment status
        await billingService.updateInvoicePaymentStatus(invoiceId, {
          status: 'failed',
          payment_id: paymentId,
          error_reason: error_description,
          failed_at: new Date().toISOString()
        });
      }

      console.log(`Payment failed: ${paymentId}, Reason: ${error_description}`);
    } catch (error) {
      console.error('Error handling payment failed:', error);
      throw error;
    }
  }

  /**
   * Handle subscription charged event
   */
  async handleSubscriptionCharged(subscription) {
    try {
      // Handle recurring subscription payment
      console.log(`Subscription charged: ${subscription.id}`);
    } catch (error) {
      console.error('Error handling subscription charged:', error);
      throw error;
    }
  }

  /**
   * Handle subscription cancelled event
   */
  async handleSubscriptionCancelled(subscription) {
    try {
      // Handle subscription cancellation
      console.log(`Subscription cancelled: ${subscription.id}`);
    } catch (error) {
      console.error('Error handling subscription cancelled:', error);
      throw error;
    }
  }

  // ========== UTILITY METHODS ==========

  /**
   * Convert amount to paisa
   */
  toPaisa(amount) {
    return Math.round(amount * 100);
  }

  /**
   * Convert paisa to rupees
   */
  toRupees(paisa) {
    return paisa / 100;
  }

  /**
   * Format amount for display
   */
  formatAmount(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency
    }).format(amount);
  }

  /**
   * Get payment method type from Razorpay payment
   */
  getPaymentMethodType(payment) {
    if (payment.method === 'card') return 'card';
    if (payment.method === 'upi') return 'upi';
    if (payment.method === 'netbanking') return 'netbanking';
    if (payment.method === 'wallet') return 'wallet';
    return 'other';
  }
}

// Export singleton instance
const paymentService = new PaymentService();
module.exports = { paymentService, PaymentService };
module.exports.default = paymentService;