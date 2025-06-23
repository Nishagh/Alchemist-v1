"""
Agent Tuning Service

Main FastAPI application for managing AI agent fine-tuning jobs.
Provides APIs for training job management, data processing, and model integration.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
from prometheus_client import make_asgi_app, Gauge, CollectorRegistry

# Import application modules
from app.config.settings import get_settings
from app.middleware.metrics import MetricsMiddleware
from app.middleware.auth import AuthMiddleware
from app.routes import training_jobs, training_data, models, health, query_generation, conversation_training
from app.services.firebase_service import FirebaseService
from app.services.training_service import TrainingService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create custom registry to avoid conflicts
metrics_registry = CollectorRegistry()

# Prometheus metrics
ACTIVE_TRAINING_JOBS = Gauge(
    'tuning_service_active_jobs',
    'Number of active training jobs',
    registry=metrics_registry
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    settings = get_settings()
    logger.info("Starting Agent Tuning Service", version="1.0.0", env=settings.environment)
    
    # Initialize services
    try:
        firebase_service = FirebaseService()
        await firebase_service.initialize()
        
        training_service = TrainingService()
        await training_service.initialize()
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down Agent Tuning Service")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Agent Tuning Service",
        description="Microservice for AI agent fine-tuning and training management",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan
    )
    
    # Security middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(AuthMiddleware)
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(training_jobs.router, prefix="/api/training/jobs", tags=["training-jobs"])
    app.include_router(training_data.router, prefix="/api/training/data", tags=["training-data"])
    app.include_router(models.router, prefix="/api/training/models", tags=["models"])
    app.include_router(query_generation.router, prefix="/api/training/queries", tags=["query-generation"])
    app.include_router(conversation_training.router, prefix="/api/training/conversation", tags=["conversation-training"])
    
    # Mount Prometheus metrics
    metrics_app = make_asgi_app(registry=metrics_registry)
    app.mount("/metrics", metrics_app)
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "agent-tuning-service",
            "version": "1.0.0",
            "status": "running",
            "environment": settings.environment
        }
    
    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=settings.environment == "development",
        log_config=None,  # Use structlog instead
        access_log=False  # Handled by middleware
    )