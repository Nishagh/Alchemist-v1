"""
Background task scheduler for monitoring
"""

import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from .health_monitor import HealthMonitor
from ..config.services import MONITORING_CONFIG

logger = logging.getLogger(__name__)

class MonitoringScheduler:
    """
    Scheduler for automated monitoring tasks
    """
    
    def __init__(self, health_monitor: HealthMonitor):
        self.health_monitor = health_monitor
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled monitoring jobs"""
        
        # Main health check job - runs every 30 seconds
        self.scheduler.add_job(
            func=self._health_check_job,
            trigger=IntervalTrigger(seconds=MONITORING_CONFIG["check_interval_seconds"]),
            id="health_check",
            name="Health Check All Services",
            replace_existing=True,
            max_instances=1
        )
        
        # Summary generation job - runs every 5 minutes
        self.scheduler.add_job(
            func=self._summary_job,
            trigger=IntervalTrigger(minutes=5),
            id="summary_generation",
            name="Generate Monitoring Summary",
            replace_existing=True,
            max_instances=1
        )
        
        # Data cleanup job - runs daily at 2 AM
        self.scheduler.add_job(
            func=self._cleanup_job,
            trigger=CronTrigger(hour=2, minute=0),
            id="data_cleanup",
            name="Cleanup Old Data",
            replace_existing=True,
            max_instances=1
        )
        
        # Heartbeat job - runs every minute to update scheduler status
        self.scheduler.add_job(
            func=self._heartbeat_job,
            trigger=IntervalTrigger(minutes=1),
            id="heartbeat",
            name="Scheduler Heartbeat",
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("Monitoring jobs configured")
    
    async def _health_check_job(self):
        """Execute health checks for all services"""
        try:
            logger.debug("Starting scheduled health check")
            start_time = datetime.utcnow()
            
            results = await self.health_monitor.check_all_services()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            healthy_count = sum(1 for r in results if r.status.value == "healthy")
            
            logger.info(
                f"Health check completed: {healthy_count}/{len(results)} services healthy "
                f"(duration: {duration:.1f}s)"
            )
            
        except Exception as e:
            logger.error(f"Health check job failed: {e}")
    
    async def _summary_job(self):
        """Generate and store monitoring summary"""
        try:
            logger.debug("Starting summary generation")
            
            summary = await self.health_monitor.get_monitoring_summary()
            
            logger.info(
                f"Summary generated: {summary.healthy_services}/{summary.total_services} healthy, "
                f"avg response: {summary.average_response_time_ms:.1f}ms, "
                f"uptime: {summary.uptime_percentage:.1f}%"
            )
            
        except Exception as e:
            logger.error(f"Summary generation job failed: {e}")
    
    async def _cleanup_job(self):
        """Cleanup old monitoring data"""
        try:
            logger.info("Starting data cleanup job")
            
            await self.health_monitor.cleanup_old_data()
            
            logger.info("Data cleanup completed")
            
        except Exception as e:
            logger.error(f"Data cleanup job failed: {e}")
    
    async def _heartbeat_job(self):
        """Scheduler heartbeat to confirm it's running"""
        try:
            active_jobs = len(self.scheduler.get_jobs())
            logger.debug(f"Scheduler heartbeat: {active_jobs} active jobs")
            
            # Store heartbeat in Firestore to track scheduler health
            await self.health_monitor.firebase_client.db.collection('monitoring').document('scheduler').set({
                'last_heartbeat': datetime.utcnow(),
                'active_jobs': active_jobs,
                'status': 'running'
            })
            
        except Exception as e:
            logger.error(f"Heartbeat job failed: {e}")
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Monitoring scheduler started")
            
            # Log scheduled jobs
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'Not scheduled'
                logger.info(f"Job '{job.name}' (ID: {job.id}) - Next run: {next_run}")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Monitoring scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
    
    def get_job_status(self) -> dict:
        """Get status of all scheduled jobs"""
        try:
            jobs_status = {}
            jobs = self.scheduler.get_jobs()
            
            for job in jobs:
                jobs_status[job.id] = {
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'max_instances': job.max_instances,
                    'trigger': str(job.trigger)
                }
            
            return {
                'scheduler_running': self.scheduler.running,
                'total_jobs': len(jobs),
                'jobs': jobs_status
            }
            
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return {'error': str(e)}
    
    async def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.warning(f"Job '{job_id}' not found")
                return False
            
            # Run the job function directly
            if job_id == "health_check":
                await self._health_check_job()
            elif job_id == "summary_generation":
                await self._summary_job()
            elif job_id == "data_cleanup":
                await self._cleanup_job()
            elif job_id == "heartbeat":
                await self._heartbeat_job()
            else:
                logger.warning(f"Unknown job ID: {job_id}")
                return False
            
            logger.info(f"Manually triggered job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger job '{job_id}': {e}")
            return False