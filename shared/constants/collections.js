/**
 * Centralized Firebase Collection Constants for Alchemist Platform
 * 
 * This module defines all Firestore collection names used across the platform
 * to ensure consistency and prevent typos in collection references.
 * 
 * Usage:
 *   import { Collections, DocumentFields } from './constants/collections';
 *   
 *   // Access collection name
 *   const agentsRef = collection(db, Collections.AGENTS);
 *   
 *   // Use in queries
 *   const q = query(collection(db, Collections.CONVERSATIONS), 
 *                   where(DocumentFields.Conversation.AGENT_ID, '==', agentId));
 */

/**
 * Centralized collection name constants.
 * All collection names follow snake_case convention for consistency.
 */
export const Collections = {
  // ============================================================================
  // CORE COLLECTIONS
  // ============================================================================
  
  // Agent management
  AGENTS: 'agents',
  AGENT_DEPLOYMENTS: 'agent_deployments',
  AGENT_USAGE_SUMMARY: 'agent_usage_summary',
  
  // Conversation and messaging
  CONVERSATIONS: 'conversations',
  COMMUNICATION_LOGS: 'communication_logs',
  
  // User and billing management
  USER_ACCOUNTS: 'user_accounts',
  CREDIT_TRANSACTIONS: 'credit_transactions',
  
  // Knowledge base
  KNOWLEDGE_FILES: 'knowledge_files',
  KNOWLEDGE_EMBEDDINGS: 'knowledge_embeddings',
  
  // Training and AI
  TRAINING_JOBS: 'training_jobs',
  
  // Integrations
  INTEGRATION_CHANNELS: 'integration_channels',
  
};

/**
 * Standardized document field names used across collections.
 * These ensure consistent field naming and help prevent typos.
 */
export const DocumentFields = {
  // ============================================================================
  // COMMON FIELDS
  // ============================================================================
  
  // Primary identifiers
  ID: 'id',
  AGENT_ID: 'agent_id',
  USER_ID: 'user_id',
  DEPLOYMENT_ID: 'deployment_id',
  FILE_ID: 'file_id',
  
  // Timestamps (using snake_case for consistency)
  CREATED_AT: 'created_at',
  UPDATED_AT: 'updated_at',
  TIMESTAMP: 'timestamp',
  
  // Status fields
  STATUS: 'status',
  PROCESSING_STATUS: 'processing_status',
  
  // ============================================================================
  // AGENT FIELDS
  // ============================================================================
  
  Agent: {
    NAME: 'name',
    DESCRIPTION: 'description',
    TYPE: 'type',
    OWNER_ID: 'owner_id',
    DEPLOYMENT_STATUS: 'deployment_status',
    ACTIVE_DEPLOYMENT_ID: 'active_deployment_id',
    SERVICE_URL: 'service_url',
    LAST_DEPLOYED_AT: 'last_deployed_at',
  },
  
  // ============================================================================
  // CONVERSATION FIELDS
  // ============================================================================
  
  Conversation: {
    CONVERSATION_ID: 'conversation_id',
    MESSAGE_CONTENT: 'message_content',
    AGENT_RESPONSE: 'agent_response',
    IS_PRODUCTION: 'is_production',
    DEPLOYMENT_TYPE: 'deployment_type',
    TOKENS: 'tokens',
    COST_USD: 'cost_usd',
    CONTEXT: 'context',
    
    // Token subfields
    PROMPT_TOKENS: 'prompt_tokens',
    COMPLETION_TOKENS: 'completion_tokens',
    TOTAL_TOKENS: 'total_tokens',
  },
  
  // ============================================================================
  // BILLING FIELDS
  // ============================================================================
  
  Billing: {
    CREDIT_BALANCE: 'credit_balance',
    TOTAL_CREDITS_PURCHASED: 'total_credits_purchased',
    TOTAL_CREDITS_USED: 'total_credits_used',
    ACCOUNT_STATUS: 'account_status',
    TRANSACTION_TYPE: 'transaction_type',
    AMOUNT: 'amount',
    PAYMENT_PROVIDER: 'payment_provider',
  },
  
  // ============================================================================
  // KNOWLEDGE BASE FIELDS
  // ============================================================================
  
  Knowledge: {
    ORIGINAL_FILENAME: 'original_filename',
    STORAGE_PATH: 'storage_path',
    FILE_SIZE_BYTES: 'file_size_bytes',
    FILE_TYPE: 'file_type',
    CHUNK_COUNT: 'chunk_count',
    TEXT_CONTENT: 'text_content',
    EMBEDDING_VECTOR: 'embedding_vector',
    PAGE_NUMBER: 'page_number',
    CHUNK_INDEX: 'chunk_index',
  },
};

