"""
Exception Handlers

FastAPI exception handlers for consistent error responses across services.
"""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from .base_exceptions import AlchemistException

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    """
    Set up consistent exception handlers for a FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(AlchemistException)
    async def alchemist_exception_handler(request: Request, exc: AlchemistException):
        """Handle Alchemist-specific exceptions."""
        logger.error(
            f"AlchemistException: {exc.error_code} - {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "url": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.warning(
            f"HTTPException: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "url": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {}
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions."""
        logger.error(
            f"ValueError: {str(exc)}",
            extra={
                "url": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "VALUE_ERROR",
                "message": str(exc),
                "details": {}
            }
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        """Handle FileNotFoundError exceptions."""
        logger.error(
            f"FileNotFoundError: {str(exc)}",
            extra={
                "url": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "FILE_NOT_FOUND",
                "message": str(exc),
                "details": {}
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
            extra={
                "exception_type": type(exc).__name__,
                "url": str(request.url),
                "method": request.method
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )