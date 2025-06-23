/**
 * Billing Database Schema Definitions
 * 
 * This file defines the structure for all billing-related Firestore collections
 */

// User Billing Profile Schema
const USER_BILLING_SCHEMA = {
  userId: '', // Firebase Auth UID
  created_at: '', // ISO timestamp
  updated_at: '', // ISO timestamp
  profile: {
    name: '',
    email: '',
    phone: '',
    company: '',
    address: {
      line1: '',
      line2: '',
      city: '',
      state: '',
      postal_code: '',
      country: 'IN' // Default to India
    },
    tax_info: {
      gstin: '', // GST Identification Number for Indian businesses
      pan: '', // PAN for Indian tax
      business_type: 'individual' // individual, business
    }
  },
  preferences: {
    currency: 'INR',
    timezone: 'Asia/Kolkata',
    email_notifications: true,
    invoice_emails: true,
    usage_alerts: true,
    spending_alerts: true
  },
  limits: {
    monthly_spending_limit: 1000, // INR
    usage_alerts_threshold: 80, // percentage
    auto_recharge: false,
    auto_recharge_amount: 500 // INR
  }
};

// Usage Tracking Schema
const USAGE_TRACKING_SCHEMA = {
  id: '', // Auto-generated document ID
  userId: '', // Firebase Auth UID
  timestamp: '', // ISO timestamp
  period: '', // 'YYYY-MM' for monthly aggregation
  
  // Usage metrics
  metrics: {
    characters_used: 0,
    tokens_used: 0,
    api_calls: 0,
    agent_interactions: 0,
    knowledge_base_queries: 0,
    deployment_minutes: 0
  },
  
  // Cost breakdown
  costs: {
    character_cost: 0, // INR
    token_cost: 0, // INR
    api_cost: 0, // INR
    deployment_cost: 0, // INR
    total_cost: 0 // INR
  },
  
  // Agent-specific usage
  agent_usage: {
    // agent_id: { characters: 0, tokens: 0, calls: 0, cost: 0 }
  },
  
  // Billing cycle info
  billing_cycle: {
    start_date: '', // ISO timestamp
    end_date: '', // ISO timestamp
    cycle_id: '' // e.g., '2024-01'
  }
};

// Subscription Schema
const SUBSCRIPTION_SCHEMA = {
  id: '', // Auto-generated document ID
  userId: '', // Firebase Auth UID
  created_at: '', // ISO timestamp
  updated_at: '', // ISO timestamp
  
  // Plan details
  plan: {
    id: 'production', // development, production, enterprise
    name: 'Production',
    type: 'pay_per_use', // pay_per_use, monthly, annual
    status: 'active', // active, inactive, suspended, cancelled
    
    // Pricing structure
    pricing: {
      character_rate: 0.001, // INR per character
      token_rate: 0.001, // INR per token
      api_rate: 0.01, // INR per API call
      deployment_rate: 1.0, // INR per minute
      
      // Tier pricing
      tiers: [
        {
          name: 'Base',
          up_to: 100000, // characters
          rate: 0.001 // INR per character
        }
      ]
    }
  },
  
  // Billing cycle
  billing: {
    cycle: 'monthly', // monthly, annual
    next_billing_date: '', // ISO timestamp
    last_billing_date: '', // ISO timestamp
    billing_day: 1, // Day of month for billing
    
    // Payment method
    payment_method_id: '', // Reference to payment method
    auto_pay: true
  },
  
  // Usage limits
  limits: {
    characters_per_month: 1000000,
    tokens_per_month: 1000000,
    api_calls_per_month: 10000,
    agents_limit: 10,
    knowledge_base_size_mb: 100
  },
  
  // Features included
  features: {
    analytics: true,
    custom_models: false,
    priority_support: false,
    whatsapp_integration: true,
    api_access: true,
    webhook_support: true
  }
};

// Payment Method Schema
const PAYMENT_METHOD_SCHEMA = {
  id: '', // Auto-generated document ID
  userId: '', // Firebase Auth UID
  created_at: '', // ISO timestamp
  updated_at: '', // ISO timestamp
  
  // Payment method details (NO sensitive data stored here)
  type: 'card', // card, upi, netbanking, wallet
  provider: 'razorpay', // razorpay, stripe
  
  // Card metadata (non-sensitive)
  card: {
    last4: '4242',
    brand: 'visa', // visa, mastercard, amex, etc.
    exp_month: 12,
    exp_year: 2027,
    country: 'IN'
  },
  
  // UPI metadata
  upi: {
    vpa: 'user@paytm' // Virtual Payment Address
  },
  
  // Status and settings
  status: 'active', // active, inactive, expired, failed
  is_default: true,
  
  // Provider-specific data
  provider_data: {
    payment_method_id: '', // Razorpay payment method ID
    customer_id: '', // Razorpay customer ID
    token: '' // Provider token for recurring payments
  }
};

