from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import files, vectors
from dotenv import load_dotenv
import os
import logging

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Knowledge Vault service...")
    
    # Start metrics collection if available
    if METRICS_AVAILABLE:
        await start_background_metrics_collection("knowledge-vault")
        logger.info("Metrics collection started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Knowledge Vault service...")
    
    # Stop metrics collection
    if METRICS_AVAILABLE:
        await stop_background_metrics_collection()
        logger.info("Metrics collection stopped")


app = FastAPI(
    title="Alchemist Knowledge Vault",
    description="Document processing and semantic search service",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add metrics middleware if available
if METRICS_AVAILABLE:
    setup_metrics_middleware(app, "knowledge-vault")
    logger.info("Metrics middleware enabled")

# Include routers
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(vectors.router, prefix="/api", tags=["vectors"])

@app.get("/")
async def root():
    return {"message": "Alchemist Knowledge Vault", "service": "knowledge-vault", "status": "running", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring services"""
    try:
        from datetime import datetime
        
        # Check environment variables
        openai_key_set = bool(os.environ.get("OPENAI_API_KEY"))
        firebase_project = os.environ.get("FIREBASE_PROJECT_ID")
        
        health_status = {
            "service": "knowledge-vault",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "components": {
                "openai": {
                    "status": "healthy" if openai_key_set else "unhealthy",
                    "configured": openai_key_set
                },
                "firebase": {
                    "status": "healthy" if firebase_project else "unhealthy",
                    "project_id": firebase_project
                }
            }
        }
        
        # Determine overall status
        if not openai_key_set or not firebase_project:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "service": "knowledge-vault",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)