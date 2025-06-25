"""
Centralized Firebase Collection Constants for Billing Service

Local copy of collection constants to avoid import path issues during deployment.
"""

class Collections:
    """Collection name constants."""
    
    # Core collections
    AGENTS = "agents"
    AGENT_DEPLOYMENTS = "agent_deployments"
    AGENT_USAGE_SUMMARY = "agent_usage_summary"
    CONVERSATIONS = "conversations"
    COMMUNICATION_LOGS = "communication_logs"
    USER_ACCOUNTS = "user_accounts"
    CREDIT_TRANSACTIONS = "credit_transactions"
    KNOWLEDGE_FILES = "knowledge_files"
    KNOWLEDGE_EMBEDDINGS = "knowledge_embeddings"
    TRAINING_JOBS = "training_jobs"
    INTEGRATION_CHANNELS = "integration_channels"
    
    # Deprecated collections
    class Deprecated:
        USER_CREDITS = "user_credits"
        AGENT_BILLING_SUMMARY = "agent_billing_summary"


class DocumentFields:
    """Document field name constants."""
    
    # Common fields
    ID = "id"
    AGENT_ID = "agent_id"
    USER_ID = "user_id"
    DEPLOYMENT_ID = "deployment_id"
    FILE_ID = "file_id"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TIMESTAMP = "timestamp"
    STATUS = "status"
    PROCESSING_STATUS = "processing_status"
    
    class Billing:
        CREDIT_BALANCE = "credit_balance"
        TOTAL_CREDITS_PURCHASED = "total_credits_purchased"
        TOTAL_CREDITS_USED = "total_credits_used"
        ACCOUNT_STATUS = "account_status"
        TRANSACTION_TYPE = "transaction_type"
        AMOUNT = "amount"
        PAYMENT_PROVIDER = "payment_provider"


class StatusValues:
    """Status value constants."""
    
    class Account:
        ACTIVE = "active"
        SUSPENDED = "suspended"
        TRIAL = "trial"
    
    class Transaction:
        PURCHASE = "purchase"
        USAGE = "usage"
        ADJUSTMENT = "adjustment"
        REFUND = "refund"