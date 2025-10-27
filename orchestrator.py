"""
Updated Training Job Orchestrator with Database Integration
"""
import os
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiohttp import web
from sqlalchemy import and_, text

# Database imports
try:
    from database import get_db_context, init_db
    from models import TrainingJobModel
    DATABASE_ENABLED = True
except ImportError:
    DATABASE_ENABLED = False
    logging.warning("Database module not available, running in standalone mode")

# Import metrics
try:
    from metrics import (
        training_jobs_total, training_job_started_timestamp,
        training_jobs_duration_seconds, notification_sent_total,
        notification_failures_total, update_job_metrics
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logging.warning("Metrics module not available, metrics disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TrainingJob:
    job_id: str
    name: str
    image: str
    command: List[str]
    schedule: str
    max_retries: int = 3
    retry_count: int = 0
    checkpoint_path: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def from_db_model(cls, db_job: 'TrainingJobModel') -> 'TrainingJob':
        """Create TrainingJob from database model"""
        return cls(
            job_id=db_job.job_id,
            name=db_job.name,
            image=db_job.image,
            command=db_job.command,
            schedule=db_job.schedule,
            max_retries=db_job.max_retries,
            retry_count=db_job.retry_count,
            checkpoint_path=db_job.checkpoint_path,
            status=JobStatus(db_job.status),
            started_at=db_job.started_at.isoformat() if db_job.started_at else None,
            completed_at=db_job.completed_at.isoformat() if db_job.completed_at else None,
            error_message=db_job.error_message
        )


class NotificationService:
    """Handle Slack and Email notifications"""
    
    def __init__(self):
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': os.getenv('SENDER_EMAIL'),
            'sender_password': os.getenv('SENDER_PASSWORD'),
            'recipient_emails': os.getenv('RECIPIENT_EMAILS', '').split(',')
        }
    
    def send_slack_notification(self, job: TrainingJob, message: str):
        """Send notification to Slack"""
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured")
            return
        
        color = {
            JobStatus.COMPLETED: "good",
            JobStatus.FAILED: "danger",
            JobStatus.RETRYING: "warning"
        }.get(job.status, "#808080")
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"Training Job: {job.name}",
                "fields": [
                    {"title": "Job ID", "value": job.job_id, "short": True},
                    {"title": "Status", "value": job.status.value, "short": True},
                    {"title": "Retry Count", "value": str(job.retry_count), "short": True},
                    {"title": "Message", "value": message, "short": False}
                ],
                "timestamp": int(time.time())
            }]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Slack notification sent for job {job.job_id}")
            
            if METRICS_ENABLED:
                notification_sent_total.labels(
                    channel='slack',
                    job_id=job.job_id
                ).inc()
                
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            
            if METRICS_ENABLED:
                notification_failures_total.labels(
                    channel='slack',
                    job_id=job.job_id,
                    error_type=type(e).__name__
                ).inc()
    
    def send_email_notification(self, job: TrainingJob, message: str):
        """Send notification via email"""
        if not self.email_config['sender_email']:
            logger.warning("Email not configured")
            return
        
        subject = f"Training Job {job.status.value.upper()}: {job.name}"
        
        body = f"""
        <html>
        <body>
            <h2>Training Job Status Update</h2>
            <table border="1" cellpadding="5">
                <tr><th>Job ID</th><td>{job.job_id}</td></tr>
                <tr><th>Name</th><td>{job.name}</td></tr>
                <tr><th>Status</th><td><strong>{job.status.value}</strong></td></tr>
                <tr><th>Retry Count</th><td>{job.retry_count}/{job.max_retries}</td></tr>
                <tr><th>Started At</th><td>{job.started_at or 'N/A'}</td></tr>
                <tr><th>Completed At</th><td>{job.completed_at or 'N/A'}</td></tr>
            </table>
            <p><strong>Message:</strong> {message}</p>
            {f'<p><strong>Error:</strong> {job.error_message}</p>' if job.error_message else ''}
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_config['sender_email']
        msg['To'] = ', '.join(self.email_config['recipient_emails'])
        
        msg.attach(MIMEText(body, 'html'))
        
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], 
                            self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                           self.email_config['sender_password'])
                server.send_message(msg)
            logger.info(f"Email notification sent for job {job.job_id}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def notify(self, job: TrainingJob, message: str):
        """Send notifications via all configured channels"""
        self.send_slack_notification(job, message)
        self.send_email_notification(job, message)


class JobOrchestrator:
    """Main orchestrator for training jobs with database integration"""
    
    def __init__(self):
        self.jobs: Dict[str, TrainingJob] = {}
        self.notification_service = NotificationService()
        self.k8s_namespace = os.getenv('K8S_NAMESPACE', 'default')
        self.database_enabled = DATABASE_ENABLED
    
    def load_jobs_from_database(self):
        """Load jobs from database"""
        if not self.database_enabled:
            logger.warning("Database not enabled, skipping job load")
            return
        
        try:
            with get_db_context() as db:
                # Load all pending and running jobs
                db_jobs = db.query(TrainingJobModel).filter(
                    TrainingJobModel.status.in_(['pending', 'running', 'retrying'])
                ).all()
                
                for db_job in db_jobs:
                    job = TrainingJob.from_db_model(db_job)
                    self.jobs[job.job_id] = job
                    logger.info(f"Loaded job {job.job_id} from database: {job.name}")
                
        except Exception as e:
            logger.error(f"Failed to load jobs from database: {e}")
    
    def sync_job_to_database(self, job: TrainingJob):
        """Sync job status to database"""
        if not self.database_enabled:
            return
        
        try:
            with get_db_context() as db:
                db_job = db.query(TrainingJobModel).filter(
                    TrainingJobModel.job_id == job.job_id
                ).first()
                
                if db_job:
                    db_job.status = job.status.value
                    db_job.retry_count = job.retry_count
                    db_job.error_message = job.error_message
                    
                    if job.started_at:
                        db_job.started_at = datetime.fromisoformat(job.started_at)
                    if job.completed_at:
                        db_job.completed_at = datetime.fromisoformat(job.completed_at)
                    
                    logger.debug(f"Synced job {job.job_id} to database")
                
        except Exception as e:
            logger.error(f"Failed to sync job {job.job_id} to database: {e}")
    
    def register_job(self, job: TrainingJob):
        """Register a new training job"""
        self.jobs[job.job_id] = job
        logger.info(f"Registered job {job.job_id}: {job.name}")
        
        if METRICS_ENABLED:
            training_jobs_total.labels(
                job_name=job.name
            ).inc()
    
    def create_k8s_job_manifest(self, job: TrainingJob) -> Dict:
        """Generate Kubernetes Job manifest"""
        command = job.command.copy()
        
        if job.checkpoint_path and job.retry_count > 0:
            command.extend(['--resume-from-checkpoint', job.checkpoint_path])
        
        manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"{job.name}-{job.job_id}",
                "namespace": self.k8s_namespace,
                "labels": {
                    "app": "training-orchestrator",
                    "job-id": job.job_id,
                    "job-name": job.name
                }
            },
            "spec": {
                "backoffLimit": 0,
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "training-orchestrator",
                            "job-id": job.job_id
                        }
                    },
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [{
                            "name": "trainer",
                            "image": job.image,
                            "command": command,
                            "env": [
                                {"name": "JOB_ID", "value": job.job_id},
                                {"name": "CHECKPOINT_DIR", "value": job.checkpoint_path or "/checkpoints"}
                            ],
                            "volumeMounts": [{
                                "name": "checkpoint-storage",
                                "mountPath": "/checkpoints"
                            }],
                            "resources": {
                                "requests": {
                                    "memory": "4Gi",
                                    "cpu": "2"
                                },
                                "limits": {
                                    "memory": "8Gi",
                                    "cpu": "4",
                                    "nvidia.com/gpu": "1"
                                }
                            }
                        }],
                        "volumes": [{
                            "name": "checkpoint-storage",
                            "persistentVolumeClaim": {
                                "claimName": "training-checkpoints"
                            }
                        }]
                    }
                }
            }
        }
        return manifest
    
    async def run_job(self, job: TrainingJob) -> bool:
        """Execute a training job"""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now().isoformat()
        logger.info(f"Starting job {job.job_id}: {job.name}")
        
        # Sync to database
        self.sync_job_to_database(job)
        
        if METRICS_ENABLED:
            training_job_started_timestamp.labels(
                job_id=job.job_id,
                job_name=job.name
            ).set(time.time())
            update_job_metrics(self.jobs)
        
        start_time = time.time()
        
        try:
            manifest = self.create_k8s_job_manifest(job)
            self._submit_k8s_job(manifest)
            success = await self._monitor_job(job)
            
            if success:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now().isoformat()
                logger.info(f"Job {job.job_id} completed successfully")
                
                self.sync_job_to_database(job)
                
                if METRICS_ENABLED:
                    duration = time.time() - start_time
                    training_jobs_duration_seconds.labels(
                        job_name=job.name,
                        status='completed'
                    ).observe(duration)
                    update_job_metrics(self.jobs)
                
                self.notification_service.notify(
                    job, 
                    f"Training job completed successfully in {self._get_duration(job)}"
                )
                return True
            else:
                raise Exception("Job failed")
                
        except Exception as e:
            job.error_message = str(e)
            logger.error(f"Job {job.job_id} failed: {e}")
            
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.RETRYING
                logger.info(f"Retrying job {job.job_id} (attempt {job.retry_count}/{job.max_retries})")
                
                self.sync_job_to_database(job)
                
                self.notification_service.notify(
                    job,
                    f"Job failed, retrying (attempt {job.retry_count}/{job.max_retries}): {str(e)}"
                )
                
                await asyncio.sleep(min(60 * (2 ** job.retry_count), 3600))
                return await self.run_job(job)
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now().isoformat()
                
                self.sync_job_to_database(job)
                
                if METRICS_ENABLED:
                    duration = time.time() - start_time
                    training_jobs_duration_seconds.labels(
                        job_name=job.name,
                        status='failed'
                    ).observe(duration)
                    update_job_metrics(self.jobs)
                
                self.notification_service.notify(
                    job,
                    f"Job failed after {job.max_retries} retries: {str(e)}"
                )
                return False
    
    def _submit_k8s_job(self, manifest: Dict):
        """Submit job to Kubernetes (mock implementation)"""
        logger.info(f"Submitting K8s job: {manifest['metadata']['name']}")
    
    async def _monitor_job(self, job: TrainingJob) -> bool:
        """Monitor job execution (mock implementation)"""
        logger.info(f"Monitoring job {job.job_id}")
        await asyncio.sleep(5)
        return True
    
    def _get_duration(self, job: TrainingJob) -> str:
        """Calculate job duration"""
        if not job.started_at or not job.completed_at:
            return "N/A"
        start = datetime.fromisoformat(job.started_at)
        end = datetime.fromisoformat(job.completed_at)
        duration = end - start
        return str(duration)
    
    async def schedule_jobs(self):
        """Main scheduling loop"""
        logger.info("Starting job scheduler")
        
        # Load jobs from database on startup
        if self.database_enabled:
            self.load_jobs_from_database()
        
        while True:
            try:
                # Reload jobs from database periodically
                if self.database_enabled:
                    self.load_jobs_from_database()
                
                # Check each job's schedule
                for job_id, job in list(self.jobs.items()):
                    if job.status == JobStatus.PENDING:
                        logger.info(f"Scheduling job {job_id}")
                        asyncio.create_task(self.run_job(job))
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)


# Health Check API
async def health_check(request):
    """Health check endpoint"""
    orchestrator = request.app['orchestrator']
    
    db_connected = False
    if DATABASE_ENABLED:
        try:
            with get_db_context() as db:
                db.execute(text("SELECT 1"))
                db_connected = True
        except:
            pass
    
    return web.json_response({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "training-orchestrator",
        "database_enabled": DATABASE_ENABLED,
        "database_connected": db_connected
    })


async def status(request):
    """Status endpoint showing job information"""
    orchestrator = request.app['orchestrator']
    
    jobs_status = {
        job_id: {
            "name": job.name,
            "status": job.status.value,
            "retry_count": job.retry_count,
            "started_at": job.started_at,
            "completed_at": job.completed_at
        }
        for job_id, job in orchestrator.jobs.items()
    }
    
    return web.json_response({
        "status": "running",
        "jobs": jobs_status,
        "total_jobs": len(orchestrator.jobs)
    })


async def start_health_server(orchestrator: JobOrchestrator, port: int = 8080):
    """Start the health check web server"""
    app = web.Application()
    app['orchestrator'] = orchestrator
    
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status)
    app.router.add_get('/', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Health check server started on port {port}")
    
    while True:
        await asyncio.sleep(3600)


async def main():
    """Main entry point"""
    # Initialize database if enabled
    if DATABASE_ENABLED:
        logger.info("Initializing database...")
        init_db()
    
    orchestrator = JobOrchestrator()
    
    # If no database, register example jobs (backward compatibility)
    if not DATABASE_ENABLED:
        logger.info("Running in standalone mode with example jobs")
        
        job1 = TrainingJob(
            job_id="train-001",
            name="resnet50-training",
            image="gcr.io/my-project/trainer:latest",
            command=["python", "train.py", "--model", "resnet50"],
            schedule="0 2 * * *",
            max_retries=3,
            checkpoint_path="/checkpoints/resnet50"
        )
        
        job2 = TrainingJob(
            job_id="train-002",
            name="bert-finetuning",
            image="gcr.io/my-project/nlp-trainer:latest",
            command=["python", "finetune.py", "--model", "bert-base"],
            schedule="0 3 * * *",
            max_retries=2,
            checkpoint_path="/checkpoints/bert"
        )
        
        orchestrator.register_job(job1)
        orchestrator.register_job(job2)
    
    # Start both the health server and job scheduler concurrently
    await asyncio.gather(
        start_health_server(orchestrator, port=8080),
        orchestrator.schedule_jobs()
    )


if __name__ == "__main__":
    asyncio.run(main())
