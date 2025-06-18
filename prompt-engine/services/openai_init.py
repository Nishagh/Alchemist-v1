"""
OpenAI Initialization Module

This module provides a central place for initializing OpenAI API access.
All components should use this module to initialize OpenAI access rather
than accessing environment variables directly.
"""
import os
import logging
from .openai_service import default_openai_service
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def initialize_openai(api_key=None, model=None):
    """
    Initialize OpenAI API access with the provided key or from environment variables.
    
    Args:
        api_key (str, optional): The OpenAI API key. If not provided, will try to get from OPENAI_API_KEY env var.
        model (str, optional): The default model to use. If not provided, will use the service default.
        
    Returns:
        bool: True if initialization was successful, False otherwise
    
    This should be called at application startup to ensure proper OpenAI API setup.
    """
    # If API key provided, use it
    if api_key:
        default_openai_service.api_key = api_key
    else:
        # If no API key provided, make sure we have one from environment
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            default_openai_service.api_key = api_key
    
    # Set model if provided
    if model:
        default_openai_service.default_model = model
    
    # Validate API key
    if not default_openai_service.validate_api_key():
        logger.error("OpenAI API key is missing or invalid. Please set a valid API key.")
        return False
    
    logger.info(f"OpenAI initialized with model: {default_openai_service.default_model}")
    return True

def get_openai_service():
    """
    Get the default OpenAI service instance.
    
    Returns:
        OpenAIService: The default OpenAI service instance
    """
    return default_openai_service
