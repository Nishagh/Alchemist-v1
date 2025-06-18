"""
Firebase Configuration Module

This module provides functionality to initialize and access Firebase services,
particularly Firestore for the conversation-centric architecture.
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import Client

# Set up module-level logger
logger = logging.getLogger(__name__)

# Cache for the Firestore client
_firestore_client = None

def is_cloud_environment() -> bool:
    """
    Check if the application is running in a cloud environment.
    
    Returns:
        True if running in a cloud environment, False otherwise
    """
    # Check for Cloud Run environment variables
    return bool(os.environ.get("K_SERVICE") or 
                os.environ.get("GOOGLE_CLOUD_PROJECT") or
                os.environ.get("GAE_APPLICATION"))

def get_firestore_client() -> Client:
    """
    Get or initialize a Firestore client, using appropriate credentials based on environment.
    
    In cloud environments, we use the default credentials (Application Default Credentials).
    In local environments, we use a credentials file.
    
    Returns:
        A Firestore client instance
    """
    global _firestore_client
    
    if _firestore_client:
        return _firestore_client
    
    try:
        # Check if we're running in a cloud environment
        if is_cloud_environment():
            # In cloud environments, use Application Default Credentials
            logger.info("Running in cloud environment, using Application Default Credentials")
            try:
                app = firebase_admin.get_app()
            except ValueError:
                # If no default app exists, initialize one without explicit credentials
                app = firebase_admin.initialize_app()
        else:
            # In local environment, use the credentials file
            logger.info("Running in local environment, using credentials file")
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if not cred_path:
                logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set in local environment")
                # Try to use firebase-credentials.json in the current directory
                cred_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firebase-credentials.json")
                if os.path.exists(cred_path):
                    logger.info(f"Using credentials file at: {cred_path}")
                else:
                    logger.error("No Firebase credentials file found")
                    raise FileNotFoundError("Firebase credentials file not found")
            
            cred = credentials.Certificate(cred_path)
            try:
                app = firebase_admin.get_app()
            except ValueError:
                app = firebase_admin.initialize_app(cred)
        
        # Initialize Firestore client
        _firestore_client = firestore.client(app)
        logger.info("Firestore client initialized successfully")
        return _firestore_client
    except Exception as e:
        logger.error(f"Error initializing Firestore client: {str(e)}")
        raise
