"""
Configuration loader for the Knowledge Base Service.
"""
import os
import subprocess
from dotenv import load_dotenv
from alchemist_shared.config import base_settings

settings = base_settings()
project_id = settings.get_project_id()
openai_config = settings.get_openai_config()
openai_key = openai_config.get("api_key")

def get_gcloud_project():
    """
    Get the current gcloud project ID
    
    Returns:
        str: Current gcloud project ID or None if not set
    """
    return settings.get_project_id()

def load_config():
    """
    Load configuration from environment variables
    
    Returns:
        dict: Configuration dictionary
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Create configuration dictionary from environment variables
    config = {}
    
    # Google Cloud configuration - use gcloud config as primary source
    config["GOOGLE_PROJECT_ID"] = project_id
    
    config["GOOGLE_REGION"] = os.getenv("GOOGLE_REGION") or os.getenv("GCP_REGION", "us-central1")
    
    # Note: Firebase credentials are handled automatically by alchemist_shared Firebase client
    # - In cloud environments: Uses Application Default Credentials
    # - For local development: Will use GOOGLE_APPLICATION_CREDENTIALS if set
    
    # OpenAI configuration
    config["OPENAI_API_KEY"] = openai_key
    
    # Firebase configuration - auto-generate bucket name if not provided
    config["FIREBASE_STORAGE_BUCKET"]  = os.getenv("FIREBASE_STORAGE_BUCKET")
        
    return config
