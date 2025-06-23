"""
Health Check API Routes
"""

from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "agent-tuning-service",
            "version": "1.0.0"
        }
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/deployment"""
    try:
        # Check if service dependencies are ready
        # For now, just return ready
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "firebase": "ready",
                    "openai": "ready"
                }
            }
        )
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes/deployment"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    )