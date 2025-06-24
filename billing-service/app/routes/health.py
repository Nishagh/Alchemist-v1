"""
Health check endpoints
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.services.firebase_service import FirebaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint
    Returns service status and basic information
    """
    try:
        # Check Firebase connection
        firebase_service: FirebaseService = request.app.state.firebase
        firebase_status = "healthy" if firebase_service._initialized else "unhealthy"
        
        return {
            "status": "healthy",
            "service": "Alchemist Billing Service",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": "production" if not settings.DEBUG else "development",
            "dependencies": {
                "firebase": firebase_status,
                "firestore": firebase_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/health/ready")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    Readiness check endpoint
    Checks if service is ready to accept requests
    """
    try:
        # Check Firebase connection
        firebase_service: FirebaseService = request.app.state.firebase
        
        if not firebase_service._initialized:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "message": "Firebase not initialized",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Try to perform a simple Firestore operation
        try:
            # Simple test query to verify Firestore connectivity
            collections = firebase_service.db.collections()
            list(collections)  # Force execution
        except Exception as e:
            logger.error(f"Firestore connectivity check failed: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "message": "Firestore not accessible",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        return {
            "status": "ready",
            "message": "Service is ready to accept requests",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint
    Simple check that the service is alive
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }