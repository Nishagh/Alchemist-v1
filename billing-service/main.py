"""
Alchemist Billing Service
FastAPI-based microservice for handling billing, credits, and payments
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from app.config.settings import settings
from app.routes import health, credits, payments, transactions, webhooks
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.usage_tracking_middleware import UsageTrackingMiddleware
from app.services.firebase_service import FirebaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Alchemist Billing Service...")
    
    # Initialize Firebase
    try:
        firebase_service = FirebaseService()
        await firebase_service.initialize()
        app.state.firebase = firebase_service
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Alchemist Billing Service...")


# Create FastAPI app
app = FastAPI(
    title="Alchemist Billing Service",
    description="Microservice for handling billing, credits, and payments",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "https://alchemist-e69bb.web.app",
    "https://alchemist-e69bb.firebaseapp.com"
]

logger.info(f"Configuring CORS with allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(UsageTrackingMiddleware)
app.add_middleware(AuthMiddleware)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if settings.DEBUG else None
        }
    )

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(credits.router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Alchemist Billing Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "credits": "/api/v1/credits",
            "payments": "/api/v1/payments",
            "transactions": "/api/v1/transactions",
            "webhooks": "/api/v1/webhooks"
        }
    }

# CORS test endpoint
@app.get("/api/v1/cors-test")
async def cors_test():
    return {
        "message": "CORS is working",
        "timestamp": datetime.now().isoformat(),
        "allowed_origins": allowed_origins
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )