"""
Shared Middleware

FastAPI middleware components for Alchemist services.
"""

from .metrics_middleware import (
    MetricsMiddleware,
    RequestTracker,
    setup_metrics_middleware,
    start_background_metrics_collection,
    stop_background_metrics_collection,
    track_endpoint_metrics
)
from .api_logging_middleware import (
    APILoggingMiddleware,
    setup_api_logging_middleware,
    shutdown_api_logging,
    get_current_request_id,
    get_current_correlation_id_from_request
)

__all__ = [
    "MetricsMiddleware",
    "RequestTracker", 
    "setup_metrics_middleware",
    "start_background_metrics_collection",
    "stop_background_metrics_collection",
    "track_endpoint_metrics",
    "APILoggingMiddleware",
    "setup_api_logging_middleware",
    "shutdown_api_logging",
    "get_current_request_id",
    "get_current_correlation_id_from_request"
]