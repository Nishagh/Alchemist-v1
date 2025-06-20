import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

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
        """Initialize Firebase client"""
        try:
            # Get storage bucket name from environment variable
            # Try multiple possible environment variable names
            storage_bucket = (
                os.environ.get('FIREBASE_STORAGE_BUCKET') or
                os.environ.get('GCS_BUCKET') or
                os.environ.get('STORAGE_BUCKET')
            )
            
            # If still not found, try to construct from project ID
            if not storage_bucket:
                project_id = (
                    os.environ.get('FIREBASE_PROJECT_ID') or
                    os.environ.get('PROJECT_ID') or
                    os.environ.get('GOOGLE_CLOUD_PROJECT') or
                    os.environ.get('GCP_PROJECT')
                )
                if project_id:
                    storage_bucket = f"{project_id}.appspot.com"
                    print(f"No explicit storage bucket set, using default: {storage_bucket}")
            
            if not storage_bucket:
                raise ValueError("Storage bucket name not specified. Set FIREBASE_STORAGE_BUCKET environment variable or ensure FIREBASE_PROJECT_ID is set.")
            
            print(f"Initializing Firebase with storage bucket: {storage_bucket}")
                
            if not firebase_admin._apps:
                # Handle credentials properly for both local and Cloud Run environments
                credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                print(f"Credentials path from env: {credentials_path}")
                
                # Check if we're in Cloud Run (no credentials file) or local development
                use_default_credentials = True
                
                if credentials_path and os.path.exists(credentials_path):
                    # Local development with credentials file
                    try:
                        print(f"Using credentials file: {credentials_path}")
                        cred = credentials.Certificate(credentials_path)
                        firebase_admin.initialize_app(cred, options={
                            'storageBucket': storage_bucket
                        })
                        print(f"Successfully initialized Firebase with credentials file: {credentials_path}")
                        use_default_credentials = False
                    except Exception as e:
                        print(f"Failed to use credentials file: {e}, falling back to default credentials")
                        use_default_credentials = True
                
                if use_default_credentials:
                    # Cloud Run with default service account - unset the env var to avoid conflicts
                    print("Using default service account authentication")
                    
                    # Temporarily unset the credentials path to force default credentials
                    original_creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                        del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                        print("Temporarily removed GOOGLE_APPLICATION_CREDENTIALS env var")
                    
                    try:
                        firebase_admin.initialize_app(options={
                            'storageBucket': storage_bucket
                        })
                        print("Successfully initialized Firebase with default service account")
                    except Exception as e:
                        # Restore the original environment variable if initialization failed
                        if original_creds_path:
                            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = original_creds_path
                        raise e
                
            # Initialize Firestore and Storage
            self.db = firestore.client()
            self.bucket = storage.bucket()
            self.files_collection = self.db.collection('knowledge_base_files')
            # Using new collection structure for embeddings: knowledge_base_embeddings/{agent_id}_embeddings/{chunk_id}
            self.embeddings_base_collection = 'knowledge_base_embeddings'
            
            print("Firebase successfully initialized")
            
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            print(f"Environment variables: FIREBASE_STORAGE_BUCKET={os.environ.get('FIREBASE_STORAGE_BUCKET')}, FIREBASE_PROJECT_ID={os.environ.get('FIREBASE_PROJECT_ID')}, PROJECT_ID={os.environ.get('PROJECT_ID')}")
            raise e
    
    def add_file(self, file_data: Dict[str, Any]) -> str:
        """Add file metadata to Firestore"""
        # Generate file ID if not provided
        file_id = file_data.get('id', str(uuid.uuid4()))
        file_data['id'] = file_id
        
        # Set upload date if not provided
        if 'upload_date' not in file_data:
            file_data['upload_date'] = datetime.now()
        
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
                'created_at': chunk.get('created_at', datetime.now()),
                'updated_at': datetime.now()
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
