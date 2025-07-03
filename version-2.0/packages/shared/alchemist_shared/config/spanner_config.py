"""
Spanner Configuration Validation

Centralizes Spanner configuration validation and provides helper functions
for checking if Spanner services are properly configured.
"""

import os
import logging
from typing import Optional, Dict, Any
from .environment import get_project_id

logger = logging.getLogger(__name__)

class SpannerConfig:
    """Centralized Spanner configuration management"""
    
    def __init__(self):
        self.project_id = None
        self.instance_id = None
        self.database_id = None
        self.credentials_path = None
        self._validated = False
        
    def validate_configuration(self, silent: bool = False) -> bool:
        """
        Validate that all required Spanner configuration is available
        
        Args:
            silent: If True, don't log errors (useful for availability checks)
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Check project ID using environment utility
            self.project_id = get_project_id()
            
            if not self.project_id:
                if not silent:
                    logger.error("Spanner configuration error: No valid project ID found. Set GOOGLE_CLOUD_PROJECT, FIREBASE_PROJECT_ID, GCP_PROJECT, or PROJECT_ID")
                return False
            
            # Check instance and database IDs
            self.instance_id = os.environ.get("SPANNER_INSTANCE_ID", "alchemist-graph")
            self.database_id = os.environ.get("SPANNER_DATABASE_ID", "agent-stories")
            
            # Check credentials
            self.credentials_path = (
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or
                os.environ.get("SPANNER_CREDENTIALS_PATH")
            )
            
            # In cloud environments, credentials might not be needed
            is_cloud_env = bool(
                os.environ.get("K_SERVICE") or 
                os.environ.get("GAE_APPLICATION") or
                os.environ.get("CLOUD_RUN_SERVICE")
            )
            
            if not is_cloud_env and not self.credentials_path:
                if not silent:
                    logger.error("Spanner configuration error: No credentials path set for local environment")
                return False
            
            if self.credentials_path and not os.path.exists(self.credentials_path):
                if not silent:
                    logger.error(f"Spanner configuration error: Credentials file not found: {self.credentials_path}")
                return False
            
            self._validated = True
            logger.info(f"Spanner configuration validated: {self.project_id}/{self.instance_id}/{self.database_id}")
            return True
            
        except Exception as e:
            if not silent:
                logger.error(f"Spanner configuration validation failed: {e}")
            return False
    
    def _get_project_from_credentials(self) -> Optional[str]:
        """Extract project ID from credentials file if available"""
        try:
            import json
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path and os.path.exists(creds_path):
                with open(creds_path, 'r') as f:
                    creds = json.load(f)
                    return creds.get('project_id')
        except Exception:
            pass
        return None
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as a dictionary"""
        return {
            "project_id": self.project_id,
            "instance_id": self.instance_id,
            "database_id": self.database_id,
            "credentials_path": self.credentials_path,
            "validated": self._validated
        }
    
    def is_configured(self) -> bool:
        """Check if configuration is valid"""
        return self._validated

# Global instance
_spanner_config = SpannerConfig()

def validate_spanner_config() -> bool:
    """Validate Spanner configuration globally"""
    return _spanner_config.validate_configuration()

def get_spanner_config() -> SpannerConfig:
    """Get the global Spanner configuration instance"""
    return _spanner_config

def is_spanner_configured() -> bool:
    """Check if Spanner is properly configured"""
    if not _spanner_config._validated:
        _spanner_config.validate_configuration(silent=True)
    return _spanner_config.is_configured()

def get_required_env_vars() -> Dict[str, str]:
    """Get required environment variables for Spanner"""
    return {
        "GOOGLE_CLOUD_PROJECT": "Google Cloud project ID (required)",
        "SPANNER_INSTANCE_ID": "Spanner instance ID (defaults to 'alchemist-graph')", 
        "SPANNER_DATABASE_ID": "Spanner database ID (defaults to 'agent-stories')",
        "GOOGLE_APPLICATION_CREDENTIALS": "Path to service account key file (required for local dev)"
    }

def print_configuration_help():
    """Print helpful configuration information"""
    print("\n🔧 Spanner Configuration Help")
    print("=" * 50)
    print("\nRequired Environment Variables:")
    for var, desc in get_required_env_vars().items():
        current_value = os.environ.get(var, "NOT SET")
        status = "✅" if current_value != "NOT SET" else "❌"
        print(f"  {status} {var}: {desc}")
        if current_value != "NOT SET":
            if "CREDENTIALS" in var and len(current_value) > 50:
                print(f"      Current: {current_value[:50]}...")
            else:
                print(f"      Current: {current_value}")
        print()
    
    config = get_spanner_config()
    print(f"\nConfiguration Status: {'✅ Valid' if config.is_configured() else '❌ Invalid'}")
    print(f"Validation Details:")
    for key, value in config.get_config_dict().items():
        if key == "credentials_path" and value and len(value) > 50:
            value = f"{value[:50]}..."
        print(f"  - {key}: {value}")

if __name__ == "__main__":
    print_configuration_help()