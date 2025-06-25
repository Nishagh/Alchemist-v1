"""
Firebase Collection Constants for GNF Integration

This module provides standardized collection names that align with the optimized
Firebase structure defined in firebase-gnf-integration.yaml
"""

# ============================================================================
# ENHANCED EXISTING COLLECTIONS (Alchemist Platform + GNF)
# ============================================================================

# Primary agent collection (enhanced with GNF identity fields)
AGENTS = "agents"

# Conversations with GNF narrative analysis
CONVERSATIONS = "conversations"

# User accounts (from optimized structure)
USER_ACCOUNTS = "user_accounts"

# Credit tracking (from optimized structure)
CREDIT_TRANSACTIONS = "credit_transactions"

# Usage summaries (from optimized structure)
AGENT_USAGE_SUMMARY = "agent_usage_summary"

# Deployment tracking (from optimized structure)
AGENT_DEPLOYMENTS = "agent_deployments"

# Knowledge base (from optimized structure)
KNOWLEDGE_FILES = "knowledge_files"
KNOWLEDGE_EMBEDDINGS = "knowledge_embeddings"

# Training system (from optimized structure)
TRAINING_JOBS = "training_jobs"

# Communication channels (from optimized structure)
INTEGRATION_CHANNELS = "integration_channels"
COMMUNICATION_LOGS = "communication_logs"

# ============================================================================
# NEW GNF-SPECIFIC COLLECTIONS
# ============================================================================

# Memory consolidation and retrieval
AGENT_MEMORIES = "agent_memories"

# Agent development milestones
AGENT_EVOLUTION_EVENTS = "agent_evolution_events"

# Responsibility and accountability tracking
AGENT_RESPONSIBILITY_RECORDS = "agent_responsibility_records"

# Multi-agent interactions and relationships
CROSS_AGENT_INTERACTIONS = "cross_agent_interactions"

# System-wide narrative events
GLOBAL_NARRATIVE_TIMELINE = "global_narrative_timeline"

# ============================================================================
# DEPRECATED COLLECTIONS (For Migration Reference)
# ============================================================================

# Original GNF collections (to be migrated)
DEPRECATED_GNF_INTERACTIONS = "interactions"
DEPRECATED_GNF_MEMORIES = "memories"
DEPRECATED_GNF_EVOLUTION_EVENTS = "evolution_events"
DEPRECATED_GNF_ACTIONS = "gnf_actions"
DEPRECATED_GNF_GLOBAL_NARRATIVE = "global_narrative"

# Original Alchemist collections (from firebase-structure-optimized.yaml)
DEPRECATED_ALCHEMIST_AGENTS = "alchemist_agents"
DEPRECATED_DEV_CONVERSATIONS = "dev_conversations"
DEPRECATED_USER_CREDITS = "user_credits"
DEPRECATED_KNOWLEDGE_BASE_FILES = "knowledge_base_files"
DEPRECATED_MANAGED_ACCOUNTS = "managed_accounts"
DEPRECATED_WEBHOOK_LOGS = "webhook_logs"

# ============================================================================
# COLLECTION GROUPS FOR BATCH OPERATIONS
# ============================================================================

# All current active collections
ACTIVE_COLLECTIONS = [
    AGENTS,
    CONVERSATIONS,
    USER_ACCOUNTS,
    CREDIT_TRANSACTIONS,
    AGENT_USAGE_SUMMARY,
    AGENT_DEPLOYMENTS,
    KNOWLEDGE_FILES,
    KNOWLEDGE_EMBEDDINGS,
    TRAINING_JOBS,
    INTEGRATION_CHANNELS,
    COMMUNICATION_LOGS,
    AGENT_MEMORIES,
    AGENT_EVOLUTION_EVENTS,
    AGENT_RESPONSIBILITY_RECORDS,
    CROSS_AGENT_INTERACTIONS,
    GLOBAL_NARRATIVE_TIMELINE,
]

# Core GNF collections for narrative tracking
GNF_CORE_COLLECTIONS = [
    AGENTS,  # Enhanced with GNF identity
    CONVERSATIONS,  # Enhanced with GNF analysis
    AGENT_MEMORIES,
    AGENT_EVOLUTION_EVENTS,
    AGENT_RESPONSIBILITY_RECORDS,
    CROSS_AGENT_INTERACTIONS,
    GLOBAL_NARRATIVE_TIMELINE,
]

# Collections requiring agent ownership validation
AGENT_OWNED_COLLECTIONS = [
    AGENTS,
    CONVERSATIONS,
    AGENT_MEMORIES,
    AGENT_EVOLUTION_EVENTS,
    AGENT_RESPONSIBILITY_RECORDS,
    KNOWLEDGE_FILES,
    KNOWLEDGE_EMBEDDINGS,
    TRAINING_JOBS,
]

# Collections for real-time listeners
REAL_TIME_COLLECTIONS = [
    AGENTS,
    CONVERSATIONS,
    AGENT_DEPLOYMENTS,
    TRAINING_JOBS,
    CROSS_AGENT_INTERACTIONS,
]

