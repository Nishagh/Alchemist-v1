"""
Firebase Configuration Module

This module provides functionality to initialize and access Firebase services,
particularly Firestore for the conversation-centric architecture.

Updated to use centralized Firebase client for consistent authentication.
"""
import logging
from firebase_admin.firestore import Client

# Import centralized Firebase client
from alchemist_shared.database.firebase_client import FirebaseClient

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
        _firebase_client = FirebaseClient()
        logger.info("Prompt Engine: Firebase client initialized using centralized authentication")
    
    return _firebase_client.db
