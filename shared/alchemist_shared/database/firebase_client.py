"""
Firebase Database Client

Centralized Firebase client management with singleton pattern.
Consolidates Firebase initialization logic from multiple services.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_admin.firestore import Client as FirestoreClient
from firebase_admin.storage import Bucket

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Singleton Firebase client for consistent database access across services.
    
    This class consolidates Firebase initialization and provides a centralized
    way to access Firestore and Storage services across all Alchemist services.
    """
    
    _instance: Optional['FirebaseClient'] = None
    _firestore_client: Optional[FirestoreClient] = None
    _storage_bucket: Optional[Bucket] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'FirebaseClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize()
            self._initialized = True
    
    def _initialize(self):
        """Initialize Firebase app with appropriate credentials."""
        try:
            # Check if app already exists
            try:
                app = firebase_admin.get_app()
                logger.info("Firebase app already initialized")
            except ValueError:
                # Initialize new app
                if self._is_cloud_environment():
                    logger.info("Initializing Firebase with Application Default Credentials")
                    app = firebase_admin.initialize_app()
                else:
                    logger.info("Initializing Firebase with credentials file")
                    cred_path = self._get_credentials_path()
                    cred = credentials.Certificate(cred_path)
                    app = firebase_admin.initialize_app(cred)
            
            # Initialize Firestore client
            self._firestore_client = firestore.client(app)
            logger.info("Firebase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase client: {e}")
            raise
    
    def _is_cloud_environment(self) -> bool:
        """Check if running in cloud environment."""
        return bool(
            os.environ.get("K_SERVICE") or 
            os.environ.get("GOOGLE_CLOUD_PROJECT") or
            os.environ.get("GAE_APPLICATION")
        )
    
    def _get_credentials_path(self) -> str:
        """Get path to Firebase credentials file."""
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not cred_path:
            # Try common locations
            possible_paths = [
                "firebase-credentials.json",
                "../firebase-credentials.json",
                "../../firebase-credentials.json",
                "/app/firebase-credentials.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    cred_path = path
                    break
        
        if not cred_path or not os.path.exists(cred_path):
            raise FileNotFoundError(
                "Firebase credentials file not found. "
                "Set GOOGLE_APPLICATION_CREDENTIALS or place firebase-credentials.json in project root."
            )
        
        logger.info(f"Using Firebase credentials from: {cred_path}")
        return cred_path
    
    @property
    def db(self) -> FirestoreClient:
        """Get Firestore client."""
        if not self._firestore_client:
            raise RuntimeError("Firebase client not initialized")
        return self._firestore_client
    
    @property
    def storage(self) -> Bucket:
        """Get Firebase Storage bucket."""
        if not self._storage_bucket:
            self._storage_bucket = self._get_storage_bucket()
        return self._storage_bucket
    
    def _get_storage_bucket(self) -> Bucket:
        """Initialize and return Firebase Storage bucket."""
        try:
            bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET")
            
            if not bucket_name:
                project_id = self._get_project_id()
                bucket_name = f"{project_id}.appspot.com"
            
            logger.info(f"Using Firebase Storage bucket: {bucket_name}")
            return storage.bucket(bucket_name)
            
        except Exception as e:
            logger.error(f"Failed to get Firebase Storage bucket: {e}")
            raise
    
    def _get_project_id(self) -> str:
        """Get Firebase project ID from environment or credentials file."""
        project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        
        if not project_id:
            try:
                cred_path = self._get_credentials_path()
                with open(cred_path, 'r') as f:
                    cred_data = json.load(f)
                    project_id = cred_data.get('project_id')
            except Exception as e:
                logger.warning(f"Could not extract project ID from credentials: {e}")
        
        if not project_id:
            raise ValueError("Firebase project ID not found in environment or credentials")
        
        return project_id
    
    def get_collection(self, collection_name: str):
        """Get a Firestore collection reference."""
        return self.db.collection(collection_name)
    
    def get_document(self, collection_name: str, document_id: str):
        """Get a Firestore document reference."""
        return self.db.collection(collection_name).document(document_id)


# Convenience functions for backward compatibility
def get_firestore_client() -> FirestoreClient:
    """Get Firestore client instance."""
    return FirebaseClient().db


def get_storage_bucket() -> Bucket:
    """Get Firebase Storage bucket instance."""
    return FirebaseClient().storage