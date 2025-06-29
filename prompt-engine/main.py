"""
Prompt Engineer Service Server

This module provides the FastAPI server for the Prompt Engineer service
that can be deployed on Google Cloud Run.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import metrics functionality
from alchemist_shared.middleware import (
    setup_metrics_middleware,
    start_background_metrics_collection,
    stop_background_metrics_collection
)

# Import alchemist-shared components
from alchemist_shared.events import init_story_event_publisher, get_story_event_publisher
from alchemist_shared.config.environment import get_project_id
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.services import init_ea3_orchestrator, get_ea3_orchestrator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the routes
from routes import router

# Initialize OpenAI service first
from services.openai_init import initialize_openai
initialize_openai()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Prompt Engine service...")
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    
    # Get project ID for cloud services
    project_id = get_project_id()
    logger.info(f"Using project ID: {project_id}")
    
    # Start metrics collection
    await start_background_metrics_collection("prompt-engine")
    logger.info("Metrics collection started")
    
    # Initialize story event publisher for EA3 integration
    if project_id:
        try:
            story_publisher = init_story_event_publisher(project_id)
            logger.info("Story event publisher initialized")
        except Exception as e:
            logger.warning(f"Story event publisher initialization failed: {e}")
    
    # Initialize EA3 orchestrator for prompt optimization tracking
    if project_id:
        try:
            redis_url = os.environ.get("REDIS_URL")
            await init_ea3_orchestrator(
                project_id=project_id,
                instance_id=os.environ.get("SPANNER_INSTANCE_ID", "alchemist-graph"),
                database_id=os.environ.get("SPANNER_DATABASE_ID", "agent-stories"),
                redis_url=redis_url,
                enable_event_processing=False  # Prompt engine publishes events but doesn't process them
            )
            logger.info("EA3 orchestrator initialized for prompt optimization tracking")
        except Exception as e:
            logger.warning(f"EA3 orchestrator initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Prompt Engine service...")
    
    # Shutdown EA3 services
    try:
        ea3_orchestrator = get_ea3_orchestrator()
        if ea3_orchestrator:
            await ea3_orchestrator.shutdown()
            logger.info("EA3 orchestrator shutdown completed")
    except Exception as e:
        logger.warning(f"Error shutting down EA3 services: {e}")
    
    # Stop metrics collection
    await stop_background_metrics_collection()
    logger.info("Metrics collection stopped")


# Create the FastAPI app
app = FastAPI(
    title="Prompt Engineer Service", 
    description="Service for creating and updating system prompts for Alchemist agents",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware
setup_metrics_middleware(app, "prompt-engine")
logger.info("Metrics middleware enabled")

# Include the routes
app.include_router(router)

# Initialize centralized settings
settings = BaseSettings()
openai_config = settings.get_openai_config()
openai_key_available = bool(openai_config.get("api_key"))

# Add a health check endpoint
@app.get("/health")
async def health_check():
    from datetime import datetime
    
    # Get EA3 and story event status
    ea3_orchestrator = get_ea3_orchestrator()
    story_publisher = get_story_event_publisher()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "prompt-engine",
        "project_id": get_project_id(),
        "config_source": "alchemist-shared",
        "components": {
            "ea3_orchestrator": ea3_orchestrator is not None,
            "story_event_publisher": story_publisher is not None,
            "openai": {
                "status": "configured" if openai_key_available else "not_configured",
                "source": "alchemist-shared"
            }
        }
    }

# Add a root endpoint that redirects to docs
@app.get("/")
async def root():
    return {"message": "Welcome to the Prompt Engineer Service. See /docs for API documentation."}

# Add API logging middleware
from alchemist_shared.middleware.api_logging_middleware import setup_api_logging_middleware
setup_api_logging_middleware(app, "prompt-engine")
logger.info("API logging middleware enabled")

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8080))
    
    # Run the server
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
