"""
Logging middleware for request/response logging
"""

import time
import uuid
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through logging middleware"""
        
        # Generate correlation ID for tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, correlation_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            await self._log_response(request, response, process_time, correlation_id)
            
            return response
            
        except Exception as e:
            # Calculate processing time for errors
            process_time = time.time() - start_time
            
            # Log error
            await self._log_error(request, e, process_time, correlation_id)
            
            # Re-raise the exception
            raise
    
    async def _log_request(self, request: Request, correlation_id: str):
        """Log incoming request"""
        try:
            # Get user info if available
            user_id = getattr(request.state, "user", {}).get("uid", "anonymous")
            
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Log request details
            logger.info(
                f"Request started",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", ""),
                    "content_type": request.headers.get("content-type", ""),
                    "content_length": request.headers.get("content-length", "0")
                }
            )
            
        except Exception as e:
            logger.error(f"Error logging request: {e}")
    
    async def _log_response(self, request: Request, response: Response, 
                           process_time: float, correlation_id: str):
        """Log outgoing response"""
        try:
            # Get user info if available
            user_id = getattr(request.state, "user", {}).get("uid", "anonymous")
            
            # Log response details
            logger.info(
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "user_id": user_id,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "response_size": response.headers.get("content-length", "unknown")
                }
            )
            
            # Log slow requests
            if process_time > 5.0:  # More than 5 seconds
                logger.warning(
                    f"Slow request detected",
                    extra={
                        "correlation_id": correlation_id,
                        "method": request.method,
                        "path": request.url.path,
                        "process_time": round(process_time, 4),
                        "user_id": user_id
                    }
                )
            
        except Exception as e:
            logger.error(f"Error logging response: {e}")
    
    async def _log_error(self, request: Request, error: Exception, 
                        process_time: float, correlation_id: str):
        """Log request error"""
        try:
            # Get user info if available
            user_id = getattr(request.state, "user", {}).get("uid", "anonymous")
            
            # Log error details
            logger.error(
                f"Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "user_id": user_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "process_time": round(process_time, 4)
                },
                exc_info=True
            )
            
        except Exception as e:
            logger.error(f"Error logging error: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first (load balancer/proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return getattr(request.client, "host", "unknown")


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for correlation ID handling"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add correlation ID to request"""
        
        # Check if correlation ID already exists in headers
        correlation_id = request.headers.get("X-Correlation-ID")
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Store in request state
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request"""
    return getattr(request.state, "correlation_id", "unknown")