"""
Metrics middleware for request tracking and monitoring
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram
import structlog

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'tuning_service_requests_total',
    'Total number of requests to tuning service',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'tuning_service_request_duration_seconds',
    'Request duration for tuning service',
    ['method', 'endpoint']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.url.path
        
        # Normalize path for metrics (remove dynamic segments)
        endpoint = self._normalize_path(path)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Log request
            logger.info(
                "Request processed",
                method=method,
                path=path,
                status=response.status_code,
                duration=round(duration, 3),
                endpoint=endpoint
            )
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            
            # Record error metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Log error
            logger.error(
                "Request failed",
                method=method,
                path=path,
                duration=round(duration, 3),
                endpoint=endpoint,
                error=str(e)
            )
            
            raise
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics by removing dynamic segments"""
        # Remove common dynamic segments
        segments = path.split('/')
        normalized = []
        
        for segment in segments:
            if not segment:
                continue
            
            # Replace UUIDs and IDs with placeholders
            if len(segment) == 36 and '-' in segment:  # UUID
                normalized.append('{uuid}')
            elif segment.isdigit():  # Numeric ID
                normalized.append('{id}')
            elif len(segment) > 20 and segment.replace('-', '').replace('_', '').isalnum():  # Long alphanumeric (likely ID)
                normalized.append('{id}')
            else:
                normalized.append(segment)
        
        return '/' + '/'.join(normalized) if normalized else '/'