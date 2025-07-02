#!/usr/bin/env python3
"""
from alchemist_shared.middleware.api_logging_middleware import setup_api_logging_middleware
Standalone Agent Web Service - A Flask web service for the standalone agent.
This service provides API endpoints for processing messages, creating conversations,
and managing agent interactions. It follows a conversation-centric architecture.
"""
import os
import logging
import sys
import datetime
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from agent import UserAgent
from dotenv import load_dotenv
from routes import register_routes
from alchemist_shared.config.base_settings import BaseSettings

# Import middleware functionality
try:
    from alchemist_shared.middleware import (
        setup_metrics_middleware,
        start_background_metrics_collection,
        stop_background_metrics_collection
    )
    from alchemist_shared.middleware.api_logging_middleware import setup_api_logging_middleware
    METRICS_AVAILABLE = True
except ImportError:
    logging.warning("Middleware not available - install alchemist-shared package")
    METRICS_AVAILABLE = False
    
    def setup_api_logging_middleware(app, service_name):
        """Fallback function when middleware is not available."""
        pass

load_dotenv()

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Sandbox Console service")
    
    if METRICS_AVAILABLE:
        try:
            await start_background_metrics_collection("alchemist-sandbox-console")
            logger.info("Background metrics collection started")
        except Exception as e:
            logger.warning(f"Failed to start metrics collection: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sandbox Console service")
    
    if METRICS_AVAILABLE:
        try:
            await stop_background_metrics_collection()
            logger.info("Background metrics collection stopped")
        except Exception as e:
            logger.warning(f"Failed to stop metrics collection: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Alchemist User Agents",
    description="API Backend for Alchemist User Agents",
    version="1.0.0",
    lifespan=lifespan
)
# Configure CORS to allow agent-studio access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local agent-studio
        "https://agent-studio-851487020021.us-central1.run.app",  # Deployed agent-studio
        "*"  # Allow all origins as fallback
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Content-Type",
        "Authorization", 
        "X-Requested-With",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since"
    ],
    expose_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Simplified CORS headers middleware for additional coverage
@app.middleware("http")
async def add_cors_headers(request, call_next):
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = Response(content="", status_code=200)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    
    response = await call_next(request)
    
    # Add CORS headers to all responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response

# Add metrics middleware if available
if METRICS_AVAILABLE:
    setup_metrics_middleware(app, "alchemist-sandbox-console")
    logger.info("Metrics middleware enabled")

register_routes(app)

# Add CORS test endpoint
@app.get("/cors-test")
async def cors_test():
    """Simple endpoint to test CORS functionality"""
    return {
        "message": "CORS test successful",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "alchemist-sandbox-console"
    }

# Add a simple status endpoint at the root
@app.get("/")
async def root():
    """Root endpoint to verify the server is running"""
    try:
        project_id = os.environ.get('PROJECT_ID', 'Not set')
        return {
            "status": "success",
            "message": "Alchemist API is running on Google Cloud Run",
            "version": "1.0.0",
            "firebase_project": project_id
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": "Alchemist API is running with issues",
            "version": "1.0.0",
            "error": str(e)
        }

@app.get('/health')
async def health_check():
    try:
        # Basic health check without complex dependencies        
        response_data = {
            "service": "alchemist-sandbox-console",
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        # Always return 200 for basic health - don't fail on configuration issues
        return response_data
        
    except Exception as e:
        # Return 200 with error info instead of 503
        return {
            "service": "alchemist-sandbox-console",
            "status": "degraded",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }

# This is what Cloud Run will look for when the container starts
# No need for a separate wsgi.py file

# API Logging Middleware
setup_api_logging_middleware(app, "sandbox-console")
if __name__ == "__main__":
    # This block only runs when executing the file directly
    # In production on Cloud Run, Gunicorn will import this file and use the 'app' variable
    import uvicorn
    
    # Get configuration from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting Alchemist API server locally on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )