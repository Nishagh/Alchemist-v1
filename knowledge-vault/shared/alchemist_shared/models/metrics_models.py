"""
Metrics Data Models

Defines data models for collecting and storing performance metrics in Firestore.
Supports time-series data for dashboard visualization.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass


class SystemMetrics(BaseModel):
    """System resource usage metrics"""
    cpu_usage_percent: float = Field(..., description="CPU usage percentage (0-100)")
    memory_usage_percent: float = Field(..., description="Memory usage percentage (0-100)")
    memory_used_bytes: int = Field(..., description="Memory used in bytes")
    memory_total_bytes: int = Field(..., description="Total memory in bytes")
    disk_usage_percent: Optional[float] = Field(None, description="Disk usage percentage")
    
    
class RequestMetrics(BaseModel):
    """HTTP request metrics"""
    total_requests: int = Field(0, description="Total number of requests")
    successful_requests: int = Field(0, description="Number of successful requests (2xx)")
    error_requests: int = Field(0, description="Number of error requests (4xx, 5xx)")
    avg_response_time_ms: float = Field(0.0, description="Average response time in milliseconds")
    min_response_time_ms: float = Field(0.0, description="Minimum response time")
    max_response_time_ms: float = Field(0.0, description="Maximum response time")


class ServiceMetrics(BaseModel):
    """Complete metrics for a service at a specific timestamp"""
    service_name: str = Field(..., description="Name of the service")
    timestamp: datetime = Field(..., description="Timestamp of the metrics")
    system_metrics: SystemMetrics = Field(..., description="System resource metrics")
    request_metrics: RequestMetrics = Field(..., description="HTTP request metrics")
    custom_metrics: Dict[str, Any] = Field(default_factory=dict, description="Service-specific metrics")
    health_status: str = Field("healthy", description="Service health status")
    version: str = Field("unknown", description="Service version")


class MetricsAggregation(BaseModel):
    """Aggregated metrics for time ranges"""
    service_name: str = Field(..., description="Name of the service")
    start_time: datetime = Field(..., description="Start of aggregation period")
    end_time: datetime = Field(..., description="End of aggregation period")
    aggregation_type: str = Field(..., description="Type of aggregation (hourly, daily)")
    
    # Aggregated values
    avg_cpu_usage: float = Field(0.0, description="Average CPU usage")
    max_cpu_usage: float = Field(0.0, description="Maximum CPU usage")
    avg_memory_usage: float = Field(0.0, description="Average memory usage")
    max_memory_usage: float = Field(0.0, description="Maximum memory usage")
    
    total_requests: int = Field(0, description="Total requests in period")
    total_errors: int = Field(0, description="Total errors in period")
    avg_response_time: float = Field(0.0, description="Average response time")
    error_rate: float = Field(0.0, description="Error rate percentage")
    
    data_points: int = Field(0, description="Number of data points aggregated")


@dataclass
class FirestoreSchema:
    """
    Firestore collection schema for metrics storage
    
    Collections:
    - metrics/service-metrics/{service_name}/raw_metrics/{timestamp_id}
    - metrics/service-metrics/{service_name}/hourly_metrics/{hour_timestamp_id}  
    - metrics/service-metrics/{service_name}/daily_metrics/{day_timestamp_id}
    - metrics/alerts/{alert_id}
    - metrics/service_health/{service_name}
    """
    
    # Collection paths
    RAW_METRICS = "metrics/service-metrics"
    HOURLY_METRICS = "hourly_metrics"
    DAILY_METRICS = "daily_metrics"
    RAW_METRICS_SUBCOLLECTION = "raw_metrics"
    ALERTS = "metrics/alerts"
    SERVICE_HEALTH = "metrics/service_health"
    
    # Index recommendations
    INDEXES = [
        {
            "collection": "metrics/service-metrics/{service_name}/raw_metrics",
            "fields": [
                {"field": "timestamp", "order": "DESCENDING"},
                {"field": "service_name", "order": "ASCENDING"}
            ]
        },
        {
            "collection": "metrics/service-metrics/{service_name}/hourly_metrics", 
            "fields": [
                {"field": "start_time", "order": "DESCENDING"},
                {"field": "service_name", "order": "ASCENDING"}
            ]
        }
    ]


class MetricsQuery(BaseModel):
    """Query parameters for retrieving metrics"""
    service_names: Optional[List[str]] = Field(None, description="Filter by service names")
    start_time: Optional[datetime] = Field(None, description="Start time for query")
    end_time: Optional[datetime] = Field(None, description="End time for query")
    aggregation: str = Field("raw", description="Aggregation level: raw, hourly, daily")
    limit: int = Field(100, description="Maximum number of records to return")


class DashboardMetrics(BaseModel):
    """Formatted metrics for dashboard display"""
    services: List[str] = Field(..., description="List of service names")
    time_range: str = Field(..., description="Time range of data")
    
    # Current metrics (latest values)
    current_cpu: Dict[str, float] = Field(default_factory=dict, description="Current CPU by service")
    current_memory: Dict[str, float] = Field(default_factory=dict, description="Current memory by service")
    current_response_time: Dict[str, float] = Field(default_factory=dict, description="Current response time by service")
    
    # Time series data for charts
    cpu_time_series: List[Dict[str, Any]] = Field(default_factory=list, description="CPU usage over time")
    memory_time_series: List[Dict[str, Any]] = Field(default_factory=list, description="Memory usage over time")
    response_time_series: List[Dict[str, Any]] = Field(default_factory=list, description="Response time over time")
    
    # Request statistics
    request_distribution: List[Dict[str, Any]] = Field(default_factory=list, description="Requests per service")
    error_statistics: List[Dict[str, Any]] = Field(default_factory=list, description="Success vs error rates")
    
    # Summary metrics
    total_requests: int = Field(0, description="Total requests across all services")
    overall_error_rate: float = Field(0.0, description="Overall error rate percentage")
    avg_response_time: float = Field(0.0, description="Average response time across services")


# Utility functions for time-based document IDs
def generate_timestamp_id(timestamp: datetime, granularity: str = "minute") -> str:
    """Generate consistent timestamp-based document IDs"""
    if granularity == "minute":
        return timestamp.strftime("%Y%m%d_%H%M")
    elif granularity == "hour":
        return timestamp.strftime("%Y%m%d_%H")
    elif granularity == "day":
        return timestamp.strftime("%Y%m%d")
    else:
        return timestamp.strftime("%Y%m%d_%H%M%S")


def get_collection_path(service_name: str, metrics_type: str = "raw") -> str:
    """Get Firestore collection path for metrics"""
    base_path = f"{FirestoreSchema.RAW_METRICS}/{service_name}"
    
    if metrics_type == "raw":
        return f"{base_path}/{FirestoreSchema.RAW_METRICS_SUBCOLLECTION}"
    elif metrics_type == "hourly":
        return f"{base_path}/{FirestoreSchema.HOURLY_METRICS}"
    elif metrics_type == "daily":
        return f"{base_path}/{FirestoreSchema.DAILY_METRICS}"
    else:
        return f"{base_path}/raw_metrics"