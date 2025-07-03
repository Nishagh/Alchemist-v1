"""
Firebase Configuration Module

This module provides functionality to initialize and access Firebase services,
particularly Firestore for the conversation-centric architecture.

Updated to use centralized Firebase client for consistent authentication.
"""
import logging
from firebase_admin.firestore import Client

# Import centralized Firebase client with fallback
try:
    from alchemist_shared.database.firebase_client import FirebaseClient
    FIREBASE_CLIENT_AVAILABLE = True
except ImportError:
    logging.warning("alchemist_shared not available - using fallback Firebase client")
    FirebaseClient = None
    FIREBASE_CLIENT_AVAILABLE = False

# Set up module-level logger
logger = logging.getLogger(__name__)

# Cache for the centralized Firebase client
_firebase_client = None

def get_firestore_client() -> Client:
    """
    Get Firestore client using centralized Firebase authentication.
    
    Returns:
        A Firestore client instance
    """
    global _firebase_client
    
    if not _firebase_client:
        if FIREBASE_CLIENT_AVAILABLE:
            _firebase_client = FirebaseClient()
            logger.info("Agent Engine: Firebase client initialized using centralized authentication")
        else:
            # Fallback to direct Firebase Admin initialization
            import firebase_admin
            from firebase_admin import credentials, firestore
            import os
            
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                logger.info("Agent Engine: Firebase initialized with fallback method")
            
            # Create a simple client wrapper
            class FallbackClient:
                def __init__(self):
                    self.db = firestore.client()
                    try:
                        from firebase_admin import storage
                        bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET")
                        if bucket_name:
                            self.storage = storage.bucket(bucket_name)
                            logger.info(f"Storage bucket initialized: {bucket_name}")
                        else:
                            logger.warning("Storage bucket name not specified. Specify the bucket name via the 'storageBucket' option when initializing the App, or specify the bucket name explicitly when calling the storage.bucket() function.")
                            self.storage = None
                    except Exception as e:
                        logger.warning(f"Storage not available: {e}")
                        self.storage = None
            
            _firebase_client = FallbackClient()
    
    return _firebase_client.db

def get_storage_bucket():
    """
    Get Firebase Storage bucket using centralized client.
    
    Returns:
        A Firebase Storage bucket instance
    """
    global _firebase_client
    
    if not _firebase_client:
        get_firestore_client()  # This will initialize the client
    
    return _firebase_client.storage
