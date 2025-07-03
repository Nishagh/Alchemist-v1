"""
Configuration management for accountable AI agent using alchemist-shared
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
import logging

# Import alchemist-shared components
try:
    from alchemist_shared.config.base_settings import BaseSettings as AlchemistBaseSettings
    from alchemist_shared.config.environment import get_project_id, detect_environment
    from alchemist_shared.database.firebase_client import FirebaseClient
    ALCHEMIST_SHARED_AVAILABLE = True
except ImportError:
    ALCHEMIST_SHARED_AVAILABLE = False
    import warnings
    warnings.warn("alchemist-shared not available. Using fallback configuration")


class AgentSettings(BaseSettings):
    """
    Configuration settings for the accountable AI agent.
    Integrates with alchemist-shared configuration patterns.
    """
    
    # ============================================================================
    # CORE AGENT SETTINGS
    # ============================================================================
    
    agent_id: str = Field(..., description="Unique agent identifier")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # ============================================================================
    # API CONFIGURATION
    # ============================================================================
    
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8080, description="Port to bind to")
    reload: bool = Field(default=False, description="Enable auto-reload for development")
    
    # ============================================================================
    # AI MODEL CONFIGURATION
    # ============================================================================
    
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    default_model: str = Field(default="gpt-4", description="Default AI model to use")
    max_tokens: int = Field(default=1000, description="Maximum tokens per response")
    temperature: float = Field(default=0.7, description="Model temperature", ge=0.0, le=2.0)
    
    # ============================================================================
    # FIREBASE CONFIGURATION
    # ============================================================================
    
    firebase_project_id: Optional[str] = Field(default=None, description="Firebase project ID")
    google_application_credentials: Optional[str] = Field(default=None, description="Path to Firebase credentials")
    
    # ============================================================================
    # GNF/EA³ ACCOUNTABILITY SETTINGS
    # ============================================================================
    
    enable_gnf: bool = Field(default=True, description="Enable Global Narrative Framework")
    story_loss_threshold: float = Field(default=0.7, description="Story-loss threshold for alerts", ge=0.0, le=1.0)
    responsibility_threshold: float = Field(default=0.5, description="Responsibility threshold for alerts", ge=0.0, le=1.0)
    narrative_coherence_threshold: float = Field(default=0.6, description="Narrative coherence threshold", ge=0.0, le=1.0)
    enable_self_reflection: bool = Field(default=True, description="Enable self-reflection minion tasks")
    
    # Development stages configuration
    development_stage_thresholds: dict = Field(default={
        "nascent": {"experience_points": 0, "interactions": 0},
        "developing": {"experience_points": 100, "interactions": 50},
        "established": {"experience_points": 500, "interactions": 200},
        "mature": {"experience_points": 1000, "interactions": 500},
        "evolved": {"experience_points": 2000, "interactions": 1000}
    })
    
    # ============================================================================
    # PERFORMANCE CONFIGURATION
    # ============================================================================
    
    max_concurrent_conversations: int = Field(default=100, description="Maximum concurrent conversations")
    conversation_memory_limit: int = Field(default=8000, description="Maximum tokens for conversation memory")
    token_cache_ttl: int = Field(default=300, description="Token cache TTL in seconds")
    
    # ============================================================================
    # KNOWLEDGE BASE CONFIGURATION
    # ============================================================================
    
    enable_knowledge_base: bool = Field(default=True, description="Enable embedded knowledge base")
    knowledge_search_top_k: int = Field(default=5, description="Top K results for knowledge search")
    knowledge_chunk_size: int = Field(default=1000, description="Size of knowledge chunks in words")
    knowledge_chunk_overlap: int = Field(default=200, description="Overlap between chunks in words")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model name")
    
    # ============================================================================
    # MCP CONFIGURATION
    # ============================================================================
    
    mcp_server_url_template: str = Field(
        default="https://mcp-{agent_id}-851487020021.us-central1.run.app",
        description="MCP server URL template"
    )
    enable_mcp_tools: bool = Field(default=True, description="Enable MCP tools integration")
    mcp_timeout: int = Field(default=30, description="MCP request timeout in seconds")
    
    # ============================================================================
    # CACHING CONFIGURATION
    # ============================================================================
    
    redis_url: Optional[str] = Field(default=None, description="Redis URL for caching")
    enable_caching: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Default cache TTL in seconds")
    
    # ============================================================================
    # MONITORING CONFIGURATION
    # ============================================================================
    
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # ============================================================================
    # SECURITY CONFIGURATION
    # ============================================================================
    
    max_request_size: int = Field(default=1024 * 1024, description="Maximum request size in bytes")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    enable_cors: bool = Field(default=True, description="Enable CORS")
    
    # ============================================================================
    # ALCHEMIST-SHARED CONFIGURATION
    # ============================================================================
    
    use_alchemist_shared: bool = Field(default=True, description="Use alchemist-shared for configuration")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def get_mcp_server_url(self) -> Optional[str]:
        """Get the MCP server URL for this agent"""
        if not self.enable_mcp_tools or not self.agent_id:
            return None
        return self.mcp_server_url_template.format(agent_id=self.agent_id)
    
    def get_knowledge_base_url(self) -> Optional[str]:
        """Get the knowledge base URL"""
        if not self.enable_knowledge_base:
            return None
        return self.knowledge_base_url
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    def get_embedding_model(self) -> str:
        """Get embedding model name"""
        return os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from alchemist-shared or fallback"""
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                alchemist_settings = AlchemistBaseSettings()
                openai_config = alchemist_settings.get_openai_config()
                api_key = openai_config.get("api_key")
                if api_key:
                    return api_key
            except Exception as e:
                logging.warning(f"Failed to get OpenAI API key from alchemist-shared: {e}")
        return self.openai_api_key or os.getenv("OPENAI_API_KEY")
    
    def get_firebase_credentials(self) -> Optional[str]:
        """Get Firebase credentials path from alchemist-shared or fallback"""
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                alchemist_settings = AlchemistBaseSettings()
                return alchemist_settings.google_application_credentials
            except Exception:
                pass
        return self.google_application_credentials or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    def get_firebase_project_id(self) -> Optional[str]:
        """Get Firebase project ID from alchemist-shared or fallback"""
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                return get_project_id()
            except Exception:
                pass
        return self.firebase_project_id or os.getenv("FIREBASE_PROJECT_ID")
    
    def get_firebase_client(self) -> Optional['FirebaseClient']:
        """Get configured Firebase client from alchemist-shared"""
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                return FirebaseClient()
            except Exception as e:
                logging.warning(f"Failed to get Firebase client from alchemist-shared: {e}")
        return None
    
    def get_openai_service(self) -> Optional[dict]:
        """Get OpenAI configuration from alchemist-shared"""
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                alchemist_settings = AlchemistBaseSettings()
                return alchemist_settings.get_openai_config()
            except Exception as e:
                import logging
                logging.warning(f"Failed to get OpenAI config from alchemist-shared: {e}")
        return None

