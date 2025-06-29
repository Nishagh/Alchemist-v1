"""
Base Settings Configuration

Provides a base settings class that all services can extend.
Handles common configuration patterns and environment variable loading.
"""

import os
import subprocess
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings as PydanticBaseSettings
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv('PROJECT_ID')


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
    PROJECT_ID: Optional[str] = Field(default=None, description="Firebase project ID", validation_alias="FIREBASE_PROJECT_ID")
    firebase_storage_bucket: Optional[str] = Field(default=None, description="Firebase storage bucket", validation_alias="FIREBASE_STORAGE_BUCKET")
    google_application_credentials: Optional[str] = Field(default=None, description="Path to Google credentials file", validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
    
    # OpenAI configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", description="Default OpenAI model")
    openai_organization: Optional[str] = Field(default=None, description="OpenAI organization ID", validation_alias="OPENAI_ORGANIZATION")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # Security configuration
    cors_origins: list[str] = Field(default=["http://localhost:3000"], description="CORS allowed origins")
    
    model_config = {
        "env_file": [".env", "../shared/.env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
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
    
    @staticmethod
    def get_gcloud_project() -> Optional[str]:
        """
        Get the current gcloud project ID from gcloud config.
        
        Returns:
            str: Current gcloud project ID or None if not set or gcloud not available
        """
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                project_id = result.stdout.strip()
                if project_id and project_id != "(unset)":
                    return project_id
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        return None
    
    def get_project_id(self) -> Optional[str]:
        """
        Get the effective Firebase project ID using multiple sources in priority order:
        1. Explicitly set FIREBASE_PROJECT_ID environment variable
        2. Current gcloud project configuration
        3. GOOGLE_CLOUD_PROJECT environment variable (Cloud Run)
        4. PROJECT_ID environment variable (legacy)
        
        Returns:
            str: Firebase project ID or None if not found
        """

        return PROJECT_ID
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get URL for another service."""
        env_var = f"{service_name.upper().replace('-', '_')}_URL"
        return os.environ.get(env_var)
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get centralized OpenAI configuration."""
        config = {"api_key": self.openai_api_key}
        if self.openai_organization:
            config["organization"] = self.openai_organization
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.model_dump()
    
    def __str__(self) -> str:
        """String representation (excludes sensitive data)."""
        safe_dict = self.model_dump()
        # Remove sensitive fields
        safe_dict.pop("openai_api_key", None)
        safe_dict.pop("google_application_credentials", None)
        return f"{self.__class__.__name__}({safe_dict})"