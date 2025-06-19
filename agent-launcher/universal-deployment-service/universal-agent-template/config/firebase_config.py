"""
Firebase Configuration - V9 Modular Approach

Centralized configuration management for Firebase services.
"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class FirebaseSettings:
    """Firebase configuration settings."""
    
    # Core settings
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None
    storage_bucket: Optional[str] = None
    
    # Firestore settings
    firestore_database: str = "(default)"
    firestore_timeout: int = 30
    
    # Storage settings
    storage_timeout: int = 60
    
    # Environment detection
    is_production: bool = False
    is_development: bool = True
    
    def __post_init__(self):
        """Initialize settings from environment variables."""
        # Use hardcoded project ID
        self.project_id = "alchemist-e69bb"
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", self.credentials_path)
        self.storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", self.storage_bucket)
        
        # Environment settings
        env = os.getenv("ENVIRONMENT", "development").lower()
        self.is_production = env == "production"
        self.is_development = env == "development"
        
        # Timeout settings
        self.firestore_timeout = int(os.getenv("FIRESTORE_TIMEOUT", self.firestore_timeout))
        self.storage_timeout = int(os.getenv("STORAGE_TIMEOUT", self.storage_timeout))
    
    def is_cloud_environment(self) -> bool:
        """Check if running in a cloud environment."""
        return bool(
            os.getenv("K_SERVICE") or  # Cloud Run
            os.getenv("GAE_APPLICATION") or  # App Engine
            os.getenv("FUNCTIONS_EMULATOR") or  # Cloud Functions
            self.is_production
        )
    
    def get_credentials_path(self) -> Optional[str]:
        """Get the path to Firebase credentials with fallback."""
        if self.credentials_path and os.path.exists(self.credentials_path):
            return self.credentials_path
        
        # Fallback paths
        fallback_paths = [
            os.path.join(os.getcwd(), "firebase-credentials.json"),
            os.path.join(os.path.expanduser("~"), ".config", "firebase", "credentials.json"),
            "/etc/firebase/credentials.json"
        ]
        
        for path in fallback_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if self.is_cloud_environment():
            # In cloud environments, we rely on Application Default Credentials
            return True
        
        # In local environments, we need explicit credentials
        return self.get_credentials_path() is not None
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "project_id": self.project_id,
            "credentials_path": self.credentials_path,
            "storage_bucket": self.storage_bucket,
            "firestore_database": self.firestore_database,
            "is_cloud_environment": self.is_cloud_environment(),
            "is_production": self.is_production,
            "is_development": self.is_development
        }


# Global settings instance
firebase_settings = FirebaseSettings()

def get_firebase_settings() -> FirebaseSettings:
    """Get the global Firebase settings instance."""
    return firebase_settings

def reload_settings() -> FirebaseSettings:
    """Reload settings from environment variables."""
    global firebase_settings
    firebase_settings = FirebaseSettings()
    return firebase_settings 