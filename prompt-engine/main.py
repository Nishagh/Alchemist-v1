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

# Import story event system (required)
from alchemist_shared.events import init_story_event_publisher
from alchemist_shared.config.base_settings import get_gcp_project_id

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
    
    # Initialize story event publisher (required)
    try:
        project_id = get_gcp_project_id()
        init_story_event_publisher(project_id)
        logger.info("Story event publisher initialized")
    except Exception as e:
        logger.error(f"Failed to initialize story event publisher: {e}")
        raise
    
    # Start metrics collection
    await start_background_metrics_collection("prompt-engine")
    logger.info("Metrics collection started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Prompt Engine service...")
    
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

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

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
