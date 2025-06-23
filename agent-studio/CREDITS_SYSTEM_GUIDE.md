# Prepaid Credits System - Complete Guide

## 🎯 Overview

The Alchemist Agent Studio now uses a **prepaid credits system** instead of postpaid billing. Users purchase credits upfront and credits are deducted in real-time as they use AI services.

### Key Benefits:
- ✅ **Better User Experience** - No surprise bills
- ✅ **Improved Cash Flow** - Payment upfront
- ✅ **Real-time Usage Control** - Services stop when credits run out
- ✅ **Transparent Pricing** - 1 credit = ₹1 = ~1000 characters
- ✅ **Bonus Credits** - Bulk purchase incentives

## 🏗️ System Architecture

```
User Purchase Credits → Credits Added to Account → API Usage Deducts Credits → Real-time Balance Updates
```

### Components:
1. **Credits Account** - User's prepaid balance
2. **Credit Packages** - Predefined purchase options
3. **Usage Tracking** - Real-time credit deduction
4. **Payment Integration** - Razorpay for Indian payments
5. **Admin Dashboard** - Credit management tools

## 💰 Pricing Structure

### Credit Value:
- **1 Credit = ₹1**
- **1 Credit ≈ 1000 characters**
- **API Call = 0.01 credits**

### Default Packages:

#### 1. Starter Pack (₹100)
- 100 base credits + 0 bonus = **100 total credits**
- Perfect for testing and small projects
- ~100,000 characters of AI processing

#### 2. Professional Pack (₹500) - POPULAR
- 500 base credits + 50 bonus = **550 total credits**
- 10% bonus credits included
- ~550,000 characters of AI processing

#### 3. Enterprise Pack (₹2000) - BEST VALUE
- 2000 base credits + 400 bonus = **2400 total credits**
- 20% bonus credits included
- ~2.4M characters of AI processing

#### 4. Custom Amount
- Minimum ₹50, Maximum ₹50,000
- Flexible top-up option
- Bonus credits based on amount

### Bonus Credit Tiers:
- **₹500+**: 10% bonus
- **₹1000+**: 15% bonus
- **₹2000+**: 20% bonus
- **₹5000+**: 25% bonus

## 🗄️ Database Schema

### Collections:
1. **`user_credits`** - User credit accounts
2. **`credit_transactions`** - All credit movements
3. **`credit_packages`** - Available packages
4. **`credit_orders`** - Purchase orders
5. **`credit_limits`** - Rate limiting

### Key Features:
- **Atomic Transactions** - Credit deduction is always consistent
- **Real-time Balance** - Updated with every API call
- **Audit Trail** - Complete transaction history
- **Bonus Tracking** - Separate bonus credit pools

## 🚀 API Endpoints

### Credits Management:
```bash
GET    /api/credits/balance          # Get current balance
GET    /api/credits/account          # Get full account details
GET    /api/credits/status           # Get comprehensive status
PUT    /api/credits/settings         # Update account settings
```

### Packages & Purchase:
```bash
GET    /api/credits/packages         # Get available packages
POST   /api/credits/purchase         # Create purchase order
POST   /api/credits/purchase/verify  # Verify payment
GET    /api/credits/orders           # Get purchase history
```

### Transaction History:
```bash
GET    /api/credits/transactions     # Get transaction history
GET    /api/credits/usage            # Get usage summary
```

### Admin Functions:
```bash
POST   /api/credits/add              # Add credits (admin only)
```

## 🔧 Implementation Details

### Credit Deduction Flow:
1. **Pre-Check** - Verify sufficient credits before API call
2. **Usage Tracking** - Monitor characters in request/response
3. **Real-time Deduction** - Deduct credits after successful API call
4. **Balance Update** - Update user's account balance
5. **Low Balance Alert** - Notify if balance falls below threshold

### Payment Flow:
1. **Order Creation** - Create credit purchase order
2. **Payment Gateway** - Redirect to Razorpay checkout
3. **Payment Verification** - Verify payment signature
4. **Credit Addition** - Add credits to user account
5. **Confirmation** - Send confirmation to user

### Security Features:
- **JWT Authentication** - All API calls require valid token
- **Signature Verification** - Razorpay webhook signatures verified
- **Atomic Transactions** - Credit operations are atomic
- **Rate Limiting** - Per-minute/hour/day usage limits
- **Audit Logging** - All credit movements logged

## 🎨 Frontend Integration

### Key Components:
1. **Credits Page** (`/credits`) - Main credits management interface
2. **Credit Balance Widget** - Real-time balance display
3. **Purchase Flow** - Razorpay integration
4. **Transaction History** - Usage and purchase history
5. **Low Balance Alerts** - Automatic notifications

### Features:
- **Real-time Balance** - Updates after each API call
- **Purchase Packages** - One-click credit purchases
- **Custom Amounts** - Flexible top-up options
- **Transaction History** - Detailed usage tracking
- **Settings Management** - Alert preferences and thresholds

## 📊 Monitoring & Analytics

### User Analytics:
- **Balance Trends** - Credit usage over time
- **Usage Patterns** - Character usage by agent/service
- **Purchase Behavior** - Preferred package sizes
- **Low Balance Alerts** - Alert frequency and response

### Business Metrics:
- **Revenue Recognition** - Immediate upon purchase
- **Credit Utilization** - Usage vs purchase ratios
- **Churn Indicators** - Users with zero balance
- **Package Performance** - Most popular packages

