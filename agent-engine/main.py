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
from routes import register_routes

# Import metrics functionality
try:
    from alchemist_shared.middleware import (
        setup_metrics_middleware,
        start_background_metrics_collection,
        stop_background_metrics_collection
    )
    METRICS_AVAILABLE = True
except ImportError:
    logging.warning("Metrics middleware not available - install alchemist-shared package")
    METRICS_AVAILABLE = False

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

# In Cloud Run, we use environment variables directly
logger.info(f"FIREBASE_PROJECT_ID from environment: {os.environ.get('FIREBASE_PROJECT_ID')}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Agent Engine service...")
    
    # Initialize OpenAI API
    initialize_openai()
    
    # Start metrics collection if available
    if METRICS_AVAILABLE:
        await start_background_metrics_collection("agent-engine")
        logger.info("Metrics collection started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent Engine service...")
    
    # Stop metrics collection
    if METRICS_AVAILABLE:
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
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=1200,  # Cache preflight requests for 20 minutes
)

# Add metrics middleware if available
if METRICS_AVAILABLE:
    setup_metrics_middleware(app, "agent-engine")
    logger.info("Metrics middleware enabled")

# Add middleware directly to ensure headers are properly set for all responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    
    # Add CORS headers to every response
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
        "firebase_project": os.environ.get("FIREBASE_PROJECT_ID", "Not set")
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
