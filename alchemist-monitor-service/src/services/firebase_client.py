"""
Firebase client for metrics storage
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from firebase_admin import firestore
from firebase_admin.firestore import Client as FirestoreClient, SERVER_TIMESTAMP

# Import centralized Firebase client
from alchemist_shared.database.firebase_client import FirebaseClient

from ..models.metrics import ServiceMetrics, HealthCheckResult, MonitoringSummary

logger = logging.getLogger(__name__)

class MonitorFirebaseClient:
    """
    Firebase client for storing monitoring metrics
    """
    
    def __init__(self):
        self.db: Optional[FirestoreClient] = None
        self._firebase_client: Optional[FirebaseClient] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Firebase using centralized client"""
        try:
            # Use centralized Firebase client
            self._firebase_client = FirebaseClient()
            self.db = self._firebase_client.db
            logger.info("Monitor service Firebase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    async def store_health_check(self, result: HealthCheckResult) -> bool:
        """Store health check result - OPTIMIZED: Fixed-size document, no storage bloat"""
        try:
            # Use service name as document ID - this REUSES the same document
            doc_id = result.service_name.lower().replace(' ', '_')
            
            # Store in simpler collection structure: service_health/{service_name}
            doc_ref = self.db.collection('service_health').document(doc_id)
            
            # Get current document to extract existing recent_checks
            current_doc = doc_ref.get()
            recent_checks = []
            
            if current_doc.exists:
                current_data = current_doc.to_dict()
                if current_data and 'recent_checks' in current_data:
                    recent_checks = current_data['recent_checks']
            
            # Add new check and maintain sliding window of last 5 checks
            new_check = {
                'timestamp': result.timestamp,
                'status': result.status.value,
                'response_time_ms': result.response_time_ms,
                'status_code': result.status_code
            }
            recent_checks.append(new_check)
            
            # Keep only last 5 checks (sliding window)
            recent_checks = recent_checks[-5:]
            
            # Update document with fixed-size data
            doc_ref.set({
                'service_name': result.service_name,
                'status': result.status.value,
                'response_time_ms': result.response_time_ms,
                'status_code': result.status_code,
                'error_message': result.error_message,
                'last_check': result.timestamp,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'metadata': result.metadata,
                'recent_checks': recent_checks  # Fixed-size array, no ArrayUnion
            })
            
            logger.debug(f"Updated health status for {result.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store health check: {e}")
            return False
    
    async def store_service_metrics(self, metrics: ServiceMetrics) -> bool:
        """Store service metrics - OPTIMIZED: Fixed-size document, no storage bloat"""
        try:
            # Use service name as document ID - this REUSES the same document
            doc_id = metrics.service_name.lower().replace(' ', '_')
            
            # Store in simpler collection structure: service_metrics/{service_name}
            doc_ref = self.db.collection('service_metrics').document(doc_id)
            
            # Get current document to extract existing recent_metrics
            current_doc = doc_ref.get()
            recent_metrics = []
            
            if current_doc.exists:
                current_data = current_doc.to_dict()
                if current_data and 'recent_metrics' in current_data:
                    recent_metrics = current_data['recent_metrics']
            
            # Add new metrics and maintain sliding window of last 3 metrics
            new_metric = {
                'timestamp': metrics.timestamp,
                'health_status': metrics.health_status.value,
                'response_time_ms': metrics.response_time_ms,
                'request_count': metrics.request_count,
                'error_count': metrics.error_count
            }
            recent_metrics.append(new_metric)
            
            # Keep only last 3 metrics (sliding window)
            recent_metrics = recent_metrics[-3:]
            
            metrics_data = {
                'service_name': metrics.service_name,
                'last_updated': metrics.timestamp,
                'health_status': metrics.health_status.value,
                'response_time_ms': metrics.response_time_ms,
                'uptime_seconds': metrics.uptime_seconds,
                'request_count': metrics.request_count,
                'error_count': metrics.error_count,
                'custom_metrics': metrics.custom_metrics,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'recent_metrics': recent_metrics  # Fixed-size array, no ArrayUnion
            }
            
            if metrics.system_metrics:
                metrics_data['system_metrics'] = {
                    'cpu_usage_percent': metrics.system_metrics.cpu_usage_percent,
                    'memory_usage_percent': metrics.system_metrics.memory_usage_percent,
                    'disk_usage_percent': metrics.system_metrics.disk_usage_percent,
                    'network_in_mbps': metrics.system_metrics.network_in_mbps,
                    'network_out_mbps': metrics.system_metrics.network_out_mbps
                }
            
            # Update document with fixed-size data
            doc_ref.set(metrics_data)
            
            logger.debug(f"Updated metrics for {metrics.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store service metrics: {e}")
            return False
    
    async def store_monitoring_summary(self, summary: MonitoringSummary) -> bool:
        """Store monitoring summary - OPTIMIZED: Fixed-size document, no storage bloat"""
        try:
            # Use fixed document ID - this REUSES the same document
            doc_ref = self.db.collection('monitoring_summary').document('current')
            
            # Get current document to extract existing recent_summaries
            current_doc = doc_ref.get()
            recent_summaries = []
            
            if current_doc.exists:
                current_data = current_doc.to_dict()
                if current_data and 'recent_summaries' in current_data:
                    recent_summaries = current_data['recent_summaries']
            
            # Add new summary and maintain sliding window of last 12 summaries (1 hour worth at 5min intervals)
            new_summary = {
                'timestamp': summary.last_check_timestamp,
                'healthy_services': summary.healthy_services,
                'total_services': summary.total_services,
                'average_response_time_ms': summary.average_response_time_ms,
                'uptime_percentage': summary.uptime_percentage
            }
            recent_summaries.append(new_summary)
            
            # Keep only last 12 summaries (sliding window)
            recent_summaries = recent_summaries[-12:]
            
            summary_data = {
                'total_services': summary.total_services,
                'healthy_services': summary.healthy_services,
                'degraded_services': summary.degraded_services,
                'unhealthy_services': summary.unhealthy_services,
                'unknown_services': summary.unknown_services,
                'average_response_time_ms': summary.average_response_time_ms,
                'total_requests': summary.total_requests,
                'total_errors': summary.total_errors,
                'error_rate_percent': summary.error_rate_percent,
                'last_check_timestamp': summary.last_check_timestamp,
                'uptime_percentage': summary.uptime_percentage,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'recent_summaries': recent_summaries  # Fixed-size array, no ArrayUnion
            }
            
            # Update document with fixed-size data
            doc_ref.set(summary_data)
            
            logger.debug("Updated monitoring summary")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store monitoring summary: {e}")
            return False
    
    async def get_latest_health_checks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest health check results - OPTIMIZED: Use new service_health collection"""
        try:
            # Get all service health documents (now there's only one per service)
            query = (self.db.collection('service_health')
                    .order_by('updated_at', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                if data:
                    results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get health checks: {e}")
            return []
    
    async def get_service_health_summary(self) -> Dict[str, Any]:
        """Get current health summary for all services - OPTIMIZED: Use new service_health collection"""
        try:
            # Get all current service health status (now only one document per service)
            query = (self.db.collection('service_health')
                    .order_by('updated_at', direction=firestore.Query.DESCENDING))
            
            docs = query.stream()
            
            services = []
            for doc in docs:
                data = doc.to_dict()
                if data:
                    # Only include recent checks (last 10 minutes to account for 5-minute interval)
                    if data.get('last_check'):
                        last_check = data['last_check']
                        if isinstance(last_check, datetime):
                            cutoff_time = datetime.utcnow() - timedelta(minutes=10)
                            if last_check >= cutoff_time:
                                services.append(data)
            
            return {
                'services': services,
                'count': len(services),
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get service health summary: {e}")
            return {'services': [], 'count': 0, 'timestamp': datetime.utcnow()}
    
    async def cleanup_old_metrics(self, retention_days: int = 30):
        """Clean up old metrics data - LEGACY CLEANUP ONLY: No longer needed for current collections"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Clean up OLD service metrics collection (legacy timestamp-based docs only)
            try:
                old_metrics_query = (self.db.collection('monitoring')
                                   .document('metrics')
                                   .collection('services')
                                   .where('timestamp', '<', cutoff_date))
                
                batch = self.db.batch()
                docs = old_metrics_query.stream()
                
                delete_count = 0
                for doc in docs:
                    batch.delete(doc.reference)
                    delete_count += 1
                    
                    # Firestore batch limit is 500
                    if delete_count >= 500:
                        batch.commit()
                        batch = self.db.batch()
                        delete_count = 0
                
                if delete_count > 0:
                    batch.commit()
                    
                logger.info(f"Cleaned up {delete_count} old legacy service metrics documents")
            except Exception as e:
                logger.warning(f"No old service metrics to clean: {e}")
            
            # Clean up OLD summaries collection (legacy timestamp-based docs only)
            try:
                old_summaries_query = (self.db.collection('monitoring')
                                     .document('summaries')
                                     .collection('daily')
                                     .where('last_check_timestamp', '<', cutoff_date))
                
                batch = self.db.batch()
                docs = old_summaries_query.stream()
                
                delete_count = 0
                for doc in docs:
                    batch.delete(doc.reference)
                    delete_count += 1
                    
                    if delete_count >= 500:
                        batch.commit()
                        batch = self.db.batch()
                        delete_count = 0
                
                if delete_count > 0:
                    batch.commit()
                    
                logger.info(f"Cleaned up {delete_count} old legacy summary documents")
            except Exception as e:
                logger.warning(f"No old summaries to clean: {e}")
            
            # NOTE: No array trimming needed - sliding windows prevent unbounded growth
            logger.info(f"Completed cleanup of legacy metrics data (retention: {retention_days} days)")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")