class AccountabilitySettings:
    """
    Specialized settings for accountability and narrative tracking
    """
    
    def __init__(self, settings: AgentSettings):
        self.settings = settings
    
    @property
    def story_loss_enabled(self) -> bool:
        """Check if story-loss tracking is enabled"""
        return self.settings.enable_gnf
    
    @property
    def responsibility_tracking_enabled(self) -> bool:
        """Check if responsibility tracking is enabled"""
        return self.settings.enable_gnf
    
    @property
    def narrative_coherence_enabled(self) -> bool:
        """Check if narrative coherence tracking is enabled"""
        return self.settings.enable_gnf
    
    @property
    def self_reflection_enabled(self) -> bool:
        """Check if self-reflection is enabled"""
        return self.settings.enable_self_reflection and self.settings.enable_gnf
    
    def should_trigger_story_loss_alert(self, story_loss: float) -> bool:
        """Check if story-loss value should trigger an alert"""
        return story_loss > self.settings.story_loss_threshold
    
    def should_trigger_responsibility_alert(self, responsibility_score: float) -> bool:
        """Check if responsibility score should trigger an alert"""
        return responsibility_score < self.settings.responsibility_threshold
    
    def should_trigger_coherence_alert(self, coherence_score: float) -> bool:
        """Check if narrative coherence should trigger an alert"""
        return coherence_score < self.settings.narrative_coherence_threshold
    
    def get_development_stage_for_metrics(self, experience_points: int, interactions: int) -> str:
        """Determine development stage based on metrics"""
        thresholds = self.settings.development_stage_thresholds
        
        if (experience_points >= thresholds["evolved"]["experience_points"] and 
            interactions >= thresholds["evolved"]["interactions"]):
            return "evolved"
        elif (experience_points >= thresholds["mature"]["experience_points"] and 
              interactions >= thresholds["mature"]["interactions"]):
            return "mature"
        elif (experience_points >= thresholds["established"]["experience_points"] and 
              interactions >= thresholds["established"]["interactions"]):
            return "established"
        elif (experience_points >= thresholds["developing"]["experience_points"] and 
              interactions >= thresholds["developing"]["interactions"]):
            return "developing"
        else:
            return "nascent"


# Global settings instance
settings = AgentSettings()
accountability_settings = AccountabilitySettings(settings)