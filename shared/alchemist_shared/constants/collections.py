"""
Centralized Firebase Collection Constants for Alchemist Platform

This module defines all Firestore collection names used across the platform
to ensure consistency and prevent typos in collection references.

Usage:
    from alchemist_shared.constants.collections import Collections
    
    # Access collection name
    agents_ref = db.collection(Collections.AGENTS)
    
    # Use in queries
    query = db.collection(Collections.CONVERSATIONS).where('agent_id', '==', agent_id)
"""

class Collections:
    """
    Centralized collection name constants.
    
    All collection names follow snake_case convention for consistency.
    """
    
    # ============================================================================
    # CORE COLLECTIONS
    # ============================================================================
    
    # Agent management
    AGENTS = "agents"
    AGENT_DEPLOYMENTS = "agent_deployments"
    AGENT_USAGE_SUMMARY = "agent_usage_summary"
    
    # Conversation and messaging
    CONVERSATIONS = "conversations"
    COMMUNICATION_LOGS = "communication_logs"
    API_LOGS = "api_logs"
    
    # User and billing management
    USER_ACCOUNTS = "user_accounts"
    CREDIT_TRANSACTIONS = "credit_transactions"
    
    # Knowledge base
    KNOWLEDGE_FILES = "knowledge_files"
    KNOWLEDGE_EMBEDDINGS = "knowledge_embeddings"
    
    # Training and AI
    TRAINING_JOBS = "training_jobs"
    
    # Integrations
    INTEGRATION_CHANNELS = "integration_channels"
    
    # ============================================================================
    # GLOBAL NARRATIVE FRAMEWORK COLLECTIONS
    # ============================================================================
    
    # Agent identity and narrative
    AGENT_IDENTITIES = "agent_identities"
    AGENT_INTERACTIONS = "agent_interactions"
    AGENT_MEMORIES = "agent_memories"
    EVOLUTION_EVENTS = "evolution_events"
    RESPONSIBILITY_ASSESSMENTS = "responsibility_assessments"
    
    # Cross-agent and global narrative
    GLOBAL_EVENTS = "global_events"
    AGENT_RELATIONSHIPS = "agent_relationships"
    
    # ============================================================================
    # DEPRECATED COLLECTIONS (For Migration Reference)
    # ============================================================================
    
    class Deprecated:
        """Legacy collection names that should be migrated to new naming."""
        ALCHEMIST_AGENTS = "alchemist_agents"
        DEV_CONVERSATIONS = "dev_conversations"
        KNOWLEDGE_BASE_FILES = "knowledge_base_files"
        USER_CREDITS = "user_credits"
        AGENT_BILLING_SUMMARY = "agent_billing_summary"
        MANAGED_ACCOUNTS = "managed_accounts"
        WEBHOOK_LOGS = "webhook_logs"
        KNOWLEDGE_BASE_EMBEDDINGS = "knowledge_base_embeddings"
    
    # ============================================================================
    # VALIDATION HELPERS
    # ============================================================================
    
    @classmethod
    def get_all_collections(cls) -> list[str]:
        """Get list of all current collection names."""
        return [
            cls.AGENTS,
            cls.AGENT_DEPLOYMENTS,
            cls.AGENT_USAGE_SUMMARY,
            cls.CONVERSATIONS,
            cls.COMMUNICATION_LOGS,
            cls.API_LOGS,
            cls.USER_ACCOUNTS,
            cls.CREDIT_TRANSACTIONS,
            cls.KNOWLEDGE_FILES,
            cls.KNOWLEDGE_EMBEDDINGS,
            cls.TRAINING_JOBS,
            cls.INTEGRATION_CHANNELS,
            # GNF Collections
            cls.AGENT_IDENTITIES,
            cls.AGENT_INTERACTIONS,
            cls.AGENT_MEMORIES,
            cls.EVOLUTION_EVENTS,
            cls.RESPONSIBILITY_ASSESSMENTS,
            cls.GLOBAL_EVENTS,
            cls.AGENT_RELATIONSHIPS,
        ]
    
    @classmethod
    def get_deprecated_collections(cls) -> list[str]:
        """Get list of deprecated collection names."""
        return [
            cls.Deprecated.ALCHEMIST_AGENTS,
            cls.Deprecated.DEV_CONVERSATIONS,
            cls.Deprecated.KNOWLEDGE_BASE_FILES,
            cls.Deprecated.USER_CREDITS,
            cls.Deprecated.AGENT_BILLING_SUMMARY,
            cls.Deprecated.MANAGED_ACCOUNTS,
            cls.Deprecated.WEBHOOK_LOGS,
            cls.Deprecated.KNOWLEDGE_BASE_EMBEDDINGS,
        ]
    
    @classmethod
    def is_valid_collection(cls, collection_name: str) -> bool:
        """Check if collection name is in current valid set."""
        return collection_name in cls.get_all_collections()
    
    @classmethod
    def is_deprecated_collection(cls, collection_name: str) -> bool:
        """Check if collection name is deprecated."""
        return collection_name in cls.get_deprecated_collections()


