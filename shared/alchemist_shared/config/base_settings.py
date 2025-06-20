"""
Base Settings Configuration

Provides a base settings class that all services can extend.
Handles common configuration patterns and environment variable loading.
"""

import os
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseSettings as PydanticBaseSettings, Field


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class BaseSettings(PydanticBaseSettings):
    """
    Base settings class with common configuration for all Alchemist services.
    
    All service-specific settings should inherit from this class.
    """
    
    # Environment configuration
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    service_name: str = Field(default="alchemist-service", description="Name of the service")
    service_version: str = Field(default="1.0.0", description="Version of the service")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    
    # Firebase configuration
    firebase_project_id: Optional[str] = Field(default=None, description="Firebase project ID")
    firebase_storage_bucket: Optional[str] = Field(default=None, description="Firebase storage bucket")
    google_application_credentials: Optional[str] = Field(default=None, description="Path to Google credentials file")
    
    # OpenAI configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="Default OpenAI model")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # Security configuration
    cors_origins: list[str] = Field(default=["http://localhost:3000"], description="CORS allowed origins")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable mapping
        fields = {
            "firebase_project_id": {"env": ["FIREBASE_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"]},
            "firebase_storage_bucket": {"env": "FIREBASE_STORAGE_BUCKET"},
            "google_application_credentials": {"env": "GOOGLE_APPLICATION_CREDENTIALS"},
            "openai_api_key": {"env": "OPENAI_API_KEY"},
            "cors_origins": {"env": "CORS_ORIGINS"},
        }
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == Environment.STAGING
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_cloud_environment(self) -> bool:
        """Check if running in cloud environment."""
        return bool(
            os.environ.get("K_SERVICE") or 
            os.environ.get("GOOGLE_CLOUD_PROJECT") or
            os.environ.get("GAE_APPLICATION")
        )
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get URL for another service."""
        env_var = f"{service_name.upper().replace('-', '_')}_URL"
        return os.environ.get(env_var)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.dict()
    
    def __str__(self) -> str:
        """String representation (excludes sensitive data)."""
        safe_dict = self.dict()
        # Remove sensitive fields
        safe_dict.pop("openai_api_key", None)
        safe_dict.pop("google_application_credentials", None)
        return f"{self.__class__.__name__}({safe_dict})"