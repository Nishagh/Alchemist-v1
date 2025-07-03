"""
Metrics data models
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthCheckResult(BaseModel):
    service_name: str
    status: ServiceStatus
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SystemMetrics(BaseModel):
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    disk_usage_percent: float = 0.0
    network_in_mbps: float = 0.0
    network_out_mbps: float = 0.0

class ServiceMetrics(BaseModel):
    service_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    health_status: ServiceStatus
    response_time_ms: Optional[float] = None
    uptime_seconds: Optional[int] = None
    request_count: int = 0
    error_count: int = 0
    system_metrics: Optional[SystemMetrics] = None
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)

class MonitoringSummary(BaseModel):
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    unknown_services: int
    average_response_time_ms: float
    total_requests: int
    total_errors: int
    error_rate_percent: float
    last_check_timestamp: datetime
    uptime_percentage: float

class ServiceHealthHistory(BaseModel):
    service_name: str
    checks: List[HealthCheckResult] = Field(default_factory=list)
    uptime_24h: float = 0.0
    avg_response_time_24h: float = 0.0
    total_checks_24h: int = 0
    failed_checks_24h: int = 0

class AlertRule(BaseModel):
    id: str
    name: str
    service_name: Optional[str] = None  # None means all services
    condition: str  # e.g., "response_time > 1000" or "status != healthy"
    threshold_value: float
    comparison_operator: str  # >, <, >=, <=, ==, !=
    enabled: bool = True
    notification_channels: List[str] = Field(default_factory=list)
    cooldown_minutes: int = 5

class Alert(BaseModel):
    id: str
    rule_id: str
    service_name: str
    message: str
    severity: str  # critical, warning, info
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "active"  # active, resolved, acknowledged
    metadata: Dict[str, Any] = Field(default_factory=dict)