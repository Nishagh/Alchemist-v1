"""
Centralized Metrics Service

Handles collection, storage, and retrieval of performance metrics across all Alchemist services.
Uses Firestore for persistence and provides real-time metrics for the admin dashboard.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque

from ..database.firebase_client import FirebaseClient
from ..models.metrics_models import (
    SystemMetrics, RequestMetrics, ServiceMetrics, MetricsAggregation,
    DashboardMetrics, MetricsQuery, generate_timestamp_id, get_collection_path
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_times = deque(maxlen=1000)  # Store last 1000 request times
        self.request_count = 0
        self.error_count = 0
        
    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system resource metrics"""
        try:
            # Get CPU usage (1-second interval for accuracy)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get disk usage for current directory
            disk = psutil.disk_usage('/')
            
            return SystemMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                memory_used_bytes=memory.used,
                memory_total_bytes=memory.total,
                disk_usage_percent=disk.percent
            )
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return default values if collection fails
            return SystemMetrics(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                memory_used_bytes=0,
                memory_total_bytes=0,
                disk_usage_percent=0.0
            )
    
    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record a request for metrics calculation"""
        self.request_times.append(response_time_ms)
        self.request_count += 1
        if is_error:
            self.error_count += 1
    
    def get_request_metrics(self) -> RequestMetrics:
        """Calculate request metrics from recorded data"""
        if not self.request_times:
            return RequestMetrics()
        
        response_times = list(self.request_times)
        
        return RequestMetrics(
            total_requests=self.request_count,
            successful_requests=self.request_count - self.error_count,
            error_requests=self.error_count,
            avg_response_time_ms=sum(response_times) / len(response_times),
            min_response_time_ms=min(response_times),
            max_response_time_ms=max(response_times)
        )
    
    def reset_request_metrics(self):
        """Reset request metrics for new collection period"""
        self.request_times.clear()
        self.request_count = 0
        self.error_count = 0


class MetricsService:
    """Central service for managing metrics collection and storage"""
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.firebase_client = FirebaseClient()
        self.collector = MetricsCollector()
        self.background_task = None
        self.collection_interval = 60  # seconds
        
    async def start_background_collection(self):
        """Start background task for periodic metrics collection"""
        if self.background_task is None:
            self.background_task = asyncio.create_task(self._background_collection_loop())
            logger.info(f"Started background metrics collection for {self.service_name}")
    
    async def stop_background_collection(self):
        """Stop background metrics collection"""
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
            self.background_task = None
            logger.info(f"Stopped background metrics collection for {self.service_name}")
    
    async def _background_collection_loop(self):
        """Background loop for collecting metrics periodically"""
        while True:
            try:
                await self.collect_and_store_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def collect_and_store_metrics(self, custom_metrics: Dict[str, Any] = None):
        """Collect current metrics and store them in Firestore"""
        try:
            timestamp = datetime.utcnow()
            
            # Collect metrics
            system_metrics = self.collector.get_system_metrics()
            request_metrics = self.collector.get_request_metrics()
            
            # Create service metrics object
            service_metrics = ServiceMetrics(
                service_name=self.service_name,
                timestamp=timestamp,
                system_metrics=system_metrics,
                request_metrics=request_metrics,
                custom_metrics=custom_metrics or {},
                health_status=self._determine_health_status(system_metrics, request_metrics),
                version=self.version
            )
            
            # Store in Firestore
            await self._store_metrics(service_metrics)
            
            # Reset request metrics for next collection period
            self.collector.reset_request_metrics()
            
            logger.debug(f"Collected and stored metrics for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to collect and store metrics: {e}")
    
    def _determine_health_status(self, system_metrics: SystemMetrics, request_metrics: RequestMetrics) -> str:
        """Determine service health based on metrics"""
        # Health criteria
        if system_metrics.cpu_usage_percent > 90:
            return "unhealthy"
        if system_metrics.memory_usage_percent > 90:
            return "unhealthy"
        
        if request_metrics.total_requests > 0:
            error_rate = (request_metrics.error_requests / request_metrics.total_requests) * 100
            if error_rate > 10:
                return "degraded"
            if request_metrics.avg_response_time_ms > 5000:  # 5 seconds
                return "degraded"
        
        return "healthy"
    
    async def _store_metrics(self, metrics: ServiceMetrics):
        """Store metrics in Firestore"""
        try:
            # Generate document ID based on timestamp
            doc_id = generate_timestamp_id(metrics.timestamp, "minute")
            
            # Get collection path
            collection_path = get_collection_path(self.service_name, "raw")
            
            # Convert to dict for Firestore
            metrics_dict = metrics.model_dump()
            metrics_dict['timestamp'] = metrics.timestamp
            
            # Store in Firestore
            doc_ref = self.firebase_client.db.collection(collection_path).document(doc_id)
            doc_ref.set(metrics_dict)
            
            # Also update current service health
            await self._update_service_health(metrics)
            
        except Exception as e:
            logger.error(f"Failed to store metrics in Firestore: {e}")
    
    async def _update_service_health(self, metrics: ServiceMetrics):
        """Update current service health status"""
        try:
            health_data = {
                "service_name": self.service_name,
                "status": metrics.health_status,
                "last_updated": metrics.timestamp,
                "version": metrics.version,
                "current_cpu": metrics.system_metrics.cpu_usage_percent,
                "current_memory": metrics.system_metrics.memory_usage_percent,
                "current_response_time": metrics.request_metrics.avg_response_time_ms
            }
            
            doc_ref = self.firebase_client.db.collection("service_health").document(self.service_name)
            doc_ref.set(health_data)
            
        except Exception as e:
            logger.error(f"Failed to update service health: {e}")
    
    def record_request(self, response_time_ms: float, status_code: int):
        """Record a request for metrics tracking"""
        is_error = status_code >= 400
        self.collector.record_request(response_time_ms, is_error)
    
    async def get_metrics(self, query: MetricsQuery) -> List[ServiceMetrics]:
        """Retrieve metrics based on query parameters"""
        try:
            # Determine which service(s) to query
            services = query.service_names or [self.service_name]
            
            all_metrics = []
            
            for service in services:
                collection_path = get_collection_path(service, query.aggregation)
                collection_ref = self.firebase_client.db.collection(collection_path)
                
                # Build query
                query_ref = collection_ref
                
                if query.start_time:
                    query_ref = query_ref.where("timestamp", ">=", query.start_time)
                if query.end_time:
                    query_ref = query_ref.where("timestamp", "<=", query.end_time)
                
                query_ref = query_ref.order_by("timestamp", direction="desc")
                query_ref = query_ref.limit(query.limit)
                
                # Execute query
                docs = query_ref.stream()
                
                for doc in docs:
                    data = doc.to_dict()
                    if data:
                        # Convert back to ServiceMetrics object
                        metrics = ServiceMetrics(**data)
                        all_metrics.append(metrics)
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Failed to retrieve metrics: {e}")
            return []
    
    async def get_dashboard_metrics(self, time_range: str = "24h") -> DashboardMetrics:
        """Get formatted metrics for dashboard display"""
        try:
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
            
            # Get all service names from health collection
            health_docs = self.firebase_client.db.collection("metrics/service_health").stream()
            services = [doc.id for doc in health_docs]
            
            if not services:
                # Fallback to known services
                services = ["agent-engine", "knowledge-vault", "agent-bridge", "agent-launcher", "tool-forge"]
            
            # Query metrics for all services
            query = MetricsQuery(
                service_names=services,
                start_time=start_time,
                end_time=datetime.utcnow(),
                limit=1000
            )
            
            metrics_data = await self.get_metrics(query)
            
            # Format for dashboard
            dashboard_metrics = self._format_dashboard_metrics(metrics_data, services, time_range)
            
            return dashboard_metrics
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            return DashboardMetrics(services=[], time_range=time_range)
    
    def _format_dashboard_metrics(self, metrics_data: List[ServiceMetrics], services: List[str], time_range: str) -> DashboardMetrics:
        """Format raw metrics data for dashboard consumption"""
        try:
            # Group metrics by service and time
            service_metrics = defaultdict(list)
            for metric in metrics_data:
                service_metrics[metric.service_name].append(metric)
            
            # Initialize dashboard metrics
            dashboard = DashboardMetrics(services=services, time_range=time_range)
            
            # Calculate current metrics (latest values)
            for service in services:
                if service in service_metrics and service_metrics[service]:
                    latest = service_metrics[service][0]  # Already sorted by timestamp desc
                    dashboard.current_cpu[service] = latest.system_metrics.cpu_usage_percent
                    dashboard.current_memory[service] = latest.system_metrics.memory_usage_percent
                    dashboard.current_response_time[service] = latest.request_metrics.avg_response_time_ms
            
            # Create time series data
            dashboard.cpu_time_series = self._create_time_series(service_metrics, "cpu", services)
            dashboard.memory_time_series = self._create_time_series(service_metrics, "memory", services)
            dashboard.response_time_series = self._create_time_series(service_metrics, "response_time", services)
            
            # Calculate request distribution
            dashboard.request_distribution = self._calculate_request_distribution(service_metrics, services)
            
            # Calculate error statistics
            dashboard.error_statistics = self._calculate_error_statistics(service_metrics)
            
            # Calculate summary metrics
            dashboard.total_requests = sum(
                sum(m.request_metrics.total_requests for m in metrics)
                for metrics in service_metrics.values()
            )
            
            total_errors = sum(
                sum(m.request_metrics.error_requests for m in metrics)
                for metrics in service_metrics.values()
            )
            
            dashboard.overall_error_rate = (total_errors / dashboard.total_requests * 100) if dashboard.total_requests > 0 else 0
            
            response_times = []
            for metrics in service_metrics.values():
                for m in metrics:
                    if m.request_metrics.avg_response_time_ms > 0:
                        response_times.append(m.request_metrics.avg_response_time_ms)
            
            dashboard.avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to format dashboard metrics: {e}")
            return DashboardMetrics(services=services, time_range=time_range)
    
    def _create_time_series(self, service_metrics: Dict[str, List[ServiceMetrics]], metric_type: str, services: List[str]) -> List[Dict[str, Any]]:
        """Create time series data for charts"""
        time_points = set()
        
        # Collect all unique timestamps
        for metrics_list in service_metrics.values():
            for metric in metrics_list:
                time_points.add(metric.timestamp.strftime("%H:%M"))
        
        time_points = sorted(time_points)
        
        # Create time series
        time_series = []
        for time_point in time_points:
            data_point = {"time": time_point}
            
            for service in services:
                value = 0
                if service in service_metrics:
                    # Find metric for this time point
                    for metric in service_metrics[service]:
                        if metric.timestamp.strftime("%H:%M") == time_point:
                            if metric_type == "cpu":
                                value = metric.system_metrics.cpu_usage_percent
                            elif metric_type == "memory":
                                value = metric.system_metrics.memory_usage_percent
                            elif metric_type == "response_time":
                                value = metric.request_metrics.avg_response_time_ms
                            break
                
                data_point[service] = value
            
            time_series.append(data_point)
        
        return time_series
    
    def _calculate_request_distribution(self, service_metrics: Dict[str, List[ServiceMetrics]], services: List[str]) -> List[Dict[str, Any]]:
        """Calculate request distribution per service"""
        distribution = []
        
        for service in services:
            total_requests = 0
            if service in service_metrics:
                total_requests = sum(m.request_metrics.total_requests for m in service_metrics[service])
            
            distribution.append({
                "service": service,
                "requests": total_requests
            })
        
        return distribution
    
    def _calculate_error_statistics(self, service_metrics: Dict[str, List[ServiceMetrics]]) -> List[Dict[str, Any]]:
        """Calculate success vs error statistics"""
        total_requests = 0
        total_errors = 0
        
        for metrics_list in service_metrics.values():
            for metric in metrics_list:
                total_requests += metric.request_metrics.total_requests
                total_errors += metric.request_metrics.error_requests
        
        total_success = total_requests - total_errors
        
        return [
            {"name": "Success", "value": total_success, "color": "#10b981"},
            {"name": "Errors", "value": total_errors, "color": "#ef4444"}
        ]


# Global metrics service instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service(service_name: str = None, version: str = "1.0.0") -> MetricsService:
    """Get or create global metrics service instance"""
    global _metrics_service
    
    if _metrics_service is None and service_name:
        _metrics_service = MetricsService(service_name, version)
    
    return _metrics_service


def init_metrics_service(service_name: str, version: str = "1.0.0") -> MetricsService:
    """Initialize metrics service for a specific service"""
    global _metrics_service
    _metrics_service = MetricsService(service_name, version)
    return _metrics_service