// Invoice Schema
const INVOICE_SCHEMA = {
  id: '', // Auto-generated document ID (also used as invoice number)
  userId: '', // Firebase Auth UID
  created_at: '', // ISO timestamp
  updated_at: '', // ISO timestamp
  
  // Invoice details
  invoice_number: 'INV-2024-001',
  invoice_date: '', // ISO timestamp
  due_date: '', // ISO timestamp
  billing_period: {
    start: '', // ISO timestamp
    end: '' // ISO timestamp
  },
  
  // Amount details
  amounts: {
    subtotal: 0, // INR before tax
    tax_amount: 0, // GST amount
    tax_rate: 18, // GST rate percentage
    discount_amount: 0,
    total_amount: 0, // Final amount
    currency: 'INR'
  },
  
  // Line items
  line_items: [
    {
      description: 'API Usage - Characters',
      quantity: 125420,
      unit: 'characters',
      unit_price: 0.001,
      amount: 125.42
    }
  ],
  
  // Payment info
  payment: {
    status: 'paid', // pending, paid, failed, cancelled
    method: 'card',
    transaction_id: '',
    paid_at: '', // ISO timestamp
    payment_method_id: ''
  },
  
  // Customer info (snapshot at time of invoice)
  customer: {
    name: '',
    email: '',
    address: {},
    tax_info: {}
  },
  
  // Files and downloads
  files: {
    pdf_url: '', // Generated PDF URL
    download_count: 0,
    last_downloaded: ''
  },
  
  // Metadata
  metadata: {
    subscription_id: '',
    billing_cycle_id: '',
    auto_generated: true
  }
};

// Transaction Schema
const TRANSACTION_SCHEMA = {
  id: '', // Auto-generated document ID
  userId: '', // Firebase Auth UID
  created_at: '', // ISO timestamp
  
  // Transaction details
  type: 'payment', // payment, refund, adjustment, credit
  status: 'completed', // pending, completed, failed, cancelled
  
  // Amount details
  amount: 0, // INR
  currency: 'INR',
  fee: 0, // Transaction fee
  net_amount: 0, // Amount after fee
  
  // Related entities
  invoice_id: '', // Related invoice
  subscription_id: '', // Related subscription
  payment_method_id: '', // Payment method used
  
  // Provider details
  provider: 'razorpay',
  provider_transaction_id: '',
  provider_data: {}, // Raw provider response
  
  // Description and metadata
  description: 'Payment for API usage',
  metadata: {
    billing_cycle: '',
    usage_period: ''
  },
  
  // Failure info (if applicable)
  failure_reason: '',
  failure_code: ''
};

// Collection names
const COLLECTIONS = {
  USER_BILLING: 'user_billing',
  USAGE_TRACKING: 'usage_tracking',
  SUBSCRIPTIONS: 'subscriptions',
  PAYMENT_METHODS: 'payment_methods',
  INVOICES: 'invoices',
  TRANSACTIONS: 'transactions'
};

// Default values and constants
const BILLING_CONSTANTS = {
  DEFAULT_CURRENCY: 'INR',
  DEFAULT_PLAN: 'production',
  DEFAULT_BILLING_CYCLE: 'monthly',
  DEFAULT_TAX_RATE: 18, // GST rate in India
  
  // Pricing (INR)
  PRICING: {
    CHARACTERS_PER_INR: 1000, // 1000 characters = 1 INR
    TOKENS_PER_INR: 1000, // 1000 tokens = 1 INR
    API_CALL_RATE: 0.01, // INR per API call
    DEPLOYMENT_RATE: 1.0 // INR per minute
  },
  
  // Plans
  PLANS: {
    DEVELOPMENT: {
      id: 'development',
      name: 'Development',
      character_rate: 0,
      monthly_limit: 10000,
      features: ['basic_analytics']
    },
    PRODUCTION: {
      id: 'production',
      name: 'Production',
      character_rate: 0.001,
      monthly_limit: 1000000,
      features: ['analytics', 'whatsapp_integration', 'api_access']
    },
    ENTERPRISE: {
      id: 'enterprise',
      name: 'Enterprise',
      character_rate: 0.0008,
      monthly_limit: -1, // Unlimited
      features: ['analytics', 'custom_models', 'priority_support', 'whatsapp_integration', 'api_access', 'webhook_support']
    }
  }
};

// Export all constants using CommonJS format
module.exports = {
  USER_BILLING_SCHEMA,
  USAGE_TRACKING_SCHEMA,
  SUBSCRIPTION_SCHEMA,
  PAYMENT_METHOD_SCHEMA,
  INVOICE_SCHEMA,
  TRANSACTION_SCHEMA,
  COLLECTIONS,
  BILLING_CONSTANTS
};