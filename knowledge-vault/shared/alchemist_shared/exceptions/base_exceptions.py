"""
Base Exception Classes

Defines common exception types used across all Alchemist services.
Replaces generic Exception handling with specific, meaningful exceptions.
"""

from typing import Optional, Dict, Any


class AlchemistException(Exception):
    """
    Base exception class for all Alchemist-specific errors.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
        status_code: HTTP status code for API errors
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }


class ValidationError(AlchemistException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )


class AuthenticationError(AlchemistException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(AlchemistException):
    """Raised when authorization/permission check fails."""
    
    def __init__(self, message: str = "Access denied", resource: Optional[str] = None):
        details = {}
        if resource:
            details["resource"] = resource
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=403
        )


class ResourceNotFoundError(AlchemistException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            status_code=404
        )


class ExternalServiceError(AlchemistException):
    """Raised when external service calls fail."""
    
    def __init__(self, service: str, message: str, original_error: Optional[Exception] = None):
        details = {"service": service}
        if original_error:
            details["original_error"] = str(original_error)
        
        super().__init__(
            message=f"External service error from {service}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
            status_code=502
        )


class ConfigurationError(AlchemistException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=500
        )