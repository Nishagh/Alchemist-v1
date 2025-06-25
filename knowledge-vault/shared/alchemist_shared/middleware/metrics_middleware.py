"""
FastAPI Metrics Middleware

Automatically collects metrics for all HTTP requests including:
- Response times
- Request counts  
- Error rates
- Status code distributions

Integrates with the centralized metrics service.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.metrics_service import get_metrics_service

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic metrics collection
    
    Tracks:
    - Request/response times
    - HTTP status codes
    - Request counts
    - Error rates
    """
    
    def __init__(self, app, service_name: str = None, exclude_paths: list = None):
        super().__init__(app)
        self.service_name = service_name
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        
        # Initialize metrics service if service name provided
        if service_name:
            from ..services.metrics_service import init_metrics_service
            self.metrics_service = init_metrics_service(service_name)
        else:
            self.metrics_service = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        
        # Skip metrics collection for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Record metrics if service is available
            if self.metrics_service:
                self.metrics_service.record_request(response_time_ms, response.status_code)
            
            # Add custom headers with metrics info
            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
            response.headers["X-Service-Name"] = self.service_name or "unknown"
            
            logger.debug(
                f"Request processed: {request.method} {request.url.path} "
                f"Status: {response.status_code} Time: {response_time_ms:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            # Calculate response time for errors
            response_time_ms = (time.time() - start_time) * 1000
            
            # Record error metrics
            if self.metrics_service:
                self.metrics_service.record_request(response_time_ms, 500)
            
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(e)} Time: {response_time_ms:.2f}ms"
            )
            
            # Re-raise the exception
            raise
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from metrics collection"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False


class RequestTracker:
    """
    Helper class for detailed request tracking
    
    Can be used in endpoints for more granular metrics collection
    """
    
    def __init__(self, request: Request, operation_name: str = None):
        self.request = request
        self.operation_name = operation_name or f"{request.method} {request.url.path}"
        self.start_time = time.time()
        self.custom_metrics = {}
    
    def add_custom_metric(self, key: str, value: any):
        """Add custom metric for this request"""
        self.custom_metrics[key] = value
    
    def record_database_query(self, query_time_ms: float, query_type: str = "unknown"):
        """Record database query metrics"""
        self.add_custom_metric(f"db_query_time_{query_type}", query_time_ms)
    
    def record_external_api_call(self, api_name: str, response_time_ms: float, status_code: int):
        """Record external API call metrics"""
        self.add_custom_metric(f"api_call_{api_name}_time", response_time_ms)
        self.add_custom_metric(f"api_call_{api_name}_status", status_code)
    
    async def finish(self, status_code: int = 200):
        """Complete request tracking and record metrics"""
        total_time_ms = (time.time() - self.start_time) * 1000
        
        # Get metrics service
        metrics_service = get_metrics_service()
        
        if metrics_service:
            # Record basic request metrics
            metrics_service.record_request(total_time_ms, status_code)
            
            # If we have custom metrics, store them
            if self.custom_metrics:
                await metrics_service.collect_and_store_metrics(self.custom_metrics)


def setup_metrics_middleware(app, service_name: str, exclude_paths: list = None):
    """
    Convenience function to set up metrics middleware
    
    Usage:
        from alchemist_shared.middleware.metrics_middleware import setup_metrics_middleware
        
        app = FastAPI()
        setup_metrics_middleware(app, "my-service")
    """
    
    middleware = MetricsMiddleware(
        app=app,
        service_name=service_name,
        exclude_paths=exclude_paths
    )
    
    app.add_middleware(MetricsMiddleware, service_name=service_name, exclude_paths=exclude_paths)
    
    logger.info(f"Metrics middleware enabled for service: {service_name}")
    
    return middleware


async def start_background_metrics_collection(service_name: str):
    """
    Start background metrics collection
    
    Should be called during application startup
    """
    try:
        metrics_service = get_metrics_service(service_name)
        if metrics_service:
            await metrics_service.start_background_collection()
            logger.info(f"Background metrics collection started for {service_name}")
    except Exception as e:
        logger.error(f"Failed to start background metrics collection: {e}")


async def stop_background_metrics_collection():
    """
    Stop background metrics collection
    
    Should be called during application shutdown
    """
    try:
        metrics_service = get_metrics_service()
        if metrics_service:
            await metrics_service.stop_background_collection()
            logger.info("Background metrics collection stopped")
    except Exception as e:
        logger.error(f"Failed to stop background metrics collection: {e}")


# Decorator for endpoint-level metrics tracking
def track_endpoint_metrics(operation_name: str = None):
    """
    Decorator for tracking detailed endpoint metrics
    
    Usage:
        @app.get("/api/data")
        @track_endpoint_metrics("get_data")
        async def get_data():
            # Your endpoint logic
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request object in arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request found, just execute function normally
                return await func(*args, **kwargs)
            
            # Start tracking
            tracker = RequestTracker(request, operation_name or func.__name__)
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Record successful completion
                await tracker.finish(200)
                
                return result
                
            except Exception as e:
                # Record error
                await tracker.finish(500)
                raise
        
        return wrapper
    return decorator