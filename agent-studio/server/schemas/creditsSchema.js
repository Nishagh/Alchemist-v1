/**
 * Credits-Based Billing Schema
 * 
 * Prepaid credits system where users buy credits before using services
 */

// User Credits Account Schema
const USER_CREDITS_SCHEMA = {
  userId: '', // Firebase Auth UID
  created_at: '', // ISO timestamp
  updated_at: '', // ISO timestamp
  
  // Current credit balance
  balance: {
    available_credits: 0, // Available credits in INR
    bonus_credits: 0, // Free/promotional credits
    total_credits: 0, // available + bonus
    reserved_credits: 0, // Credits held for ongoing operations
    
    // Credit history summary
    lifetime_purchased: 0, // Total credits ever purchased
    lifetime_used: 0, // Total credits ever used
    last_purchase_date: '', // ISO timestamp
    last_usage_date: '' // ISO timestamp
  },
  
  // Account settings
  settings: {
    low_balance_threshold: 50, // INR - when to send alerts
    auto_recharge_enabled: false,
    auto_recharge_amount: 500, // INR
    auto_recharge_trigger: 20, // INR - balance level to trigger recharge
    
    // Notification preferences
    balance_alerts: true,
    purchase_notifications: true,
    usage_alerts: true
  },
  
  // Account status
  status: {
    account_status: 'active', // active, suspended, frozen
    credit_limit: 0, // Maximum negative balance allowed (if any)
    restriction_reason: '', // If account is restricted
    last_activity: '' // ISO timestamp
  }
};

// Credit Transactions Schema
const CREDIT_TRANSACTION_SCHEMA = {
  id: '', // Auto-generated document ID
  userId: '', // Firebase Auth UID
  timestamp: '', // ISO timestamp
  
  // Transaction details
  type: 'purchase', // purchase, usage, refund, bonus, adjustment
  category: 'api_usage', // api_usage, credit_purchase, refund, bonus, admin_adjustment
  amount: 0, // Credit amount (positive for additions, negative for deductions)
  
  // Balance tracking
  balance_before: 0, // Balance before this transaction
  balance_after: 0, // Balance after this transaction
  
  // Transaction metadata
  description: 'API usage - character processing',
  reference_id: '', // External reference (payment ID, order ID, etc.)
  
  // Usage details (for usage transactions)
  usage_details: {
    characters: 0,
    tokens: 0,
    api_calls: 0,
    agent_id: '',
    cost_per_unit: 0.001, // INR per character
    service_type: 'character_processing' // character_processing, api_call, deployment, etc.
  },
  
  // Purchase details (for purchase transactions)
  purchase_details: {
    package_id: '', // Credit package purchased
    package_name: 'Starter Pack',
    base_amount: 0, // Amount before bonuses
    bonus_amount: 0, // Bonus credits added
    payment_method: 'razorpay',
    payment_id: '', // Payment gateway transaction ID
    invoice_id: '' // Generated invoice ID
  },
  
  // System metadata
  metadata: {
    ip_address: '',
    user_agent: '',
    session_id: '',
    admin_action: false, // True if done by admin
    admin_user_id: '' // Admin who performed the action
  }
};

// Credit Packages Schema (predefined packages users can buy)
const CREDIT_PACKAGE_SCHEMA = {
  id: '', // Package ID
  created_at: '', // ISO timestamp
  updated_at: '', // ISO timestamp
  
  // Package details
  name: 'Starter Pack',
  description: 'Perfect for getting started with AI agents',
  
  // Pricing
  base_credits: 100, // Base credits in INR
  bonus_credits: 0, // Additional free credits
  total_credits: 100, // base + bonus
  price: 100, // Actual price to pay in INR
  
  // Package metadata
  popular: false, // Mark as popular package
  best_value: false, // Mark as best value
  category: 'starter', // starter, professional, enterprise, custom
  
  // Validity and limits
  validity_days: 365, // Credits expire after days (0 = no expiry)
  min_purchase: 1, // Minimum quantity
  max_purchase: 10, // Maximum quantity per transaction
  
  // Features included
  features: [
    '100 credits (₹100 value)',
    '1 year validity',
    'All AI models',
    'Basic support'
  ],
  
  // Status
  status: 'active', // active, inactive, discontinued
  sort_order: 1 // Display order
};

