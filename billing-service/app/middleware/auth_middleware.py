"""
Authentication middleware for Firebase Auth integration
"""

import logging
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.firebase_service import FirebaseService

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for handling authentication"""
    
    def __init__(self, app):
        super().__init__(app)
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
            "/api/v1/credits/packages",
            "/api/v1/cors-test"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through auth middleware"""
        
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract and verify token
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "error": "Authorization header required",
                        "error_code": "MISSING_AUTH_HEADER"
                    }
                )
            
            # Extract token from "Bearer <token>" format
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "error": "Invalid authorization header format",
                        "error_code": "INVALID_AUTH_FORMAT"
                    }
                )
            
            token = auth_header.split("Bearer ", 1)[1]
            
            # Verify token with Firebase
            firebase_service: FirebaseService = request.app.state.firebase
            decoded_token = await firebase_service.verify_id_token(token)
            
            # Add user info to request state
            request.state.user = decoded_token
            
            # Continue with request
            response = await call_next(request)
            return response
            
        except ValueError as e:
            logger.warning(f"Token verification failed: {e}")
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Invalid or expired token",
                    "error_code": "INVALID_TOKEN"
                }
            )
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Authentication service error",
                    "error_code": "AUTH_SERVICE_ERROR"
                }
            )


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": "User not authenticated",
                "error_code": "NOT_AUTHENTICATED"
            }
        )
    
    return request.state.user


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency to get current user if authenticated, None otherwise"""
    return getattr(request.state, "user", None)


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency to require admin privileges"""
    # TODO: Implement admin role checking logic
    # For now, check if user has admin custom claim or is in admin list
    
    is_admin = current_user.get("admin", False) or current_user.get("uid") in [
        # Add admin user IDs here
    ]
    
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": "Admin privileges required",
                "error_code": "INSUFFICIENT_PRIVILEGES"
            }
        )
    
    return current_user


def extract_user_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """Dependency to extract user ID from authenticated user"""
    user_id = current_user.get("uid")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": "Invalid user token",
                "error_code": "INVALID_USER_TOKEN"
            }
        )
    
    return user_id


class APIKeyAuth:
    """API Key authentication for service-to-service communication"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def __call__(self, request: Request) -> bool:
        """Verify API key"""
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != self.api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": "Invalid API key",
                    "error_code": "INVALID_API_KEY"
                }
            )
        return True


def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify Firebase token and return decoded token"""
    try:
        # This would be used in routes that need explicit token verification
        # The middleware already handles this, but this can be used as a dependency
        # for routes that need the decoded token
        pass
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": "Token verification failed",
                "error_code": "TOKEN_VERIFICATION_FAILED"
            }
        )


async def get_firebase_service(request: Request) -> FirebaseService:
    """Dependency to get Firebase service instance"""
    firebase_service = getattr(request.app.state, 'firebase', None)
    if not firebase_service:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Firebase service not available",
                "error_code": "FIREBASE_SERVICE_UNAVAILABLE"
            }
        )
    return firebase_service