## ⚙️ Configuration

### Environment Variables:
```bash
# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Credits Configuration
DEFAULT_LOW_BALANCE_THRESHOLD=50
MIN_PURCHASE_AMOUNT=50
MAX_PURCHASE_AMOUNT=50000
DEFAULT_CREDIT_VALIDITY_DAYS=365

# Rate Limiting
CREDITS_PER_MINUTE_LIMIT=10
CREDITS_PER_HOUR_LIMIT=100
CREDITS_PER_DAY_LIMIT=1000
```

### Package Configuration:
Credit packages are stored in Firestore and can be updated via admin interface:

```javascript
{
  id: 'professional_500',
  name: 'Professional Pack',
  base_credits: 500,
  bonus_credits: 50,
  price: 500,
  popular: true,
  features: [...]
}
```

## 🧪 Testing

### Test Scenarios:

#### Credit Purchase:
1. **Successful Purchase** - Complete purchase flow
2. **Payment Failure** - Handle failed payments
3. **Webhook Verification** - Test webhook processing
4. **Bonus Credits** - Verify bonus credit calculation

#### Credit Usage:
1. **Sufficient Credits** - Normal API usage
2. **Insufficient Credits** - Reject API calls
3. **Real-time Deduction** - Verify immediate deduction
4. **Balance Updates** - Check balance consistency

#### Edge Cases:
1. **Concurrent Usage** - Multiple API calls simultaneously
2. **Race Conditions** - Credit deduction atomicity
3. **Network Failures** - Handle payment/webhook failures
4. **Invalid Requests** - Malformed purchase requests

### Test Data:
```bash
# Create test credit packages
POST /api/credits/packages (admin)

# Add test credits to user
POST /api/credits/add
{
  "targetUserId": "test_user_id",
  "amount": 100,
  "reason": "Testing"
}

# Test API usage
POST /api/alchemist/interact
{
  "message": "Test message to deduct credits"
}
```

## 🚀 Deployment

### Pre-deployment Checklist:
- [ ] Razorpay account configured
- [ ] Webhook endpoints secured
- [ ] Environment variables set
- [ ] Database collections created
- [ ] Default packages initialized
- [ ] Payment gateway tested
- [ ] Credit deduction tested
- [ ] Frontend integration tested

### Deployment Steps:
1. **Deploy Backend** - Credits API and middleware
2. **Configure Webhooks** - Razorpay webhook URLs
3. **Initialize Packages** - Default credit packages
4. **Test Payments** - End-to-end payment flow
5. **Deploy Frontend** - Updated credits interface
6. **Monitor Logs** - Watch for errors

### Post-deployment:
- **Monitor Payments** - Check successful transactions
- **Verify Webhooks** - Ensure webhook processing
- **Test User Flow** - Complete purchase and usage flow
- **Check Analytics** - Credit usage metrics

## 🔧 Maintenance

### Regular Tasks:
- **Monitor Low Balances** - Users needing credits
- **Track Usage Patterns** - Identify heavy users
- **Update Packages** - Adjust pricing/bonuses
- **Process Refunds** - Handle refund requests
- **Audit Transactions** - Verify credit movements

### Troubleshooting:

#### Common Issues:
1. **Credits Not Added** - Check webhook processing
2. **Double Deduction** - Verify transaction atomicity
3. **Payment Failures** - Check Razorpay configuration
4. **Balance Inconsistency** - Audit transaction logs

#### Solutions:
1. **Webhook Replay** - Replay failed webhooks
2. **Manual Credit Addition** - Admin credit adjustment
3. **Transaction Reversal** - Reverse incorrect deductions
4. **Balance Reconciliation** - Recalculate from transactions

## 📈 Future Enhancements

### Planned Features:
1. **Auto-recharge** - Automatic credit purchases
2. **Credit Gifting** - Transfer credits between users
3. **Usage Predictions** - Predict credit needs
4. **Bulk Discounts** - Enterprise pricing tiers
5. **Credit Expiry** - Time-based credit expiration
6. **Referral Credits** - Bonus credits for referrals

### Integration Options:
1. **Multiple Payment Gateways** - Stripe, PayPal support
2. **Mobile Payments** - UPI, mobile wallet integration
3. **Cryptocurrency** - Bitcoin/Ethereum payments
4. **Enterprise Billing** - Invoice-based purchases
5. **Subscription Model** - Monthly credit allowances

## 📞 Support

### User Support:
- **Credit Purchase Issues** - Payment gateway problems
- **Balance Discrepancies** - Credit calculation errors
- **Refund Requests** - Credit refund processing
- **Usage Questions** - How credits are calculated

### Developer Support:
- **API Integration** - Credit checking in custom apps
- **Webhook Implementation** - Payment processing
- **Database Queries** - Credit transaction analysis
- **Rate Limiting** - Usage threshold configuration

---

## 🎉 Benefits of Prepaid Credits System

### For Users:
- **No Surprises** - Know exactly what you're spending
- **Better Control** - Stop services when credits run out
- **Bonus Credits** - Get more value with bulk purchases
- **Transparent Pricing** - Clear cost per character/API call

### For Business:
- **Improved Cash Flow** - Payment received upfront
- **Reduced Churn** - Users think twice before leaving with credits
- **Better Analytics** - Real-time usage tracking
- **Scalable Model** - Easy to add new pricing tiers

The prepaid credits system provides a much better experience for both users and the business, with transparent pricing, real-time usage control, and improved cash flow management.