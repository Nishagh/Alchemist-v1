# Billing System Setup Guide

This guide will help you set up the comprehensive billing system for Alchemist Agent Studio.

## Overview

The billing system includes:
- **Real-time usage tracking** (characters, tokens, API calls)
- **Razorpay payment integration** (Indian payments)
- **Subscription management** (Development, Production, Enterprise plans)
- **Invoice generation** (with GST support)
- **Payment method management**
- **Webhook handling** for automatic payment processing
- **Firestore database** for billing data storage

## Prerequisites

1. **Firebase Project** with Firestore enabled
2. **Razorpay Account** (for Indian payments)
3. **Node.js 18+** and **npm**
4. **Google Cloud Project** (for Firebase Admin)

## Step 1: Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in your configuration:

### Firebase Configuration
```bash
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_firebase_client_email@your_project.iam.gserviceaccount.com
```

### Razorpay Configuration
```bash
RAZORPAY_KEY_ID=rzp_test_your_key_id  # Use rzp_live_ for production
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

## Step 2: Install Dependencies

```bash
npm install
```

The billing system uses these key dependencies:
- `razorpay` - Payment processing
- `firebase-admin` - Database operations
- `express` - API routes
- `crypto` - Webhook signature verification

## Step 3: Database Setup

The system automatically creates the following Firestore collections:
- `user_billing` - User billing profiles
- `usage_tracking` - Real-time usage data
- `subscriptions` - User subscription plans
- `payment_methods` - Payment method metadata
- `invoices` - Invoice records
- `transactions` - Payment transaction logs

No manual database setup required - collections are created automatically.

## Step 4: Razorpay Setup

### Create Razorpay Account
1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Create an account and complete verification
3. Get your API keys from Settings > API Keys

### Configure Webhooks
1. Go to Settings > Webhooks in Razorpay Dashboard
2. Add webhook URL: `https://yourdomain.com/webhooks/razorpay`
3. Select these events:
   - `payment.captured`
   - `payment.failed`
   - `subscription.charged`
   - `subscription.cancelled`
4. Set webhook secret and add to your `.env` file

## Step 5: Start the Application

```bash
npm run start:prod
```

The server will:
1. Load billing modules automatically
2. Create database collections on first use
3. Set up API endpoints at `/api/billing/*`
4. Configure webhook endpoints at `/webhooks/*`

## Step 6: Testing the Integration

### Test Usage Tracking
```bash
# Track character usage
curl -X POST http://localhost:8080/api/billing/usage/track \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"characters": 1000, "agentId": "test_agent"}'
```

### Test Payment Method
```bash
# Get payment methods
curl -X GET http://localhost:8080/api/billing/payment-methods \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test Invoice Generation
```bash
# Generate invoice for current period
curl -X POST http://localhost:8080/api/billing/invoices/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

## API Endpoints

### Billing Profile
- `GET /api/billing/profile` - Get user billing profile
- `PUT /api/billing/profile` - Update billing profile

### Subscription
- `GET /api/billing/subscription` - Get current subscription
- `PUT /api/billing/subscription/plan` - Change subscription plan

### Usage Tracking
- `GET /api/billing/usage/current` - Get current month usage
- `GET /api/billing/usage/history` - Get usage history
- `POST /api/billing/usage/track` - Track usage (internal)

### Invoices
- `GET /api/billing/invoices` - Get user invoices
- `POST /api/billing/invoices/generate` - Generate invoice
- `GET /api/billing/invoices/:id/download` - Download invoice PDF

### Payment Methods
- `GET /api/billing/payment-methods` - Get payment methods
- `POST /api/billing/payment-methods` - Add payment method
- `DELETE /api/billing/payment-methods/:id` - Delete payment method

### Settings
- `GET /api/billing/settings` - Get billing settings
- `PUT /api/billing/settings` - Update billing settings

### Webhooks
- `POST /webhooks/razorpay` - Razorpay payment webhooks
- `GET /webhooks/health` - Webhook health check

## Pricing Configuration

The system supports three plans:

### Development Plan (Free)
- 10,000 characters per month
- Basic analytics
- API access

### Production Plan (Pay-as-you-use)
- ₹1 per 1,000 characters
- Full analytics
- WhatsApp integration
- 1M characters included

### Enterprise Plan (Custom)
- ₹0.80 per 1,000 characters
- Custom models
- Priority support
- Unlimited usage

## Usage Tracking

The system automatically tracks:
- **Characters used** in API requests and responses
- **API calls** to agent endpoints
- **Agent-specific usage** for detailed analytics
- **Cost calculations** in real-time
- **Monthly billing cycles**

## Security Features

- **Webhook signature verification** for payment security
- **JWT token authentication** for all API calls
- **User isolation** - users can only access their own data
- **Rate limiting** based on subscription limits
- **PCI DSS compliance** - no sensitive payment data stored

## Monitoring and Alerts

- **Usage alerts** at 80% of monthly limit
- **Spending alerts** for cost management
- **Payment failure notifications**
- **Webhook failure monitoring**

## Troubleshooting

### Common Issues

1. **Billing service not available**
   - Check that ES modules are loading properly
   - Verify environment variables are set
   - Check server logs for module loading errors

2. **Webhook verification failed**
   - Verify webhook secret in Razorpay dashboard
   - Check webhook URL is accessible
   - Ensure raw body parsing is enabled

3. **Firebase permission errors**
   - Verify Firebase service account credentials
   - Check Firestore security rules
   - Ensure collections have proper permissions

4. **Payment processing errors**
   - Check Razorpay API key validity
   - Verify test/live mode configuration
   - Review Razorpay dashboard for errors

### Debug Mode

Enable debug logging:
```bash
DEBUG=billing:* npm run start:prod
```

## Production Deployment

For production deployment:

1. **Use live Razorpay keys**:
   ```bash
   RAZORPAY_KEY_ID=rzp_live_your_live_key
   ```

2. **Configure proper webhook URLs**:
   ```bash
   https://yourdomain.com/webhooks/razorpay
   ```

3. **Set up SSL/TLS** for webhook security

4. **Configure monitoring** for payment failures

5. **Set up backup** for billing data

6. **Test webhook delivery** in production

## Support

For billing system issues:
1. Check server logs for detailed errors
2. Verify environment configuration
3. Test API endpoints with proper authentication
4. Review Firestore collections for data consistency
5. Check Razorpay dashboard for payment issues

## Next Steps

1. **Implement PDF invoice generation**
2. **Add email notifications** for payments
3. **Set up recurring billing** for subscriptions
4. **Add payment analytics dashboard**
5. **Implement refund processing**
6. **Add multi-currency support**