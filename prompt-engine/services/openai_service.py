"""
OpenAI Service Module

This module provides a centralized service for OpenAI API key management.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Service for centralized OpenAI API key management.
    
    This class provides a single source of truth for API keys used
    across the application.
    """
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self._api_key = None
        self._default_model = "gpt-4o"
        
        # Try to load API key from environment variables at initialization
        self._api_key = os.environ.get("OPENAI_API_KEY")
        if self._api_key:
            logger.info("OpenAI API key loaded from environment variables")
        else:
            logger.warning("No OpenAI API key found in environment variables")
    
    @property
    def api_key(self) -> Optional[str]:
        """
        Get the current OpenAI API key.
        
        Returns:
            The current API key or None if not set
        """
        return self._api_key
        
    @api_key.setter
    def api_key(self, value: str) -> None:
        """
        Set the OpenAI API key.
        
        Args:
            value: The OpenAI API key to use
        """
        self._api_key = value
        
        # Also set it in environment variables for backward compatibility
        os.environ["OPENAI_API_KEY"] = value
        
        logger.info("OpenAI API key has been set")
    
    @property
    def default_model(self) -> str:
        """
        Get the default OpenAI model.
        
        Returns:
            The default model name
        """
        return self._default_model
        
    @default_model.setter
    def default_model(self, value: str) -> None:
        """
        Set the default OpenAI model.
        
        Args:
            value: The model name to use
        """
        self._default_model = value
        logger.info(f"Default OpenAI model set to {value}")
    
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
            return False
            
        # Basic validation - OpenAI keys start with 'sk-' and are longer than 20 chars
        if self._api_key.startswith("sk-") and len(self._api_key) > 20:
            return True
            
        return False

# Create a default singleton instance
default_openai_service = OpenAIService()

def get_openai_service() -> OpenAIService:
    """
    Get the OpenAI service singleton.
    
    Returns:
        The OpenAI service instance
    """
    return default_openai_service
