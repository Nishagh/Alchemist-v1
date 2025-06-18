"""
Firebase Configuration Module

This module provides functionality to initialize and access Firebase services,
particularly Firestore for the conversation-centric architecture.
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore, storage
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

def get_storage_bucket():
    """
    Get Firebase Storage bucket with proper configuration.
    
    Returns:
        A Firebase Storage bucket instance
    """
    try:
        # Get the Firebase app (will be initialized by get_firestore_client if needed)
        try:
            app = firebase_admin.get_app()
        except ValueError:
            # Initialize app if it doesn't exist
            get_firestore_client()  # This will initialize the app
            app = firebase_admin.get_app()
        
        # Get bucket name from environment or construct from project ID
        bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET")
        if not bucket_name:
            project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
            
            # If no project ID in environment, try to get it from credentials file
            if not project_id:
                try:
                    import json
                    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                    if not cred_path:
                        cred_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firebase-credentials.json")
                    
                    if os.path.exists(cred_path):
                        with open(cred_path, 'r') as f:
                            cred_data = json.load(f)
                            project_id = cred_data.get('project_id')
                            logger.info(f"Extracted project ID from credentials file: {project_id}")
                except Exception as e:
                    logger.warning(f"Could not extract project ID from credentials file: {e}")
            
            if project_id:
                bucket_name = f"{project_id}.appspot.com"
            else:
                logger.error("No storage bucket name or project ID found")
                raise ValueError("Firebase Storage bucket name not configured")
        
        logger.info(f"Using Firebase Storage bucket: {bucket_name}")
        return storage.bucket(bucket_name, app)
        
    except Exception as e:
        logger.error(f"Error getting Firebase Storage bucket: {str(e)}")
        raise
