"""
Firebase Configuration Module - V9 Modular Approach

This module provides a modern, modular approach to Firebase services,
following dependency injection patterns and separation of concerns.
Updated to use centralized Firebase authentication.
"""
import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from abc import ABC, abstractmethod

from google.cloud import firestore as gcp_firestore
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.transforms import SERVER_TIMESTAMP
from config.firebase_config import get_firestore_client, get_storage_bucket, get_firebase_settings, FirebaseSettings

# Set up module-level logger
logger = logging.getLogger(__name__)


class FirebaseApp:
    """Singleton Firebase app manager with centralized configuration."""
    
    _instance: Optional['FirebaseApp'] = None
    _firestore_client: Optional[FirestoreClient] = None
    _storage_bucket = None
    
    def __new__(cls) -> 'FirebaseApp':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.config = get_firebase_settings()
            self._initialized = True
    
    def get_firestore_client(self) -> FirestoreClient:
        """Get Firestore client using centralized authentication."""
        if not self._firestore_client:
            self._firestore_client = get_firestore_client()
            logger.info("Firebase service: Using centralized Firestore client")
        return self._firestore_client
    
    def get_storage_bucket(self):
        """Get Storage bucket using centralized authentication."""
        if not self._storage_bucket:
            self._storage_bucket = get_storage_bucket()
            logger.info("Firebase service: Using centralized Storage bucket")
        return self._storage_bucket
    
    def initialize(self) -> 'FirebaseApp':
        """Initialize Firebase connections using centralized clients."""
        try:
            # Initialize clients using centralized authentication
            self.get_firestore_client()
            self.get_storage_bucket()
            
            logger.info("Firebase app initialized successfully using centralized clients")
            logger.debug(f"Configuration: {self.config.to_dict()}")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase app: {str(e)}")
            raise


class FirestoreService:
    """Modular Firestore service with modern patterns."""
    
    def __init__(self, app: Optional['FirebaseApp'] = None):
        self._app = app or FirebaseApp()
        self._client: Optional[FirestoreClient] = None
    
    @property
    def client(self) -> FirestoreClient:
        """Get Firestore client instance."""
        if not self._client:
            self._client = self._app.get_firestore_client()
            logger.info("Firestore client initialized using centralized authentication")
        return self._client
    
    def collection(self, path: str):
        """Get a collection reference."""
        return self.client.collection(path)
    
    def document(self, path: str):
        """Get a document reference."""
        return self.client.document(path)
    
    @contextmanager
    def transaction(self):
        """Context manager for Firestore transactions."""
        transaction = self.client.transaction()
        try:
            yield transaction
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise
    
    def batch(self):
        """Get a new batch instance."""
        return self.client.batch()


class ConversationRepository:
    """Repository pattern for conversation operations."""
    
    def __init__(self, firestore_service: FirestoreService):
        self.db = firestore_service
    
    def create_conversation(self, agent_id: str, conversation_data: Dict[str, Any]) -> str:
        """Create a new conversation."""
        conversation_ref = self.db.collection('agents').document(agent_id).collection('conversations')
        
        # Add server timestamp
        conversation_data['created_at'] = SERVER_TIMESTAMP
        conversation_data['updated_at'] = SERVER_TIMESTAMP
        
        doc_ref, doc = conversation_ref.add(conversation_data)
        conversation_id = doc.id
        
        logger.info(f"Created conversation {conversation_id} for agent {agent_id}")
        return conversation_id
    
    def get_conversation(self, agent_id: str, conversation_id: str):
        """Get a conversation by ID."""
        doc_ref = self.db.collection('agents').document(agent_id).collection('conversations').document(conversation_id)
        return doc_ref.get()
    
    def add_message(
        self, 
        agent_id: str, 
        conversation_id: str, 
        message_data: Dict[str, Any]
    ) -> str:
        """Add a message to a conversation."""
        conversation_ref = self.db.collection('agents').document(agent_id).collection('conversations').document(conversation_id)
        
        # Check if conversation exists
        if not conversation_ref.get().exists:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Add timestamp
        message_data['timestamp'] = SERVER_TIMESTAMP
        
        # Add message
        message_ref, message_doc = conversation_ref.collection('messages').add(message_data)
        message_id = message_doc.id
        
        # Update conversation metadata
        conversation_ref.update({
            'updated_at': SERVER_TIMESTAMP,
            'message_count': gcp_firestore.Increment(1),
            'last_message': message_data.get('content', '')[:100]
        })
        
        logger.info(f"Added message {message_id} to conversation {conversation_id}")
        return message_id
    
    def get_messages(
        self, 
        agent_id: str, 
        conversation_id: str, 
        limit: Optional[int] = None
    ):
        """Get messages from a conversation."""
        query = (
            self.db.collection('agents')
            .document(agent_id)
            .collection('conversations')
            .document(conversation_id)
            .collection('messages')
            .order_by('timestamp')
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.stream()


class StorageService:
    """Modular Storage service."""
    
    def __init__(self, app: Optional['FirebaseApp'] = None):
        self._app = app or FirebaseApp()
        self._bucket = None
    
    @property
    def bucket(self):
        """Get Storage bucket instance."""
        if not self._bucket:
            self._bucket = self._app.get_storage_bucket()
            logger.info("Storage bucket initialized using centralized authentication")
        return self._bucket
    
    def upload_file(self, source_path: str, destination_path: str) -> str:
        """Upload a file to Storage."""
        blob = self.bucket.blob(destination_path)
        blob.upload_from_filename(source_path)
        logger.info(f"Uploaded {source_path} to {destination_path}")
        return destination_path
    
    def download_file(self, source_path: str, destination_path: str) -> str:
        """Download a file from Storage."""
        blob = self.bucket.blob(source_path)
        blob.download_to_filename(destination_path)
        logger.info(f"Downloaded {source_path} to {destination_path}")
        return destination_path


# Factory functions for dependency injection
def get_firestore_service() -> FirestoreService:
    """Factory function to get FirestoreService instance."""
    return FirestoreService()

def get_conversation_repository() -> ConversationRepository:
    """Factory function to get ConversationRepository instance."""
    return ConversationRepository(get_firestore_service())

def get_storage_service() -> StorageService:
    """Factory function to get StorageService instance."""
    return StorageService()

# Legacy compatibility
def get_firestore_client() -> FirestoreClient:
    """Legacy function for backward compatibility."""
    return get_firestore_service().client