# Collections for aggregation triggers
AGGREGATION_SOURCE_COLLECTIONS = [
    CONVERSATIONS,
    CREDIT_TRANSACTIONS,
    AGENT_RESPONSIBILITY_RECORDS,
    AGENT_EVOLUTION_EVENTS,
]

# ============================================================================
# FIELD PATH CONSTANTS FOR GNF ENHANCED FIELDS
# ============================================================================

class AgentFields:
    """Field paths for the enhanced agents collection"""
    
    # Original Alchemist fields
    AGENT_ID = "agent_id"
    NAME = "name"
    DESCRIPTION = "description"
    TYPE = "type"
    OWNER_ID = "owner_id"
    DEPLOYMENT_STATUS = "deployment_status"
    ACTIVE_DEPLOYMENT_ID = "active_deployment_id"
    SERVICE_URL = "service_url"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    LAST_DEPLOYED_AT = "last_deployed_at"
    
    # GNF Identity fields
    PERSONALITY_CORE = "gnf_identity.personality_core"
    PERSONALITY_TRAITS = "gnf_identity.personality_core.traits"
    PERSONALITY_VALUES = "gnf_identity.personality_core.values"
    PERSONALITY_GOALS = "gnf_identity.personality_core.goals"
    
    BACKGROUND_INFO = "gnf_identity.background_info"
    BACKGROUND_ORIGIN = "gnf_identity.background_info.origin"
    BACKGROUND_ACHIEVEMENTS = "gnf_identity.background_info.achievements"
    
    CAPABILITIES = "gnf_identity.capabilities"
    CAPABILITIES_SKILLS = "gnf_identity.capabilities.skills"
    CAPABILITIES_KNOWLEDGE_DOMAINS = "gnf_identity.capabilities.knowledge_domains"
    
    NARRATIVE_INFO = "gnf_identity.narrative_info"
    NARRATIVE_CURRENT_ARC = "gnf_identity.narrative_info.current_arc"
    NARRATIVE_STORY_ELEMENTS = "gnf_identity.narrative_info.story_elements"
    
    EVOLUTION_INFO = "gnf_identity.evolution_info"
    EVOLUTION_DEVELOPMENT_STAGE = "gnf_identity.evolution_info.development_stage"
    EVOLUTION_EXPERIENCE_POINTS = "gnf_identity.evolution_info.experience_points"
    
    MEMORY_ANCHORS = "gnf_identity.memory_anchors"
    MEMORY_DEFINING_MOMENTS = "gnf_identity.memory_anchors.defining_moments"
    
    RESPONSIBILITY_TRACKER = "gnf_identity.responsibility_tracker"
    RESPONSIBILITY_ACCOUNTABILITY_SCORE = "gnf_identity.responsibility_tracker.accountability_score"
    RESPONSIBILITY_ETHICAL_DEVELOPMENT = "gnf_identity.responsibility_tracker.ethical_development_level"
    
    # GNF Metadata fields
    GNF_ENABLED = "gnf_metadata.gnf_enabled"
    GNF_VERSION = "gnf_metadata.gnf_version"
    LAST_NARRATIVE_UPDATE = "gnf_metadata.last_narrative_update"
    TOTAL_INTERACTIONS_TRACKED = "gnf_metadata.total_interactions_tracked"
    NARRATIVE_COHERENCE_SCORE = "gnf_metadata.narrative_coherence_score"


class ConversationFields:
    """Field paths for the enhanced conversations collection"""
    
    # Original Alchemist fields
    CONVERSATION_ID = "conversation_id"
    AGENT_ID = "agent_id"
    USER_ID = "user_id"
    MESSAGE_CONTENT = "message_content"
    AGENT_RESPONSE = "agent_response"
    IS_PRODUCTION = "is_production"
    DEPLOYMENT_TYPE = "deployment_type"
    TOKENS = "tokens"
    COST_USD = "cost_usd"
    TIMESTAMP = "timestamp"
    CREATED_AT = "created_at"
    CONTEXT = "context"
    
    # GNF Analysis fields
    NARRATIVE_ANALYSIS = "gnf_analysis.narrative_analysis"
    NARRATIVE_SIGNIFICANCE = "gnf_analysis.narrative_analysis.narrative_significance"
    INTERACTION_TYPE = "gnf_analysis.narrative_analysis.interaction_type"
    IMPACT_LEVEL = "gnf_analysis.narrative_analysis.impact_level"
    EMOTIONAL_TONE = "gnf_analysis.narrative_analysis.emotional_tone"
    
    PERSONALITY_IMPACT = "gnf_analysis.narrative_analysis.personality_impact"
    LEARNING_OUTCOME = "gnf_analysis.narrative_analysis.learning_outcome"
    RESPONSIBILITY_IMPACT = "gnf_analysis.narrative_analysis.responsibility_impact"
    
    CROSS_AGENT_DATA = "gnf_analysis.cross_agent_data"
    PARTICIPANTS = "gnf_analysis.cross_agent_data.participants"
    
    AI_ENHANCEMENT = "gnf_analysis.ai_enhancement"
    AI_INSIGHTS = "gnf_analysis.ai_enhancement.ai_insights"
    
    # GNF Processing fields
    GNF_PROCESSING = "gnf_processing"
    ANALYSIS_COMPLETED = "gnf_processing.analysis_completed"
    PROCESSING_TIME_MS = "gnf_processing.processing_time_ms"


