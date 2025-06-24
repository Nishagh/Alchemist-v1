"""
Transactions API routes
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from app.models.billing_models import APIResponse
from app.services.firebase_service import FirebaseService
from app.services.credits_service import CreditsService
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def get_credits_service(request: Request) -> CreditsService:
    """Get credits service dependency"""
    firebase_service: FirebaseService = request.app.state.firebase
    return CreditsService(firebase_service)


# ========== TRANSACTION HISTORY ROUTES ==========

@router.get("")
async def get_transactions(
    request: Request,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    transaction_type: Optional[str] = Query(default=None, description="Filter by transaction type")
):
    """Get user transaction history"""
    try:
        credits_service = get_credits_service(request)
        user_id = current_user["uid"]
        
        transactions = await credits_service.get_user_transactions(
            user_id, limit, transaction_type
        )
        
        return APIResponse(
            success=True,
            data=transactions
        )
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get transactions",
                "details": str(e)
            }
        )


@router.get("/usage")
async def get_usage_summary(
    request: Request,
    current_user: dict = Depends(get_current_user),
    period: str = Query(default="current_month", description="Summary period")
):
    """Get usage summary for current period"""
    try:
        credits_service = get_credits_service(request)
        user_id = current_user["uid"]
        
        # Get usage transactions for the period
        usage_transactions = await credits_service.get_user_transactions(user_id, 100, "usage")
        
        # Calculate usage summary
        total_credits_used = 0.0
        total_characters = 0
        total_api_calls = 0
        agent_usage = {}
        
        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        
        for transaction in usage_transactions:
            # Parse timestamp
            try:
                transaction_date = datetime.fromisoformat(
                    transaction["timestamp"].replace('Z', '+00:00')
                )
            except:
                continue
            
            # Filter by period (for now, just current month)
            if transaction_date >= start_of_month:
                total_credits_used += abs(transaction["amount"])
                
                tx_data = transaction.get("transaction_data", {})
                if tx_data:
                    total_characters += tx_data.get("characters", 0)
                    total_api_calls += tx_data.get("api_calls", 0)
                    
                    agent_id = tx_data.get("agent_id")
                    if agent_id:
                        if agent_id not in agent_usage:
                            agent_usage[agent_id] = {
                                "credits": 0.0,
                                "characters": 0,
                                "api_calls": 0
                            }
                        agent_usage[agent_id]["credits"] += abs(transaction["amount"])
                        agent_usage[agent_id]["characters"] += tx_data.get("characters", 0)
                        agent_usage[agent_id]["api_calls"] += tx_data.get("api_calls", 0)
        
        summary_data = {
            "period": period,
            "summary": {
                "total_credits_used": total_credits_used,
                "total_characters": total_characters,
                "total_api_calls": total_api_calls,
                "average_cost_per_character": (
                    total_credits_used / total_characters if total_characters > 0 else 0
                )
            },
            "agent_usage": agent_usage,
            "period_start": start_of_month.isoformat(),
            "period_end": now.isoformat()
        }
        
        return APIResponse(
            success=True,
            data=summary_data
        )
        
    except Exception as e:
        logger.error(f"Error getting usage summary: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get usage summary",
                "details": str(e)
            }
        )


@router.get("/usage/trend")
async def get_usage_trend(
    request: Request,
    current_user: dict = Depends(get_current_user),
    days: int = Query(default=30, ge=7, le=90, description="Number of days for trend analysis")
):
    """Get usage trend analysis"""
    try:
        credits_service = get_credits_service(request)
        user_id = current_user["uid"]
        
        # Get recent transactions
        transactions = await credits_service.get_user_transactions(user_id, days * 5, "usage")
        
        # Calculate trend
        if len(transactions) < 2:
            trend = "stable"
        else:
            # Split into two periods
            mid_point = len(transactions) // 2
            recent_transactions = transactions[:mid_point]
            older_transactions = transactions[mid_point:mid_point*2]
            
            if not recent_transactions or not older_transactions:
                trend = "stable"
            else:
                recent_avg = sum(abs(t["amount"]) for t in recent_transactions) / len(recent_transactions)
                older_avg = sum(abs(t["amount"]) for t in older_transactions) / len(older_transactions)
                
                if older_avg == 0:
                    trend = "increasing" if recent_avg > 0 else "stable"
                else:
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100
                    
                    if change_percent > 20:
                        trend = "increasing"
                    elif change_percent < -20:
                        trend = "decreasing"
                    else:
                        trend = "stable"
        
        # Calculate daily usage for days remaining
        if transactions:
            recent_usage = transactions[:min(7, len(transactions))]
            daily_usage = sum(abs(t["amount"]) for t in recent_usage) / len(recent_usage)
        else:
            daily_usage = 0
        
        # Get current balance
        balance_info = await credits_service.get_user_balance(user_id)
        current_balance = balance_info["balance"].get("total_credits", 0)
        
        # Calculate days remaining
        days_remaining = credits_service.calculate_days_remaining(current_balance, daily_usage)
        
        trend_data = {
            "trend": trend,
            "daily_usage_avg": round(daily_usage, 2),
            "current_balance": current_balance,
            "days_remaining": days_remaining if days_remaining != float('inf') else None,
            "total_transactions_analyzed": len(transactions)
        }
        
        return APIResponse(
            success=True,
            data=trend_data
        )
        
    except Exception as e:
        logger.error(f"Error getting usage trend: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get usage trend",
                "details": str(e)
            }
        )


# ========== TRANSACTION DETAILS ROUTES ==========

@router.get("/{transaction_id}")
async def get_transaction_details(
    transaction_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get specific transaction details"""
    try:
        credits_service = get_credits_service(request)
        user_id = current_user["uid"]
        
        # Get transaction from Firebase
        firebase_service = credits_service.firebase
        doc_ref = firebase_service.db.collection(
            firebase_service.settings.CREDIT_TRANSACTIONS_COLLECTION
        ).document(transaction_id)
        
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "Transaction not found",
                    "error_code": "TRANSACTION_NOT_FOUND"
                }
            )
        
        transaction_data = doc.to_dict()
        
        # Verify transaction belongs to current user
        if transaction_data.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "error": "Transaction does not belong to current user",
                    "error_code": "UNAUTHORIZED_TRANSACTION"
                }
            )
        
        # Enhance transaction data
        enhanced_transaction = credits_service._enhance_transaction_info({
            "id": doc.id,
            **transaction_data
        })
        
        return APIResponse(
            success=True,
            data=enhanced_transaction
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction details: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get transaction details",
                "details": str(e)
            }
        )