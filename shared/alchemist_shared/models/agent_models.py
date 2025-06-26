"""
Agent Data Models

Models for agent configuration, status, and metadata.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator
from datetime import datetime
from .base_models import TimestampedModel


class AgentStatus(str, Enum):
    """Agent deployment and operational status."""
    DRAFT = "draft"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    INACTIVE = "inactive"


class DevelopmentStage(str, Enum):
    """Agent development stages from GNF."""
    NASCENT = "nascent"
    DEVELOPING = "developing"
    ESTABLISHED = "established"
    MATURE = "mature"
    EVOLVED = "evolved"


class AgentConfig(TimestampedModel):
    """
    Agent configuration model.
    
    Contains all configuration parameters for an AI agent.
    """
    
    name: str = Field(..., description="Agent name", min_length=1, max_length=100)
    description: Optional[str] = Field(default="", description="Agent description", max_length=500)
    
    # AI Model configuration
    model: str = Field(default="gpt-4", description="AI model to use")
    system_prompt: str = Field(default="", description="System prompt for the agent", max_length=10000)
    max_tokens: int = Field(default=1000, description="Maximum tokens per response", ge=1, le=4000)
    temperature: float = Field(default=0.7, description="Model temperature", ge=0.0, le=2.0)
    
    # Domain and specialization
    domain: Optional[str] = Field(default=None, description="Agent domain/specialization")
    use_cases: List[str] = Field(default_factory=list, description="List of use cases")
    
    # Integration settings
    knowledge_base_enabled: bool = Field(default=False, description="Enable knowledge base integration")
    api_integrations: List[str] = Field(default_factory=list, description="List of enabled API integrations")
    whatsapp_enabled: bool = Field(default=False, description="Enable WhatsApp integration")
    
    # Environment variables and secrets
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    
    @field_validator("name")
    def validate_name(cls, v):
        """Validate agent name."""
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v.strip()
    
    @field_validator("system_prompt")
    def validate_system_prompt(cls, v):
        """Validate system prompt."""
        if len(v) > 10000:
            raise ValueError("System prompt too long (max 10000 characters)")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Customer Support Agent",
                "description": "AI agent for handling customer inquiries",
                "model": "gpt-4",
                "system_prompt": "You are a helpful customer support agent...",
                "domain": "customer_service",
                "knowledge_base_enabled": True,
                "whatsapp_enabled": True
            }
        }
    }


class Agent(TimestampedModel):
    """
    Complete agent model with configuration and runtime information.
    """
    
    user_id: str = Field(..., description="ID of the user who owns this agent")
    config: AgentConfig = Field(..., description="Agent configuration")
    status: AgentStatus = Field(default=AgentStatus.DRAFT, description="Agent status")
    
    # Deployment information
    deployment_url: Optional[str] = Field(default=None, description="Deployed agent URL")
    deployment_id: Optional[str] = Field(default=None, description="Deployment identifier")
    deployment_region: Optional[str] = Field(default=None, description="Deployment region")
    
    # Runtime statistics
    total_conversations: int = Field(default=0, description="Total number of conversations")
    total_messages: int = Field(default=0, description="Total number of messages processed")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")
    
    # Error information
    last_error: Optional[str] = Field(default=None, description="Last error message")
    error_count: int = Field(default=0, description="Number of errors encountered")
    
    # ============================================================================
    # GLOBAL NARRATIVE FRAMEWORK FIELDS
    # ============================================================================
    
    # GNF Identity Integration
    narrative_identity_id: Optional[str] = Field(default=None, description="Reference to GNF agent identity")
    development_stage: DevelopmentStage = Field(default=DevelopmentStage.NASCENT, description="Current development stage")
    narrative_coherence_score: float = Field(default=0.5, description="Narrative coherence score (0.0-1.0)", ge=0.0, le=1.0)
    responsibility_score: float = Field(default=0.5, description="Responsibility accountability score (0.0-1.0)", ge=0.0, le=1.0)
    experience_points: int = Field(default=0, description="Total experience points gained", ge=0)
    total_narrative_interactions: int = Field(default=0, description="Total interactions tracked by GNF", ge=0)
    defining_moments_count: int = Field(default=0, description="Number of defining moments", ge=0)
    
    # Current narrative state
    current_narrative_arc: Optional[str] = Field(default=None, description="Current narrative arc")
    dominant_personality_traits: List[str] = Field(default_factory=list, description="Top 5 personality traits")
    core_values: List[str] = Field(default_factory=list, description="Agent's core values")
    primary_goals: List[str] = Field(default_factory=list, description="Agent's primary goals")
    
    # GNF Integration status
    gnf_enabled: bool = Field(default=True, description="Whether GNF tracking is enabled for this agent")
    last_gnf_sync: Optional[datetime] = Field(default=None, description="Last time GNF data was synchronized")
    
    @field_validator("user_id")
    def validate_user_id(cls, v):
        """Validate user ID."""
        if not v or not v.strip():
            raise ValueError("User ID cannot be empty")
        return v.strip()
    
    def is_deployed(self) -> bool:
        """Check if agent is deployed and active."""
        return self.status == AgentStatus.ACTIVE and self.deployment_url is not None
    
    def increment_conversation_count(self):
        """Increment conversation counter."""
        self.total_conversations += 1
        self.last_activity = datetime.utcnow()
        self.update_timestamp()
    
    def increment_message_count(self):
        """Increment message counter."""
        self.total_messages += 1
        self.last_activity = datetime.utcnow()
        self.update_timestamp()
    
    def record_error(self, error_message: str):
        """Record an error for this agent."""
        self.last_error = error_message
        self.error_count += 1
        self.update_timestamp()
    
    def clear_errors(self):
        """Clear error information."""
        self.last_error = None
        self.error_count = 0
        self.update_timestamp()
    
    # ============================================================================
    # GNF INTEGRATION METHODS
    # ============================================================================
    
    def has_narrative_identity(self) -> bool:
        """Check if agent has a GNF identity created."""
        return self.narrative_identity_id is not None
    
    def is_gnf_enabled(self) -> bool:
        """Check if GNF tracking is enabled."""
        return self.gnf_enabled
    
    def update_gnf_data(self, gnf_data: Dict[str, Any]):
        """Update agent with GNF-sourced data."""
        if 'development_stage' in gnf_data:
            self.development_stage = DevelopmentStage(gnf_data['development_stage'])
        if 'narrative_coherence_score' in gnf_data:
            self.narrative_coherence_score = gnf_data['narrative_coherence_score']
        if 'responsibility_score' in gnf_data:
            self.responsibility_score = gnf_data['responsibility_score']
        if 'experience_points' in gnf_data:
            self.experience_points = gnf_data['experience_points']
        if 'total_interactions' in gnf_data:
            self.total_narrative_interactions = gnf_data['total_interactions']
        if 'defining_moments_count' in gnf_data:
            self.defining_moments_count = gnf_data['defining_moments_count']
        if 'current_arc' in gnf_data:
            self.current_narrative_arc = gnf_data['current_arc']
        if 'dominant_traits' in gnf_data:
            self.dominant_personality_traits = gnf_data['dominant_traits'][:5]  # Limit to top 5
        if 'core_values' in gnf_data:
            self.core_values = gnf_data['core_values']
        if 'primary_goals' in gnf_data:
            self.primary_goals = gnf_data['primary_goals']
        
        self.last_gnf_sync = datetime.utcnow()
        self.update_timestamp()
    
    def get_gnf_summary(self) -> Dict[str, Any]:
        """Get a summary of GNF-related data for this agent."""
        return {
            'narrative_identity_id': self.narrative_identity_id,
            'development_stage': self.development_stage.value,
            'narrative_coherence_score': self.narrative_coherence_score,
            'responsibility_score': self.responsibility_score,
            'experience_points': self.experience_points,
            'total_narrative_interactions': self.total_narrative_interactions,
            'defining_moments_count': self.defining_moments_count,
            'current_narrative_arc': self.current_narrative_arc,
            'dominant_personality_traits': self.dominant_personality_traits,
            'core_values': self.core_values,
            'primary_goals': self.primary_goals,
            'gnf_enabled': self.gnf_enabled,
            'last_gnf_sync': self.last_gnf_sync.isoformat() if self.last_gnf_sync else None
        }
    
    def set_narrative_identity(self, identity_id: str):
        """Set the narrative identity ID for this agent."""
        self.narrative_identity_id = identity_id
        self.last_gnf_sync = datetime.utcnow()
        self.update_timestamp()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user123",
                "config": {
                    "name": "Customer Support Agent",
                    "model": "gpt-4",
                    "system_prompt": "You are a helpful customer support agent..."
                },
                "status": "active",
                "deployment_url": "https://agent-123.run.app",
                "narrative_identity_id": "gnf_identity_123",
                "development_stage": "developing",
                "narrative_coherence_score": 0.7,
                "responsibility_score": 0.8,
                "experience_points": 250,
                "current_narrative_arc": "learning_and_growth",
                "dominant_personality_traits": ["helpful", "patient", "analytical"],
                "core_values": ["customer_satisfaction", "accuracy", "empathy"],
                "gnf_enabled": True
            }
        }
    }