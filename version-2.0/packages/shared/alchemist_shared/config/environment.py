"""Environment detection and configuration utilities."""

import os
from typing import Optional, Dict, Any


def detect_environment() -> str:
    """
    Detect the current deployment environment.
    
    Returns:
        Environment name (development, staging, production)
    """
    # Check explicit environment variable
    env = os.getenv("ENVIRONMENT", "").lower()
    if env in ["development", "staging", "production"]:
        return env
    
    # Check for cloud environment indicators
    if os.getenv("K_SERVICE"):  # Cloud Run
        return "production"
    
    if os.getenv("GAE_APPLICATION"):  # App Engine
        return "production"
    
    # Default to development
    return "development"


def is_cloud_environment() -> bool:
    """Check if running in a cloud environment."""
    return bool(
        os.environ.get("K_SERVICE") or 
        os.environ.get("GOOGLE_CLOUD_PROJECT") or
        os.environ.get("GAE_APPLICATION")
    )


def get_project_id() -> Optional[str]:
    """Get Google Cloud project ID from various sources."""
    return (
        os.getenv("GOOGLE_CLOUD_PROJECT") or
        os.getenv("FIREBASE_PROJECT_ID") or
        os.getenv("GCP_PROJECT") or
        os.getenv("PROJECT_ID")
    )


def get_service_info() -> Dict[str, Any]:
    """Get information about the current service."""
    return {
        "service_name": os.getenv("K_SERVICE", "unknown"),
        "service_revision": os.getenv("K_REVISION", "unknown"),
        "service_config": os.getenv("K_CONFIGURATION", "unknown"),
        "project_id": get_project_id(),
        "region": os.getenv("FUNCTION_REGION", os.getenv("GOOGLE_CLOUD_REGION", "unknown")),
        "environment": detect_environment(),
        "is_cloud": is_cloud_environment(),
    }