class MemoryFields:
    """Field paths for the agent_memories collection"""
    
    MEMORY_ID = "memory_id"
    AGENT_ID = "agent_id"
    MEMORY_TYPE = "memory_type"
    CONTENT = "content"
    METADATA = "metadata"
    IMPORTANCE_SCORE = "metadata.importance_score"
    CONSOLIDATION_STRENGTH = "metadata.consolidation_strength"
    EMOTIONAL_VALENCE = "metadata.emotional_valence"
    TAGS = "metadata.tags"
    CREATED_AT = "created_at"
    LAST_REINFORCED = "last_reinforced"


class EvolutionFields:
    """Field paths for the agent_evolution_events collection"""
    
    EVENT_ID = "event_id"
    AGENT_ID = "agent_id"
    EVENT_TYPE = "event_type"
    TRIGGER_TYPE = "trigger_type"
    DESCRIPTION = "description"
    SIGNIFICANCE_LEVEL = "significance_level"
    CHANGES_MADE = "changes_made"
    TRIGGER_DATA = "trigger_data"
    PRE_EVOLUTION_STATE = "pre_evolution_state"
    POST_EVOLUTION_STATE = "post_evolution_state"
    IMPACT_ANALYSIS = "impact_analysis"
    CREATED_AT = "created_at"


class ResponsibilityFields:
    """Field paths for the agent_responsibility_records collection"""
    
    ACTION_ID = "action_id"
    AGENT_ID = "agent_id"
    ACTION_TYPE = "action_type"
    DESCRIPTION = "description"
    INTENDED_OUTCOME = "intended_outcome"
    ACTUAL_OUTCOME = "actual_outcome"
    SUCCESS_LEVEL = "success_level"
    RESPONSIBILITY_ANALYSIS = "responsibility_analysis"
    OVERALL_RESPONSIBILITY_SCORE = "responsibility_analysis.overall_responsibility_score"
    ETHICAL_WEIGHT = "responsibility_analysis.ethical_weight"
    CONSEQUENCES = "consequences"
    DECISION_PROCESS = "decision_process"
    PERFORMED_AT = "performed_at"
    SOURCE_INTERACTION_ID = "source_interaction_id"


# ============================================================================
# MIGRATION MAPPING
# ============================================================================

MIGRATION_MAPPINGS = {
    # GNF collection migrations
    DEPRECATED_GNF_INTERACTIONS: CONVERSATIONS,
    DEPRECATED_GNF_MEMORIES: AGENT_MEMORIES,
    DEPRECATED_GNF_EVOLUTION_EVENTS: AGENT_EVOLUTION_EVENTS,
    DEPRECATED_GNF_ACTIONS: AGENT_RESPONSIBILITY_RECORDS,
    DEPRECATED_GNF_GLOBAL_NARRATIVE: GLOBAL_NARRATIVE_TIMELINE,
    
    # Alchemist collection migrations (from optimized structure)
    DEPRECATED_ALCHEMIST_AGENTS: AGENTS,
    DEPRECATED_DEV_CONVERSATIONS: CONVERSATIONS,
    DEPRECATED_USER_CREDITS: USER_ACCOUNTS,
    DEPRECATED_KNOWLEDGE_BASE_FILES: KNOWLEDGE_FILES,
    DEPRECATED_MANAGED_ACCOUNTS: INTEGRATION_CHANNELS,
    DEPRECATED_WEBHOOK_LOGS: COMMUNICATION_LOGS,
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def is_valid_collection(collection_name: str) -> bool:
    """Check if collection name is valid in current schema"""
    return collection_name in ACTIVE_COLLECTIONS

def is_deprecated_collection(collection_name: str) -> bool:
    """Check if collection name is deprecated"""
    return collection_name in MIGRATION_MAPPINGS.keys()

def get_migrated_collection(deprecated_name: str) -> str:
    """Get the new collection name for a deprecated collection"""
    return MIGRATION_MAPPINGS.get(deprecated_name, deprecated_name)

def is_gnf_enhanced_collection(collection_name: str) -> bool:
    """Check if collection has GNF enhancements"""
    return collection_name in GNF_CORE_COLLECTIONS

def requires_agent_ownership(collection_name: str) -> bool:
    """Check if collection requires agent ownership validation"""
    return collection_name in AGENT_OWNED_COLLECTIONS

def supports_real_time_updates(collection_name: str) -> bool:
    """Check if collection supports real-time listeners"""
    return collection_name in REAL_TIME_COLLECTIONS