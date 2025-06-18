"""
Alchemist Monitor Service
Main FastAPI application for monitoring all Alchemist services
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.api.monitoring import router as monitoring_router, monitor
from src.services.scheduler import MonitoringScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global scheduler
    
    # Startup
    logger.info("Starting Alchemist Monitor Service")
    
    try:
        # Initialize scheduler
        scheduler = MonitoringScheduler(monitor)
        scheduler.start()
        
        # Run initial health check
        logger.info("Running initial health check")
        await monitor.check_all_services()
        
        logger.info("Monitor service startup completed")
        
    except Exception as e:
        logger.error(f"Failed to start monitor service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Alchemist Monitor Service")
    
    try:
        if scheduler:
            scheduler.stop()
        
        await monitor.close()
        
        logger.info("Monitor service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="Alchemist Monitor Service",
    description="Centralized monitoring service for all Alchemist microservices",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(monitoring_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Alchemist Monitor Service",
        "version": "1.0.0",
        "status": "healthy",
        "description": "Centralized monitoring for Alchemist microservices"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check if scheduler is running
        scheduler_status = scheduler.get_job_status() if scheduler else {"error": "Scheduler not initialized"}
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # This will be replaced by actual timestamp
            "service": "alchemist-monitor-service",
            "version": "1.0.0",
            "scheduler": scheduler_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not initialized")
        
        status = scheduler.get_job_status()
        return {
            "success": True,
            "data": status,
            "message": "Scheduler status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@app.post("/api/scheduler/trigger/{job_id}")
async def trigger_scheduler_job(job_id: str):
    """Manually trigger a scheduler job"""
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not initialized")
        
        success = await scheduler.trigger_job(job_id)
        
        if success:
            return {
                "success": True,
                "message": f"Job '{job_id}' triggered successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found or failed to trigger")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger job: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception in {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc)
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"Starting Alchemist Monitor Service on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )