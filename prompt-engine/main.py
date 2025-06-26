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
    
    # Start metrics collection if available
    if METRICS_AVAILABLE:
        await start_background_metrics_collection("prompt-engine")
        logger.info("Metrics collection started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Prompt Engine service...")
    
    # Stop metrics collection
    if METRICS_AVAILABLE:
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

# Add metrics middleware if available
if METRICS_AVAILABLE:
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
try:
    from alchemist_shared.middleware.api_logging_middleware import setup_api_logging_middleware
    setup_api_logging_middleware(app, "prompt-engine")
    logger.info("API logging middleware enabled")
except ImportError:
    logger.warning("API logging middleware not available")
    
    # Fallback to basic logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8080))
    
    # Run the server
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
