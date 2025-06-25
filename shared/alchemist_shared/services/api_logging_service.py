"""
Centralized API Logging Service

Provides centralized logging for all API requests across Alchemist services.
Logs are stored in a single Firestore collection for unified monitoring and debugging.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from google.cloud import firestore
from google.cloud.firestore import AsyncClient as AsyncFirestoreClient

from ..database.firebase_client import get_firestore_client
from ..models.api_log_models import (
    APILogEntry, 
    APILogFirestoreDocument, 
    APILogQuery, 
    APILogStats,
    APILogConfig
)
from ..logging.logger import get_logger

logger = get_logger(__name__)


class APILoggingService:
    """
    Centralized service for logging API requests across all services.
    
    Features:
    - Asynchronous batch logging for performance
    - Automatic log retention
    - Query capabilities for monitoring
    - Error tracking and alerting
    """
    
    def __init__(self, service_name: str, firestore_client: Optional[AsyncFirestoreClient] = None):
        self.service_name = service_name
        self.db = firestore_client or get_firestore_client()
        self.collection_ref = self.db.collection(APILogConfig.COLLECTION_NAME)
        
        # Batch processing
        self._log_batch: List[APILogFirestoreDocument] = []
        self._last_flush_time = time.time()
        self._flush_lock = asyncio.Lock()
        
        # Rate limiting
        self._request_counts = {}
        self._last_rate_limit_reset = time.time()
        
        logger.info(f"API logging service initialized for {service_name}")
    
    async def log_request(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        status_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
        full_url: Optional[str] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        request_content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an API request.
        
        Args:
            request_id: Unique identifier for the request
            method: HTTP method
            endpoint: API endpoint path
            status_code: HTTP response status code
            response_time_ms: Response time in milliseconds
            error_message: Error message if request failed
            error_type: Type of error
            stack_trace: Stack trace for server errors
            user_id: Authenticated user ID
            client_ip: Client IP address
            user_agent: Client user agent
            correlation_id: Correlation ID for request tracing
            full_url: Complete request URL
            request_size_bytes: Request body size
            response_size_bytes: Response body size
            request_content_type: Request content type
            metadata: Additional service-specific metadata
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                logger.warning(f"Rate limit exceeded for service {self.service_name}")
                return False
            
            # Create log entry
            log_entry = APILogEntry(
                request_id=request_id,
                correlation_id=correlation_id,
                service_name=self.service_name,
                method=method,
                endpoint=endpoint,
                full_url=full_url,
                user_agent=user_agent,
                client_ip=client_ip,
                user_id=user_id,
                response_time_ms=response_time_ms,
                status_code=status_code,
                response_size_bytes=response_size_bytes,
                error_message=self._truncate_string(error_message, APILogConfig.MAX_ERROR_MESSAGE_LENGTH),
                error_type=error_type,
                stack_trace=self._truncate_string(stack_trace, APILogConfig.MAX_STACK_TRACE_LENGTH),
                request_size_bytes=request_size_bytes,
                request_content_type=request_content_type,
                metadata=metadata or {}
            )
            
            # Convert to Firestore document
            doc = APILogFirestoreDocument.from_api_log_entry(log_entry)
            
            # Add to batch
            await self._add_to_batch(doc)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log API request: {e}", exc_info=True)
            return False
    
    async def log_request_start(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        full_url: Optional[str] = None,
        request_size_bytes: Optional[int] = None,
        request_content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log the start of an API request (before processing)."""
        
        return await self.log_request(
            request_id=request_id,
            method=method,
            endpoint=endpoint,
            correlation_id=correlation_id,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            full_url=full_url,
            request_size_bytes=request_size_bytes,
            request_content_type=request_content_type,
            metadata=metadata
        )
    
    async def log_request_complete(
        self,
        request_id: str,
        status_code: int,
        response_time_ms: float,
        response_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing log entry with completion details."""
        
        try:
            # Find the existing document
            query = self.collection_ref.where("req_id", "==", request_id).limit(1)
            docs = [doc async for doc in query.stream()]
            
            if not docs:
                logger.warning(f"No existing log entry found for request_id: {request_id}")
                return False
            
            doc_ref = docs[0].reference
            
            # Update with completion data
            update_data = {
                "status": status_code,
                "resp_ms": response_time_ms,
                "resp_size": response_size_bytes,
            }
            
            # Add error information if present
            if error_message:
                update_data["err_msg"] = self._truncate_string(error_message, APILogConfig.MAX_ERROR_MESSAGE_LENGTH)
            if error_type:
                update_data["err_type"] = error_type
            if stack_trace:
                update_data["stack"] = self._truncate_string(stack_trace, APILogConfig.MAX_STACK_TRACE_LENGTH)
            
            # Merge additional metadata
            if metadata:
                existing_doc = docs[0].to_dict()
                existing_meta = existing_doc.get("meta", {})
                existing_meta.update(metadata)
                update_data["meta"] = existing_meta
            
            await doc_ref.update(update_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to update API log entry: {e}", exc_info=True)
            return False
    
    async def _add_to_batch(self, doc: APILogFirestoreDocument):
        """Add document to batch for efficient writing."""
        
        async with self._flush_lock:
            self._log_batch.append(doc)
            
            # Check if we should flush
            should_flush = (
                len(self._log_batch) >= APILogConfig.BATCH_SIZE or
                time.time() - self._last_flush_time >= APILogConfig.FLUSH_INTERVAL_SECONDS
            )
            
            if should_flush:
                await self._flush_batch()
    
    async def _flush_batch(self):
        """Flush the current batch to Firestore."""
        
        if not self._log_batch:
            return
        
        try:
            # Create batch write
            batch = self.db.batch()
            
            for doc in self._log_batch:
                doc_ref = self.collection_ref.document()
                batch.set(doc_ref, doc.dict(exclude_unset=True))
            
            # Commit batch
            await batch.commit()
            
            logger.debug(f"Flushed {len(self._log_batch)} API log entries")
            
            # Clear batch
            self._log_batch.clear()
            self._last_flush_time = time.time()
            
        except Exception as e:
            logger.error(f"Failed to flush API log batch: {e}", exc_info=True)
            # Don't clear the batch on error - retry on next flush
    
    async def force_flush(self):
        """Force flush any pending log entries."""
        async with self._flush_lock:
            await self._flush_batch()
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        
        current_time = time.time()
        
        # Reset rate limiting counters every minute
        if current_time - self._last_rate_limit_reset >= 60:
            self._request_counts.clear()
            self._last_rate_limit_reset = current_time
        
        # Check current minute's count
        minute_key = int(current_time // 60)
        current_count = self._request_counts.get(minute_key, 0)
        
        if current_count >= APILogConfig.MAX_LOGS_PER_MINUTE:
            return False
        
        self._request_counts[minute_key] = current_count + 1
        return True
    
    def _truncate_string(self, value: Optional[str], max_length: int) -> Optional[str]:
        """Truncate string to maximum length."""
        if not value:
            return value
        
        if len(value) <= max_length:
            return value
        
        return value[:max_length - 3] + "..."
    
    async def query_logs(self, query: APILogQuery) -> List[Dict[str, Any]]:
        """Query API logs with filtering."""
        
        try:
            collection_query = self.collection_ref
            
            # Apply filters
            if query.service_name:
                collection_query = collection_query.where("svc", "==", query.service_name)
            if query.method:
                collection_query = collection_query.where("method", "==", query.method)
            if query.status_code:
                collection_query = collection_query.where("status", "==", query.status_code)
            if query.user_id:
                collection_query = collection_query.where("uid", "==", query.user_id)
            if query.errors_only:
                collection_query = collection_query.where("status", ">=", 400)
            
            # Time range filtering
            if query.start_time:
                collection_query = collection_query.where("ts", ">=", query.start_time)
            if query.end_time:
                collection_query = collection_query.where("ts", "<=", query.end_time)
            
            # Apply ordering and limits
            collection_query = collection_query.order_by("ts", direction=firestore.Query.DESCENDING)
            collection_query = collection_query.offset(query.offset).limit(query.limit)
            
            # Execute query
            docs = [doc.to_dict() async for doc in collection_query.stream()]
            
            # Filter by response time if specified (post-query filtering)
            if query.min_response_time_ms or query.max_response_time_ms:
                filtered_docs = []
                for doc in docs:
                    resp_time = doc.get("resp_ms")
                    if resp_time is None:
                        continue
                    
                    if query.min_response_time_ms and resp_time < query.min_response_time_ms:
                        continue
                    if query.max_response_time_ms and resp_time > query.max_response_time_ms:
                        continue
                    
                    filtered_docs.append(doc)
                docs = filtered_docs
            
            return docs
            
        except Exception as e:
            logger.error(f"Failed to query API logs: {e}", exc_info=True)
            return []
    
    async def get_api_stats(
        self,
        start_time: datetime,
        end_time: datetime,
        service_name: Optional[str] = None
    ) -> Optional[APILogStats]:
        """Get API statistics for a time period."""
        
        try:
            query = APILogQuery(
                service_name=service_name,
                start_time=start_time,
                end_time=end_time,
                limit=10000  # Get a large sample for stats
            )
            
            logs = await self.query_logs(query)
            
            if not logs:
                return None
            
            # Calculate statistics
            total_requests = len(logs)
            success_requests = len([log for log in logs if log.get("status", 500) < 400])
            error_requests = total_requests - success_requests
            
            response_times = [log.get("resp_ms", 0) for log in logs if log.get("resp_ms") is not None]
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            sorted_times = sorted(response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            p95_response_time = sorted_times[p95_idx] if sorted_times else 0
            p99_response_time = sorted_times[p99_idx] if sorted_times else 0
            
            # Group by method and status
            methods = {}
            statuses = {}
            services = {}
            
            for log in logs:
                method = log.get("method", "unknown")
                status = str(log.get("status", "unknown"))
                service = log.get("svc", "unknown")
                
                methods[method] = methods.get(method, 0) + 1
                statuses[status] = statuses.get(status, 0) + 1
                services[service] = services.get(service, 0) + 1
            
            error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
            
            return APILogStats(
                total_requests=total_requests,
                success_requests=success_requests,
                error_requests=error_requests,
                avg_response_time_ms=avg_response_time,
                p95_response_time_ms=p95_response_time,
                p99_response_time_ms=p99_response_time,
                requests_by_method=methods,
                requests_by_status=statuses,
                requests_by_service=services,
                error_rate_percent=error_rate,
                time_period_start=start_time,
                time_period_end=end_time
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate API stats: {e}", exc_info=True)
            return None
    
    async def cleanup_old_logs(self, retention_days: int = APILogConfig.DEFAULT_RETENTION_DAYS):
        """Clean up old log entries."""
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Query old documents
            old_docs_query = self.collection_ref.where("ts", "<", cutoff_date).limit(1000)
            docs_to_delete = [doc async for doc in old_docs_query.stream()]
            
            if not docs_to_delete:
                logger.info("No old API logs to clean up")
                return
            
            # Delete in batches
            batch = self.db.batch()
            delete_count = 0
            
            for doc in docs_to_delete:
                batch.delete(doc.reference)
                delete_count += 1
                
                # Commit batch when it gets large
                if delete_count % 500 == 0:
                    await batch.commit()
                    batch = self.db.batch()
            
            # Commit remaining deletes
            if delete_count % 500 != 0:
                await batch.commit()
            
            logger.info(f"Cleaned up {delete_count} old API log entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old API logs: {e}", exc_info=True)


# Global service instance
_api_logging_service: Optional[APILoggingService] = None


def get_api_logging_service(service_name: Optional[str] = None) -> Optional[APILoggingService]:
    """Get the global API logging service instance."""
    global _api_logging_service
    
    if _api_logging_service is None and service_name:
        _api_logging_service = APILoggingService(service_name)
    
    return _api_logging_service


def init_api_logging_service(service_name: str) -> APILoggingService:
    """Initialize the global API logging service."""
    global _api_logging_service
    _api_logging_service = APILoggingService(service_name)
    return _api_logging_service


async def shutdown_api_logging_service():
    """Shutdown the API logging service and flush remaining logs."""
    global _api_logging_service
    
    if _api_logging_service:
        await _api_logging_service.force_flush()
        logger.info("API logging service shut down")