"""
Webhooks API routes
"""

import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from app.models.billing_models import APIResponse
from app.services.firebase_service import FirebaseService
from app.services.credits_service import CreditsService
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_services(request: Request):
    """Get service dependencies"""
    firebase_service: FirebaseService = request.app.state.firebase
    credits_service = CreditsService(firebase_service)
    payment_service = PaymentService()
    return credits_service, payment_service


# ========== RAZORPAY WEBHOOK ROUTES ==========

@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature")
):
    """Handle Razorpay webhook events"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Get services
        credits_service, payment_service = get_services(request)
        
        # Verify webhook signature
        is_valid_signature = payment_service.verify_webhook_signature(body, x_razorpay_signature)
        
        if not is_valid_signature:
            logger.warning("Invalid webhook signature received")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid webhook signature",
                    "error_code": "INVALID_SIGNATURE"
                }
            )
        
        # Parse webhook payload
        try:
            webhook_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook JSON: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid JSON payload",
                    "error_code": "INVALID_JSON"
                }
            )
        
        # Process webhook event
        result = await payment_service.process_webhook_event(webhook_data)
        
        # Handle specific events
        if result.get("event_type") == "payment.captured":
            await _handle_payment_captured_webhook(result, credits_service)
        elif result.get("event_type") == "payment.failed":
            await _handle_payment_failed_webhook(result, credits_service)
        
        logger.info(f"Webhook processed successfully: {result.get('event_type')}")
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to process webhook",
                "details": str(e)
            }
        )


async def _handle_payment_captured_webhook(
    webhook_result: Dict[str, Any],
    credits_service: CreditsService
):
    """Handle payment captured webhook event"""
    try:
        purpose = webhook_result.get("purpose")
        
        if purpose == "credit_purchase":
            # Get order details
            credit_order_id = webhook_result.get("credit_order_id")
            payment_id = webhook_result.get("payment_id")
            
            if credit_order_id and payment_id:
                # Complete the credit order
                await credits_service.complete_credit_order(credit_order_id, {
                    "payment_id": payment_id,
                    "verified": True
                })
                logger.info(f"Credit order {credit_order_id} completed via webhook")
        
        elif purpose == "invoice_payment":
            # Handle invoice payment if needed
            invoice_id = webhook_result.get("invoice_id")
            logger.info(f"Invoice {invoice_id} payment completed via webhook")
        
    except Exception as e:
        logger.error(f"Error handling payment captured webhook: {e}")
        # Don't re-raise - webhook should still be marked as processed


async def _handle_payment_failed_webhook(
    webhook_result: Dict[str, Any],
    credits_service: CreditsService
):
    """Handle payment failed webhook event"""
    try:
        purpose = webhook_result.get("purpose")
        
        if purpose == "credit_purchase":
            # Update order status to failed
            credit_order_id = webhook_result.get("credit_order_id")
            
            if credit_order_id:
                # Get order and update status
                order = await credits_service.firebase.get_credit_order(credit_order_id)
                if order:
                    await credits_service.firebase.update_credit_order(credit_order_id, {
                        "status": "failed",
                        "payment.status": "failed",
                        "payment.error_description": webhook_result.get("error_description")
                    })
                    logger.info(f"Credit order {credit_order_id} marked as failed via webhook")
        
    except Exception as e:
        logger.error(f"Error handling payment failed webhook: {e}")
        # Don't re-raise - webhook should still be marked as processed


# ========== WEBHOOK HEALTH CHECK ==========

@router.get("/health")
async def webhook_health_check():
    """Health check for webhook endpoint"""
    return {
        "status": "healthy",
        "endpoint": "webhooks",
        "message": "Webhook endpoint is operational"
    }


# ========== WEBHOOK TESTING (Development Only) ==========

@router.post("/test")
async def test_webhook(
    test_data: dict,
    request: Request
):
    """Test webhook processing (development only)"""
    try:
        # This endpoint should only be available in development
        from app.config.settings import settings
        if not settings.DEBUG:
            raise HTTPException(
                status_code=404,
                detail="Endpoint not available in production"
            )
        
        credits_service, payment_service = get_services(request)
        
        # Process test webhook data
        result = await payment_service.process_webhook_event(test_data)
        
        return APIResponse(
            success=True,
            data={
                "message": "Test webhook processed",
                "result": result
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing test webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to process test webhook",
                "details": str(e)
            }
        )