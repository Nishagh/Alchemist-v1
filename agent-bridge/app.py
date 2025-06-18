"""
Main FastAPI application for WhatsApp BSP (Business Solution Provider) service
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

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

# Import models
from models.account_models import (
    CreateAccountRequest, CreateAccountResponse,
    VerifyPhoneRequest, VerifyPhoneResponse,
    RequestVerificationRequest, RequestVerificationResponse,
    SendTestMessageRequest, SendTestMessageResponse,
    DeleteAccountRequest, DeleteAccountResponse,
    AccountHealthResponse, ErrorResponse
)
from models.webhook_models import (
    WhatsAppWebhook, WebhookVerification, SendMessageRequest, SendMessageResponse
)

# Import services
from services.firebase_service import get_firebase_service
from services.whatsapp_provider import WhatsAppProvider
from services.bsp_provider import BSPProviderError, AccountCreationError, VerificationError
from config.settings import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
bsp_providers: Dict[str, Any] = {}
firebase_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global bsp_providers, firebase_service
    
    # Startup
    logger.info("Starting WhatsApp BSP Service...")
    
    try:
        # Initialize Firebase service
        firebase_service = get_firebase_service()
        logger.info("Firebase service initialized")
        
        # Initialize BSP providers
        settings = get_settings()
        
        # Initialize WhatsApp Business API provider
        if settings.whatsapp_access_token and settings.whatsapp_app_id and settings.whatsapp_app_secret:
            whatsapp_config = {
                'access_token': settings.whatsapp_access_token,
                'app_id': settings.whatsapp_app_id,
                'app_secret': settings.whatsapp_app_secret,
                'api_version': settings.whatsapp_api_version
            }
            bsp_providers['whatsapp'] = WhatsAppProvider(whatsapp_config)
            logger.info("WhatsApp Business API provider initialized")
        
        # Start metrics collection if available
        if METRICS_AVAILABLE:
            await start_background_metrics_collection("agent-bridge")
            logger.info("Metrics collection started")
        
        logger.info("BSP Service startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize BSP service: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down WhatsApp BSP Service...")
    
    # Stop metrics collection
    if METRICS_AVAILABLE:
        await stop_background_metrics_collection()
        logger.info("Metrics collection stopped")


# Create FastAPI app
app = FastAPI(
    title="Alchemist Agent Bridge",
    description="WhatsApp Business integration service for the Alchemist platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware if available
if METRICS_AVAILABLE:
    setup_metrics_middleware(app, "agent-bridge")
    logger.info("Metrics middleware enabled")


# Dependency functions
def get_bsp_provider(provider_name: str = "whatsapp"):
    """Get BSP provider instance"""
    if provider_name not in bsp_providers:
        raise HTTPException(
            status_code=404,
            detail=f"BSP provider '{provider_name}' not available"
        )
    return bsp_providers[provider_name]


def get_firebase():
    """Get Firebase service instance"""
    global firebase_service
    if firebase_service is None:
        raise HTTPException(
            status_code=500,
            detail="Firebase service not initialized"
        )
    return firebase_service


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            details={"validation_errors": exc.errors()}
        ).dict()
    )


@app.exception_handler(BSPProviderError)
async def bsp_provider_exception_handler(request: Request, exc: BSPProviderError):
    status_code = 400
    if isinstance(exc, AccountCreationError):
        status_code = 409
    elif isinstance(exc, VerificationError):
        status_code = 422
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__.lower(),
            message=str(exc),
            details={
                "provider": exc.provider,
                "error_code": exc.error_code,
                "timestamp": exc.timestamp.isoformat()
            }
        ).dict()
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "agent-bridge",
        "message": "Alchemist Agent Bridge - WhatsApp Business Integration",
        "status": "running",
        "version": "1.0.0"
    }

# Health check endpoints
@app.get("/health")
async def health_check():
    """Service health check"""
    try:
        firebase = get_firebase()
        firebase_health = await firebase.health_check()
        
        provider_health = {}
        for name, provider in bsp_providers.items():
            provider_health[name] = await provider.health_check()
        
        return {
            "service": "agent-bridge", 
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "firebase": firebase_health,
                "providers": provider_health
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "service": "whatsapp-bsp",
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


# BSP Account Management Endpoints
@app.post("/api/bsp/create-account", response_model=CreateAccountResponse)
async def create_account(
    request: CreateAccountRequest,
    provider: Any = Depends(get_bsp_provider),
    firebase: Any = Depends(get_firebase)
):
    """Create a new managed WhatsApp Business account"""
    try:
        logger.info(f"Creating account for deployment: {request.account_id}")
        
        # Check if account already exists
        existing_account = await firebase.get_managed_account_by_deployment(request.account_id)
        if existing_account:
            raise HTTPException(
                status_code=409,
                detail="Account already exists for this deployment"
            )
        
        # Create account with BSP provider
        response = await provider.create_account(request)
        
        # Store managed account in Firebase
        account_data = {
            "deployment_id": request.account_id,
            "phone_number": response.phone_number,
            "business_name": request.business_profile.name,
            "business_industry": request.business_profile.industry,
            "business_description": request.business_profile.description,
            "webhook_url": response.webhook_url,
            "agent_webhook_url": request.agent_webhook_url,
            "bsp_account_id": response.account_id,
            "bsp_sender_id": response.sender_id,
            "status": response.status,
            "verification_required": response.verification_required,
            "verification_methods": response.verification_methods,
            "verification_attempts": 0
        }
        
        account_id = await firebase.create_managed_account(account_data)
        logger.info(f"Managed account created with ID: {account_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Account creation failed")


@app.post("/api/bsp/verify-phone", response_model=VerifyPhoneResponse)
async def verify_phone_number(
    request: VerifyPhoneRequest,
    provider: Any = Depends(get_bsp_provider),
    firebase: Any = Depends(get_firebase)
):
    """Verify phone number ownership"""
    try:
        logger.info(f"Verifying phone for account: {request.account_id}")
        
        # Get managed account
        account = await firebase.get_managed_account_by_deployment(request.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Verify with BSP provider
        response = await provider.verify_phone_number(request)
        
        # Update account status in Firebase
        await firebase.update_verification_status(
            account['id'],
            response.verified,
            {
                "verification_attempts": response.attempts,
                "last_verification_attempt": datetime.utcnow()
            }
        )
        
        logger.info(f"Phone verification result: {response.verified}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phone verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Phone verification failed")


@app.post("/api/bsp/request-verification", response_model=RequestVerificationResponse)
async def request_verification_code(
    request: RequestVerificationRequest,
    provider: Any = Depends(get_bsp_provider),
    firebase: Any = Depends(get_firebase)
):
    """Request a new verification code"""
    try:
        logger.info(f"Requesting verification code for account: {request.account_id}")
        
        # Get managed account
        account = await firebase.get_managed_account_by_deployment(request.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Request verification code from BSP provider
        response = await provider.request_verification_code(request)
        
        # Update last verification request time
        await firebase.update_managed_account(
            account['id'],
            {"last_verification_request": datetime.utcnow()}
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification code request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification code request failed")


@app.post("/api/bsp/send-test-message", response_model=SendTestMessageResponse)
async def send_test_message(
    request: SendTestMessageRequest,
    provider: Any = Depends(get_bsp_provider),
    firebase: Any = Depends(get_firebase)
):
    """Send a test WhatsApp message"""
    try:
        logger.info(f"Sending test message for account: {request.account_id}")
        
        # Get managed account
        account = await firebase.get_managed_account_by_deployment(request.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if account['status'] != 'active':
            raise HTTPException(
                status_code=400,
                detail="Account must be active to send messages"
            )
        
        # Send test message via BSP provider
        response = await provider.send_test_message(request, account['bsp_sender_id'], account['phone_number'])
        
        # Update last test message info
        await firebase.update_managed_account(
            account['id'],
            {
                "last_test_sent": datetime.utcnow(),
                "last_test_recipient": request.to
            }
        )
        
        logger.info(f"Test message sent successfully: {response.message_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test message sending failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Test message sending failed")


@app.get("/api/bsp/account-health/{deployment_id}", response_model=AccountHealthResponse)
async def get_account_health(
    deployment_id: str,
    provider: Any = Depends(get_bsp_provider),
    firebase: Any = Depends(get_firebase)
):
    """Get account health status"""
    try:
        logger.info(f"Getting health for deployment: {deployment_id}")
        
        # Get managed account
        account = await firebase.get_managed_account_by_deployment(deployment_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get health from BSP provider
        response = await provider.get_account_health(
            account['bsp_account_id'],
            account['bsp_sender_id'],
            account['phone_number']
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.delete("/api/bsp/delete-account/{deployment_id}", response_model=DeleteAccountResponse)
async def delete_account(
    deployment_id: str,
    provider: Any = Depends(get_bsp_provider),
    firebase: Any = Depends(get_firebase)
):
    """Delete/deactivate a managed account"""
    try:
        logger.info(f"Deleting account for deployment: {deployment_id}")
        
        # Get managed account
        account = await firebase.get_managed_account_by_deployment(deployment_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Delete from BSP provider
        success = await provider.delete_account(
            account['bsp_account_id'],
            account['bsp_sender_id']
        )
        
        if success:
            # Delete from Firebase
            await firebase.delete_managed_account(account['id'])
            
            return DeleteAccountResponse(
                success=True,
                account_id=deployment_id,
                message="Account deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Account deletion failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Account deletion failed")


# Webhook endpoints
@app.get("/api/webhook/whatsapp")
async def webhook_verification(request: Request):
    """WhatsApp webhook verification endpoint"""
    try:
        # Get query parameters
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        # Verify the webhook
        settings = get_settings()
        if mode == "subscribe" and token == settings.webhook_verify_token:
            logger.info("Webhook verified successfully")
            return PlainTextResponse(challenge)
        else:
            logger.warning("Webhook verification failed")
            raise HTTPException(status_code=403, detail="Verification failed")
            
    except Exception as e:
        logger.error(f"Webhook verification error: {str(e)}")
        raise HTTPException(status_code=400, detail="Webhook verification error")


@app.post("/api/webhook/whatsapp")
async def webhook_handler(
    webhook_data: WhatsAppWebhook,
    background_tasks: BackgroundTasks,
    firebase: Any = Depends(get_firebase)
):
    """WhatsApp webhook message handler"""
    try:
        logger.info("Received WhatsApp webhook")
        
        # Process webhook in background
        background_tasks.add_task(process_webhook, webhook_data, firebase)
        
        # Return success immediately
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing error")


async def process_webhook(webhook_data: WhatsAppWebhook, firebase):
    """Process webhook data in background"""
    try:
        for entry in webhook_data.entry:
            for change in entry.changes:
                if change.field == "messages":
                    # Extract messages
                    if change.value.messages:
                        for message in change.value.messages:
                            logger.info(f"Processing message: {message.id}")
                            
                            # Find associated account by phone number
                            phone_number_id = change.value.metadata.get("phone_number_id")
                            
                            # Log webhook event
                            await firebase.create_webhook_log({
                                "webhook_id": f"wh_{entry.id}_{change.field}",
                                "account_id": phone_number_id or "unknown",
                                "payload": webhook_data.dict(),
                                "processed_messages": [message.dict()],
                                "status": "processed",
                                "processing_time_ms": 100  # Placeholder
                            })
                            
                            # Here you would route the message to the appropriate AI agent
                            # This would be implemented based on your agent architecture
                            logger.info(f"Message from {message.from_} processed")
                    
    except Exception as e:
        logger.error(f"Background webhook processing failed: {str(e)}")


# Message sending endpoint
@app.post("/api/bsp/send-message", response_model=SendMessageResponse)
async def send_message(
    message_request: SendMessageRequest,
    deployment_id: str,
    provider: Any = Depends(get_bsp_provider),
    firebase: Any = Depends(get_firebase)
):
    """Send WhatsApp message"""
    try:
        # Get managed account
        account = await firebase.get_managed_account_by_deployment(deployment_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if account['status'] != 'active':
            raise HTTPException(
                status_code=400,
                detail="Account must be active to send messages"
            )
        
        # Send message via BSP provider
        response = await provider.send_message(message_request, account['bsp_sender_id'], account['phone_number'])
        
        logger.info(f"Message sent successfully: {response.message_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Message sending failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Message sending failed")


# Account listing endpoint
@app.get("/api/bsp/accounts/{deployment_id}")
async def get_managed_accounts(
    deployment_id: str,
    firebase: Any = Depends(get_firebase)
):
    """Get managed accounts for a deployment"""
    try:
        accounts = await firebase.list_managed_accounts_by_deployment(deployment_id)
        return {"accounts": accounts}
        
    except Exception as e:
        logger.error(f"Failed to get managed accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get managed accounts")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)