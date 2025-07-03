"""
Alchemist API Server - Cloud Run Entry Point

This is the main entry point for the Alchemist API server running on Google Cloud Run.
It defines a FastAPI application with proper CORS configuration and imports routes from routes.py.
"""
import os
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from dotenv import load_dotenv
from alchemist.services.openai_init import initialize_openai
from alchemist_shared.config.environment import get_project_id
from routes import register_routes

# Import metrics functionality
from alchemist_shared.middleware import (
        setup_metrics_middleware,
        start_background_metrics_collection,
        stop_background_metrics_collection
    )

# Import eA³ (Epistemic Autonomy) services and story event system (optional)
from alchemist_shared.services import init_ea3_orchestrator
from alchemist_shared.events import init_story_event_publisher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("alchemist-api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Agent Engine service...")
    
    # Initialize OpenAI API
    try:
        initialize_openai()
        logger.info("OpenAI API initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI API: {e} - some features may be limited")
    
    # Start metrics collection if available
    await start_background_metrics_collection("agent-engine")
    logger.info("Metrics collection started")
    
    # Initialize eA³ (Epistemic Autonomy, Accountability, Alignment) services with story event system (required)
    # Get Google Cloud project ID - try multiple methods
    project_id = get_project_id()
                
    # Initialize eA³ services if available
    if init_story_event_publisher and init_ea3_orchestrator:
        try:
            # Initialize story event publisher
            story_publisher = init_story_event_publisher(project_id)
            logger.info("Story event publisher initialized")
            
            # Initialize eA³ orchestrator with Spanner Graph and event processing
            redis_url = os.environ.get("REDIS_URL")  # Optional Redis for caching
            await init_ea3_orchestrator(
                project_id=project_id,
                instance_id=os.environ.get("SPANNER_INSTANCE_ID", "alchemist-graph"),
                database_id=os.environ.get("SPANNER_DATABASE_ID", "agent-stories"),
                redis_url=redis_url,
                enable_event_processing=True  # Now safe with thread-based processing
            )
            logger.info("eA³ services initialized with story event system and Google Cloud Spanner Graph")
        except Exception as e:
            logger.warning(f"Failed to initialize eA³ services: {e} - continuing without advanced features")
    else:
        logger.info("eA³ services not available - running with basic functionality")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent Engine service...")
    
    # Shutdown eA³ services if available
    try:
        from alchemist_shared.services import get_ea3_orchestrator
        ea3_orchestrator = get_ea3_orchestrator()
        if ea3_orchestrator:
            await ea3_orchestrator.shutdown()
            logger.info("eA³ services shutdown completed")
    except Exception as e:
            logger.warning(f"Error shutting down eA³ services: {e}")
    
    # Stop metrics collection
    await stop_background_metrics_collection()
    logger.info("Metrics collection stopped")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="Alchemist Agent Engine",
    description="Core orchestration service for the Alchemist AI platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure standard CORS middleware
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
    max_age=1200,  # Cache preflight requests for 20 minutes
)

# Add metrics middleware if available
setup_metrics_middleware(app, "agent-engine")
logger.info("Metrics middleware enabled")

# Add middleware directly to ensure headers are properly set for all responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    
    # Add CORS headers to every response
    origin = request.headers.get("origin")
    if origin == "https://alchemist.olbrain.com" or origin in ["http://localhost:3000", "http://127.0.0.1:3000"]:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "1200"
    
    return response

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

# Register all routes with the FastAPI app
register_routes(app)

# Add a simple status endpoint at the root
@app.get("/")
async def root():
    """Root endpoint to verify the server is running"""
    return {
        "status": "success",
        "service": "agent-engine",
        "message": "Alchemist Agent Engine is running",
        "version": "1.0.0",
    }

# This is what Cloud Run will look for when the container starts
# No need for a separate wsgi.py file
if __name__ == "__main__":
    # This block only runs when executing the file directly
    # In production on Cloud Run, Gunicorn will import this file and use the 'app' variable
    import uvicorn
    
    # Get configuration from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting Alchemist Agent Engine locally on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
