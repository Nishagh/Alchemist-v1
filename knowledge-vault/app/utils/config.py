"""
Configuration loader for the Knowledge Base Service.
"""
import os
from dotenv import load_dotenv

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
    
    # Google Cloud configuration
    config["GOOGLE_PROJECT_ID"] = os.getenv("GOOGLE_PROJECT_ID") or os.getenv("PROJECT_ID")
    config["GOOGLE_REGION"] = os.getenv("GOOGLE_REGION") or os.getenv("GCP_REGION", "us-central1")
    config["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")    
    # OpenAI configuration
    config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    
    # Firebase configuration
    config["FIREBASE_SERVICE_ACCOUNT_KEY_PATH"] = os.getenv("FIREBASE_CREDENTIALS_PATH")
    config["FIREBASE_STORAGE_BUCKET"] = os.getenv("FIREBASE_STORAGE_BUCKET")
        
    return config
