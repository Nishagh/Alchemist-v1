"""
Monitoring API endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from ..models.metrics import ServiceStatus, HealthCheckResult, MonitoringSummary
from ..services.health_monitor import HealthMonitor
from ..config.services import MONITORED_SERVICES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Global monitor instance
monitor = HealthMonitor()

class HealthResponse(BaseModel):
    success: bool = True
    message: str = "Monitor service is healthy"
    timestamp: datetime
    version: str = "1.0.0"
    services_monitored: int

class ServiceHealthResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    message: str = "Service health retrieved successfully"
    timestamp: datetime

class MetricsSummaryResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    message: str = "Metrics summary retrieved successfully"
    timestamp: datetime

@router.get("/health", response_model=HealthResponse)
async def get_monitor_health():
    """Health check for the monitoring service itself"""
    return HealthResponse(
        timestamp=datetime.utcnow(),
        services_monitored=len(MONITORED_SERVICES)
    )

@router.get("/services/health", response_model=ServiceHealthResponse)
async def get_services_health():
    """Get current health status of all monitored services"""
    try:
        logger.info("Getting services health status")
        
        # Get latest health data from Firestore
        health_data = await monitor.firebase_client.get_service_health_summary()
        
        if not health_data['services']:
            # If no recent data, trigger fresh check
            logger.info("No recent health data found, triggering fresh check")
            health_results = await monitor.check_all_services()
            
            # Convert to response format
            services_data = []
            for result in health_results:
                services_data.append({
                    "service_name": result.service_name,
                    "status": result.status.value,
                    "last_updated": result.timestamp,
                    "current_cpu": 0.0,  # Would need system metrics integration
                    "current_memory": 0.0,  # Would need system metrics integration
                    "current_response_time": result.response_time_ms or 0.0,
                    "status_code": result.status_code,
                    "error_message": result.error_message
                })
            
            health_data = {
                "services": services_data,
                "count": len(services_data),
                "timestamp": datetime.utcnow()
            }
        else:
            # Format existing data
            for service in health_data['services']:
                service['current_response_time'] = service.get('response_time_ms', 0.0)
                service['current_cpu'] = 0.0  # Placeholder
                service['current_memory'] = 0.0  # Placeholder
        
        return ServiceHealthResponse(
            data=health_data,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get services health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve services health: {str(e)}")

@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_monitoring_summary(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d")
):
    """Get monitoring summary statistics"""
    try:
        logger.info(f"Getting monitoring summary for time range: {time_range}")
        
        # Get current summary
        summary = await monitor.get_monitoring_summary()
        
        # Get service metrics for detailed view
        service_metrics = await monitor.get_service_metrics()
        
        # Format response
        summary_data = {
            "summary": {
                "total_services": summary.total_services,
                "healthy_services": summary.healthy_services,
                "degraded_services": summary.degraded_services,
                "unhealthy_services": summary.unhealthy_services,
                "unknown_services": summary.unknown_services,
                "total_requests": summary.total_requests,
                "total_errors": summary.total_errors,
                "avg_cpu_usage": 0.0,  # Would need system metrics
                "avg_memory_usage": 0.0,  # Would need system metrics
                "avg_response_time": summary.average_response_time_ms,
                "error_rate": summary.error_rate_percent,
                "uptime_percentage": summary.uptime_percentage
            },
            "time_range": time_range,
            "services": [metric.service_name for metric in service_metrics],
            "last_check": summary.last_check_timestamp
        }
        
        return MetricsSummaryResponse(
            data=summary_data,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get monitoring summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve monitoring summary: {str(e)}")

@router.get("/services/{service_name}/health")
async def get_service_health(service_name: str):
    """Get health status for a specific service"""
    try:
        logger.info(f"Getting health for service: {service_name}")
        
        # Find service config
        service_config = None
        for svc in MONITORED_SERVICES:
            if svc.name.lower() == service_name.lower():
                service_config = svc
                break
        
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        # Get latest health check
        result = await monitor.check_single_service(service_config)
        
        return {
            "success": True,
            "data": {
                "service_name": result.service_name,
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "status_code": result.status_code,
                "error_message": result.error_message,
                "timestamp": result.timestamp,
                "metadata": result.metadata
            },
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service health: {str(e)}")

@router.post("/check/all")
async def trigger_health_check(background_tasks: BackgroundTasks):
    """Manually trigger health check for all services"""
    try:
        logger.info("Manually triggering health check for all services")
        
        # Run check in background
        background_tasks.add_task(monitor.check_all_services)
        
        return {
            "success": True,
            "message": "Health check triggered for all services",
            "timestamp": datetime.utcnow(),
            "services_count": len(MONITORED_SERVICES)
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger health check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger health check: {str(e)}")

@router.post("/check/{service_name}")
async def trigger_service_check(service_name: str):
    """Manually trigger health check for a specific service"""
    try:
        logger.info(f"Manually triggering health check for service: {service_name}")
        
        # Find service config
        service_config = None
        for svc in MONITORED_SERVICES:
            if svc.name.lower() == service_name.lower():
                service_config = svc
                break
        
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        # Run check
        result = await monitor.check_single_service(service_config)
        
        # Store result
        await monitor.firebase_client.store_health_check(result)
        
        return {
            "success": True,
            "message": f"Health check completed for {service_name}",
            "data": {
                "service_name": result.service_name,
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "timestamp": result.timestamp
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger service check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger service check: {str(e)}")

@router.get("/services")
async def list_monitored_services():
    """Get list of all monitored services"""
    try:
        services_data = []
        for service in MONITORED_SERVICES:
            services_data.append({
                "name": service.name,
                "url": service.url,
                "health_endpoint": service.health_endpoint,
                "description": service.description,
                "service_type": service.service_type,
                "version": service.version,
                "port": service.port,
                "icon": service.icon,
                "timeout": service.timeout
            })
        
        return {
            "success": True,
            "data": {
                "services": services_data,
                "count": len(services_data)
            },
            "message": "Monitored services retrieved successfully",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_data(background_tasks: BackgroundTasks):
    """Trigger cleanup of old monitoring data"""
    try:
        logger.info("Triggering cleanup of old monitoring data")
        
        background_tasks.add_task(monitor.cleanup_old_data)
        
        return {
            "success": True,
            "message": "Cleanup of old data triggered",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")