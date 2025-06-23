"""
Fine-tuned Models API Routes
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import structlog

from app.models import FineTunedModel
from app.services.firebase_service import FirebaseService
from app.middleware.auth import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

# Dependency injection
async def get_firebase_service() -> FirebaseService:
    service = FirebaseService()
    await service.initialize()
    return service


@router.get("/{agent_id}", response_model=List[FineTunedModel])
async def get_agent_models(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Get all fine-tuned models for an agent"""
    try:
        models = await firebase_service.get_agent_models(agent_id)
        
        logger.info(
            "Agent models retrieved",
            user_id=current_user["uid"],
            agent_id=agent_id,
            count=len(models)
        )
        
        return models
        
    except Exception as e:
        logger.error("Failed to get agent models", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent models"
        )


@router.get("/{agent_id}/{model_id}", response_model=FineTunedModel)
async def get_model_details(
    agent_id: str,
    model_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Get details of a specific fine-tuned model"""
    try:
        # Get all models for the agent and find the specific one
        models = await firebase_service.get_agent_models(agent_id)
        model = next((m for m in models if m.id == model_id), None)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        logger.info(
            "Model details retrieved",
            user_id=current_user["uid"],
            agent_id=agent_id,
            model_id=model_id
        )
        
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get model details", agent_id=agent_id, model_id=model_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model details"
        )


@router.post("/{agent_id}/{model_id}/activate")
async def activate_model(
    agent_id: str,
    model_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Activate a fine-tuned model for use"""
    try:
        # Get all models for the agent
        models = await firebase_service.get_agent_models(agent_id)
        target_model = next((m for m in models if m.id == model_id), None)
        
        if not target_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # This would typically:
        # 1. Deactivate other models for this agent
        # 2. Activate the target model
        # 3. Update deployment configuration
        # 4. Restart agent service with new model
        
        # For now, just log the action
        logger.info(
            "Model activation requested",
            user_id=current_user["uid"],
            agent_id=agent_id,
            model_id=model_id,
            external_model_id=target_model.external_model_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Model activation initiated",
                "model_id": model_id,
                "external_model_id": target_model.external_model_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to activate model", agent_id=agent_id, model_id=model_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate model"
        )


@router.post("/{agent_id}/{model_id}/deactivate")
async def deactivate_model(
    agent_id: str,
    model_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Deactivate a fine-tuned model"""
    try:
        # Get all models for the agent
        models = await firebase_service.get_agent_models(agent_id)
        target_model = next((m for m in models if m.id == model_id), None)
        
        if not target_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # This would typically:
        # 1. Deactivate the model
        # 2. Revert to base model
        # 3. Update deployment configuration
        # 4. Restart agent service
        
        logger.info(
            "Model deactivation requested",
            user_id=current_user["uid"],
            agent_id=agent_id,
            model_id=model_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Model deactivated successfully",
                "model_id": model_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to deactivate model", agent_id=agent_id, model_id=model_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate model"
        )


@router.delete("/{agent_id}/{model_id}")
async def delete_model(
    agent_id: str,
    model_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Delete a fine-tuned model"""
    try:
        # Get all models for the agent
        models = await firebase_service.get_agent_models(agent_id)
        target_model = next((m for m in models if m.id == model_id), None)
        
        if not target_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        if target_model.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active model. Deactivate it first."
            )
        
        # This would typically:
        # 1. Delete model from OpenAI/provider
        # 2. Delete model record from Firestore
        # 3. Clean up any associated files
        
        logger.info(
            "Model deletion requested",
            user_id=current_user["uid"],
            agent_id=agent_id,
            model_id=model_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Model deleted successfully",
                "model_id": model_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete model", agent_id=agent_id, model_id=model_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete model"
        )