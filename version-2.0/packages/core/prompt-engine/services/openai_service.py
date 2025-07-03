"""
OpenAI Service Module

This module provides centralized access to OpenAI services and configuration.
All OpenAI API calls should go through this service to ensure consistent handling
of API keys, models, and error handling.

Uses centralized configuration from alchemist_shared to detect environment
and load API keys appropriately (local .env or cloud secrets).
"""
import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import centralized configuration from alchemist_shared
try:
    from alchemist_shared.config.base_settings import BaseSettings
    from alchemist_shared.config.environment import detect_environment, is_cloud_environment
    ALCHEMIST_SHARED_AVAILABLE = True
except ImportError:
    logging.warning("alchemist_shared not available - using fallback configuration")
    ALCHEMIST_SHARED_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Centralized service for OpenAI API access.
    
    This class handles all OpenAI API interactions, including:
    - API key management
    - Model configuration
    
    Uses alchemist_shared for centralized configuration management.
    This is a singleton class, so only one instance will exist.
    All OpenAI API interactions should go through this service.
    """
    
    _instance = None
    _api_key: str = None
    _default_model: str = "gpt-4o"
    _settings: Optional[BaseSettings] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(OpenAIService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the service by loading the API key from centralized configuration."""
        # Try to use centralized configuration first
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                self._settings = BaseSettings()
                
                # Log environment detection
                environment = detect_environment()
                is_cloud = is_cloud_environment()
                logger.info(f"Environment detected: {environment} (cloud: {is_cloud})")
                
                # Get OpenAI configuration from centralized settings
                openai_config = self._settings.get_openai_config()
                self._api_key = openai_config.get("api_key")
                
                if self._api_key:
                    logger.info("Using OpenAI API key from centralized configuration")
                    # Set in environment for backward compatibility
                    os.environ["OPENAI_API_KEY"] = self._api_key
                else:
                    logger.warning("No OpenAI API key found in centralized configuration")
                
                # Use centralized model configuration
                self._default_model = self._settings.openai_model
                logger.info(f"Using centralized model configuration: {self._default_model}")
                
            except Exception as e:
                logger.warning(f"Failed to load centralized configuration: {e}, falling back to direct env vars")
                self._api_key = None
        
        # Fallback to direct environment variable if centralized config fails or not available
        if not self._api_key:
            self._api_key = os.getenv("OPENAI_API_KEY", "")
            if self._api_key:
                logger.info("Using OpenAI API key from OPENAI_API_KEY environment variable")
            else:
                logger.warning("OPENAI_API_KEY environment variable is not set!")
        
        # Log masked API key for debugging
        if self._api_key:
            logger.info(f"OpenAI API key loaded: {self._api_key[:5]}...")
    
    @property
    def api_key(self) -> str:
        """Get the OpenAI API key."""
        if not self._api_key:
            # Try to reload from centralized config first
            if ALCHEMIST_SHARED_AVAILABLE and self._settings:
                try:
                    openai_config = self._settings.get_openai_config()
                    self._api_key = openai_config.get("api_key")
                    if self._api_key:
                        os.environ["OPENAI_API_KEY"] = self._api_key
                        logger.info("Reloaded OpenAI API key from centralized configuration")
                except Exception as e:
                    logger.warning(f"Failed to reload from centralized config: {e}")
            
            # Fallback to environment variable
            if not self._api_key:
                self._api_key = os.getenv("OPENAI_API_KEY", "")
        
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str):
        """Set the OpenAI API key."""
        if not value:
            logger.warning("Attempted to set empty OpenAI API key")
            return
        
        if value != self._api_key:
            self._api_key = value
            logger.info(f"OpenAI API key updated: {value[:5]}...")
            
            # Set as environment variable to ensure all components use the same key
            os.environ["OPENAI_API_KEY"] = value
    
    @property
    def default_model(self) -> str:
        """Get the default OpenAI model."""
        return self._default_model
    
    @default_model.setter
    def default_model(self, value: str):
        """Set the default OpenAI model."""
        if value != self._default_model:
            self._default_model = value
            logger.info(f"Default OpenAI model updated to: {value}")
    
    def get_api_key(self) -> Optional[str]:
        """
        Get the current OpenAI API key.
        
        Returns:
            The current API key or None if not set
        """
        return self._api_key
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key is set and appears to be valid.
        This doesn't make an actual API call, just checks if the key exists
        and has the expected format.
        
        Returns:
            True if the API key appears valid, False otherwise
        """
        if not self._api_key:
            logger.warning("OpenAI API key is not set")
            return False
            
        # Basic validation - OpenAI keys start with 'sk-' and are longer than 20 chars
        if self._api_key.startswith("sk-") and len(self._api_key) > 20:
            return True
            
        logger.warning(f"OpenAI API key format appears invalid: {self._api_key[:10]}...")
        return False
    
    def from_config(self, config: Dict[str, Any]) -> None:
        """
        Configure the service from a configuration dictionary.
        
        Args:
            config: Configuration dictionary with optional 'openai_api_key' and 'model' keys
        """
        if "openai_api_key" in config and config["openai_api_key"]:
            self.api_key = config["openai_api_key"]
        
        if "model" in config and config["model"]:
            self.default_model = config["model"]

# Create a default singleton instance
default_openai_service = OpenAIService()

def get_openai_service() -> OpenAIService:
    """
    Get the OpenAI service singleton.
    
    Returns:
        The OpenAI service instance
    """
    return default_openai_service
