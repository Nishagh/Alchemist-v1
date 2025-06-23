"""
Configuration settings for the Agent Tuning Service
"""

import os
from typing import List, Optional
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Service configuration
    service_name: str = "agent-tuning-service"
    port: int = 8080
    host: str = "0.0.0.0"
    
    # Security
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["*"]
    
    # Firebase
    firebase_project_id: str = os.getenv("TUNING_FIREBASE_PROJECT_ID", "alchemist-agent-v1")
    firebase_credentials_path: Optional[str] = None
    firestore_collection_training_jobs: str = "training_jobs"
    firestore_collection_training_data: str = "training_data"
    firestore_collection_fine_tuned_models: str = "fine_tuned_models"
    
    # Google Cloud Storage
    gcs_bucket_training_data: str = "alchemist-training-data"
    gcs_bucket_models: str = "alchemist-models"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_organization: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Claude/Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: str = "https://api.anthropic.com"
    
    # Training configuration
    max_training_data_size: int = 100 * 1024 * 1024  # 100MB
    max_training_pairs: int = 10000
    min_training_pairs: int = 10
    default_training_epochs: int = 3
    default_batch_size: int = 32
    
    # Job management
    max_concurrent_jobs: int = 5
    job_timeout_hours: int = 24
    cleanup_completed_jobs_days: int = 30
    
    # Redis (for job queue)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def validate_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "TUNING_",
        "case_sensitive": False,
        "protected_namespaces": ()
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Environment-specific configurations
def get_development_settings() -> Settings:
    """Development environment settings"""
    settings = get_settings()
    settings.debug = True
    settings.log_level = "DEBUG"
    settings.cors_origins = ["http://localhost:3000", "http://localhost:3001"]
    return settings


def get_production_settings() -> Settings:
    """Production environment settings"""
    settings = get_settings()
    settings.debug = False
    settings.log_level = "INFO"
    settings.allowed_hosts = ["agent-tuning-service-*", "*.run.app"]
    return settings