"""
Credits API routes
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from google.cloud import firestore

from app.models.billing_models import (
    CreditPurchaseRequest, CreditAccount, CreditPackage, CreditOrder,
    CreditStatus, APIResponse, SettingsUpdateRequest
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


# ========== CREDITS BALANCE ROUTES ==========

@router.get("/balance")
async def get_credit_balance(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get user credit balance"""
    try:
        credits_service, _ = get_services(request)
        user_id = current_user["uid"]
        
        balance = await credits_service.get_user_balance(user_id)
        
        return APIResponse(
            success=True,
            data=balance
        )
        
    except Exception as e:
        logger.error(f"Error getting credit balance: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get credit balance",
                "details": str(e)
            }
        )


@router.get("/account")
async def get_credits_account(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get complete user credits account"""
    try:
        credits_service, _ = get_services(request)
        user_id = current_user["uid"]
        
        account = await credits_service.get_user_credits_account(user_id)
        
        return APIResponse(
            success=True,
            data=account
        )
        
    except Exception as e:
        logger.error(f"Error getting credits account: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get credits account",
                "details": str(e)
            }
        )


@router.get("/status")
async def get_credit_status(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive credit status for user"""
    try:
        credits_service, _ = get_services(request)
        user_id = current_user["uid"]
        
        # Get account and low balance check
        account = await credits_service.get_user_credits_account(user_id)
        low_balance_check = await credits_service.check_low_balance_alert(user_id)
        
        status_data = {
            "balance": account.get("balance", {}),
            "settings": account.get("settings", {}),
            "status": account.get("status", "active"),
            "alerts": low_balance_check,
            "can_use_services": account.get("balance", {}).get("total_credits", 0) > 0
        }
        
        return APIResponse(
            success=True,
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Error getting credit status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get credit status",
                "details": str(e)
            }
        )


# ========== CREDIT PACKAGES ROUTES ==========

@router.get("/packages")
async def get_credit_packages(request: Request):
    """Get available credit packages (public endpoint)"""
    try:
        credits_service, _ = get_services(request)
        
        packages = await credits_service.get_credit_packages()
        
        return APIResponse(
            success=True,
            data=packages
        )
        
    except Exception as e:
        logger.error(f"Error getting credit packages: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get credit packages",
                "details": str(e)
            }
        )


@router.get("/packages/{package_id}")
async def get_credit_package(
    package_id: str,
    request: Request
):
    """Get specific credit package"""
    try:
        credits_service, _ = get_services(request)
        
        packages = await credits_service.get_credit_packages()
        package = next((p for p in packages if p["id"] == package_id), None)
        
        if not package:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Package not found",
                    "error_code": "PACKAGE_NOT_FOUND"
                }
            )
        
        return APIResponse(
            success=True,
            data=package
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credit package: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get credit package",
                "details": str(e)
            }
        )


# ========== CREDIT PURCHASE ROUTES ==========

@router.post("/purchase")
async def create_credit_purchase(
    purchase_request: CreditPurchaseRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create credit purchase order"""
    try:
        credits_service, payment_service = get_services(request)
        user_id = current_user["uid"]
        
        # Validate custom amount if needed
        if purchase_request.package_id == "custom_amount":
            if not purchase_request.custom_amount:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "Custom amount is required for custom packages",
                        "error_code": "MISSING_CUSTOM_AMOUNT"
                    }
                )
            
            if purchase_request.custom_amount < 1000:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": f"Minimum purchase amount is ₹1000",
                        "error_code": "AMOUNT_TOO_LOW"
                    }
                )
            
            if purchase_request.custom_amount > 50000:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": f"Maximum purchase amount is ₹50,000",
                        "error_code": "AMOUNT_TOO_HIGH"
                    }
                )
        
        # Create credit order
        order = await credits_service.create_credit_order(
            user_id,
            purchase_request.package_id,
            purchase_request.quantity,
            purchase_request.custom_amount
        )
        
        # Create payment with Razorpay
        payment = await payment_service.create_credit_purchase_order(
            user_id,
            order["id"],
            order["total_amount"],
            {
                "package_id": order["package_id"],
                "total_credits": order["total_credits"]
            }
        )
        
        # Update order with payment details
        await credits_service.firebase.update_credit_order(order["id"], {
            "payment.gateway_order_id": payment["id"],
            "payment.payment_link": f"https://rzp.io/i/{payment['id']}"
        })
        
        # Return updated order
        updated_order = {
            **order,
            "payment": {
                **order["payment"],
                "gateway_order_id": payment["id"],
                "payment_link": f"https://rzp.io/i/{payment['id']}"
            }
        }
        
        return APIResponse(
            success=True,
            data={
                "order": updated_order,
                "payment_details": payment
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        logger.error(f"Error creating credit purchase: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to create credit purchase",
                "details": str(e)
            }
        )


@router.get("/orders")
async def get_credit_orders(
    request: Request,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=10, ge=1, le=100),
    status: Optional[str] = Query(default=None)
):
    """Get user's credit purchase orders"""
    try:
        credits_service, _ = get_services(request)
        user_id = current_user["uid"]
        
        # Get orders from Firebase
        firebase_service = credits_service.firebase
        
        from app.config.settings import settings
        query = firebase_service.db.collection(settings.CREDIT_ORDERS_COLLECTION)\
                                    .where("user_id", "==", user_id)\
                                    .limit(limit)
        
        if status:
            query = query.where("status", "==", status)
        
        docs = query.stream()
        
        orders = []
        for doc in docs:
            orders.append({"id": doc.id, **doc.to_dict()})
        
        return APIResponse(
            success=True,
            data=orders
        )
        
    except Exception as e:
        logger.error(f"Error getting credit orders: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get credit orders",
                "details": str(e)
            }
        )


