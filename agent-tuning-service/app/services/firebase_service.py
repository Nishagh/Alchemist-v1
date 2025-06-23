"""
Firebase service for the Agent Tuning Service
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import structlog

from app.config.settings import get_settings
from app.models import TrainingJob, TrainingPair, FineTunedModel, JobStatus

logger = structlog.get_logger(__name__)


class FirebaseService:
    """Service for Firebase/Firestore operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db: Optional[firestore.AsyncClient] = None
        self.storage_client: Optional[storage.Client] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Firebase services"""
        if self._initialized:
            return
        
        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                if self.settings.firebase_credentials_path:
                    cred = credentials.Certificate(self.settings.firebase_credentials_path)
                else:
                    # Use default credentials (service account key)
                    cred = credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred, {
                    'projectId': self.settings.firebase_project_id,
                })
            
            # Initialize Firestore client
            self.db = firestore.AsyncClient(project=self.settings.firebase_project_id)
            
            # Initialize Cloud Storage client
            self.storage_client = storage.Client(project=self.settings.firebase_project_id)
            
            self._initialized = True
            logger.info("Firebase services initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Firebase services", error=str(e))
            raise
    
    def _ensure_initialized(self):
        """Ensure Firebase is initialized"""
        if not self._initialized:
            raise RuntimeError("Firebase service not initialized. Call initialize() first.")
    
    # Training Jobs
    async def create_training_job(self, training_job: TrainingJob) -> str:
        """Create a new training job in Firestore"""
        self._ensure_initialized()
        
        try:
            doc_ref = self.db.collection(self.settings.firestore_collection_training_jobs).document()
            training_job.id = doc_ref.id
            
            job_data = training_job.dict()
            # Convert datetime objects to Firestore timestamp
            job_data['created_at'] = training_job.created_at
            if training_job.started_at:
                job_data['started_at'] = training_job.started_at
            if training_job.completed_at:
                job_data['completed_at'] = training_job.completed_at
            
            await doc_ref.set(job_data)
            
            logger.info("Training job created", job_id=training_job.id, agent_id=training_job.agent_id)
            return training_job.id
            
        except Exception as e:
            logger.error("Failed to create training job", error=str(e))
            raise
    
    async def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get a training job by ID"""
        self._ensure_initialized()
        
        try:
            doc_ref = self.db.collection(self.settings.firestore_collection_training_jobs).document(job_id)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return None
            
            job_data = doc.to_dict()
            job_data['id'] = doc.id
            
            return TrainingJob(**job_data)
            
        except Exception as e:
            logger.error("Failed to get training job", job_id=job_id, error=str(e))
            raise
    
    async def update_training_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update a training job"""
        self._ensure_initialized()
        
        try:
            doc_ref = self.db.collection(self.settings.firestore_collection_training_jobs).document(job_id)
            
            # Add updated timestamp
            updates['updated_at'] = datetime.now(timezone.utc)
            
            await doc_ref.update(updates)
            
            logger.info("Training job updated", job_id=job_id, updates=list(updates.keys()))
            return True
            
        except Exception as e:
            logger.error("Failed to update training job", job_id=job_id, error=str(e))
            raise
    
    async def list_training_jobs(
        self, 
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[TrainingJob]:
        """List training jobs with optional filters"""
        self._ensure_initialized()
        
        try:
            query = self.db.collection(self.settings.firestore_collection_training_jobs)
            
            # Apply filters
            if agent_id:
                query = query.where('agent_id', '==', agent_id)
            if user_id:
                query = query.where('user_id', '==', user_id)
            if status:
                query = query.where('status', '==', status.value)
            
            # Order by creation time (descending)
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            query = query.limit(limit)
            
            docs = await query.get()
            
            jobs = []
            for doc in docs:
                job_data = doc.to_dict()
                job_data['id'] = doc.id
                jobs.append(TrainingJob(**job_data))
            
            logger.info("Listed training jobs", count=len(jobs), agent_id=agent_id, user_id=user_id)
            return jobs
            
        except Exception as e:
            logger.error("Failed to list training jobs", error=str(e))
            raise
    
    async def delete_training_job(self, job_id: str) -> bool:
        """Delete a training job"""
        self._ensure_initialized()
        
        try:
            doc_ref = self.db.collection(self.settings.firestore_collection_training_jobs).document(job_id)
            await doc_ref.delete()
            
            logger.info("Training job deleted", job_id=job_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete training job", job_id=job_id, error=str(e))
            raise
    
    # Training Data
    async def store_training_data(self, agent_id: str, training_pairs: List[TrainingPair]) -> str:
        """Store training data in Firestore and return collection path"""
        self._ensure_initialized()
        
        try:
            # Create a new document for this training data batch
            batch_doc_ref = self.db.collection(self.settings.firestore_collection_training_data).document()
            batch_id = batch_doc_ref.id
            
            # Store metadata about the batch
            batch_data = {
                'id': batch_id,
                'agent_id': agent_id,
                'total_pairs': len(training_pairs),
                'created_at': datetime.now(timezone.utc)
            }
            await batch_doc_ref.set(batch_data)
            
            # Store individual training pairs as subcollection
            pairs_collection = batch_doc_ref.collection('pairs')
            
            # Batch write for efficiency
            batch = self.db.batch()
            for pair in training_pairs:
                pair_doc_ref = pairs_collection.document()
                pair_data = pair.dict()
                pair_data['id'] = pair_doc_ref.id
                batch.set(pair_doc_ref, pair_data)
            
            await batch.commit()
            
            logger.info("Training data stored", batch_id=batch_id, agent_id=agent_id, pairs_count=len(training_pairs))
            return batch_id
            
        except Exception as e:
            logger.error("Failed to store training data", agent_id=agent_id, error=str(e))
            raise
    
    async def get_training_data(self, batch_id: str) -> List[TrainingPair]:
        """Get training data by batch ID"""
        self._ensure_initialized()
        
        try:
            batch_doc_ref = self.db.collection(self.settings.firestore_collection_training_data).document(batch_id)
            pairs_collection = batch_doc_ref.collection('pairs')
            
            docs = await pairs_collection.get()
            
            training_pairs = []
            for doc in docs:
                pair_data = doc.to_dict()
                training_pairs.append(TrainingPair(**pair_data))
            
            logger.info("Training data retrieved", batch_id=batch_id, pairs_count=len(training_pairs))
            return training_pairs
            
        except Exception as e:
            logger.error("Failed to get training data", batch_id=batch_id, error=str(e))
            raise
    
    # Fine-tuned Models
    async def store_fine_tuned_model(self, model: FineTunedModel) -> str:
        """Store fine-tuned model information"""
        self._initialized()
        
        try:
            doc_ref = self.db.collection(self.settings.firestore_collection_fine_tuned_models).document()
            model.id = doc_ref.id
            
            model_data = model.dict()
            model_data['created_at'] = model.created_at
            model_data['updated_at'] = model.updated_at
            model_data['training_completed_at'] = model.training_completed_at
            
            await doc_ref.set(model_data)
            
            logger.info("Fine-tuned model stored", model_id=model.id, agent_id=model.agent_id)
            return model.id
            
        except Exception as e:
            logger.error("Failed to store fine-tuned model", error=str(e))
            raise
    
    async def get_agent_models(self, agent_id: str) -> List[FineTunedModel]:
        """Get all fine-tuned models for an agent"""
        self._ensure_initialized()
        
        try:
            query = self.db.collection(self.settings.firestore_collection_fine_tuned_models)
            query = query.where('agent_id', '==', agent_id)
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            
            docs = await query.get()
            
            models = []
            for doc in docs:
                model_data = doc.to_dict()
                model_data['id'] = doc.id
                models.append(FineTunedModel(**model_data))
            
            logger.info("Agent models retrieved", agent_id=agent_id, count=len(models))
            return models
            
        except Exception as e:
            logger.error("Failed to get agent models", agent_id=agent_id, error=str(e))
            raise
    
    # File Storage
    async def upload_training_file(self, file_content: bytes, file_name: str, agent_id: str) -> str:
        """Upload training file to Cloud Storage"""
        self._ensure_initialized()
        
        try:
            bucket = self.storage_client.bucket(self.settings.gcs_bucket_training_data)
            blob_name = f"{agent_id}/{file_name}"
            blob = bucket.blob(blob_name)
            
            # Run upload in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, 
                blob.upload_from_string,
                file_content,
                'application/json'
            )
            
            # Make file publicly readable (optional, depending on security requirements)
            # blob.make_public()
            
            file_url = f"gs://{self.settings.gcs_bucket_training_data}/{blob_name}"
            
            logger.info("Training file uploaded", file_url=file_url, agent_id=agent_id)
            return file_url
            
        except Exception as e:
            logger.error("Failed to upload training file", error=str(e))
            raise
    
    async def download_training_file(self, file_url: str) -> bytes:
        """Download training file from Cloud Storage"""
        self._ensure_initialized()
        
        try:
            # Parse GCS URL
            if not file_url.startswith('gs://'):
                raise ValueError("Invalid GCS URL")
            
            path_parts = file_url[5:].split('/', 1)  # Remove 'gs://' prefix
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Run download in thread pool
            content = await asyncio.get_event_loop().run_in_executor(
                None,
                blob.download_as_bytes
            )
            
            logger.info("Training file downloaded", file_url=file_url)
            return content
            
        except Exception as e:
            logger.error("Failed to download training file", file_url=file_url, error=str(e))
            raise
    
    # Conversation Session Methods
    
    async def save_conversation_session(self, session) -> bool:
        """Save conversation session to Firestore"""
        self._ensure_initialized()
        
        try:
            # Convert session to dict
            session_data = {
                'session_id': session.session_id,
                'agent_id': session.agent_id,
                'user_id': session.user_id,
                'started_at': session.started_at,
                'status': session.status,
                'training_pairs': [
                    {
                        'query': pair.query,
                        'response': pair.response,
                        'timestamp': pair.timestamp,
                        'session_id': pair.session_id,
                        'query_metadata': pair.query_metadata or {}
                    }
                    for pair in session.training_pairs
                ],
                'auto_training_config': {
                    'agent_id': session.auto_training_config.agent_id,
                    'min_pairs_for_training': session.auto_training_config.min_pairs_for_training,
                    'auto_trigger_enabled': session.auto_training_config.auto_trigger_enabled,
                    'training_frequency': session.auto_training_config.training_frequency,
                    'model_config': session.auto_training_config.model_config.dict() if session.auto_training_config.model_config else None
                } if session.auto_training_config else None,
                'updated_at': datetime.now(timezone.utc)
            }
            
            # Save to Firestore
            doc_ref = self.db.collection('conversation_sessions').document(session.session_id)
            await doc_ref.set(session_data)
            
            logger.info("Conversation session saved", session_id=session.session_id)
            return True
            
        except Exception as e:
            logger.error("Failed to save conversation session", session_id=session.session_id, error=str(e))
            return False
    
    async def get_conversation_session(self, session_id: str):
        """Get conversation session from Firestore"""
        self._ensure_initialized()
        
        try:
            doc_ref = self.db.collection('conversation_sessions').document(session_id)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Import here to avoid circular imports
            from app.models import ConversationSession, ConversationTrainingPair, AutoTrainingConfig, TrainingJobConfig
            
            # Reconstruct training pairs
            training_pairs = []
            for pair_data in data.get('training_pairs', []):
                pair = ConversationTrainingPair(
                    query=pair_data['query'],
                    response=pair_data['response'],
                    timestamp=pair_data['timestamp'],
                    session_id=pair_data['session_id'],
                    query_metadata=pair_data.get('query_metadata')
                )
                training_pairs.append(pair)
            
            # Reconstruct auto training config
            auto_config = None
            if data.get('auto_training_config'):
                config_data = data['auto_training_config']
                model_config = None
                if config_data.get('model_config'):
                    model_config = TrainingJobConfig(**config_data['model_config'])
                
                auto_config = AutoTrainingConfig(
                    agent_id=config_data['agent_id'],
                    min_pairs_for_training=config_data['min_pairs_for_training'],
                    auto_trigger_enabled=config_data['auto_trigger_enabled'],
                    training_frequency=config_data['training_frequency'],
                    model_config=model_config
                )
            
            # Reconstruct session
            session = ConversationSession(
                session_id=data['session_id'],
                agent_id=data['agent_id'],
                user_id=data['user_id'],
                started_at=data['started_at'],
                training_pairs=training_pairs,
                auto_training_config=auto_config,
                status=data['status']
            )
            
            return session
            
        except Exception as e:
            logger.error("Failed to get conversation session", session_id=session_id, error=str(e))
            return None
    
    async def list_conversation_sessions(
        self, 
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List:
        """List conversation sessions with optional filters"""
        self._ensure_initialized()
        
        try:
            query = self.db.collection('conversation_sessions')
            
            # Apply filters
            if agent_id:
                query = query.where('agent_id', '==', agent_id)
            if user_id:
                query = query.where('user_id', '==', user_id)
            if status:
                query = query.where('status', '==', status)
            
            # Order by started_at descending and limit
            query = query.order_by('started_at', direction='DESCENDING').limit(limit)
            
            # Execute query
            docs = query.stream()
            
            sessions = []
            async for doc in docs:
                data = doc.to_dict()
                
                # Import here to avoid circular imports
                from app.models import ConversationSession, ConversationTrainingPair, AutoTrainingConfig, TrainingJobConfig
                
                # Reconstruct training pairs
                training_pairs = []
                for pair_data in data.get('training_pairs', []):
                    pair = ConversationTrainingPair(
                        query=pair_data['query'],
                        response=pair_data['response'],
                        timestamp=pair_data['timestamp'],
                        session_id=pair_data['session_id'],
                        query_metadata=pair_data.get('query_metadata')
                    )
                    training_pairs.append(pair)
                
                # Reconstruct auto training config
                auto_config = None
                if data.get('auto_training_config'):
                    config_data = data['auto_training_config']
                    model_config = None
                    if config_data.get('model_config'):
                        model_config = TrainingJobConfig(**config_data['model_config'])
                    
                    auto_config = AutoTrainingConfig(
                        agent_id=config_data['agent_id'],
                        min_pairs_for_training=config_data['min_pairs_for_training'],
                        auto_trigger_enabled=config_data['auto_trigger_enabled'],
                        training_frequency=config_data['training_frequency'],
                        model_config=model_config
                    )
                
                # Reconstruct session
                session = ConversationSession(
                    session_id=data['session_id'],
                    agent_id=data['agent_id'],
                    user_id=data['user_id'],
                    started_at=data['started_at'],
                    training_pairs=training_pairs,
                    auto_training_config=auto_config,
                    status=data['status']
                )
                
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error("Failed to list conversation sessions", error=str(e))
            return []
    
    async def save_auto_training_config(self, agent_id: str, config) -> bool:
        """Save auto training configuration for an agent"""
        self._ensure_initialized()
        
        try:
            config_data = {
                'agent_id': config.agent_id,
                'min_pairs_for_training': config.min_pairs_for_training,
                'auto_trigger_enabled': config.auto_trigger_enabled,
                'training_frequency': config.training_frequency,
                'model_config': config.model_config.dict() if config.model_config else None,
                'updated_at': datetime.now(timezone.utc)
            }
            
            doc_ref = self.db.collection('auto_training_configs').document(agent_id)
            await doc_ref.set(config_data)
            
            logger.info("Auto training config saved", agent_id=agent_id)
            return True
            
        except Exception as e:
            logger.error("Failed to save auto training config", agent_id=agent_id, error=str(e))
            return False