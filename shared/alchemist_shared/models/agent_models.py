"""
Agent Data Models

Models for agent configuration, status, and metadata.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import Field, validator
from datetime import datetime
from .base_models import TimestampedModel


class AgentStatus(str, Enum):
    """Agent deployment and operational status."""
    DRAFT = "draft"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    INACTIVE = "inactive"


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
    
    @validator("name")
    def validate_name(cls, v):
        """Validate agent name."""
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v.strip()
    
    @validator("system_prompt")
    def validate_system_prompt(cls, v):
        """Validate system prompt."""
        if len(v) > 10000:
            raise ValueError("System prompt too long (max 10000 characters)")
        return v
    
    class Config:
        schema_extra = {
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
    
    @validator("user_id")
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
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "config": {
                    "name": "Customer Support Agent",
                    "model": "gpt-4",
                    "system_prompt": "You are a helpful customer support agent..."
                },
                "status": "active",
                "deployment_url": "https://agent-123.run.app"
            }
        }