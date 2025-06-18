"""
Firebase client for metrics storage
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import Client as FirestoreClient

from ..models.metrics import ServiceMetrics, HealthCheckResult, MonitoringSummary

logger = logging.getLogger(__name__)

class MonitorFirebaseClient:
    """
    Firebase client for storing monitoring metrics
    """
    
    def __init__(self):
        self.db: Optional[FirestoreClient] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Firebase connection"""
        try:
            # Check if app already exists
            try:
                app = firebase_admin.get_app()
                logger.info("Firebase app already initialized")
            except ValueError:
                # Initialize new app
                cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with service account")
                else:
                    # Try default credentials for Cloud Run
                    firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            
            self.db = firestore.client()
            logger.info("Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    async def store_health_check(self, result: HealthCheckResult) -> bool:
        """Store health check result"""
        try:
            doc_id = f"{result.service_name}_{result.timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            doc_ref = self.db.collection('monitoring').document('health_checks').collection('results').document(doc_id)
            
            doc_ref.set({
                'service_name': result.service_name,
                'status': result.status.value,
                'response_time_ms': result.response_time_ms,
                'status_code': result.status_code,
                'error_message': result.error_message,
                'timestamp': result.timestamp,
                'metadata': result.metadata
            })
            
            logger.debug(f"Stored health check for {result.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store health check: {e}")
            return False
    
    async def store_service_metrics(self, metrics: ServiceMetrics) -> bool:
        """Store service metrics"""
        try:
            doc_id = f"{metrics.service_name}_{metrics.timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            doc_ref = self.db.collection('monitoring').document('metrics').collection('services').document(doc_id)
            
            metrics_data = {
                'service_name': metrics.service_name,
                'timestamp': metrics.timestamp,
                'health_status': metrics.health_status.value,
                'response_time_ms': metrics.response_time_ms,
                'uptime_seconds': metrics.uptime_seconds,
                'request_count': metrics.request_count,
                'error_count': metrics.error_count,
                'custom_metrics': metrics.custom_metrics
            }
            
            if metrics.system_metrics:
                metrics_data['system_metrics'] = {
                    'cpu_usage_percent': metrics.system_metrics.cpu_usage_percent,
                    'memory_usage_percent': metrics.system_metrics.memory_usage_percent,
                    'disk_usage_percent': metrics.system_metrics.disk_usage_percent,
                    'network_in_mbps': metrics.system_metrics.network_in_mbps,
                    'network_out_mbps': metrics.system_metrics.network_out_mbps
                }
            
            doc_ref.set(metrics_data)
            
            logger.debug(f"Stored metrics for {metrics.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store service metrics: {e}")
            return False
    
    async def store_monitoring_summary(self, summary: MonitoringSummary) -> bool:
        """Store monitoring summary"""
        try:
            doc_id = summary.last_check_timestamp.strftime('%Y%m%d_%H%M%S')
            
            doc_ref = self.db.collection('monitoring').document('summaries').collection('daily').document(doc_id)
            
            doc_ref.set({
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
                'uptime_percentage': summary.uptime_percentage
            })
            
            logger.debug("Stored monitoring summary")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store monitoring summary: {e}")
            return False
    
    async def get_latest_health_checks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest health check results"""
        try:
            query = (self.db.collection('monitoring')
                    .document('health_checks')
                    .collection('results')
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
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
        """Get current health summary for all services"""
        try:
            # Get recent health checks (last 5 minutes)
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            
            query = (self.db.collection('monitoring')
                    .document('health_checks')
                    .collection('results')
                    .where('timestamp', '>=', cutoff_time)
                    .order_by('timestamp', direction=firestore.Query.DESCENDING))
            
            docs = query.stream()
            
            # Group by service name to get latest status
            service_statuses = {}
            for doc in docs:
                data = doc.to_dict()
                if data and data['service_name'] not in service_statuses:
                    service_statuses[data['service_name']] = data
            
            return {
                'services': list(service_statuses.values()),
                'count': len(service_statuses),
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get service health summary: {e}")
            return {'services': [], 'count': 0, 'timestamp': datetime.utcnow()}
    
    async def cleanup_old_metrics(self, retention_days: int = 30):
        """Clean up old metrics data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Clean up health checks
            old_checks_query = (self.db.collection('monitoring')
                              .document('health_checks')
                              .collection('results')
                              .where('timestamp', '<', cutoff_date))
            
            batch = self.db.batch()
            docs = old_checks_query.stream()
            
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
            
            logger.info(f"Cleaned up old metrics data (retention: {retention_days} days)")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")