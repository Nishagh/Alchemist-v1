"""
Usage tracking middleware for cross-service credit deduction
"""

import time
import asyncio
import logging
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API usage and deducting credits"""
    
    def __init__(self, app):
        super().__init__(app)
        self.tracked_paths = {
            # Billing service should NOT charge for its own operations
            # These are administrative/management functions, not usage
            "/api/v1/credits/purchase": {"credits": 0, "track": False},
            "/api/v1/credits/balance": {"credits": 0.0, "track": False},
            "/api/v1/credits/account": {"credits": 0.0, "track": False},
            "/api/v1/credits/packages": {"credits": 0.0, "track": False},
            "/api/v1/credits/orders": {"credits": 0.0, "track": False},
            "/api/v1/transactions": {"credits": 0.0, "track": False},
            "/api/v1/payments/verify": {"credits": 0.0, "track": False},
        }
        
        # Excluded paths (no tracking)
        self.excluded_paths = {
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/live",
            "/api/v1/webhooks/razorpay",
            "/api/v1/webhooks/health",
            "/api/v1/cors-test"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through usage tracking middleware"""
        
        # Skip tracking for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Skip tracking for non-authenticated requests
        if not hasattr(request.state, "user"):
            return await call_next(request)
        
        # Skip tracking for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Get tracking configuration for this path
        tracking_config = self._get_tracking_config(request.url.path, request.method)
        
        if not tracking_config or not tracking_config.get("track", False):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Track usage asynchronously (don't block response)
        if response.status_code < 400:  # Only track successful requests
            asyncio.create_task(
                self._track_usage(request, response, process_time, tracking_config)
            )
        
        return response
    
    def _get_tracking_config(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """Get tracking configuration for a path and method"""
        
        # Exact path match
        if path in self.tracked_paths:
            return self.tracked_paths[path]
        
        # Pattern matching for dynamic paths - NO tracking for billing endpoints
        if path.startswith("/api/v1/credits/orders"):
            return {"credits": 0.0, "track": False}
        
        if path.startswith("/api/v1/transactions/"):
            return {"credits": 0.0, "track": False}
        
        # Default: NO tracking for billing service internal calls
        # Only track external usage calls explicitly
        return None
    
    async def _track_usage(self, request: Request, response: Response, 
                          process_time: float, tracking_config: Dict[str, Any]):
        """Track usage and deduct credits"""
        try:
            user = getattr(request.state, "user", {})
            user_id = user.get("uid")
            
            if not user_id:
                return
            
            # Calculate credits to deduct
            base_credits = tracking_config.get("credits", 0.1)
            
            # Apply multipliers based on processing time (for expensive operations)
            if process_time > 2.0:
                base_credits *= 2  # Double charge for slow requests
            elif process_time > 5.0:
                base_credits *= 3  # Triple charge for very slow requests
            
            # Calculate content-based charges
            content_credits = await self._calculate_content_credits(request, response)
            
            total_credits = base_credits + content_credits
            
            if total_credits <= 0:
                return
            
            # Prepare usage details
            usage_details = {
                "usage_type": "api_call",
                "service": "billing-service",
                "endpoint": request.url.path,
                "method": request.method,
                "process_time": round(process_time, 4),
                "status_code": response.status_code,
                "api_calls": 1,
                "session_id": request.headers.get("X-Session-ID"),
                "request_id": getattr(request.state, "correlation_id", None),
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add content-specific details
            if content_credits > 0:
                usage_details.update({
                    "content_based_charge": content_credits,
                    "base_charge": base_credits
                })
            
            # Deduct credits (call the credits service)
            await self._deduct_credits(user_id, total_credits, usage_details)
            
            logger.info(f"Usage tracked: {total_credits} credits deducted for user {user_id}")
            
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Error tracking usage: {e}")
    
    async def _calculate_content_credits(self, request: Request, response: Response) -> float:
        """Calculate credits based on content size"""
        try:
            content_credits = 0.0
            
            # Charge based on response size for large responses
            response_size = response.headers.get("content-length")
            if response_size:
                size_bytes = int(response_size)
                # Charge extra for responses larger than 100KB
                if size_bytes > 100 * 1024:
                    content_credits += (size_bytes / (1024 * 1024)) * 0.1  # 0.1 credit per MB
            
            return content_credits
            
        except Exception as e:
            logger.error(f"Error calculating content credits: {e}")
            return 0.0
    
    async def _deduct_credits(self, user_id: str, amount: float, usage_details: Dict[str, Any]):
        """Deduct credits from user account"""
        try:
            # Get services from app state
            # Note: This is a simplified approach. In production, you might want to use
            # a message queue or direct service call for better decoupling
            
            # For now, we'll create a minimal credits service instance
            from app.services.firebase_service import FirebaseService
            from app.services.credits_service import CreditsService
            
            # This is not ideal - we should inject dependencies properly
            # But for middleware, this is a reasonable approach
            firebase_service = FirebaseService()
            if not firebase_service._initialized:
                await firebase_service.initialize()
            
            credits_service = CreditsService(firebase_service)
            
            # Deduct credits
            await credits_service.deduct_credits(user_id, amount, usage_details)
            
        except ValueError as e:
            if "Insufficient credits" in str(e):
                logger.warning(f"User {user_id} has insufficient credits for usage")
                # In production, you might want to:
                # 1. Send a notification to the user
                # 2. Throttle their requests
                # 3. Redirect to purchase page
            else:
                logger.error(f"Error deducting credits: {e}")
        except Exception as e:
            logger.error(f"Error deducting credits: {e}")


class ServiceUsageTracker:
    """Class for tracking usage from other services"""
    
    @staticmethod
    async def track_external_usage(user_id: str, service_name: str, 
                                  usage_details: Dict[str, Any]) -> bool:
        """Track usage from external services"""
        try:
            from app.services.firebase_service import FirebaseService
            from app.services.credits_service import CreditsService
            
            firebase_service = FirebaseService()
            if not firebase_service._initialized:
                await firebase_service.initialize()
            
            credits_service = CreditsService(firebase_service)
            
            # Extract credit amount from usage details
            credit_amount = usage_details.get("credits", 0.1)
            
            # Enhance usage details
            enhanced_details = {
                **usage_details,
                "service": service_name,
                "usage_type": usage_details.get("usage_type", "external_api_call"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Deduct credits
            await credits_service.deduct_credits(user_id, credit_amount, enhanced_details)
            
            logger.info(f"External usage tracked: {credit_amount} credits for {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking external usage: {e}")
            return False


# Utility functions for other services to use

async def track_agent_usage(user_id: str, agent_id: str, characters: int, 
                           api_calls: int = 1, session_id: Optional[str] = None) -> bool:
    """Track usage from agent services"""
    credits = characters / 1000  # 1000 characters = 1 credit
    
    usage_details = {
        "credits": credits,
        "usage_type": "agent_processing",
        "agent_id": agent_id,
        "characters": characters,
        "api_calls": api_calls,
        "session_id": session_id
    }
    
    return await ServiceUsageTracker.track_external_usage(
        user_id, "agent-engine", usage_details
    )


async def track_knowledge_usage(user_id: str, documents_processed: int, 
                               storage_mb: float, session_id: Optional[str] = None) -> bool:
    """Track usage from knowledge base services"""
    credits = (documents_processed * 0.1) + (storage_mb * 0.01)  # Pricing example
    
    usage_details = {
        "credits": credits,
        "usage_type": "knowledge_processing",
        "documents_processed": documents_processed,
        "storage_mb": storage_mb,
        "session_id": session_id
    }
    
    return await ServiceUsageTracker.track_external_usage(
        user_id, "knowledge-vault", usage_details
    )


async def track_deployment_usage(user_id: str, deployment_minutes: int, 
                                resource_units: float, session_id: Optional[str] = None) -> bool:
    """Track usage from deployment services"""
    credits = (deployment_minutes * 0.01) + (resource_units * 0.05)  # Pricing example
    
    usage_details = {
        "credits": credits,
        "usage_type": "deployment",
        "deployment_minutes": deployment_minutes,
        "resource_units": resource_units,
        "session_id": session_id
    }
    
    return await ServiceUsageTracker.track_external_usage(
        user_id, "agent-launcher", usage_details
    )