"""
OpenAI Initialization Module

This module provides a central place for initializing OpenAI API access.
All components should use this module to initialize OpenAI access rather
than accessing environment variables directly.

Uses centralized configuration from alchemist_shared to detect environment
and load API keys appropriately (local .env or cloud secrets).
"""
import os
import logging
from .openai_service import default_openai_service

# Import centralized configuration from alchemist_shared
try:
    from alchemist_shared.config.base_settings import BaseSettings
    from alchemist_shared.config.environment import detect_environment, is_cloud_environment
    ALCHEMIST_SHARED_AVAILABLE = True
except ImportError:
    logging.warning("alchemist_shared not available - using fallback configuration")
    ALCHEMIST_SHARED_AVAILABLE = False

logger = logging.getLogger(__name__)

def initialize_openai(api_key=None, model=None):
    """
    Initialize OpenAI API access using centralized configuration.
    
    Uses alchemist_shared to detect environment and load API keys:
    - Local development: Loads from parent directory .env file
    - Cloud deployment: Uses Google Secret Manager via environment variables
    
    Args:
        api_key (str, optional): The OpenAI API key. If not provided, will use centralized config.
        model (str, optional): The default model to use. If not provided, will use centralized config.
        
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    
    # Use centralized configuration if available
    if ALCHEMIST_SHARED_AVAILABLE and not api_key:
        try:
            # Load settings from centralized configuration
            # This will automatically use the correct .env file path and environment detection
            settings = BaseSettings()
            
            # Log environment detection
            environment = detect_environment()
            is_cloud = is_cloud_environment()
            logger.info(f"Environment detected: {environment} (cloud: {is_cloud})")
            
            # Get OpenAI configuration from centralized settings
            openai_config = settings.get_openai_config()
            api_key = openai_config.get("api_key")
            
            if api_key:
                logger.info("Using OpenAI API key from centralized configuration")
            else:
                logger.warning("No OpenAI API key found in centralized configuration")
                
            # Use centralized model if not provided
            if not model:
                model = settings.openai_model
                logger.info(f"Using centralized model configuration: {model}")
                
        except Exception as e:
            logger.warning(f"Failed to load centralized configuration: {e}, falling back to direct env vars")
            api_key = None
    
    # Fallback to direct environment variable if centralized config fails or not available
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            logger.info("Using OpenAI API key from OPENAI_API_KEY environment variable")
        else:
            logger.error("No OpenAI API key found in environment variables")
    
    # Set API key in service
    if api_key:
        default_openai_service.api_key = api_key
    
    # Set model if provided or use default
    if model:
        default_openai_service.default_model = model
    elif not hasattr(default_openai_service, 'default_model'):
        default_openai_service.default_model = "gpt-4"
    
    # Validate API key
    if not default_openai_service.validate_api_key():
        logger.error("OpenAI API key is missing or invalid. Please set a valid API key.")
        return False
    
    logger.info(f"OpenAI initialized successfully with model: {default_openai_service.default_model}")
    return True

def get_openai_service():
    """
    Get the default OpenAI service instance.
    
    Returns:
        OpenAIService: The default OpenAI service instance
    """
    return default_openai_service