# ========== CREDIT MANAGEMENT ROUTES ==========

@router.post("/add")
async def add_credits(
    add_request: dict,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Add credits (admin only or promotional)"""
    try:
        credits_service, _ = get_services(request)
        
        target_user_id = add_request.get("target_user_id")
        base_amount = add_request.get("amount", 0)
        bonus_amount = add_request.get("bonus_amount", 0)
        reason = add_request.get("reason")
        
        if not target_user_id or base_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Target user ID and valid amount are required",
                    "error_code": "INVALID_REQUEST"
                }
            )
        
        # TODO: Add admin permission check here
        admin_user_id = current_user["uid"]
        
        result = await credits_service.add_credits(
            target_user_id,
            base_amount,
            bonus_amount,
            {
                "package_name": "Admin Credit Addition",
                "admin_action": True,
                "admin_user_id": admin_user_id,
                "reason": reason or "Manual credit addition"
            }
        )
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to add credits",
                "details": str(e)
            }
        )


@router.put("/settings")
async def update_credit_settings(
    settings_request: SettingsUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update credit account settings"""
    try:
        credits_service, _ = get_services(request)
        user_id = current_user["uid"]
        
        # Build settings update
        settings_update = {}
        if settings_request.low_balance_threshold is not None:
            settings_update["low_balance_threshold"] = settings_request.low_balance_threshold
        if settings_request.email_alerts is not None:
            settings_update["email_alerts"] = settings_request.email_alerts
        if settings_request.usage_alerts is not None:
            settings_update["usage_alerts"] = settings_request.usage_alerts
        
        # Update account settings
        await credits_service.firebase.db.collection(settings.USER_CREDITS_COLLECTION)\
                                          .document(user_id)\
                                          .update({
                                              "settings": settings_update,
                                              "updated_at": datetime.now(timezone.utc).isoformat()
                                          })
        
        # Get updated account
        updated_account = await credits_service.get_user_credits_account(user_id)
        
        return APIResponse(
            success=True,
            data=updated_account.get("settings", {})
        )
        
    except Exception as e:
        logger.error(f"Error updating credit settings: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to update settings",
                "details": str(e)
            }
        )


# ========== CREDIT USAGE ROUTES ==========

@router.post("/deduct")
async def deduct_credits(
    deduct_request: dict,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Deduct credits for usage (internal API)"""
    try:
        credits_service, _ = get_services(request)
        user_id = current_user["uid"]
        
        amount = deduct_request.get("amount", 0)
        usage_details = deduct_request.get("usage_details", {})
        
        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Credit amount must be positive",
                    "error_code": "INVALID_AMOUNT"
                }
            )
        
        result = await credits_service.deduct_credits(user_id, amount, usage_details)
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except ValueError as e:
        if "Insufficient credits" in str(e):
            raise HTTPException(
                status_code=402,
                detail={
                    "success": False,
                    "error": str(e),
                    "error_code": "INSUFFICIENT_CREDITS",
                    "actions": ["Purchase more credits", "Check current balance"]
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": str(e),
                    "error_code": "VALIDATION_ERROR"
                }
            )
    except Exception as e:
        logger.error(f"Error deducting credits: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to deduct credits",
                "details": str(e)
            }
        )