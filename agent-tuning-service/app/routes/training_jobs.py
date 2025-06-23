"""
Training Jobs API Routes
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
import structlog

from app.models import (
    TrainingJob, CreateTrainingJobRequest, JobStatus,
    TrainingJobProgress, TrainingJobConfig
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


@router.post("/", response_model=TrainingJob, status_code=status.HTTP_201_CREATED)
async def create_training_job(
    request: CreateTrainingJobRequest,
    current_user: dict = Depends(get_current_user),
    training_service: TrainingService = Depends(get_training_service)
):
    """Create a new training job"""
    try:
        job = await training_service.create_training_job(
            agent_id=request.agent_id,
            user_id=current_user["uid"],
            job_name=request.job_name,
            description=request.description,
            config=request.config,
            training_pairs=request.training_data
        )
        
        logger.info(
            "Training job created via API",
            job_id=job.id,
            agent_id=request.agent_id,
            user_id=current_user["uid"]
        )
        
        return job
        
    except ValueError as e:
        logger.warning("Invalid training job request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create training job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create training job"
        )


@router.get("/", response_model=List[TrainingJob])
async def list_training_jobs(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status_filter: Optional[JobStatus] = Query(None, alias="status", description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """List training jobs for the current user"""
    try:
        jobs = await firebase_service.list_training_jobs(
            agent_id=agent_id,
            user_id=current_user["uid"],
            status=status_filter,
            limit=limit
        )
        
        logger.info(
            "Training jobs listed",
            user_id=current_user["uid"],
            count=len(jobs),
            agent_id=agent_id,
            status=status_filter
        )
        
        return jobs
        
    except Exception as e:
        logger.error("Failed to list training jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list training jobs"
        )


@router.get("/{job_id}", response_model=TrainingJob)
async def get_training_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Get a specific training job"""
    try:
        job = await firebase_service.get_training_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found"
            )
        
        # Check if user owns this job
        if job.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info("Training job retrieved", job_id=job_id, user_id=current_user["uid"])
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get training job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get training job"
        )


@router.get("/{job_id}/status", response_model=TrainingJobProgress)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service),
    training_service: TrainingService = Depends(get_training_service)
):
    """Get real-time job status and progress"""
    try:
        job = await firebase_service.get_training_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found"
            )
        
        # Check if user owns this job
        if job.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update progress if job is running
        if job.status in [JobStatus.RUNNING, JobStatus.QUEUED]:
            await training_service.check_job_progress(job_id)
            # Refetch updated job
            job = await firebase_service.get_training_job(job_id)
        
        progress = TrainingJobProgress(
            job_id=job.id,
            status=job.status,
            progress_percentage=job.progress_percentage,
            current_epoch=job.current_epoch,
            loss=job.loss,
            validation_loss=job.validation_loss,
            message=job.error_message if job.status == JobStatus.FAILED else None,
            updated_at=datetime.now(timezone.utc)
        )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.post("/{job_id}/start")
async def start_training_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service),
    training_service: TrainingService = Depends(get_training_service)
):
    """Start a pending training job"""
    try:
        job = await firebase_service.get_training_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found"
            )
        
        # Check if user owns this job
        if job.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if job.status != JobStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not in pending status. Current status: {job.status}"
            )
        
        await training_service.start_training_job(job_id)
        
        logger.info("Training job started via API", job_id=job_id, user_id=current_user["uid"])
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Training job started successfully"}
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to start training job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start training job"
        )


@router.post("/{job_id}/cancel")
async def cancel_training_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service),
    training_service: TrainingService = Depends(get_training_service)
):
    """Cancel a running training job"""
    try:
        job = await firebase_service.get_training_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found"
            )
        
        # Check if user owns this job
        if job.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if job.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job cannot be cancelled. Current status: {job.status}"
            )
        
        await training_service.cancel_training_job(job_id)
        
        logger.info("Training job cancelled via API", job_id=job_id, user_id=current_user["uid"])
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Training job cancelled successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel training job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel training job"
        )


@router.delete("/{job_id}")
async def delete_training_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Delete a training job (only if completed, failed, or cancelled)"""
    try:
        job = await firebase_service.get_training_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found"
            )
        
        # Check if user owns this job
        if job.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Only allow deletion of completed/failed/cancelled jobs
        if job.status in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active job. Cancel it first."
            )
        
        await firebase_service.delete_training_job(job_id)
        
        logger.info("Training job deleted via API", job_id=job_id, user_id=current_user["uid"])
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Training job deleted successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete training job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete training job"
        )