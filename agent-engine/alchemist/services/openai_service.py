"""
OpenAI Service Module

This module provides centralized access to OpenAI services and configuration.
All OpenAI API calls should go through this service to ensure consistent handling
of API keys, models, and error handling.

Updated to use centralized alchemist_shared modules for configuration and authentication.
"""
import logging
from typing import Optional, Dict, Any, Tuple
from langchain_openai import ChatOpenAI

# Import centralized configuration from alchemist_shared
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.database.firebase_client import FirebaseClient

logger = logging.getLogger(__name__)

# Cache for LLM instances
_LLM_CACHE: Dict[Tuple[str, float], ChatOpenAI] = {}

class OpenAIService:
    """
    Centralized service for OpenAI API access.
    
    This class handles all OpenAI API interactions, including:
    - API key management
    - Model configuration
    - ChatOpenAI instance creation
    - Integration with centralized alchemist_shared configuration
    
    This is a singleton class, so only one instance will exist.
    All OpenAI API interactions should go through this service.
    """
    
    _instance = None
    _api_key: str = None
    _default_model: str = "gpt-4"
    _settings: Optional[BaseSettings] = None
    _firebase_client: Optional[FirebaseClient] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(OpenAIService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the service using centralized configuration."""
        # Load centralized settings
        self._settings = BaseSettings()
        
        # Initialize Firebase client for potential future use
        self._firebase_client = FirebaseClient()
        
        # Get OpenAI configuration from centralized settings
        openai_config = self._settings.get_openai_config()
        self._api_key = openai_config.get("api_key")
        self._default_model = self._settings.openai_model
        
        if self._api_key:
            logger.info(f"OpenAI API key loaded from centralized config: {self._api_key[:5]}...")
        else:
            logger.warning("No OpenAI API key found in centralized configuration")
            
        logger.info(f"Using centralized model configuration: {self._default_model}")
    
    @property
    def api_key(self) -> str:
        """Get the OpenAI API key."""
        if not self._api_key and self._settings:
            openai_config = self._settings.get_openai_config()
            self._api_key = openai_config.get("api_key", "")
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str):
        """Set the OpenAI API key."""
        if not value:
            logger.warning("Attempted to set empty OpenAI API key")
            return
        
        if value != self._api_key:
            self._api_key = value
            # Reset cached models when API key changes
            global _LLM_CACHE
            _LLM_CACHE = {}
            logger.info(f"OpenAI API key updated: {value[:5]}...")
    
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
    
    def get_chat_model(self, model: Optional[str] = None, temperature: float = 0.2) -> ChatOpenAI:
        """
        Get a ChatOpenAI instance with the specified model and temperature.
        
        Args:
            model: Model name (defaults to the default model)
            temperature: Temperature for the model (defaults to 0.2)
            
        Returns:
            ChatOpenAI instance
            
        Raises:
            ValueError: If the API key is not set
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is not set. Please set it using the OPENAI_API_KEY environment variable or OpenAIService.api_key")
        
        model_name = model or self._default_model
        cache_key = (model_name, temperature)
        
        if cache_key not in _LLM_CACHE:
            logger.info(f"Creating new ChatOpenAI instance for model: {model_name}, temperature: {temperature}")
            _LLM_CACHE[cache_key] = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=self.api_key,
                verbose=True
            )
        
        return _LLM_CACHE[cache_key]
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key is set and valid.
        
        Returns:
            True if the API key is valid, False otherwise
        """
        if not self.api_key:
            logger.warning("OpenAI API key is not set")
            return False
        
        # More validation could be added here, such as making a test API call
        
        return True
    
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
    
    @property
    def firebase_client(self) -> Optional[FirebaseClient]:
        """Get the Firebase client instance."""
        return self._firebase_client
    
    @property
    def settings(self) -> Optional[BaseSettings]:
        """Get the centralized settings instance."""
        return self._settings
    
    def reload_config(self) -> bool:
        """
        Reload configuration from centralized settings.
        
        Returns:
            bool: True if reload was successful, False otherwise
        """
        try:
            # Reload settings
            self._settings = BaseSettings()
            
            # Update OpenAI configuration
            openai_config = self._settings.get_openai_config()
            new_api_key = openai_config.get("api_key")
            
            if new_api_key and new_api_key != self._api_key:
                self.api_key = new_api_key
                logger.info("OpenAI API key updated from centralized config")
            
            # Update model if changed
            new_model = self._settings.openai_model
            if new_model and new_model != self._default_model:
                self.default_model = new_model
                logger.info(f"Default model updated to: {new_model}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False

# Create a default instance
default_openai_service = OpenAIService()
