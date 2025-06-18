"""
Health monitoring service
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
import time

from ..models.metrics import (
    ServiceStatus, HealthCheckResult, ServiceMetrics, 
    MonitoringSummary, SystemMetrics
)
from ..config.services import MONITORED_SERVICES, MONITORING_CONFIG, ServiceConfig
from .firebase_client import MonitorFirebaseClient

logger = logging.getLogger(__name__)

class HealthMonitor:
    """
    Service health monitoring and metrics collection
    """
    
    def __init__(self):
        self.firebase_client = MonitorFirebaseClient()
        self.last_check_time = datetime.utcnow()
        self.check_history: Dict[str, List[HealthCheckResult]] = {}
        self.client = httpx.AsyncClient(timeout=MONITORING_CONFIG["health_check_timeout"])
    
    async def check_single_service(self, service: ServiceConfig) -> HealthCheckResult:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            logger.debug(f"Checking health for {service.name}")
            
            response = await self.client.get(
                f"{service.url}{service.health_endpoint}",
                timeout=service.timeout
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine status based on response
            if response.status_code == 200:
                status = ServiceStatus.HEALTHY
            elif 200 < response.status_code < 400:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.UNHEALTHY
            
            # Try to parse response for additional metrics
            metadata = {}
            try:
                response_data = response.json()
                if isinstance(response_data, dict):
                    metadata = response_data
            except:
                pass
            
            result = HealthCheckResult(
                service_name=service.name,
                status=status,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                metadata=metadata
            )
            
            logger.debug(f"Health check completed for {service.name}: {status.value} ({response_time_ms:.1f}ms)")
            return result
            
        except httpx.TimeoutException:
            response_time_ms = service.timeout * 1000
            result = HealthCheckResult(
                service_name=service.name,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message=f"Request timeout after {service.timeout}s"
            )
            logger.warning(f"Health check timeout for {service.name}")
            return result
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service_name=service.name,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
            logger.error(f"Health check failed for {service.name}: {e}")
            return result
    
    async def check_all_services(self) -> List[HealthCheckResult]:
        """Check health of all monitored services"""
        logger.info(f"Starting health checks for {len(MONITORED_SERVICES)} services")
        
        # Run all health checks concurrently
        tasks = [self.check_single_service(service) for service in MONITORED_SERVICES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to HealthCheckResult
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Health check exception for {MONITORED_SERVICES[i].name}: {result}")
                health_results.append(HealthCheckResult(
                    service_name=MONITORED_SERVICES[i].name,
                    status=ServiceStatus.UNKNOWN,
                    error_message=str(result)
                ))
            else:
                health_results.append(result)
        
        # Store results in history
        for result in health_results:
            if result.service_name not in self.check_history:
                self.check_history[result.service_name] = []
            
            self.check_history[result.service_name].append(result)
            
            # Keep only recent history (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.check_history[result.service_name] = [
                r for r in self.check_history[result.service_name] 
                if r.timestamp > cutoff_time
            ]
        
        # Store results in Firestore
        await self._store_health_results(health_results)
        
        self.last_check_time = datetime.utcnow()
        logger.info(f"Completed health checks for {len(health_results)} services")
        
        return health_results
    
    async def get_monitoring_summary(self) -> MonitoringSummary:
        """Generate monitoring summary"""
        latest_results = await self.check_all_services()
        
        # Calculate summary statistics
        total_services = len(latest_results)
        healthy_count = sum(1 for r in latest_results if r.status == ServiceStatus.HEALTHY)
        degraded_count = sum(1 for r in latest_results if r.status == ServiceStatus.DEGRADED)
        unhealthy_count = sum(1 for r in latest_results if r.status == ServiceStatus.UNHEALTHY)
        unknown_count = sum(1 for r in latest_results if r.status == ServiceStatus.UNKNOWN)
        
        # Calculate average response time (exclude failed requests)
        response_times = [r.response_time_ms for r in latest_results if r.response_time_ms and r.status != ServiceStatus.UNHEALTHY]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate uptime percentage based on 24h history
        uptime_percentage = self._calculate_uptime_percentage()
        
        summary = MonitoringSummary(
            total_services=total_services,
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            unknown_services=unknown_count,
            average_response_time_ms=avg_response_time,
            total_requests=0,  # This would come from service metrics
            total_errors=0,    # This would come from service metrics
            error_rate_percent=0,  # This would be calculated from service metrics
            last_check_timestamp=self.last_check_time,
            uptime_percentage=uptime_percentage
        )
        
        # Store summary
        await self.firebase_client.store_monitoring_summary(summary)
        
        return summary
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate overall uptime percentage from 24h history"""
        if not self.check_history:
            return 100.0
        
        total_checks = 0
        successful_checks = 0
        
        for service_name, results in self.check_history.items():
            total_checks += len(results)
            successful_checks += sum(1 for r in results if r.status == ServiceStatus.HEALTHY)
        
        if total_checks == 0:
            return 100.0
        
        return (successful_checks / total_checks) * 100
    
    async def _store_health_results(self, results: List[HealthCheckResult]):
        """Store health check results in Firestore"""
        try:
            tasks = [self.firebase_client.store_health_check(result) for result in results]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Failed to store health results: {e}")
    
    async def get_service_metrics(self, service_name: Optional[str] = None) -> List[ServiceMetrics]:
        """Get service metrics"""
        metrics = []
        
        for svc_name, history in self.check_history.items():
            if service_name and svc_name.lower() != service_name.lower():
                continue
            
            if not history:
                continue
            
            latest = history[-1]
            
            # Calculate basic metrics from history
            total_checks = len(history)
            successful_checks = sum(1 for r in history if r.status == ServiceStatus.HEALTHY)
            
            response_times = [r.response_time_ms for r in history if r.response_time_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            metric = ServiceMetrics(
                service_name=svc_name,
                timestamp=latest.timestamp,
                health_status=latest.status,
                response_time_ms=avg_response_time,
                request_count=total_checks,
                error_count=total_checks - successful_checks,
                custom_metrics={
                    "uptime_24h": (successful_checks / total_checks) * 100 if total_checks > 0 else 100,
                    "total_checks_24h": total_checks,
                    "latest_status_code": latest.status_code,
                    "latest_error": latest.error_message
                }
            )
            
            metrics.append(metric)
        
        return metrics
    
    async def cleanup_old_data(self):
        """Cleanup old monitoring data"""
        try:
            await self.firebase_client.cleanup_old_metrics(
                retention_days=MONITORING_CONFIG["metrics_retention_days"]
            )
            logger.info("Completed cleanup of old monitoring data")
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()