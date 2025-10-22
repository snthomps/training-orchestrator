"""
Prometheus metrics for the Training Job Orchestrator
"""

from prometheus_client import Counter, Gauge, Histogram, Info
import time
from functools import wraps
from typing import Callable

# Job metrics
training_jobs_total = Counter(
    'training_jobs_total',
    'Total number of training jobs created',
    ['job_name']
)

training_jobs_completed = Gauge(
    'training_jobs_completed',
    'Number of completed training jobs',
    ['job_name']
)

training_jobs_failed = Gauge(
    'training_jobs_failed', 
    'Number of failed training jobs',
    ['job_name']
)

training_jobs_pending = Gauge(
    'training_jobs_pending',
    'Number of pending training jobs'
)

training_jobs_running = Gauge(
    'training_jobs_running',
    'Number of running training jobs'
)

training_jobs_retrying = Gauge(
    'training_jobs_retrying',
    'Number of jobs being retried'
)

training_job_retry_count = Gauge(
    'training_job_retry_count',
    'Number of retry attempts for a job',
    ['job_id', 'job_name']
)

training_jobs_duration_seconds = Histogram(
    'training_jobs_duration_seconds',
    'Duration of training jobs in seconds',
    ['job_name', 'status'],
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 28800, 86400)
)

training_job_started_timestamp = Gauge(
    'training_job_started_timestamp',
    'Timestamp when job started',
    ['job_id', 'job_name']
)

training_job_info = Info(
    'training_job',
    'Information about training jobs',
)

# Notification metrics
notification_sent_total = Counter(
    'notification_sent_total',
    'Total notifications sent',
    ['channel', 'job_id']
)

notification_failures_total = Counter(
    'notification_failures_total',
    'Total notification failures',
    ['channel', 'job_id', 'error_type']
)

# Database metrics
database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

database_connection_errors_total = Counter(
    'database_connection_errors_total',
    'Database connection errors'
)

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# Checkpoint metrics
checkpoint_save_total = Counter(
    'checkpoint_save_total',
    'Total checkpoints saved',
    ['job_id']
)

checkpoint_save_failures = Counter(
    'checkpoint_save_failures',
    'Failed checkpoint saves',
    ['job_id']
)

checkpoint_load_total = Counter(
    'checkpoint_load_total',
    'Total checkpoints loaded',
    ['job_id']
)


def track_time(metric: Histogram, labels: dict = None):
    """Decorator to track execution time"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def update_job_metrics(jobs: dict):
    """Update all job-related metrics"""
    from orchestrator import JobStatus
    
    pending = sum(1 for j in jobs.values() if j.status == JobStatus.PENDING)
    running = sum(1 for j in jobs.values() if j.status == JobStatus.RUNNING)
    completed = sum(1 for j in jobs.values() if j.status == JobStatus.COMPLETED)
    failed = sum(1 for j in jobs.values() if j.status == JobStatus.FAILED)
    retrying = sum(1 for j in jobs.values() if j.status == JobStatus.RETRYING)
    
    training_jobs_pending.set(pending)
    training_jobs_running.set(running)
    training_jobs_retrying.set(retrying)
    
    for job in jobs.values():
        if job.status == JobStatus.COMPLETED:
            training_jobs_completed.labels(job_name=job.name).set(1)
        elif job.status == JobStatus.FAILED:
            training_jobs_failed.labels(job_name=job.name).set(1)
        
        training_job_retry_count.labels(
            job_id=job.job_id,
            job_name=job.name
        ).set(job.retry_count)