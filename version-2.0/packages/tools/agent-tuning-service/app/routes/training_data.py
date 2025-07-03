"""
Training Data API Routes
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
import structlog

from app.models import (
    ProcessTrainingDataRequest, ProcessTrainingDataResponse,
    TrainingDataValidation, TrainingPair
)
from app.services.training_service import TrainingService
from app.services.firebase_service import FirebaseService
from app.middleware.auth import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

# Dependency injection
async def get_training_service() -> TrainingService:
    service = TrainingService()
    await service.initialize()
    return service

async def get_firebase_service() -> FirebaseService:
    service = FirebaseService()
    await service.initialize()
    return service


@router.post("/validate", response_model=TrainingDataValidation)
async def validate_training_data(
    training_pairs: List[TrainingPair],
    current_user: dict = Depends(get_current_user),
    training_service: TrainingService = Depends(get_training_service)
):
    """Validate training data quality and format"""
    try:
        validation = await training_service.validate_training_data(training_pairs)
        
        logger.info(
            "Training data validated",
            user_id=current_user["uid"],
            total_pairs=validation.total_pairs,
            valid_pairs=validation.valid_pairs,
            is_valid=validation.is_valid
        )
        
        return validation
        
    except Exception as e:
        logger.error("Failed to validate training data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate training data"
        )


@router.post("/process", response_model=ProcessTrainingDataResponse)
async def process_training_data(
    request: ProcessTrainingDataRequest,
    current_user: dict = Depends(get_current_user),
    training_service: TrainingService = Depends(get_training_service)
):
    """Process training data into required format"""
    try:
        response = await training_service.process_training_data(
            training_pairs=request.training_pairs,
            format=request.format,
            agent_id=request.agent_id if not request.validate_only else None
        )
        
        logger.info(
            "Training data processed",
            user_id=current_user["uid"],
            agent_id=request.agent_id,
            pairs_count=len(request.training_pairs),
            format=request.format,
            validate_only=request.validate_only
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to process training data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process training data"
        )


@router.get("/{agent_id}", response_model=List[TrainingPair])
async def get_agent_training_data(
    agent_id: str,
    batch_id: str = None,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Get training data for a specific agent"""
    try:
        if batch_id:
            # Get specific batch
            training_pairs = await firebase_service.get_training_data(batch_id)
        else:
            # For now, return empty list - would need to implement agent-level aggregation
            training_pairs = []
        
        logger.info(
            "Agent training data retrieved",
            user_id=current_user["uid"],
            agent_id=agent_id,
            batch_id=batch_id,
            pairs_count=len(training_pairs)
        )
        
        return training_pairs
        
    except Exception as e:
        logger.error("Failed to get agent training data", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get training data"
        )


@router.post("/{agent_id}/export")
async def export_training_data(
    agent_id: str,
    format: str = "json",
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Export training data for an agent in specified format"""
    try:
        # This would typically aggregate all training data for the agent
        # For now, return a placeholder response
        
        export_data = {
            "agent_id": agent_id,
            "exported_at": "2024-01-01T00:00:00Z",
            "format": format,
            "training_pairs": [],
            "metadata": {
                "total_pairs": 0,
                "export_version": "1.0"
            }
        }
        
        logger.info(
            "Training data exported",
            user_id=current_user["uid"],
            agent_id=agent_id,
            format=format
        )
        
        return export_data
        
    except Exception as e:
        logger.error("Failed to export training data", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export training data"
        )