#!/usr/bin/env python3
"""
Advanced scheduler with cron support, job dependencies, and priority queuing.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
import redis
import json

from orchestrator import JobOrchestrator, TrainingJob, JobStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ScheduledJob:
    """Enhanced job with scheduling information"""
    job: TrainingJob
    priority: JobPriority = JobPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    max_concurrent: int = 1
    timeout_minutes: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


class JobScheduler:
    """Advanced job scheduler with dependency management"""
    
    def __init__(self, orchestrator: JobOrchestrator):
        self.orchestrator = orchestrator
        self.scheduler = AsyncIOScheduler()
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}
        self.running_jobs: Set[str] = set()
        self.job_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # Redis for distributed locking
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.max_workers = int(os.getenv('MAX_WORKERS', '5'))
        self.workers: List[asyncio.Task] = []
    
    def add_scheduled_job(self, scheduled_job: ScheduledJob):
        """Register a job with the scheduler"""
        job = scheduled_job.job
        job_id = job.job_id
        
        if not scheduled_job.enabled:
            logger.info(f"Job {job_id} is disabled, skipping")
            return
        
        self.scheduled_jobs[job_id] = scheduled_job
        self.orchestrator.register_job(job)
        
        # Parse cron schedule
        try:
            cron = CronTrigger.from_crontab(job.schedule)
            self.scheduler.add_job(
                self._schedule_job,
                trigger=cron,
                args=[job_id],
                id=job_id,
                name=job.name,
                replace_existing=True
            )
            logger.info(f"Scheduled job {job_id} with schedule: {job.schedule}")
        except Exception as e:
            logger.error(f"Failed to schedule job {job_id}: {e}")
    
    def remove_scheduled_job(self, job_id: str):
        """Remove a scheduled job"""
        if job_id in self.scheduled_jobs:
            del self.scheduled_jobs[job_id]
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job {job_id}")
    
    async def _schedule_job(self, job_id: str):
        """Called by APScheduler when job should run"""
        scheduled_job = self.scheduled_jobs.get(job_id)
        if not scheduled_job:
            logger.warning(f"Job {job_id} not found in scheduled jobs")
            return
        
        # Check dependencies
        if not await self._check_dependencies(scheduled_job):
            logger.warning(f"Job {job_id} dependencies not met, skipping")
            return
        
        # Check concurrency limit
        if not await self._check_concurrency(scheduled_job):
            logger.warning(f"Job {job_id} concurrency limit reached, queuing")
        
        # Add to priority queue
        priority = -scheduled_job.priority.value  # Negative for max heap
        await self.job_queue.put((priority, datetime.now(), job_id))
        logger.info(f"Job {job_id} queued with priority {scheduled_job.priority.name}")
    
    async def _check_dependencies(self, scheduled_job: ScheduledJob) -> bool:
        """Check if job dependencies are satisfied"""
        if not scheduled_job.dependencies:
            return True
        
        for dep_job_id in scheduled_job.dependencies:
            dep_job = self.orchestrator.jobs.get(dep_job_id)
            if not dep_job or dep_job.status != JobStatus.COMPLETED:
                logger.info(f"Dependency {dep_job_id} not completed")
                return False
        
        return True
    
    async def _check_concurrency(self, scheduled_job: ScheduledJob) -> bool:
        """Check if job can run based on concurrency limits"""
        job_id = scheduled_job.job.job_id
        
        # Check max concurrent for this specific job
        running_count = sum(
            1 for jid in self.running_jobs 
            if jid == job_id
        )
        
        if running_count >= scheduled_job.max_concurrent:
            return False
        
        # Check global worker limit
        if len(self.running_jobs) >= self.max_workers:
            return False
        
        return True
    
    async def _worker(self, worker_id: int):
        """Worker coroutine that processes jobs from queue"""
        logger.info(f"Worker {worker_id} started")
        
        while True:
            try:
                # Get next job from queue
                priority, queued_at, job_id = await self.job_queue.get()
                
                scheduled_job = self.scheduled_jobs.get(job_id)
                if not scheduled_job:
                    logger.warning(f"Worker {worker_id}: Job {job_id} not found")
                    continue
                
                # Acquire distributed lock
                lock_key = f"job_lock:{job_id}"
                if not self.redis_client.set(lock_key, worker_id, nx=True, ex=3600):
                    logger.warning(f"Worker {worker_id}: Could not acquire lock for {job_id}")
                    continue
                
                try:
                    # Mark as running
                    self.running_jobs.add(job_id)
                    
                    wait_time = (datetime.now() - queued_at).total_seconds()
                    logger.info(
                        f"Worker {worker_id}: Starting job {job_id} "
                        f"(waited {wait_time:.1f}s)"
                    )
                    
                    # Run the job with timeout
                    if scheduled_job.timeout_minutes:
                        timeout = scheduled_job.timeout_minutes * 60
                        await asyncio.wait_for(
                            self.orchestrator.run_job(scheduled_job.job),
                            timeout=timeout
                        )
                    else:
                        await self.orchestrator.run_job(scheduled_job.job)
                    
                    logger.info(f"Worker {worker_id}: Completed job {job_id}")
                    
                except asyncio.TimeoutError:
                    logger.error(f"Worker {worker_id}: Job {job_id} timed out")
                    scheduled_job.job.status = JobStatus.FAILED
                    scheduled_job.job.error_message = "Job timeout exceeded"
                    
                except Exception as e:
                    logger.error(f"Worker {worker_id}: Job {job_id} failed: {e}")
                
                finally:
                    # Release lock and remove from running
                    self.redis_client.delete(lock_key)
                    self.running_jobs.discard(job_id)
                    self.job_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def start(self):
        """Start the scheduler and workers"""
        logger.info("Starting job scheduler...")
        
        # Start APScheduler
        self.scheduler.start()
        
        # Start worker coroutines
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"Scheduler started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the scheduler gracefully"""
        logger.info("Stopping scheduler...")
        
        # Stop accepting new jobs
        self.scheduler.shutdown()
        
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for running jobs to complete
        await self.job_queue.join()
        
        logger.info("Scheduler stopped")
    
    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Get next scheduled run time for a job"""
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None
    
    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            "running": self.scheduler.running,
            "num_scheduled_jobs": len(self.scheduled_jobs),
            "num_running_jobs": len(self.running_jobs),
            "queue_size": self.job_queue.qsize(),
            "num_workers": len(self.workers),
            "jobs": [
                {
                    "job_id": job_id,
                    "name": sj.job.name,
                    "priority": sj.priority.name,
                    "next_run": self.get_next_run_time(job_id),
                    "enabled": sj.enabled
                }
                for job_id, sj in self.scheduled_jobs.items()
            ]
        }
    
    async def trigger_job_now(self, job_id: str):
        """Manually trigger a job to run immediately"""
        scheduled_job = self.scheduled_jobs.get(job_id)
        if not scheduled_job:
            raise ValueError(f"Job {job_id} not found")
        
        # Add to queue with highest priority
        await self.job_queue.put((
            -JobPriority.CRITICAL.value,
            datetime.now(),
            job_id
        ))
        logger.info(f"Job {job_id} triggered manually")


# Example usage and configuration
async def main():
    """Example usage of the scheduler"""
    import os
    
    # Create orchestrator
    orchestrator = JobOrchestrator()
    
    # Create scheduler
    scheduler = JobScheduler(orchestrator)
    
    # Define jobs with dependencies and priorities
    job1 = TrainingJob(
        job_id="data-preprocessing",
        name="Data Preprocessing",
        image="preprocess:latest",
        command=["python", "preprocess.py"],
        schedule="0 0 * * *",  # Daily at midnight
        max_retries=2
    )
    
    job2 = TrainingJob(
        job_id="model-training",
        name="Model Training",
        image="trainer:latest",
        command=["python", "train.py"],
        schedule="0 2 * * *",  # Daily at 2 AM
        max_retries=3,
        checkpoint_path="/checkpoints/model"
    )
    
    job3 = TrainingJob(
        job_id="model-evaluation",
        name="Model Evaluation",
        image="evaluator:latest",
        command=["python", "evaluate.py"],
        schedule="0 4 * * *",  # Daily at 4 AM
        max_retries=1
    )
    
    # Add jobs with scheduling configuration
    scheduler.add_scheduled_job(ScheduledJob(
        job=job1,
        priority=JobPriority.HIGH,
        timeout_minutes=60,
        tags=["preprocessing", "daily"]
    ))
    
    scheduler.add_scheduled_job(ScheduledJob(
        job=job2,
        priority=JobPriority.NORMAL,
        dependencies=["data-preprocessing"],  # Depends on job1
        timeout_minutes=240,
        tags=["training", "daily"]
    ))
    
    scheduler.add_scheduled_job(ScheduledJob(
        job=job3,
        priority=JobPriority.NORMAL,
        dependencies=["model-training"],  # Depends on job2
        timeout_minutes=30,
        tags=["evaluation", "daily"]
    ))
    
    # Start scheduler
    await scheduler.start()
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(60)
            status = scheduler.get_scheduler_status()
            logger.info(f"Scheduler status: {status}")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await scheduler.stop()


if __name__ == "__main__":
    import os
    asyncio.run(main())