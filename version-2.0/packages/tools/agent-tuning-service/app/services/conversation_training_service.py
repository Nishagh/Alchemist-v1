"""
Conversation-based Training Service
Manages automated training from conversation data
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import structlog

from app.config.settings import get_settings
from app.models import (
    ConversationSession, ConversationTrainingPair, AutoTrainingConfig,
    TrainingPair, TrainingJobConfig, JobStatus, ModelProvider
)
from app.services.firebase_service import FirebaseService
from app.services.training_service import TrainingService

logger = structlog.get_logger(__name__)


class ConversationTrainingService:
    """Service for managing conversation-based automated training"""
    
    def __init__(self):
        self.settings = get_settings()
        self.firebase_service = FirebaseService()
        self.training_service = TrainingService()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the conversation training service"""
        if self._initialized:
            return
        
        try:
            await self.firebase_service.initialize()
            await self.training_service.initialize()
            
            self._initialized = True
            logger.info("Conversation training service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize conversation training service", error=str(e))
            raise
    
    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            raise RuntimeError("Conversation training service not initialized. Call initialize() first.")
    
    async def create_conversation_session(
        self, 
        agent_id: str, 
        user_id: str,
        auto_training_config: Optional[AutoTrainingConfig] = None
    ) -> ConversationSession:
        """Create a new conversation training session"""
        self._ensure_initialized()
        
        session_id = str(uuid.uuid4())
        
        # Default auto training config if not provided
        if not auto_training_config:
            auto_training_config = AutoTrainingConfig(
                agent_id=agent_id,
                min_pairs_for_training=20,
                auto_trigger_enabled=True,
                training_frequency="on_threshold"
            )
        
        session = ConversationSession(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            started_at=datetime.now(timezone.utc),
            auto_training_config=auto_training_config,
            status="active"
        )
        
        # Save session to Firebase
        await self.firebase_service.save_conversation_session(session)
        
        logger.info(
            "Conversation session created",
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id
        )
        
        return session
    
    async def add_training_pair(
        self, 
        session_id: str, 
        query: str, 
        response: str,
        query_metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTrainingPair:
        """Add a training pair to a conversation session"""
        self._ensure_initialized()
        
        # Get existing session
        session = await self.firebase_service.get_conversation_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Create training pair
        training_pair = ConversationTrainingPair(
            query=query,
            response=response,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            query_metadata=query_metadata
        )
        
        # Add to session
        session.training_pairs.append(training_pair)
        
        # Check if we should trigger automatic training
        should_trigger = await self._should_trigger_training(session)
        
        if should_trigger:
            session.status = "training_triggered"
            # Trigger automatic training job
            await self._trigger_automatic_training(session)
        
        # Save updated session
        await self.firebase_service.save_conversation_session(session)
        
        logger.info(
            "Training pair added to session",
            session_id=session_id,
            pair_count=len(session.training_pairs),
            training_triggered=should_trigger
        )
        
        return training_pair
    
    async def _should_trigger_training(self, session: ConversationSession) -> bool:
        """Determine if training should be triggered for this session"""
        
        if not session.auto_training_config or not session.auto_training_config.auto_trigger_enabled:
            return False
        
        # Check if we have enough training pairs
        min_pairs = session.auto_training_config.min_pairs_for_training
        current_pairs = len(session.training_pairs)
        
        if current_pairs < min_pairs:
            return False
        
        # Check frequency-based rules
        if session.auto_training_config.training_frequency == "on_threshold":
            # Trigger when threshold is reached
            return current_pairs >= min_pairs
        
        elif session.auto_training_config.training_frequency == "daily":
            # Check if last training was more than 24 hours ago
            last_training = await self._get_last_training_time(session.agent_id)
            if not last_training:
                return True
            return datetime.now(timezone.utc) - last_training > timedelta(days=1)
        
        elif session.auto_training_config.training_frequency == "weekly":
            # Check if last training was more than 7 days ago
            last_training = await self._get_last_training_time(session.agent_id)
            if not last_training:
                return True
            return datetime.now(timezone.utc) - last_training > timedelta(days=7)
        
        return False
    
    async def _get_last_training_time(self, agent_id: str) -> Optional[datetime]:
        """Get the timestamp of the last training job for an agent"""
        try:
            jobs = await self.firebase_service.list_training_jobs(
                agent_id=agent_id,
                limit=1,
                status=JobStatus.COMPLETED
            )
            
            if jobs and len(jobs) > 0:
                return jobs[0].completed_at
            
            return None
            
        except Exception as e:
            logger.warning("Failed to get last training time", agent_id=agent_id, error=str(e))
            return None
    
    async def _trigger_automatic_training(self, session: ConversationSession) -> bool:
        """Trigger automatic training job creation"""
        try:
            # Convert conversation pairs to training pairs
            training_pairs = []
            
            for conv_pair in session.training_pairs:
                training_pair = TrainingPair(
                    id=str(uuid.uuid4()),
                    query=conv_pair.query,
                    response=conv_pair.response,
                    query_type=conv_pair.query_metadata.get("category", "general") if conv_pair.query_metadata else "general",
                    context=conv_pair.query_metadata.get("context", "") if conv_pair.query_metadata else "",
                    timestamp=conv_pair.timestamp,
                    approved=True,
                    metadata={
                        "source": "conversation_training",
                        "session_id": session.session_id,
                        "auto_generated": True
                    }
                )
                training_pairs.append(training_pair)
            
            # Create training job config
            config = session.auto_training_config.model_config or TrainingJobConfig(
                model_provider=ModelProvider.OPENAI,
                base_model="gpt-3.5-turbo-1106",
                epochs=3,
                batch_size=32,
                learning_rate=0.0001
            )
            
            # Create training job
            job = await self.training_service.create_training_job(
                agent_id=session.agent_id,
                user_id=session.user_id,
                job_name=f"Auto Training - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description=f"Automatically triggered training from conversation session {session.session_id}",
                config=config,
                training_pairs=training_pairs
            )
            
            # Start the training job immediately
            await self.training_service.start_training_job(job.id)
            
            logger.info(
                "Automatic training job created and started",
                session_id=session.session_id,
                agent_id=session.agent_id,
                job_id=job.id,
                pair_count=len(training_pairs)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to trigger automatic training",
                session_id=session.session_id,
                agent_id=session.agent_id,
                error=str(e)
            )
            return False
    
    async def get_conversation_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a conversation session by ID"""
        self._ensure_initialized()
        return await self.firebase_service.get_conversation_session(session_id)
    
    async def list_conversation_sessions(
        self, 
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[ConversationSession]:
        """List conversation sessions with optional filters"""
        self._ensure_initialized()
        return await self.firebase_service.list_conversation_sessions(
            agent_id=agent_id,
            user_id=user_id,
            status=status,
            limit=limit
        )
    
    async def update_auto_training_config(
        self, 
        agent_id: str, 
        config: AutoTrainingConfig
    ) -> bool:
        """Update auto training configuration for an agent"""
        self._ensure_initialized()
        
        try:
            # Find active session for agent
            sessions = await self.list_conversation_sessions(
                agent_id=agent_id,
                status="active",
                limit=1
            )
            
            if sessions:
                session = sessions[0]
                session.auto_training_config = config
                await self.firebase_service.save_conversation_session(session)
            
            # Also save as default config for future sessions
            await self.firebase_service.save_auto_training_config(agent_id, config)
            
            logger.info(
                "Auto training config updated",
                agent_id=agent_id,
                min_pairs=config.min_pairs_for_training,
                enabled=config.auto_trigger_enabled
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update auto training config",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    async def get_training_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get training statistics for an agent"""
        self._ensure_initialized()
        
        try:
            # Get all sessions for agent
            sessions = await self.list_conversation_sessions(agent_id=agent_id)
            
            total_pairs = sum(len(session.training_pairs) for session in sessions)
            active_sessions = len([s for s in sessions if s.status == "active"])
            completed_sessions = len([s for s in sessions if s.status == "completed"])
            training_triggered_sessions = len([s for s in sessions if s.status == "training_triggered"])
            
            # Get training jobs
            jobs = await self.firebase_service.list_training_jobs(agent_id=agent_id)
            auto_jobs = [j for j in jobs if j.description and "conversation session" in j.description]
            
            return {
                "total_conversation_pairs": total_pairs,
                "active_sessions": active_sessions,
                "completed_sessions": completed_sessions,
                "training_triggered_sessions": training_triggered_sessions,
                "total_training_jobs": len(jobs),
                "auto_training_jobs": len(auto_jobs),
                "last_training": jobs[0].completed_at if jobs else None
            }
            
        except Exception as e:
            logger.error("Failed to get training stats", agent_id=agent_id, error=str(e))
            return {}