// Credit Purchase Orders Schema
const CREDIT_ORDER_SCHEMA = {
  id: '', // Auto-generated document ID
  userId: '', // Firebase Auth UID
  created_at: '', // ISO timestamp
  updated_at: '', // ISO timestamp
  
  // Order details
  order_number: 'ORD-2024-001',
  status: 'pending', // pending, paid, failed, cancelled, refunded
  
  // Package details
  package_id: '',
  package_name: 'Starter Pack',
  quantity: 1,
  
  // Pricing
  unit_price: 100, // Price per package
  subtotal: 100, // unit_price * quantity
  tax_amount: 18, // GST amount
  tax_rate: 18, // GST rate percentage
  discount_amount: 0, // Any discounts applied
  total_amount: 118, // Final amount to pay
  currency: 'INR',
  
  // Credits
  base_credits: 100, // Base credits to be added
  bonus_credits: 0, // Bonus credits to be added
  total_credits: 100, // Total credits to be added
  
  // Payment details
  payment: {
    method: 'razorpay', // razorpay, stripe, manual
    gateway_order_id: '', // Payment gateway order ID
    gateway_payment_id: '', // Payment gateway payment ID
    paid_at: '', // ISO timestamp when payment completed
    payment_link: '', // Payment link for user
    
    // Payment failure details
    failure_reason: '',
    failure_code: '',
    retry_count: 0
  },
  
  // Customer details (snapshot)
  customer: {
    name: '',
    email: '',
    phone: '',
    address: {},
    tax_info: {}
  },
  
  // Fulfillment
  fulfillment: {
    fulfilled: false, // Whether credits have been added to account
    fulfilled_at: '', // ISO timestamp
    transaction_id: '', // Credit transaction ID
    notes: ''
  },
  
  // Invoice
  invoice: {
    invoice_id: '',
    invoice_number: 'INV-2024-001',
    generated: false,
    generated_at: '',
    download_url: ''
  }
};

// Credit Usage Limits Schema (rate limiting based on credits)
const CREDIT_LIMITS_SCHEMA = {
  userId: '', // Firebase Auth UID
  updated_at: '', // ISO timestamp
  
  // Rate limits (per time period)
  limits: {
    per_minute: {
      max_credits: 10, // Max credits that can be used per minute
      used_credits: 0, // Credits used in current minute
      reset_at: '' // When the counter resets
    },
    per_hour: {
      max_credits: 100,
      used_credits: 0,
      reset_at: ''
    },
    per_day: {
      max_credits: 1000,
      used_credits: 0,
      reset_at: ''
    }
  },
  
  // Subscription-based limits
  subscription_limits: {
    plan: 'production', // development, production, enterprise
    daily_limit: 1000, // Credits per day based on plan
    monthly_limit: 30000, // Credits per month
    concurrent_requests: 10 // Max simultaneous requests
  }
};

// Collection names
const COLLECTIONS = {
  USER_CREDITS: 'user_credits',
  CREDIT_TRANSACTIONS: 'credit_transactions',
  CREDIT_PACKAGES: 'credit_packages',
  CREDIT_ORDERS: 'credit_orders',
  CREDIT_LIMITS: 'credit_limits'
};

