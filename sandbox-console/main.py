#!/usr/bin/env python3
"""
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
import firebase_admin
from firebase_admin import credentials, firestore
from agent import UserAgent
from dotenv import load_dotenv
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

load_dotenv()

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Sandbox Console service")
    
    if METRICS_AVAILABLE:
        try:
            start_background_metrics_collection("sandbox-console")
            logger.info("Background metrics collection started")
        except Exception as e:
            logger.warning(f"Failed to start metrics collection: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sandbox Console service")
    
    if METRICS_AVAILABLE:
        try:
            stop_background_metrics_collection()
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

# Add metrics middleware if available
if METRICS_AVAILABLE:
    setup_metrics_middleware(app, "sandbox-console")
    logger.info("Metrics middleware enabled")

register_routes(app)

# Add a simple status endpoint at the root
@app.get("/")
async def root():
    """Root endpoint to verify the server is running"""
    return {
        "status": "success",
        "message": "Alchemist API is running on Google Cloud Run",
        "version": "1.0.0",
        "firebase_project": os.environ.get("FIREBASE_PROJECT_ID", "Not set")
    }

@app.get('/health')
async def health_check():
    try:
        # Check OpenAI API key configuration
        openai_configured = bool(os.getenv('OPENAI_API_KEY'))
        
        # Check Firebase project configuration
        firebase_configured = bool(os.getenv('FIREBASE_PROJECT_ID'))
        
        # Check if tools are properly configured
        tools_configured = os.path.exists('knowledge_base_tool.py') and os.path.exists('mcp_tool.py')
        
        response_data = {
            "service": "sandbox-console",
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "openai": {
                    "status": "healthy" if openai_configured else "degraded",
                    "configured": openai_configured
                },
                "firebase": {
                    "status": "healthy" if firebase_configured else "degraded", 
                    "configured": firebase_configured
                },
                "tools": {
                    "status": "healthy" if tools_configured else "degraded",
                    "configured": tools_configured
                }
            }
        }
        
        # Determine overall status
        if not openai_configured or not firebase_configured or not tools_configured:
            response_data["status"] = "degraded"
        
        return response_data
        
    except Exception as e:
        error_response = {
            "service": "sandbox-console",
            "status": "unhealthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }
        raise HTTPException(status_code=503, detail=error_response)

# Legacy health endpoint for backward compatibility
@app.get('/healthz')
async def legacy_health_check():
    return {
        'status': 'ok', 
        'timestamp': datetime.datetime.now().isoformat()
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
    
    logger.info(f"Starting Alchemist API server locally on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )