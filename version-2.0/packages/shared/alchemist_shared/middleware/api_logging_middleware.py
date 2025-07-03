"""
API Logging Middleware for FastAPI

Middleware that automatically logs all API requests and responses to the centralized logging system.
This middleware captures request/response details, timing, errors, and other metadata.
"""

import time
import uuid
import json
import asyncio
from typing import Callable, Optional, Dict, Any, Set
from urllib.parse import urlparse, parse_qs

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from ..services.api_logging_service import get_api_logging_service, init_api_logging_service
from ..logging.logger import get_logger, set_correlation_id, get_correlation_id
from ..models.api_log_models import APILogConfig

logger = get_logger(__name__)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic API request/response logging.
    
    Features:
    - Logs all API requests and responses
    - Captures timing information
    - Records errors and stack traces
    - Handles correlation ID management
    - Respects security settings for sensitive data
    - Configurable exclusions for health checks, etc.
    """
    
    def __init__(
        self,
        app,
        service_name: str,
        service_version: Optional[str] = None,
        exclude_paths: Optional[Set[str]] = None,
        exclude_health_checks: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 1024  # Max body size to log in bytes
    ):
        super().__init__(app)
        self.service_name = service_name
        self.service_version = service_version
        self.max_body_size = max_body_size
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        
        # Default excluded paths
        default_excludes = {"/health", "/healthz", "/metrics", "/docs", "/openapi.json", "/favicon.ico"}
        if exclude_health_checks:
            self.exclude_paths = default_excludes.union(exclude_paths or set())
        else:
            self.exclude_paths = exclude_paths or set()
        
        # Initialize API logging service
        self.api_logging_service = init_api_logging_service(service_name)
        
        logger.info(f"API logging middleware initialized for {service_name}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log API call details."""
        
        # Skip logging for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Generate request ID and correlation ID
        request_id = str(uuid.uuid4())
        correlation_id = get_correlation_id() or str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # Record start time
        start_time = time.time()
        
        # Extract request details
        request_details = await self._extract_request_details(request)
        
        # Log request start
        await self._log_request_start(
            request_id=request_id,
            correlation_id=correlation_id,
            **request_details
        )
        
        # Process the request
        response = None
        error_message = None
        error_type = None
        stack_trace = None
        
        try:
            response = await call_next(request)
            
        except Exception as e:
            # Capture error details
            error_message = str(e)
            error_type = type(e).__name__
            
            # Get stack trace
            import traceback
            stack_trace = traceback.format_exc()
            
            # Re-raise the exception
            raise
        
        finally:
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract response details
            response_details = await self._extract_response_details(response) if response else {}
            
            # Log request completion
            await self._log_request_completion(
                request_id=request_id,
                response_time_ms=response_time_ms,
                error_message=error_message,
                error_type=error_type,
                stack_trace=stack_trace,
                **response_details
            )
        
        return response
    
    async def _extract_request_details(self, request: Request) -> Dict[str, Any]:
        """Extract relevant details from the request."""
        
        try:
            # Basic request info
            details = {
                "method": request.method,
                "endpoint": request.url.path,
                "full_url": str(request.url),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent"),
                "request_content_type": request.headers.get("content-type"),
            }
            
            # Extract user ID if available (check common auth headers/tokens)
            details["user_id"] = await self._extract_user_id(request)
            
            # Calculate request size
            content_length = request.headers.get("content-length")
            if content_length:
                details["request_size_bytes"] = int(content_length)
            
            # Extract metadata
            metadata = {}
            
            # Add query parameters (excluding sensitive ones)
            query_params = dict(request.query_params)
            filtered_params = self._filter_sensitive_data(query_params, APILogConfig.SENSITIVE_QUERY_PARAMS)
            if filtered_params:
                metadata["query_params"] = filtered_params
            
            # Add headers (excluding sensitive ones)
            headers = dict(request.headers)
            filtered_headers = self._filter_sensitive_data(headers, APILogConfig.SENSITIVE_HEADERS)
            if filtered_headers:
                metadata["headers"] = filtered_headers
            
            # Add request body if enabled and safe
            if self.log_request_body and details.get("request_size_bytes", 0) <= self.max_body_size:
                body = await self._safely_read_body(request)
                if body:
                    metadata["request_body"] = body
            
            details["metadata"] = metadata
            
            return details
            
        except Exception as e:
            logger.error(f"Failed to extract request details: {e}")
            return {
                "method": request.method,
                "endpoint": request.url.path,
                "metadata": {}
            }
    
    async def _extract_response_details(self, response: Response) -> Dict[str, Any]:
        """Extract relevant details from the response."""
        
        details = {}
        
        if response:
            details["status_code"] = response.status_code
            
            # Get response size from headers
            content_length = response.headers.get("content-length")
            if content_length:
                details["response_size_bytes"] = int(content_length)
            
            # Add response metadata
            metadata = {}
            
            # Add response headers (excluding sensitive ones)
            headers = dict(response.headers)
            filtered_headers = self._filter_sensitive_data(headers, APILogConfig.SENSITIVE_HEADERS)
            if filtered_headers:
                metadata["response_headers"] = filtered_headers
            
            # Add response body if enabled and safe
            if (self.log_response_body and 
                details.get("response_size_bytes", 0) <= self.max_body_size and
                not isinstance(response, StreamingResponse)):
                
                body = await self._safely_read_response_body(response)
                if body:
                    metadata["response_body"] = body
            
            if metadata:
                details["metadata"] = metadata
        
        return details
    
    async def _log_request_start(
        self,
        request_id: str,
        correlation_id: str,
        **request_details
    ):
        """Log the start of a request."""
        
        try:
            await self.api_logging_service.log_request_start(
                request_id=request_id,
                correlation_id=correlation_id,
                **request_details
            )
        except Exception as e:
            logger.error(f"Failed to log request start: {e}")
    
    async def _log_request_completion(
        self,
        request_id: str,
        response_time_ms: float,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        **response_details
    ):
        """Log the completion of a request."""
        
        try:
            # Determine status code
            status_code = response_details.get("status_code", 500 if error_message else 200)
            
            await self.api_logging_service.log_request_complete(
                request_id=request_id,
                status_code=status_code,
                response_time_ms=response_time_ms,
                error_message=error_message,
                error_type=error_type,
                stack_trace=stack_trace,
                **{k: v for k, v in response_details.items() if k != "status_code"}
            )
        except Exception as e:
            logger.error(f"Failed to log request completion: {e}")
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        
        # Check forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client info
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if available."""
        
        try:
            # Check if user is attached to request (common in auth middleware)
            if hasattr(request.state, "user") and request.state.user:
                if hasattr(request.state.user, "id"):
                    return str(request.state.user.id)
                elif hasattr(request.state.user, "uid"):
                    return str(request.state.user.uid)
                elif isinstance(request.state.user, dict):
                    return request.state.user.get("id") or request.state.user.get("uid")
            
            # Check authorization header for JWT token
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # Could decode JWT here if needed
                # For now, just indicate that user is authenticated
                return "authenticated_user"
            
            return None
            
        except Exception:
            return None
    
    async def _safely_read_body(self, request: Request) -> Optional[str]:
        """Safely read request body without consuming it."""
        
        try:
            # Read body
            body = await request.body()
            
            if not body:
                return None
            
            # Try to decode as text
            try:
                body_str = body.decode('utf-8')
                
                # If it looks like JSON, try to parse and re-serialize for clean formatting
                if body_str.strip().startswith('{') or body_str.strip().startswith('['):
                    try:
                        parsed = json.loads(body_str)
                        return json.dumps(parsed, separators=(',', ':'))
                    except json.JSONDecodeError:
                        pass
                
                return body_str[:self.max_body_size]
                
            except UnicodeDecodeError:
                return f"<binary data, {len(body)} bytes>"
                
        except Exception as e:
            logger.debug(f"Could not read request body: {e}")
            return None
    
    async def _safely_read_response_body(self, response: Response) -> Optional[str]:
        """Safely read response body if possible."""
        
        try:
            if hasattr(response, 'body') and response.body:
                body = response.body
                
                if isinstance(body, bytes):
                    try:
                        body_str = body.decode('utf-8')
                        return body_str[:self.max_body_size]
                    except UnicodeDecodeError:
                        return f"<binary data, {len(body)} bytes>"
                
                return str(body)[:self.max_body_size]
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not read response body: {e}")
            return None
    
    def _filter_sensitive_data(self, data: Dict[str, Any], sensitive_keys: Set[str]) -> Dict[str, Any]:
        """Filter out sensitive data from dictionaries."""
        
        filtered = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key contains sensitive information
            is_sensitive = any(sensitive_key in key_lower for sensitive_key in sensitive_keys)
            
            if is_sensitive:
                filtered[key] = "<redacted>"
            else:
                filtered[key] = value
        
        return filtered
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from logging."""
        
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        
        return False


