"""
API Logging Models

Data models for centralized API request/response logging across all services.
All API calls are logged to a single Firestore collection for monitoring and debugging.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from google.cloud.firestore import SERVER_TIMESTAMP

from ..constants.collections import Collections


class APILogEntry(BaseModel):
    """
    Model for API request/response log entries stored in Firestore.
    
    This captures all essential information about API calls across services
    for monitoring, debugging, and analytics.
    """
    
    # Request identification
    request_id: str = Field(..., description="Unique identifier for this request")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracing")
    
    # Service information
    service_name: str = Field(..., description="Name of the service handling the request")
    service_version: Optional[str] = Field(None, description="Version of the service")
    
    # Request details
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    endpoint: str = Field(..., description="API endpoint path")
    full_url: Optional[str] = Field(None, description="Complete request URL")
    
    # Request metadata
    user_agent: Optional[str] = Field(None, description="Client user agent")
    client_ip: Optional[str] = Field(None, description="Client IP address")
    user_id: Optional[str] = Field(None, description="Authenticated user ID if available")
    
    # Request/Response timing
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the request started")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    
    # Response details
    status_code: Optional[int] = Field(None, description="HTTP response status code")
    response_size_bytes: Optional[int] = Field(None, description="Response body size in bytes")
    
    # Error information (if applicable)
    error_message: Optional[str] = Field(None, description="Error message if request failed")
    error_type: Optional[str] = Field(None, description="Type of error (validation, server, etc.)")
    stack_trace: Optional[str] = Field(None, description="Stack trace for server errors")
    
    # Request payload information (for monitoring, not storing sensitive data)
    request_size_bytes: Optional[int] = Field(None, description="Request body size in bytes")
    request_content_type: Optional[str] = Field(None, description="Content type of request")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional service-specific metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APILogFirestoreDocument(BaseModel):
    """
    Firestore document structure for API logs.
    
    This is the actual document that gets stored in Firestore,
    with server timestamp and optimized field names.
    """
    
    # Use shorter field names for Firestore efficiency
    req_id: str  # request_id
    corr_id: Optional[str] = None  # correlation_id
    svc: str  # service_name
    svc_ver: Optional[str] = None  # service_version
    
    method: str
    endpoint: str
    url: Optional[str] = None  # full_url
    
    ua: Optional[str] = None  # user_agent
    ip: Optional[str] = None  # client_ip
    uid: Optional[str] = None  # user_id
    
    ts: Any = SERVER_TIMESTAMP  # timestamp
    resp_ms: Optional[float] = None  # response_time_ms
    
    status: Optional[int] = None  # status_code
    resp_size: Optional[int] = None  # response_size_bytes
    
    err_msg: Optional[str] = None  # error_message
    err_type: Optional[str] = None  # error_type
    stack: Optional[str] = None  # stack_trace
    
    req_size: Optional[int] = None  # request_size_bytes
    req_ct: Optional[str] = None  # request_content_type
    
    meta: Dict[str, Any] = Field(default_factory=dict)  # metadata
    
    @classmethod
    def from_api_log_entry(cls, entry: APILogEntry) -> "APILogFirestoreDocument":
        """Convert APILogEntry to Firestore document format."""
        return cls(
            req_id=entry.request_id,
            corr_id=entry.correlation_id,
            svc=entry.service_name,
            svc_ver=entry.service_version,
            method=entry.method,
            endpoint=entry.endpoint,
            url=entry.full_url,
            ua=entry.user_agent,
            ip=entry.client_ip,
            uid=entry.user_id,
            resp_ms=entry.response_time_ms,
            status=entry.status_code,
            resp_size=entry.response_size_bytes,
            err_msg=entry.error_message,
            err_type=entry.error_type,
            stack=entry.stack_trace,
            req_size=entry.request_size_bytes,
            req_ct=entry.request_content_type,
            meta=entry.metadata
        )


class APILogQuery(BaseModel):
    """Model for querying API logs."""
    
    service_name: Optional[str] = None
    method: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    user_id: Optional[str] = None
    
    # Time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Response time filtering
    min_response_time_ms: Optional[float] = None
    max_response_time_ms: Optional[float] = None
    
    # Error filtering
    errors_only: bool = False
    
    # Pagination
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class APILogStats(BaseModel):
    """Statistics for API logs over a time period."""
    
    total_requests: int
    success_requests: int
    error_requests: int
    
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    
    requests_by_method: Dict[str, int]
    requests_by_status: Dict[str, int]
    requests_by_service: Dict[str, int]
    
    error_rate_percent: float
    
    time_period_start: datetime
    time_period_end: datetime


# Constants for log retention and batching
class APILogConfig:
    """Configuration constants for API logging."""
    
    COLLECTION_NAME = Collections.API_LOGS
    
    # Retention policy (in days)
    DEFAULT_RETENTION_DAYS = 30
    ERROR_LOG_RETENTION_DAYS = 90
    
    # Batch settings for performance
    BATCH_SIZE = 100
    FLUSH_INTERVAL_SECONDS = 5.0
    
    # Size limits
    MAX_ERROR_MESSAGE_LENGTH = 2000
    MAX_STACK_TRACE_LENGTH = 5000
    MAX_METADATA_SIZE_KB = 64
    
    # Rate limiting
    MAX_LOGS_PER_MINUTE = 1000
    
    # Fields to exclude from logging for security
    SENSITIVE_HEADERS = {
        'authorization',
        'cookie',
        'x-api-key',
        'x-auth-token',
        'bearer'
    }
    
    SENSITIVE_QUERY_PARAMS = {
        'password',
        'token',
        'secret',
        'key',
        'credential'
    }