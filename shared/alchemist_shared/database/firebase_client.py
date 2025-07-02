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
from firebase_admin.firestore import Client as FirestoreClient, SERVER_TIMESTAMP

# Import centralized collection constants
from alchemist_shared.constants.collections import Collections, DocumentFields, StatusValues

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Singleton Firebase client for consistent database access across services.
    
    This class consolidates Firebase initialization and provides a centralized
    way to access Firestore and Storage services across all Alchemist services.
    """
    
    _instance: Optional['FirebaseClient'] = None
    _firestore_client: Optional[FirestoreClient] = None
    _storage_bucket: Optional[Any] = None
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
        
        # Validate deployment security
        self.validate_deployment_security()
        
        logger.info("Firebase client initialized successfully")
    
    def _is_cloud_environment(self) -> bool:
        """Check if running in cloud environment."""
        return bool(
            os.environ.get("K_SERVICE") or 
            os.environ.get("GOOGLE_CLOUD_PROJECT") or
            os.environ.get("GAE_APPLICATION")
        )
    
    def _get_credentials_path(self) -> str:
        """Get path to Firebase credentials file with centralized priority logic."""
        # Priority 1: Explicit environment variable for credentials path
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            logger.info(f"Using Firebase credentials from FIREBASE_CREDENTIALS_PATH: {cred_path}")
            return cred_path
        
        # Priority 2: Standard GOOGLE_APPLICATION_CREDENTIALS
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            logger.info(f"Using Firebase credentials from GOOGLE_APPLICATION_CREDENTIALS: {cred_path}")
            return cred_path
        
        # Priority 3: Shared folder credentials (for local development)
        shared_cred_path = self._find_shared_credentials()
        if shared_cred_path:
            logger.info(f"Using Firebase credentials from shared folder: {shared_cred_path}")
            return shared_cred_path
        
        # Priority 4: Centralized root directory (enforced for consistency)
        root_cred_path = self._find_project_root_credentials()
        if root_cred_path:
            logger.info(f"Using centralized Firebase credentials from project root: {root_cred_path}")
            return root_cred_path
        
        # Priority 5: Legacy fallback locations (with deprecation warning)
        legacy_paths = [
            "firebase-credentials.json",
            "../firebase-credentials.json", 
            "../../firebase-credentials.json",
            "/app/firebase-credentials.json"
        ]
        
        for path in legacy_paths:
            if os.path.exists(path):
                logger.warning(
                    f"Using legacy Firebase credentials location: {path}. "
                    "Consider moving to shared folder or setting FIREBASE_CREDENTIALS_PATH"
                )
                return path
        
        raise FileNotFoundError(
            "Firebase credentials file not found. Please:\n"
            "1. Set FIREBASE_CREDENTIALS_PATH environment variable, or\n"
            "2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable, or\n"
            "3. Place firebase-credentials.json in shared folder, or\n"
            "4. Place firebase-credentials.json in project root directory"
        )
    
    def _find_project_root_credentials(self) -> Optional[str]:
        """Find firebase-credentials.json in project root directory."""
        current_dir = os.getcwd()
        
        # Look for project root indicators and firebase-credentials.json
        for _ in range(5):  # Max 5 levels up
            cred_path = os.path.join(current_dir, "firebase-credentials.json")
            
            # Check if this is likely the project root
            if os.path.exists(cred_path):
                # Verify this is actually the project root by checking for other indicators
                indicators = [
                    "agent-engine", "agent-studio", "billing-service", 
                    "knowledge-vault", "shared", ".git"
                ]
                
                if any(os.path.exists(os.path.join(current_dir, indicator)) for indicator in indicators):
                    return cred_path
            
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached filesystem root
                break
            current_dir = parent_dir
        
        return None
    
    def _find_shared_credentials(self) -> Optional[str]:
        """Find firebase-credentials.json in shared folder for local development."""
        current_dir = os.getcwd()
        
        # Look for shared folder and firebase-credentials.json
        for _ in range(5):  # Max 5 levels up
            shared_dir = os.path.join(current_dir, "shared")
            
            if os.path.exists(shared_dir):
                cred_path = os.path.join(shared_dir, "firebase-credentials.json")
                if os.path.exists(cred_path):
                    logger.info(f"Found shared credentials at: {cred_path}")
                    return cred_path
            
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached filesystem root
                break
            current_dir = parent_dir
        
        return None
    
    @property
    def db(self) -> FirestoreClient:
        """Get Firestore client."""
        if not self._firestore_client:
            raise RuntimeError("Firebase client not initialized")
        return self._firestore_client
    
    @property
    def storage(self):
        """Get Firebase Storage bucket."""
        if not self._storage_bucket:
            self._storage_bucket = self._get_storage_bucket()
        return self._storage_bucket
    
    def _get_storage_bucket(self):
        """Initialize and return Firebase Storage bucket."""
        bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET")
        
        if not bucket_name:
            project_id = self._get_project_id()
            bucket_name = f"{project_id}.appspot.com"
        
        logger.info(f"Using Firebase Storage bucket: {bucket_name}")
        return storage.bucket(bucket_name)
    
    def _get_project_id(self) -> str:
        """Get Firebase project ID from environment or credentials file."""
        project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        
        if not project_id:
            cred_path = self._get_credentials_path()
            with open(cred_path, 'r') as f:
                cred_data = json.load(f)
                project_id = cred_data.get('project_id')
        
        if not project_id:
            raise ValueError("Firebase project ID not found in environment or credentials")
        
        return project_id
    
    def validate_deployment_security(self):
        """Validate that no credential files are present in deployment environment."""
        if not self._is_cloud_environment():
            return  # Only validate in cloud environments
        
        # Check for credential files that shouldn't exist in cloud deployments
        credential_files = [
            "firebase-credentials.json",
        ]
        
        found_files = []
        for filename in credential_files:
            if os.path.exists(filename):
                found_files.append(filename)
                
        if found_files:
            logger.warning(
                f"Security Alert: Credential files found in cloud deployment: {found_files}. "
                "These should be excluded from deployment images."
            )
    
    def get_collection(self, collection_name: str):
        """Get a Firestore collection reference with validation."""
        from alchemist_shared.constants.collections import validate_collection_usage
        validate_collection_usage(collection_name)
        return self.db.collection(collection_name)
    
    def get_document(self, collection_name: str, document_id: str):
        """Get a Firestore document reference with validation."""
        from alchemist_shared.constants.collections import validate_collection_usage
        validate_collection_usage(collection_name)
        return self.db.collection(collection_name).document(document_id)
    
    # Convenience methods for common collections
    def get_agents_collection(self):
        """Get the agents collection reference."""
        return self.get_collection(Collections.AGENTS)
    
    def get_conversations_collection(self):
        """Get the conversations collection reference."""
        return self.get_collection(Collections.CONVERSATIONS)
    
    def get_deployments_collection(self):
        """Get the agent deployments collection reference."""
        return self.get_collection(Collections.AGENT_DEPLOYMENTS)
    
    def get_user_accounts_collection(self):
        """Get the user accounts collection reference."""
        return self.get_collection(Collections.USER_ACCOUNTS)
    
    def get_credit_transactions_collection(self):
        """Get the credit transactions collection reference."""
        return self.get_collection(Collections.CREDIT_TRANSACTIONS)
    
    def get_knowledge_files_collection(self):
        """Get the knowledge files collection reference."""
        return self.get_collection(Collections.KNOWLEDGE_FILES)
    
    def get_knowledge_embeddings_collection(self):
        """Get the knowledge embeddings collection reference."""
        return self.get_collection(Collections.KNOWLEDGE_EMBEDDINGS)
    
    # CRUD operation methods
    async def add_document(self, collection_name: str, data: Dict[str, Any]) -> str:
        """Add a document to a collection and return the document ID."""
        doc_ref = self.get_collection(collection_name).add(data)
        # Handle both sync and async returns from Firestore
        if hasattr(doc_ref, '__await__'):
            doc_ref = await doc_ref
        # doc_ref is a tuple (timestamp, document_reference) for add operations
        if isinstance(doc_ref, tuple):
            return doc_ref[1].id
        return doc_ref.id
    
    async def update_document(self, collection_name: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in a collection."""
        doc_ref = self.get_document(collection_name, document_id)
        result = doc_ref.update(data)
        # Handle both sync and async returns from Firestore
        if hasattr(result, '__await__'):
            await result
        return True
    
    async def get_document_data(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document's data from a collection."""
        doc_ref = self.get_document(collection_name, document_id)
        doc = doc_ref.get()
        # Handle both sync and async returns from Firestore
        if hasattr(doc, '__await__'):
            doc = await doc
        return doc.to_dict() if doc.exists else None
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from a collection."""
        doc_ref = self.get_document(collection_name, document_id)
        result = doc_ref.delete()
        # Handle both sync and async returns from Firestore
        if hasattr(result, '__await__'):
            await result
        return True


# Convenience functions for backward compatibility
def get_firestore_client() -> FirestoreClient:
    """Get Firestore client instance."""
    return FirebaseClient().db


def get_storage_bucket():
    """Get Firebase Storage bucket instance."""
    return FirebaseClient().storage