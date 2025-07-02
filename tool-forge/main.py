#!/usr/bin/env python3
"""
Tool Forge Service - Main Entry Point
Dynamically creates and deploys MCP servers for individual agents
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from datetime import datetime

# Import alchemist-shared components
from alchemist_shared.middleware import (
    setup_metrics_middleware,
    start_background_metrics_collection,
    stop_background_metrics_collection
)
from alchemist_shared.middleware.api_logging_middleware import setup_api_logging_middleware
from alchemist_shared.events import init_story_event_publisher, get_story_event_publisher
from alchemist_shared.config.environment import get_project_id
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.services import init_ea3_orchestrator, get_ea3_orchestrator
from alchemist_shared.services.agent_lifecycle_service import init_agent_lifecycle_service, get_agent_lifecycle_service

# Import routes
from routes import router, status_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with eA³ integration"""
    # Startup
    logger.info("Starting Tool Forge service...")
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    
    # Get project ID for cloud services
    project_id = get_project_id()
    logger.info(f"Using project ID: {project_id}")
    
    # Start metrics collection
    await start_background_metrics_collection("tool-forge")
    logger.info("Metrics collection started")
    
    # Initialize story event publisher for eA³ integration
    if project_id:
        try:
            story_publisher = init_story_event_publisher(project_id)
            logger.info("Story event publisher initialized")
        except Exception as e:
            logger.warning(f"Story event publisher initialization failed: {e}")
    
    # Initialize agent lifecycle service for event tracking
    try:
        init_agent_lifecycle_service()
        logger.info("Agent lifecycle service initialized")
    except Exception as e:
        logger.warning(f"Agent lifecycle service initialization failed: {e}")
    
    # Initialize eA³ orchestrator for MCP deployment tracking
    if project_id:
        try:
            redis_url = os.environ.get("REDIS_URL")
            await init_ea3_orchestrator(
                project_id=project_id,
                instance_id=os.environ.get("SPANNER_INSTANCE_ID", "alchemist-graph"),
                database_id=os.environ.get("SPANNER_DATABASE_ID", "agent-stories"),
                redis_url=redis_url,
                enable_event_processing=False  # Tool forge publishes events but doesn't process them
            )
            logger.info("eA³ orchestrator initialized for MCP deployment tracking")
        except Exception as e:
            logger.warning(f"eA³ orchestrator initialization failed: {e}")
    
    # Initialize status manager
    try:
        logger.info("Status manager initialized for Cloud Run Jobs mode")
    except Exception as e:
        logger.warning(f"Status manager initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Tool Forge service...")
    
    # Status manager cleanup (if needed)
    try:
        logger.info("Status manager cleanup completed")
    except Exception as e:
        logger.warning(f"Error during status manager cleanup: {e}")
    
    # Shutdown eA³ services
    try:
        ea3_orchestrator = get_ea3_orchestrator()
        if ea3_orchestrator:
            await ea3_orchestrator.shutdown()
            logger.info("eA³ orchestrator shutdown completed")
    except Exception as e:
        logger.warning(f"Error shutting down eA³ services: {e}")
    
    # Stop metrics collection
    await stop_background_metrics_collection()
    logger.info("Metrics collection stopped")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Alchemist Tool Forge Service",
        description="Dynamically creates and deploys MCP servers for individual agents with identity and life journey tracking",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://alchemist.olbrain.com",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "*"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=1200,
    )
    
    # Add metrics middleware
    setup_metrics_middleware(app, "tool-forge")
    logger.info("Metrics middleware enabled")
    
    # Add API logging middleware
    setup_api_logging_middleware(app, "tool-forge")
    logger.info("API logging middleware enabled")
    
    # Include routes
    app.include_router(router)
    
    return app

# Create the FastAPI app
app = create_app()

# Initialize centralized settings
settings = BaseSettings()

# Health check endpoint with eA³ status
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run with eA³ status."""
    # Get eA³ and story event status
    ea3_orchestrator = get_ea3_orchestrator()
    story_publisher = get_story_event_publisher()
    lifecycle_service = get_agent_lifecycle_service()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "tool-forge",
        "project_id": get_project_id(),
        "config_source": "alchemist-shared",
        "components": {
            "ea3_orchestrator": ea3_orchestrator is not None,
            "story_event_publisher": story_publisher is not None,
            "lifecycle_service": lifecycle_service is not None,
            "status_manager": status_manager is not None,
            "deployment_mode": "cloud_run_jobs",
            "settings": {
                "status": "configured",
                "source": "alchemist-shared"
            }
        }
    }

# Add a root endpoint
@app.get("/")
async def root():
    """Root endpoint to verify the server is running"""
    return {
        "status": "success",
        "service": "tool-forge",
        "message": "Alchemist Tool Forge is running",
        "version": "1.0.0",
    }

# Add POST handler for root endpoint (Eventarc events)
@app.post("/")
async def handle_eventarc_events(request: Request):
    """Handle Eventarc events at root endpoint"""
    from routes import trigger_mcp_deployment
    return await trigger_mcp_deployment(request, BackgroundTasks())

# Handle OPTIONS requests explicitly
@app.options("/{path:path}")
async def options_route(request: Request, path: str):
    response = Response(
        content="",
        media_type="text/plain",
    )
    origin = request.headers.get("origin")
    if origin == "https://alchemist.olbrain.com" or origin in ["http://localhost:3000", "http://127.0.0.1:3000"]:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "1200"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Tool Forge locally on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)