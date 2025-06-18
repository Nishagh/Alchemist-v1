"""
Metrics API Routes

Provides REST endpoints for retrieving performance metrics for the admin dashboard.
Aggregates data from all Alchemist services.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Check if metrics functionality is available
METRICS_AVAILABLE = False
try:
    from alchemist_shared.services.metrics_service import MetricsService, get_metrics_service
    from alchemist_shared.models.metrics_models import (
        MetricsQuery, DashboardMetrics, ServiceMetrics
    )
    METRICS_AVAILABLE = True
    logger.info("Metrics service available")
except ImportError as e:
    logger.warning(f"Metrics service not available: {e}")


class MetricsResponse(BaseModel):
    """Response model for metrics endpoints"""
    success: bool = True
    data: Any = None
    message: str = "Metrics retrieved successfully"
    timestamp: datetime = datetime.utcnow()


class ServiceHealthResponse(BaseModel):
    """Response model for service health"""
    service_name: str
    status: str
    last_updated: datetime
    current_cpu: float
    current_memory: float
    current_response_time: float


# Mock data for fallback
def get_mock_dashboard_data():
    """Return mock data when metrics service is not available"""
    return {
        "services": ["agent-engine", "knowledge-vault", "agent-bridge", "agent-launcher", "tool-forge"],
        "time_range": "24h",
        "current_cpu": {
            "agent-engine": 45.2,
            "knowledge-vault": 38.7,
            "agent-bridge": 29.4,
            "agent-launcher": 22.1,
            "tool-forge": 19.8
        },
        "current_memory": {
            "agent-engine": 62.3,
            "knowledge-vault": 58.9,
            "agent-bridge": 45.1,
            "agent-launcher": 41.7,
            "tool-forge": 38.2
        },
        "current_response_time": {
            "agent-engine": 125.4,
            "knowledge-vault": 189.2,
            "agent-bridge": 98.7,
            "agent-launcher": 156.3,
            "tool-forge": 87.1
        },
        "cpu_time_series": [],
        "memory_time_series": [],
        "response_time_series": [],
        "request_distribution": [
            {"service": "agent-engine", "requests": 3542},
            {"service": "knowledge-vault", "requests": 1287},
            {"service": "agent-bridge", "requests": 2156},
            {"service": "agent-launcher", "requests": 743},
            {"service": "tool-forge", "requests": 521}
        ],
        "error_statistics": [
            {"name": "Success", "value": 8139, "color": "#10b981"},
            {"name": "Errors", "value": 110, "color": "#ef4444"}
        ],
        "total_requests": 8249,
        "overall_error_rate": 1.33,
        "avg_response_time": 131.3
    }


@router.get("/dashboard", response_model=MetricsResponse)
async def get_dashboard_metrics(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d")
):
    """Get formatted metrics for dashboard display"""
    try:
        if not METRICS_AVAILABLE:
            logger.warning("Metrics service not available, returning mock data")
            return MetricsResponse(
                data=get_mock_dashboard_data(),
                message="Metrics service not available - showing sample data"
            )
        
        # Use real metrics service
        logger.info(f"Getting dashboard metrics for time range: {time_range}")
        metrics_service = MetricsService("metrics-api")
        dashboard_metrics = await metrics_service.get_dashboard_metrics(time_range)
        
        return MetricsResponse(
            data=dashboard_metrics.dict(),
            message=f"Dashboard metrics for {time_range} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        # Return mock data on error
        return MetricsResponse(
            data=get_mock_dashboard_data(),
            message=f"Error retrieving metrics, showing sample data: {str(e)}"
        )


@router.get("/health", response_model=MetricsResponse)
async def get_services_health():
    """Get current health status of all services"""
    try:
        if not METRICS_AVAILABLE:
            logger.warning("Metrics service not available, returning mock health data")
            return MetricsResponse(
                data={
                    "services": [
                        {
                            "service_name": "agent-engine",
                            "status": "healthy",
                            "last_updated": datetime.utcnow(),
                            "current_cpu": 45.2,
                            "current_memory": 62.3,
                            "current_response_time": 125.4
                        }
                    ],
                    "count": 1
                },
                message="Metrics service not available - showing sample health data"
            )
        
        logger.info("Getting services health status")
        metrics_service = MetricsService("metrics-api")
        
        # Get current service health from Firestore
        health_collection = metrics_service.firebase_client.db.collection("metrics/service_health")
        health_docs = health_collection.stream()
        
        health_data = []
        for doc in health_docs:
            data = doc.to_dict()
            if data:
                health_data.append(ServiceHealthResponse(
                    service_name=data.get("service_name", doc.id),
                    status=data.get("status", "unknown"),
                    last_updated=data.get("last_updated", datetime.utcnow()),
                    current_cpu=data.get("current_cpu", 0.0),
                    current_memory=data.get("current_memory", 0.0),
                    current_response_time=data.get("current_response_time", 0.0)
                ))
        
        return MetricsResponse(
            data={
                "services": [health.dict() for health in health_data],
                "count": len(health_data)
            },
            message="Service health status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get services health: {e}")
        return MetricsResponse(
            data={"services": [], "count": 0},
            message=f"Failed to retrieve services health: {str(e)}"
        )


@router.get("/services", response_model=MetricsResponse)
async def get_service_metrics(
    service_name: Optional[str] = Query(None, description="Specific service name"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, description="Maximum number of records"),
    aggregation: str = Query("raw", description="Aggregation level: raw, hourly, daily")
):
    """Get detailed service metrics"""
    try:
        if not METRICS_AVAILABLE:
            return MetricsResponse(
                data={"metrics": [], "count": 0, "query": {}},
                message="Metrics service not available"
            )
        
        logger.info(f"Getting service metrics for: {service_name}")
        metrics_service = MetricsService("metrics-api")
        
        # Build query
        query = MetricsQuery(
            service_names=[service_name] if service_name else None,
            start_time=start_time,
            end_time=end_time,
            aggregation=aggregation,
            limit=limit
        )
        
        # Get metrics
        metrics_data = await metrics_service.get_metrics(query)
        
        # Convert to dict format
        metrics_dict = [metric.dict() for metric in metrics_data]
        
        return MetricsResponse(
            data={
                "metrics": metrics_dict,
                "count": len(metrics_dict),
                "query": query.dict()
            },
            message="Service metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get service metrics: {e}")
        return MetricsResponse(
            data={"metrics": [], "count": 0},
            message=f"Failed to retrieve service metrics: {str(e)}"
        )


@router.get("/summary", response_model=MetricsResponse)
async def get_metrics_summary(
    time_range: str = Query("24h", description="Time range for summary")
):
    """Get high-level metrics summary"""
    try:
        if not METRICS_AVAILABLE:
            return MetricsResponse(
                data={
                    "summary": {
                        "total_services": 5,
                        "healthy_services": 4,
                        "total_requests": 8249,
                        "total_errors": 110,
                        "avg_cpu_usage": 35.2,
                        "avg_memory_usage": 49.1,
                        "avg_response_time": 131.3,
                        "error_rate": 1.33
                    },
                    "time_range": time_range,
                    "services": ["agent-engine", "knowledge-vault", "agent-bridge", "agent-launcher", "tool-forge"]
                },
                message="Metrics service not available - showing sample summary"
            )
        
        logger.info(f"Getting metrics summary for: {time_range}")
        metrics_service = MetricsService("metrics-api")
        
        # Parse time range
        if time_range == "1h":
            start_time = datetime.utcnow() - timedelta(hours=1)
        elif time_range == "6h":
            start_time = datetime.utcnow() - timedelta(hours=6)
        elif time_range == "24h":
            start_time = datetime.utcnow() - timedelta(hours=24)
        elif time_range == "7d":
            start_time = datetime.utcnow() - timedelta(days=7)
        else:
            start_time = datetime.utcnow() - timedelta(hours=24)
        
        # Get recent metrics
        query = MetricsQuery(
            start_time=start_time,
            end_time=datetime.utcnow(),
            limit=1000
        )
        
        metrics_data = await metrics_service.get_metrics(query)
        
        # Calculate summary statistics
        if not metrics_data:
            return MetricsResponse(
                data={
                    "summary": {
                        "total_services": 0,
                        "healthy_services": 0,
                        "total_requests": 0,
                        "total_errors": 0,
                        "avg_cpu_usage": 0.0,
                        "avg_memory_usage": 0.0,
                        "avg_response_time": 0.0,
                        "error_rate": 0.0
                    },
                    "time_range": time_range
                },
                message="No metrics data available"
            )
        
        # Group by service to get latest metrics
        service_latest = {}
        for metric in metrics_data:
            if metric.service_name not in service_latest:
                service_latest[metric.service_name] = metric
            elif metric.timestamp > service_latest[metric.service_name].timestamp:
                service_latest[metric.service_name] = metric
        
        # Calculate aggregated values
        total_requests = sum(m.request_metrics.total_requests for m in service_latest.values())
        total_errors = sum(m.request_metrics.error_requests for m in service_latest.values())
        healthy_services = sum(1 for m in service_latest.values() if m.health_status == "healthy")
        
        cpu_values = [m.system_metrics.cpu_usage_percent for m in service_latest.values()]
        memory_values = [m.system_metrics.memory_usage_percent for m in service_latest.values()]
        response_times = [m.request_metrics.avg_response_time_ms for m in service_latest.values() if m.request_metrics.avg_response_time_ms > 0]
        
        summary_data = {
            "total_services": len(service_latest),
            "healthy_services": healthy_services,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "avg_cpu_usage": sum(cpu_values) / len(cpu_values) if cpu_values else 0.0,
            "avg_memory_usage": sum(memory_values) / len(memory_values) if memory_values else 0.0,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0.0,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0.0
        }
        
        return MetricsResponse(
            data={
                "summary": summary_data,
                "time_range": time_range,
                "services": list(service_latest.keys())
            },
            message="Metrics summary retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        return MetricsResponse(
            data={"summary": {}, "time_range": time_range},
            message=f"Failed to retrieve metrics summary: {str(e)}"
        )


@router.post("/collect", response_model=MetricsResponse)
async def trigger_metrics_collection():
    """Manually trigger metrics collection"""
    try:
        if not METRICS_AVAILABLE:
            return MetricsResponse(
                data={"message": "Metrics service not available"},
                message="Cannot trigger collection - metrics service not available"
            )
        
        logger.info("Triggering metrics collection")
        metrics_service = MetricsService("metrics-api")
        
        # Trigger collection
        await metrics_service.collect_and_store_metrics()
        
        return MetricsResponse(
            data={"collected_at": datetime.utcnow()},
            message="Metrics collection triggered successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger metrics collection: {e}")
        return MetricsResponse(
            data={"error": str(e)},
            message=f"Failed to trigger metrics collection: {str(e)}"
        )