"""
User Data Models

Models for user accounts, authentication, and permissions.
"""

from enum import Enum
from typing import Optional, List
from pydantic import Field, EmailStr, field_validator
from .base_models import TimestampedModel


class UserRole(str, Enum):
    """User role types."""
    USER = "user"
    ADMIN = "admin"
    DEVELOPER = "developer"


class User(TimestampedModel):
    """
    User account model.
    
    Contains user profile information and account settings.
    """
    
    email: EmailStr = Field(..., description="User email address")
    display_name: Optional[str] = Field(default=None, description="User display name")
    photo_url: Optional[str] = Field(default=None, description="Profile photo URL")
    
    # Account status
    is_active: bool = Field(default=True, description="Account is active")
    is_verified: bool = Field(default=False, description="Email is verified")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    
    # Usage statistics
    total_agents: int = Field(default=0, description="Total number of agents created")
    total_conversations: int = Field(default=0, description="Total conversations across all agents")
    
    # Subscription and limits
    subscription_tier: str = Field(default="free", description="Subscription tier")
    agent_limit: int = Field(default=3, description="Maximum number of agents allowed")
    monthly_message_limit: int = Field(default=1000, description="Monthly message limit")
    monthly_message_count: int = Field(default=0, description="Current month message count")
    
    # Preferences
    preferences: dict = Field(default_factory=dict, description="User preferences")
    
    @field_validator("email")
    def validate_email(cls, v):
        """Validate email address."""
        if not v:
            raise ValueError("Email address is required")
        return v.lower().strip()
    
    @field_validator("display_name")
    def validate_display_name(cls, v):
        """Validate display name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) > 100:
                raise ValueError("Display name too long (max 100 characters)")
        return v
    
    def can_create_agent(self) -> bool:
        """Check if user can create a new agent."""
        return self.is_active and self.total_agents < self.agent_limit
    
    def can_send_message(self) -> bool:
        """Check if user can send a message (within limits)."""
        return self.is_active and self.monthly_message_count < self.monthly_message_limit
    
    def increment_agent_count(self):
        """Increment agent counter."""
        self.total_agents += 1
        self.update_timestamp()
    
    def decrement_agent_count(self):
        """Decrement agent counter."""
        if self.total_agents > 0:
            self.total_agents -= 1
        self.update_timestamp()
    
    def increment_message_count(self):
        """Increment message counter."""
        self.monthly_message_count += 1
        self.total_conversations += 1
        self.update_timestamp()
    
    def reset_monthly_counts(self):
        """Reset monthly usage counters."""
        self.monthly_message_count = 0
        self.update_timestamp()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "display_name": "John Doe",
                "is_active": True,
                "role": "user",
                "subscription_tier": "pro",
                "total_agents": 2
            }
        }
    }