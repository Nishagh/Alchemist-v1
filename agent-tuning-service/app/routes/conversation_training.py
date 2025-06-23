"""
Conversation Training API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog

from app.models import (
    ConversationSession, ConversationTrainingPair, AutoTrainingConfig,
    GenerateQueriesRequest, GenerateQueriesResponse
)
from app.services.conversation_training_service import ConversationTrainingService
from app.services.query_generation_service import QueryGenerationService
from app.middleware.auth import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

# Request/Response models
class StartConversationRequest(BaseModel):
    """Request to start a conversation training session"""
    agent_id: str = Field(..., min_length=1)
    auto_training_config: Optional[AutoTrainingConfig] = None

class AddTrainingPairRequest(BaseModel):
    """Request to add a training pair to conversation"""
    session_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    query_metadata: Optional[dict] = None

class ConversationStatsResponse(BaseModel):
    """Response with conversation training statistics"""
    total_conversation_pairs: int
    active_sessions: int
    completed_sessions: int
    training_triggered_sessions: int
    total_training_jobs: int
    auto_training_jobs: int
    last_training: Optional[str] = None

class GenerateAndAddRequest(BaseModel):
    """Request to generate query and wait for response"""
    session_id: str = Field(..., min_length=1)
    query_request: GenerateQueriesRequest

# Dependency injection
async def get_conversation_training_service() -> ConversationTrainingService:
    service = ConversationTrainingService()
    await service.initialize()
    return service

async def get_query_generation_service() -> QueryGenerationService:
    service = QueryGenerationService()
    await service.initialize()
    return service


@router.post("/start", response_model=ConversationSession, status_code=status.HTTP_201_CREATED)
async def start_conversation_training(
    request: StartConversationRequest,
    conversation_service: ConversationTrainingService = Depends(get_conversation_training_service)
):
    """Start a new conversation training session"""
    try:
        session = await conversation_service.create_conversation_session(
            agent_id=request.agent_id,
            user_id="anonymous",
            auto_training_config=request.auto_training_config
        )
        
        logger.info(
            "Conversation training session started",
            session_id=session.session_id,
            agent_id=request.agent_id,
            user_id="anonymous"
        )
        
        return session
        
    except ValueError as e:
        logger.warning("Invalid start conversation request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to start conversation training", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start conversation training"
        )


@router.post("/generate-and-respond", response_model=dict, status_code=status.HTTP_200_OK)
async def generate_query_and_respond(
    request: GenerateAndAddRequest,
    conversation_service: ConversationTrainingService = Depends(get_conversation_training_service),
    query_service: QueryGenerationService = Depends(get_query_generation_service)
):
    """Generate a query for the conversation and return it for user response"""
    try:
        # Get session
        session = await conversation_service.get_conversation_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Generate query using query generation service
        queries = await query_service.generate_queries(
            agent_context=request.query_request.agent_context,
            query_settings=request.query_request.query_settings
        )
        
        if not queries:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query"
            )
        
        generated_query = queries[0]
        
        logger.info(
            "Query generated for conversation",
            session_id=request.session_id,
            agent_id=request.query_request.agent_context.agent_id,
            user_id="anonymous"
        )
        
        return {
            "session_id": request.session_id,
            "generated_query": {
                "query": generated_query.query,
                "category": generated_query.category,
                "difficulty": generated_query.difficulty,
                "context": generated_query.context,
                "metadata": generated_query.metadata
            },
            "instructions": "Please provide your ideal response to this query. Your response will be used for training."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate query for conversation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate query"
        )


@router.post("/add-pair", response_model=ConversationTrainingPair, status_code=status.HTTP_201_CREATED)
async def add_training_pair(
    request: AddTrainingPairRequest,
    conversation_service: ConversationTrainingService = Depends(get_conversation_training_service)
):
    """Add a training pair to the conversation session"""
    try:
        # Get session
        session = await conversation_service.get_conversation_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Add training pair
        training_pair = await conversation_service.add_training_pair(
            session_id=request.session_id,
            query=request.query,
            response=request.response,
            query_metadata=request.query_metadata
        )
        
        logger.info(
            "Training pair added to conversation",
            session_id=request.session_id,
            user_id="anonymous"
        )
        
        return training_pair
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid add training pair request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to add training pair", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add training pair"
        )


@router.get("/sessions", response_model=List[ConversationSession])
async def list_conversation_sessions(
    agent_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    conversation_service: ConversationTrainingService = Depends(get_conversation_training_service)
):
    """List conversation training sessions for the current user"""
    try:
        sessions = await conversation_service.list_conversation_sessions(
            agent_id=agent_id,
            status=status_filter,
            limit=limit
        )
        
        logger.info(
            "Conversation sessions listed",
            count=len(sessions),
            agent_id=agent_id
        )
        
        return sessions
        
    except Exception as e:
        logger.error("Failed to list conversation sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversation sessions"
        )


@router.get("/sessions/{session_id}", response_model=ConversationSession)
async def get_conversation_session(
    session_id: str,
    conversation_service: ConversationTrainingService = Depends(get_conversation_training_service)
):
    """Get a specific conversation training session"""
    try:
        session = await conversation_service.get_conversation_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info("Conversation session retrieved", session_id=session_id)
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation session"
        )


@router.put("/auto-config/{agent_id}", status_code=status.HTTP_200_OK)
async def update_auto_training_config(
    agent_id: str,
    config: AutoTrainingConfig,
    conversation_service: ConversationTrainingService = Depends(get_conversation_training_service)
):
    """Update auto training configuration for an agent"""
    try:
        success = await conversation_service.update_auto_training_config(agent_id, config)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update auto training config"
            )
        
        logger.info(
            "Auto training config updated",
            agent_id=agent_id
        )
        
        return {"message": "Auto training config updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update auto training config", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update auto training config"
        )


@router.get("/stats/{agent_id}", response_model=ConversationStatsResponse)
async def get_training_stats(
    agent_id: str,
    conversation_service: ConversationTrainingService = Depends(get_conversation_training_service)
):
    """Get training statistics for an agent"""
    try:
        stats = await conversation_service.get_training_stats(agent_id)
        
        logger.info(
            "Training stats retrieved",
            agent_id=agent_id
        )
        
        return ConversationStatsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get training stats", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get training stats"
        )