"""
Payments API routes
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.models.billing_models import (
    PaymentVerificationRequest, APIResponse
)
from app.services.firebase_service import FirebaseService
from app.services.credits_service import CreditsService
from app.services.payment_service import PaymentService
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def get_services(request: Request):
    """Get service dependencies"""
    firebase_service: FirebaseService = request.app.state.firebase
    credits_service = CreditsService(firebase_service)
    payment_service = PaymentService()
    return credits_service, payment_service


# ========== PAYMENT VERIFICATION ROUTES ==========

@router.post("/verify")
async def verify_payment(
    verification_request: PaymentVerificationRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Verify payment and complete credit purchase"""
    try:
        credits_service, payment_service = get_services(request)
        user_id = current_user["uid"]
        
        order_id = verification_request.order_id
        payment_id = verification_request.payment_id
        signature = verification_request.signature
        
        # Get the credit order
        order = await credits_service.firebase.get_credit_order(order_id)
        if not order:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Order not found",
                    "error_code": "ORDER_NOT_FOUND"
                }
            )
        
        # Verify order belongs to current user
        if order["user_id"] != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "error": "Order does not belong to current user",
                    "error_code": "UNAUTHORIZED_ORDER"
                }
            )
        
        # Verify payment signature with Razorpay
        gateway_order_id = order["payment"]["gateway_order_id"]
        is_valid_signature = payment_service.verify_payment_signature(
            gateway_order_id, payment_id, signature
        )
        
        if not is_valid_signature:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid payment signature",
                    "error_code": "INVALID_SIGNATURE"
                }
            )
        
        # Complete the credit order
        result = await credits_service.complete_credit_order(order_id, {
            "payment_id": payment_id,
            "verified": True
        })
        
        logger.info(f"Payment verified and order completed: {order_id}")
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to verify payment",
                "details": str(e)
            }
        )


# ========== PAYMENT STATUS ROUTES ==========

@router.get("/status/{payment_id}")
async def get_payment_status(
    payment_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get payment status from Razorpay"""
    try:
        _, payment_service = get_services(request)
        
        payment_details = await payment_service.get_payment_details(payment_id)
        
        if not payment_details:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Payment not found",
                    "error_code": "PAYMENT_NOT_FOUND"
                }
            )
        
        return APIResponse(
            success=True,
            data=payment_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get payment status",
                "details": str(e)
            }
        )


@router.get("/order/{order_id}")
async def get_payment_order_status(
    order_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get payment order status from Razorpay"""
    try:
        _, payment_service = get_services(request)
        
        order_details = await payment_service.get_order_details(order_id)
        
        if not order_details:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Payment order not found",
                    "error_code": "ORDER_NOT_FOUND"
                }
            )
        
        return APIResponse(
            success=True,
            data=order_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment order status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get payment order status",
                "details": str(e)
            }
        )


# ========== REFUND ROUTES ==========

@router.post("/refund")
async def create_refund(
    refund_request: dict,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create refund for a payment (admin only)"""
    try:
        _, payment_service = get_services(request)
        
        payment_id = refund_request.get("payment_id")
        amount = refund_request.get("amount")  # Optional - full refund if not specified
        reason = refund_request.get("reason")
        
        if not payment_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Payment ID is required",
                    "error_code": "MISSING_PAYMENT_ID"
                }
            )
        
        # TODO: Add admin permission check here
        
        # Create refund
        refund = await payment_service.create_refund(payment_id, amount, reason)
        
        logger.info(f"Refund created: {refund['id']} for payment {payment_id}")
        
        return APIResponse(
            success=True,
            data=refund
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating refund: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to create refund",
                "details": str(e)
            }
        )