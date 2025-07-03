"""
Structured Logging Configuration

Provides consistent logging setup across all Alchemist services.
Uses structured logging with correlation IDs and proper formatting.
"""

import os
import sys
import logging
import logging.config
from typing import Optional, Dict, Any
import structlog
import uuid
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class CorrelationIdProcessor:
    """Processor to add correlation ID to log records."""
    
    def __call__(self, logger, method_name, event_dict):
        correlation_id = correlation_id_var.get()
        if correlation_id:
            event_dict["correlation_id"] = correlation_id
        return event_dict


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: str = "json",
    correlation_id: Optional[str] = None
) -> None:
    """
    Set up structured logging for a service.
    
    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format type ("json" or "text")
        correlation_id: Optional correlation ID for request tracking
    """
    
    # Set correlation ID if provided
    if correlation_id:
        correlation_id_var.set(correlation_id)
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        CorrelationIdProcessor(),
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
        force=True
    )
    
    # Set up service-specific logger
    logger = structlog.get_logger(service_name)
    logger.info("Logging configured", service=service_name, log_level=log_level, log_format=log_format)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for request tracking.
    
    Args:
        correlation_id: Optional correlation ID, generates one if not provided
        
    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear correlation ID from context."""
    correlation_id_var.set(None)


class RequestLoggingMiddleware:
    """FastAPI middleware for request logging and correlation ID management."""
    
    def __init__(self, app, service_name: str):
        self.app = app
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}.requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID for request
        correlation_id = set_correlation_id()
        
        # Log request start
        self.logger.info(
            "Request started",
            method=scope["method"],
            path=scope["path"],
            correlation_id=correlation_id
        )
        
        try:
            await self.app(scope, receive, send)
            self.logger.info("Request completed", correlation_id=correlation_id)
        except Exception as e:
            self.logger.error(
                "Request failed",
                error=str(e),
                correlation_id=correlation_id,
                exc_info=True
            )
            raise
        finally:
            clear_correlation_id()