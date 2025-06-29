from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import files, vectors
from dotenv import load_dotenv
import os
import logging
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.config.environment import get_project_id
from alchemist_shared.middleware import (
        setup_metrics_middleware,
        start_background_metrics_collection,
        stop_background_metrics_collection
    )
# Import eA³ (Epistemic Autonomy) services and story event system (required)
from alchemist_shared.services import (
    init_ea3_orchestrator, get_ea3_orchestrator, ConversationContext
)
from alchemist_shared.events import init_story_event_publisher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize centralized settings if available
settings = BaseSettings()
project_id = get_project_id()  # Use the proper environment-aware function
openai_config = settings.get_openai_config()
openai_key_set = bool(openai_config.get("api_key"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Knowledge Vault service...")
    
    # Start metrics collection if available
    await start_background_metrics_collection("knowledge-vault")
    logger.info("Metrics collection started")
        
    # Initialize story event publisher (required)
    story_publisher = init_story_event_publisher(project_id)
    logger.info("Story event publisher initialized in knowledge vault")
    
    # Initialize eA³ orchestrator with Spanner Graph (no event processing in knowledge vault)
    redis_url = os.environ.get("REDIS_URL")  # Optional Redis for caching
    await init_ea3_orchestrator(
        project_id=project_id,
        instance_id=os.environ.get("SPANNER_INSTANCE_ID", "alchemist-graph"),
        database_id=os.environ.get("SPANNER_DATABASE_ID", "agent-stories"),
        redis_url=redis_url,
        enable_event_processing=False  # Knowledge vault publishes events but doesn't process them
    )
    logger.info("eA³ services initialized in knowledge vault for agent story tracking")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Knowledge Vault service...")
    
    # Stop metrics collection
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
                
        health_status = {
            "service": "knowledge-vault",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "config_source": "centralized" if settings else "environment",
            "components": {
                "alchemist_shared": {
                    "status": "healthy",
                    "configured": True
                },
                "openai": {
                    "status": "healthy" if openai_key_set else "unhealthy",
                    "configured": openai_key_set
                },
                "firebase": {
                    "status": "healthy",
                    "project_id": project_id
                }
            }
        }        
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