class DocumentFields:
    """
    Standardized document field names used across collections.
    
    These ensure consistent field naming and help prevent typos.
    """
    
    # ============================================================================
    # COMMON FIELDS
    # ============================================================================
    
    # Primary identifiers
    ID = "id"
    AGENT_ID = "agent_id"
    USER_ID = "user_id"
    DEPLOYMENT_ID = "deployment_id"
    FILE_ID = "file_id"
    
    # Timestamps (using snake_case for consistency)
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TIMESTAMP = "timestamp"
    
    # Status fields
    STATUS = "status"
    PROCESSING_STATUS = "processing_status"
    
    # ============================================================================
    # AGENT FIELDS
    # ============================================================================
    
    class Agent:
        NAME = "name"
        DESCRIPTION = "description"
        TYPE = "type"
        OWNER_ID = "owner_id"
        DEPLOYMENT_STATUS = "deployment_status"
        ACTIVE_DEPLOYMENT_ID = "active_deployment_id"
        SERVICE_URL = "service_url"
        LAST_DEPLOYED_AT = "last_deployed_at"
    
    # ============================================================================
    # CONVERSATION FIELDS
    # ============================================================================
    
    class Conversation:
        CONVERSATION_ID = "conversation_id"
        MESSAGE_CONTENT = "message_content"
        AGENT_RESPONSE = "agent_response"
        IS_PRODUCTION = "is_production"
        DEPLOYMENT_TYPE = "deployment_type"
        TOKENS = "tokens"
        COST_USD = "cost_usd"
        CONTEXT = "context"
        
        # Token subfields
        PROMPT_TOKENS = "prompt_tokens"
        COMPLETION_TOKENS = "completion_tokens"
        TOTAL_TOKENS = "total_tokens"
    
    # ============================================================================
    # BILLING FIELDS
    # ============================================================================
    
    class Billing:
        CREDIT_BALANCE = "credit_balance"
        TOTAL_CREDITS_PURCHASED = "total_credits_purchased"
        TOTAL_CREDITS_USED = "total_credits_used"
        ACCOUNT_STATUS = "account_status"
        TRANSACTION_TYPE = "transaction_type"
        AMOUNT = "amount"
        PAYMENT_PROVIDER = "payment_provider"
    
    # ============================================================================
    # KNOWLEDGE BASE FIELDS
    # ============================================================================
    
    class Knowledge:
        ORIGINAL_FILENAME = "original_filename"
        STORAGE_PATH = "storage_path"
        FILE_SIZE_BYTES = "file_size_bytes"
        FILE_TYPE = "file_type"
        CHUNK_COUNT = "chunk_count"
        TEXT_CONTENT = "text_content"
        EMBEDDING_VECTOR = "embedding_vector"
        PAGE_NUMBER = "page_number"
        CHUNK_INDEX = "chunk_index"
    
    # ============================================================================
    # GLOBAL NARRATIVE FRAMEWORK FIELDS
    # ============================================================================
    
    class GNF:
        # Agent Identity fields
        NARRATIVE_IDENTITY_ID = "narrative_identity_id"
        DEVELOPMENT_STAGE = "development_stage"
        NARRATIVE_COHERENCE_SCORE = "narrative_coherence_score"
        RESPONSIBILITY_SCORE = "responsibility_score"
        EXPERIENCE_POINTS = "experience_points"
        TOTAL_INTERACTIONS = "total_interactions"
        DEFINING_MOMENTS_COUNT = "defining_moments_count"
        
        # Personality fields
        PERSONALITY_TRAITS = "personality_traits"
        CORE_VALUES = "core_values"
        PRIMARY_GOALS = "primary_goals"
        MOTIVATIONS = "motivations"
        FEARS = "fears"
        
        # Narrative fields
        CURRENT_ARC = "current_arc"
        STORY_ELEMENTS = "story_elements"
        CHARACTER_DEVELOPMENT = "character_development"
        
        # Interaction fields
        INTERACTION_TYPE = "interaction_type"
        PARTICIPANTS = "participants"
        IMPACT_LEVEL = "impact_level"
        EMOTIONAL_TONE = "emotional_tone"
        NARRATIVE_SIGNIFICANCE = "narrative_significance"
        PERSONALITY_IMPACT = "personality_impact"
        LEARNING_OUTCOME = "learning_outcome"
        RESPONSIBILITY_IMPACT = "responsibility_impact"
        
        # Memory fields
        MEMORY_TYPE = "memory_type"
        CONSOLIDATION_STRENGTH = "consolidation_strength"
        IMPORTANCE_SCORE = "importance_score"
        EMOTIONAL_VALENCE = "emotional_valence"
        TAGS = "tags"
        
        # Evolution fields
        EVENT_TYPE = "event_type"
        TRIGGER = "trigger"
        PRE_EVOLUTION_STATE = "pre_evolution_state"
        POST_EVOLUTION_STATE = "post_evolution_state"
        CHANGES = "changes"
        
        # Responsibility fields
        ACTION_TYPE = "action_type"
        RESPONSIBILITY_LEVEL = "responsibility_level"
        CONTRIBUTING_FACTORS = "contributing_factors"
        MITIGATION_ACTIONS = "mitigation_actions"
        ACCOUNTABILITY_SCORE = "accountability_score"
        ETHICAL_WEIGHT = "ethical_weight"
        DECISION_QUALITY = "decision_quality"
        LEARNING_POTENTIAL = "learning_potential"