// Default credit packages
const DEFAULT_CREDIT_PACKAGES = [
  {
    id: 'starter_100',
    name: 'Starter Pack',
    description: 'Perfect for trying out AI agents',
    base_credits: 100,
    bonus_credits: 0,
    total_credits: 100,
    price: 100,
    popular: false,
    best_value: false,
    category: 'starter',
    features: [
      '100 credits (₹100 value)',
      '~100,000 characters',
      '1 year validity',
      'All AI models',
      'Basic support'
    ],
    status: 'active',
    sort_order: 1
  },
  {
    id: 'professional_500',
    name: 'Professional Pack',
    description: 'Great for regular AI agent usage',
    base_credits: 500,
    bonus_credits: 50, // 10% bonus
    total_credits: 550,
    price: 500,
    popular: true,
    best_value: false,
    category: 'professional',
    features: [
      '550 credits (₹500 + ₹50 bonus)',
      '~550,000 characters',
      '1 year validity',
      'All AI models',
      'Priority support'
    ],
    status: 'active',
    sort_order: 2
  },
  {
    id: 'enterprise_2000',
    name: 'Enterprise Pack',
    description: 'Best value for heavy AI usage',
    base_credits: 2000,
    bonus_credits: 400, // 20% bonus
    total_credits: 2400,
    price: 2000,
    popular: false,
    best_value: true,
    category: 'enterprise',
    features: [
      '2400 credits (₹2000 + ₹400 bonus)',
      '~2.4M characters',
      '1 year validity',
      'All AI models',
      'Premium support',
      'Custom integrations'
    ],
    status: 'active',
    sort_order: 3
  },
  {
    id: 'custom_amount',
    name: 'Custom Amount',
    description: 'Add any amount to your account',
    base_credits: 0, // Will be set based on user input
    bonus_credits: 0,
    total_credits: 0,
    price: 0,
    popular: false,
    best_value: false,
    category: 'custom',
    features: [
      'Add any amount (₹50 minimum)',
      '1 credit = ₹1',
      '1 year validity',
      'Flexible top-up'
    ],
    status: 'active',
    sort_order: 4
  }
];

// Credit system constants
const CREDITS_CONSTANTS = {
  // Pricing (all in INR)
  CHARACTERS_PER_CREDIT: 1000, // 1000 characters = 1 credit (₹1)
  TOKENS_PER_CREDIT: 1000, // 1000 tokens = 1 credit
  API_CALL_COST: 0.01, // Credits per API call
  
  // Credit constraints
  MIN_BALANCE: 0, // Minimum balance allowed
  MIN_PURCHASE: 50, // Minimum purchase amount in INR
  MAX_PURCHASE: 50000, // Maximum purchase amount in INR
  DEFAULT_LOW_BALANCE_THRESHOLD: 50, // Default alert threshold
  
  // Auto-recharge settings
  DEFAULT_AUTO_RECHARGE_AMOUNT: 500,
  DEFAULT_AUTO_RECHARGE_TRIGGER: 20,
  
  // Credit expiry
  DEFAULT_CREDIT_VALIDITY_DAYS: 365, // 1 year
  
  // Rate limiting
  DEFAULT_RATE_LIMITS: {
    per_minute: 10,
    per_hour: 100,
    per_day: 1000
  },
  
  // Bonus credit rules
  BONUS_THRESHOLDS: [
    { min_amount: 500, bonus_percentage: 10 }, // 10% bonus for ₹500+
    { min_amount: 1000, bonus_percentage: 15 }, // 15% bonus for ₹1000+
    { min_amount: 2000, bonus_percentage: 20 }, // 20% bonus for ₹2000+
    { min_amount: 5000, bonus_percentage: 25 }  // 25% bonus for ₹5000+
  ]
};

// CommonJS exports
module.exports = {
  USER_CREDITS_SCHEMA,
  CREDIT_TRANSACTION_SCHEMA,
  CREDIT_PACKAGE_SCHEMA,
  CREDIT_ORDER_SCHEMA,
  CREDIT_LIMITS_SCHEMA,
  COLLECTIONS,
  DEFAULT_CREDIT_PACKAGES,
  CREDITS_CONSTANTS
};