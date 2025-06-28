"""
Configuration loader for the Knowledge Base Service.
"""
import os
import subprocess
from dotenv import load_dotenv

def get_gcloud_project():
    """
    Get the current gcloud project ID
    
    Returns:
        str: Current gcloud project ID or None if not set
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
    gcloud_project = get_gcloud_project()
    config["GOOGLE_PROJECT_ID"] = (
        gcloud_project or 
        os.getenv("GOOGLE_PROJECT_ID") or 
        os.getenv("PROJECT_ID") or
        os.getenv("FIREBASE_PROJECT_ID")
    )
    
    config["GOOGLE_REGION"] = os.getenv("GOOGLE_REGION") or os.getenv("GCP_REGION", "us-central1")
    
    # Note: Firebase credentials are handled automatically by alchemist_shared Firebase client
    # - In cloud environments: Uses Application Default Credentials
    # - For local development: Will use GOOGLE_APPLICATION_CREDENTIALS if set
    
    # OpenAI configuration
    config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    
    # Firebase configuration - auto-generate bucket name if not provided
    config["FIREBASE_STORAGE_BUCKET"] = (
        os.getenv("FIREBASE_STORAGE_BUCKET") or
        f"{config['GOOGLE_PROJECT_ID']}.appspot.com" if config["GOOGLE_PROJECT_ID"] else None
    )
        
    return config
