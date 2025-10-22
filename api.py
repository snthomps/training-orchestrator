from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import logging
from enum import Enum

# Import our orchestrator
from orchestrator import JobOrchestrator, TrainingJob, JobStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Training Job Orchestrator API",
    description="API for managing ML training jobs with automatic retry and notifications",
    version="1.0.0"
)

# Global orchestrator instance
orchestrator = JobOrchestrator()


# Pydantic models
class JobCreate(BaseModel):
    name: str
    image: str
    command: List[str]
    schedule: str
    max_retries: int = 3
    checkpoint_path: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    name: str
    status: str
    retry_count: int
    max_retries: int
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check if orchestrator is initialized
        if orchestrator is None:
            raise Exception("Orchestrator not initialized")
        return {"status": "ready", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


# Job management endpoints
@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(job: JobCreate, background_tasks: BackgroundTasks):
    """Create a new training job"""
    try:
        job_id = f"job-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        training_job = TrainingJob(
            job_id=job_id,
            name=job.name,
            image=job.image,
            command=job.command,
            schedule=job.schedule,
            max_retries=job.max_retries,
            checkpoint_path=job.checkpoint_path
        )
        
        orchestrator.register_job(training_job)
        
        # Start job in background
        background_tasks.add_task(orchestrator.run_job, training_job)
        
        logger.info(f"Created job {job_id}")
        
        return JobResponse(
            job_id=training_job.job_id,
            name=training_job.name,
            status=training_job.status.value,
            retry_count=training_job.retry_count,
            max_retries=training_job.max_retries,
            started_at=training_job.started_at,
            completed_at=training_job.completed_at,
            error_message=training_job.error_message
        )
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(status: Optional[str] = None, limit: int = 100):
    """List all training jobs with optional status filter"""
    try:
        jobs = list(orchestrator.jobs.values())
        
        # Filter by status if provided
        if status:
            try:
                status_enum = JobStatus(status.lower())
                jobs = [j for j in jobs if j.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Apply limit
        jobs = jobs[:limit]
        
        job_responses = [
            JobResponse(
                job_id=job.job_id,
                name=job.name,
                status=job.status.value,
                retry_count=job.retry_count,
                max_retries=job.max_retries,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message
            )
            for job in jobs
        ]
        
        return JobListResponse(jobs=job_responses, total=len(orchestrator.jobs))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get details of a specific job"""
    job = orchestrator.jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobResponse(
        job_id=job.job_id,
        name=job.name,
        status=job.status.value,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message
    )


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    job = orchestrator.jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status == JobStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Cannot delete running job")
    
    del orchestrator.jobs[job_id]
    logger.info(f"Deleted job {job_id}")
    
    return {"message": f"Job {job_id} deleted successfully"}


@app.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, background_tasks: BackgroundTasks):
    """Manually retry a failed job"""
    job = orchestrator.jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status not in [JobStatus.FAILED, JobStatus.COMPLETED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Job must be in FAILED or COMPLETED status to retry. Current: {job.status.value}"
        )
    
    # Reset job state
    job.status = JobStatus.PENDING
    job.retry_count = 0
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    
    # Start job in background
    background_tasks.add_task(orchestrator.run_job, job)
    
    logger.info(f"Retrying job {job_id}")
    
    return {"message": f"Job {job_id} queued for retry"}


@app.get("/stats")
async def get_stats():
    """Get overall statistics"""
    jobs = list(orchestrator.jobs.values())
    
    stats = {
        "total_jobs": len(jobs),
        "pending": sum(1 for j in jobs if j.status == JobStatus.PENDING),
        "running": sum(1 for j in jobs if j.status == JobStatus.RUNNING),
        "completed": sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
        "failed": sum(1 for j in jobs if j.status == JobStatus.FAILED),
        "retrying": sum(1 for j in jobs if j.status == JobStatus.RETRYING),
    }
    
    return stats


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    metrics_output = generate_latest()
    return JSONResponse(
        content=metrics_output.decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )


def main():
    """Main entry point for package"""
    import sys
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv('API_PORT', 8080)),
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )


if __name__ == "__main__":
    main()