/**
 * Standardized status values used across the platform.
 */
export const StatusValues = {
  // ============================================================================
  // DEPLOYMENT STATUS
  // ============================================================================
  
  Deployment: {
    PENDING: 'pending',
    BUILDING: 'building',
    DEPLOYED: 'deployed',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
  },
  
  // ============================================================================
  // PROCESSING STATUS
  // ============================================================================
  
  Processing: {
    PENDING: 'pending',
    PROCESSING: 'processing',
    COMPLETED: 'completed',
    FAILED: 'failed',
  },
  
  // ============================================================================
  // ACCOUNT STATUS
  // ============================================================================
  
  Account: {
    ACTIVE: 'active',
    SUSPENDED: 'suspended',
    TRIAL: 'trial',
  },
  
  // ============================================================================
  // TRANSACTION TYPES
  // ============================================================================
  
  Transaction: {
    PURCHASE: 'purchase',
    USAGE: 'usage',
    ADJUSTMENT: 'adjustment',
    REFUND: 'refund',
  },
  
  // ============================================================================
  // AGENT TYPES
  // ============================================================================
  
  AgentType: {
    GENERAL: 'general',
    CODE: 'code',
    RESEARCH: 'research',
    WRITING: 'writing',
    DATA: 'data',
    CUSTOMER: 'customer',
  },
};

/**
 * Standardized error messages for common Firebase operations.
 */
export const ErrorMessages = {
  AGENT_NOT_FOUND: 'Agent not found',
  AGENT_ACCESS_DENIED: 'Access denied: You do not own this agent',
  USER_NOT_AUTHENTICATED: 'User not authenticated',
  INSUFFICIENT_CREDITS: 'Insufficient credits for this operation',
  INVALID_COLLECTION_NAME: 'Invalid collection name',
};

/**
 * Get list of all current collection names.
 * @returns {string[]} Array of collection names
 */
export const getAllCollections = () => {
  return [
    Collections.AGENTS,
    Collections.AGENT_DEPLOYMENTS,
    Collections.AGENT_USAGE_SUMMARY,
    Collections.CONVERSATIONS,
    Collections.COMMUNICATION_LOGS,
    Collections.USER_ACCOUNTS,
    Collections.CREDIT_TRANSACTIONS,
    Collections.KNOWLEDGE_FILES,
    Collections.KNOWLEDGE_EMBEDDINGS,
    Collections.TRAINING_JOBS,
    Collections.INTEGRATION_CHANNELS,
  ];
};


/**
 * Check if collection name is in current valid set.
 * @param {string} collectionName - The collection name to validate
 * @returns {boolean} True if valid, false otherwise
 */
export const isValidCollection = (collectionName) => {
  return getAllCollections().includes(collectionName);
};


/**
 * Validate collection name usage.
 * @param {string} collectionName - The collection name to validate
 * @throws {Error} If collection name is not recognized
 */
export const validateCollectionUsage = (collectionName) => {
  if (!isValidCollection(collectionName)) {
    throw new Error(`${ErrorMessages.INVALID_COLLECTION_NAME}: ${collectionName}`);
  }
};



// ============================================================================
// TYPESCRIPT TYPE DEFINITIONS (when used in .ts files)
// ============================================================================

/**
 * @typedef {Object} AgentDocument
 * @property {string} agent_id
 * @property {string} name
 * @property {string} description
 * @property {string} type
 * @property {string} owner_id
 * @property {string} deployment_status
 * @property {string} [active_deployment_id]
 * @property {string} [service_url]
 * @property {Date} created_at
 * @property {Date} updated_at
 * @property {Date} [last_deployed_at]
 */

/**
 * @typedef {Object} ConversationDocument
 * @property {string} conversation_id
 * @property {string} agent_id
 * @property {string} [user_id]
 * @property {string} message_content
 * @property {string} agent_response
 * @property {boolean} is_production
 * @property {string} deployment_type
 * @property {Object} tokens
 * @property {number} tokens.prompt_tokens
 * @property {number} tokens.completion_tokens
 * @property {number} tokens.total_tokens
 * @property {number} cost_usd
 * @property {Date} timestamp
 * @property {Date} created_at
 */

/**
 * @typedef {Object} UserAccountDocument
 * @property {string} user_id
 * @property {string} email
 * @property {string} display_name
 * @property {number} credit_balance
 * @property {number} total_credits_purchased
 * @property {number} total_credits_used
 * @property {string} account_status
 * @property {number} [trial_credits_remaining]
 * @property {Date} created_at
 * @property {Date} updated_at
 * @property {Date} [last_activity_at]
 */