class StatusValues:
    """
    Standardized status values used across the platform.
    """
    
    # ============================================================================
    # DEPLOYMENT STATUS
    # ============================================================================
    
    class Deployment:
        PENDING = "pending"
        BUILDING = "building"
        DEPLOYED = "deployed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    
    # ============================================================================
    # PROCESSING STATUS
    # ============================================================================
    
    class Processing:
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
    
    # ============================================================================
    # ACCOUNT STATUS
    # ============================================================================
    
    class Account:
        ACTIVE = "active"
        SUSPENDED = "suspended"
        TRIAL = "trial"
    
    # ============================================================================
    # TRANSACTION TYPES
    # ============================================================================
    
    class Transaction:
        PURCHASE = "purchase"
        USAGE = "usage"
        ADJUSTMENT = "adjustment"
        REFUND = "refund"
    
    # ============================================================================
    # AGENT TYPES
    # ============================================================================
    
    class AgentType:
        GENERAL = "general"
        CODE = "code"
        RESEARCH = "research"
        WRITING = "writing"
        DATA = "data"
        CUSTOMER = "customer"


class ErrorMessages:
    """
    Standardized error messages for common Firebase operations.
    """
    
    AGENT_NOT_FOUND = "Agent not found"
    AGENT_ACCESS_DENIED = "Access denied: You do not own this agent"
    USER_NOT_AUTHENTICATED = "User not authenticated"
    INSUFFICIENT_CREDITS = "Insufficient credits for this operation"
    INVALID_COLLECTION_NAME = "Invalid collection name"
    DEPRECATED_COLLECTION_WARNING = "Warning: Using deprecated collection name"


def validate_collection_usage(collection_name: str) -> None:
    """
    Validate collection name usage and log warnings for deprecated names.
    
    Args:
        collection_name: The collection name to validate
        
    Raises:
        ValueError: If collection name is not recognized
        
    Logs:
        Warning: If collection name is deprecated
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if Collections.is_deprecated_collection(collection_name):
        logger.warning(f"{ErrorMessages.DEPRECATED_COLLECTION_WARNING}: {collection_name}")
    elif not Collections.is_valid_collection(collection_name):
        raise ValueError(f"{ErrorMessages.INVALID_COLLECTION_NAME}: {collection_name}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_collection_mapping() -> dict[str, str]:
    """
    Get mapping from old collection names to new standardized names.
    
    Returns:
        Dictionary mapping deprecated names to current names
    """
    return {
        Collections.Deprecated.ALCHEMIST_AGENTS: Collections.AGENTS,
        Collections.Deprecated.DEV_CONVERSATIONS: Collections.CONVERSATIONS,
        Collections.Deprecated.KNOWLEDGE_BASE_FILES: Collections.KNOWLEDGE_FILES,
        Collections.Deprecated.USER_CREDITS: Collections.USER_ACCOUNTS,
        Collections.Deprecated.AGENT_BILLING_SUMMARY: Collections.AGENT_USAGE_SUMMARY,
        Collections.Deprecated.MANAGED_ACCOUNTS: Collections.INTEGRATION_CHANNELS,
        Collections.Deprecated.WEBHOOK_LOGS: Collections.COMMUNICATION_LOGS,
        Collections.Deprecated.KNOWLEDGE_BASE_EMBEDDINGS: Collections.KNOWLEDGE_EMBEDDINGS,
    }


def get_migration_sql() -> str:
    """
    Generate migration script for collection name changes.
    
    Returns:
        String containing migration commands
    """
    mapping = get_collection_mapping()
    commands = []
    
    for old_name, new_name in mapping.items():
        commands.append(f"-- Migrate {old_name} to {new_name}")
        commands.append(f"-- This would be done via Firebase Admin SDK or gcloud firestore")
        commands.append("")
    
    return "\n".join(commands)