def setup_api_logging_middleware(
    app,
    service_name: str,
    service_version: Optional[str] = None,
    exclude_paths: Optional[Set[str]] = None,
    exclude_health_checks: bool = True,
    log_request_body: bool = False,
    log_response_body: bool = False,
    max_body_size: int = 1024
):
    """
    Convenience function to set up API logging middleware.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service
        service_version: Version of the service
        exclude_paths: Additional paths to exclude from logging
        exclude_health_checks: Whether to exclude health check endpoints
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        max_body_size: Maximum body size to log in bytes
    
    Usage:
        from alchemist_shared.middleware.api_logging_middleware import setup_api_logging_middleware
        
        app = FastAPI()
        setup_api_logging_middleware(app, "my-service")
    """
    
    middleware = APILoggingMiddleware(
        app=app,
        service_name=service_name,
        service_version=service_version,
        exclude_paths=exclude_paths,
        exclude_health_checks=exclude_health_checks,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        max_body_size=max_body_size
    )
    
    app.add_middleware(
        APILoggingMiddleware,
        service_name=service_name,
        service_version=service_version,
        exclude_paths=exclude_paths,
        exclude_health_checks=exclude_health_checks,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        max_body_size=max_body_size
    )
    
    logger.info(f"API logging middleware enabled for service: {service_name}")
    
    return middleware


async def shutdown_api_logging():
    """Shutdown API logging and flush remaining logs."""
    
    from ..services.api_logging_service import shutdown_api_logging_service
    await shutdown_api_logging_service()


# Helper function to get request ID from current request
def get_current_request_id(request: Request) -> Optional[str]:
    """Get the current request ID from the request state."""
    return getattr(request.state, "request_id", None)


def get_current_correlation_id_from_request(request: Request) -> Optional[str]:
    """Get the current correlation ID from the request state."""
    return getattr(request.state, "correlation_id", None)