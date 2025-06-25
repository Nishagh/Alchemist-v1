import os
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

# Import centralized Firebase client
from alchemist_shared.database.firebase_client import FirebaseClient
from alchemist_shared.constants.collections import Collections
from firebase_admin.firestore import SERVER_TIMESTAMP

# Load environment variables
load_dotenv()

class FirebaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Firebase using centralized client"""
        try:
            # Use centralized Firebase client
            self._firebase_client = FirebaseClient()
            self.db = self._firebase_client.db
            self.bucket = self._firebase_client.storage
            
            # Initialize collection references using centralized constants
            self.files_collection = self._firebase_client.get_knowledge_files_collection()
            self.embeddings_base_collection = Collections.KNOWLEDGE_EMBEDDINGS
            
            print("Knowledge Vault Firebase service initialized successfully using centralized client")
            
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            raise e
    
    def add_file(self, file_data: Dict[str, Any]) -> str:
        """Add file metadata to Firestore"""
        # Generate file ID if not provided
        file_id = file_data.get('id', str(uuid.uuid4()))
        file_data['id'] = file_id
        
        # Set upload date if not provided
        if 'upload_date' not in file_data:
            file_data['upload_date'] = SERVER_TIMESTAMP
        
        # Store in Firestore - create new document
        self.files_collection.document(file_id).set(file_data)
        return file_id
    
    def update_file(self, file_id: str, data: Dict[str, Any]) -> None:
        """Update file metadata in Firestore"""
        self.files_collection.document(file_id).update(data)
    
    def delete_file(self, file_id: str) -> None:
        """Delete file metadata from Firestore"""
        # Get file info to determine agent_id
        file_data = self.get_file(file_id)
        if not file_data:
            return
            
        agent_id = file_data.get('agent_id')
        
        # Delete file metadata
        self.files_collection.document(file_id).delete()
        
        # Delete all embeddings associated with this file
        if agent_id:
            self.delete_embeddings_by_file(agent_id, file_id)
    
    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Firestore"""
        doc = self.files_collection.document(file_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def get_files_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all files for an agent"""
        query = self.files_collection.where('agent_id', '==', agent_id)
        return [doc.to_dict() for doc in query.stream()]
    
    def add_embeddings(self, agent_id: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """Add document chunks with embeddings to agent-specific Firestore collection"""
        batch = self.db.batch()
        chunk_ids = []
        
        # Get agent-specific embeddings collection using proper subcollection structure
        embeddings_collection = self.db.collection(self.embeddings_base_collection).document(agent_id).collection('embeddings')
        
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            doc_ref = embeddings_collection.document(chunk_id)
            
            # Prepare embedding document
            embedding_doc = {
                'id': chunk_id,
                'file_id': chunk.get('file_id'),
                'agent_id': agent_id,
                'filename': chunk.get('filename'),
                'content': chunk.get('content'),
                'page_number': chunk.get('page_number', 1),
                'embedding': chunk.get('embedding'),
                'created_at': chunk.get('created_at', SERVER_TIMESTAMP),
                'updated_at': SERVER_TIMESTAMP
            }
            
            batch.set(doc_ref, embedding_doc)
            chunk_ids.append(chunk_id)
            
        batch.commit()
        return chunk_ids
    
    def get_embeddings_by_file(self, agent_id: str, file_id: str) -> List[Dict[str, Any]]:
        """Get all embeddings for a specific file"""
        embeddings_collection = self.db.collection(self.embeddings_base_collection).document(agent_id).collection('embeddings')
        query = embeddings_collection.where('file_id', '==', file_id)
        return [doc.to_dict() for doc in query.stream()]
    
    def get_embeddings_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all embeddings for an agent"""
        embeddings_collection = self.db.collection(self.embeddings_base_collection).document(agent_id).collection('embeddings')
        return [doc.to_dict() for doc in embeddings_collection.stream()]
    
    def upload_file_to_storage(self, file_content: bytes, storage_path: str) -> None:
        """Upload file to Firebase Storage"""
        print("Uploading file to Firebase Storage", storage_path)
        blob = self.bucket.blob(storage_path)
        blob.upload_from_string(file_content)
        print("File uploaded to Firebase Storage")
    
    def delete_file_from_storage(self, storage_path: str) -> None:
        """Delete file from Firebase Storage"""
        blob = self.bucket.blob(storage_path)
        blob.delete()
    
    def download_file_from_storage(self, storage_path: str) -> bytes:
        """Download file from Firebase Storage
        
        Args:
            storage_path: Path to the file in storage
            
        Returns:
            File content as bytes
        """
        try:
            blob = self.bucket.blob(storage_path)
            
            if not blob.exists():
                raise Exception(f"File not found in storage: {storage_path}")
            
            return blob.download_as_bytes()
            
        except Exception as e:
            raise Exception(f"Error downloading file from storage: {str(e)}")
    
    def get_download_url(self, storage_path: str) -> str:
        """Get download URL for a file"""
        import datetime as dt
        blob = self.bucket.blob(storage_path)
        return blob.generate_signed_url(dt.timedelta(minutes=15))
        
    def delete_embeddings_by_file(self, agent_id: str, file_id: str) -> int:
        """Delete all embeddings for a specific file
        
        Args:
            agent_id: Agent ID that owns the embeddings
            file_id: File ID to delete embeddings for
            
        Returns:
            Number of embeddings deleted
        """
        try:
            embeddings_collection = self.db.collection(self.embeddings_base_collection).document(agent_id).collection('embeddings')
            query = embeddings_collection.where('file_id', '==', file_id)
            embeddings = query.stream()
            
            deleted_count = 0
            for embedding in embeddings:
                embedding.reference.delete()
                deleted_count += 1
                
            return deleted_count
        except Exception as e:
            print(f"Error deleting embeddings by file: {str(e)}")
            return 0
            
    def delete_all_embeddings_by_agent(self, agent_id: str) -> int:
        """Delete all embeddings for an agent
        
        Args:
            agent_id: Agent ID to delete embeddings for
            
        Returns:
            Number of embeddings deleted
        """
        try:
            embeddings_collection = self.db.collection(self.embeddings_base_collection).document(agent_id).collection('embeddings')
            embeddings = embeddings_collection.stream()
            
            deleted_count = 0
            for embedding in embeddings:
                embedding.reference.delete()
                deleted_count += 1
                
            return deleted_count
        except Exception as e:
            print(f"Error deleting all embeddings by agent: {str(e)}")
            return 0
            
    def get_embedding_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics about embeddings for an agent
        
        Args:
            agent_id: Agent ID to get stats for
            
        Returns:
            Dictionary with embedding statistics
        """
        try:
            embeddings = self.get_embeddings_by_agent(agent_id)
            
            # Count unique files
            file_ids = set()
            for embedding in embeddings:
                if embedding.get('file_id'):
                    file_ids.add(embedding['file_id'])
            
            return {
                'agent_id': agent_id,
                'total_embeddings': len(embeddings),
                'unique_files': len(file_ids),
                'file_ids': list(file_ids)
            }
        except Exception as e:
            print(f"Error getting embedding stats: {str(e)}")
            return {
                'agent_id': agent_id,
                'total_embeddings': 0,
                'unique_files': 0,
                'file_ids': [],
                'error': str(e)
            }
