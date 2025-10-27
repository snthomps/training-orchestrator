"""
FastAPI REST API for Training Job Orchestrator
"""
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from database import get_db, init_db, engine
from models import TrainingJobModel
from schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    StatsResponse, HealthResponse, ErrorResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Training Job Orchestrator API",
    description="REST API for managing ML training jobs with automated scheduling and failure recovery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/", response_model=HealthResponse)
async def root(db: Session = Depends(get_db)):
    """Root endpoint - returns health status"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "timestamp": datetime.now().isoformat(),
        "service": "training-orchestrator-api",
        "database_connected": db_connected
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        db_connected = False
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "timestamp": datetime.now().isoformat(),
        "service": "training-orchestrator-api",
        "database_connected": db_connected
    }


@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """
    Create a new training job
    
    - **name**: Unique name for the job
    - **image**: Docker image to use
    - **command**: Command to run in the container
    - **schedule**: Cron expression for scheduling
    - **max_retries**: Maximum number of retry attempts
    - **checkpoint_path**: Optional path to checkpoint directory
    """
    # Check if job with same name already exists
    existing_job = db.query(TrainingJobModel).filter(
        TrainingJobModel.name == job.name
    ).first()
    
    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job with name '{job.name}' already exists"
        )
    
    # Generate unique job ID
    job_id = f"train-{uuid.uuid4().hex[:8]}"
    
    # Create new job
    db_job = TrainingJobModel(
        job_id=job_id,
        name=job.name,
        image=job.image,
        command=job.command,
        schedule=job.schedule,
        max_retries=job.max_retries,
        checkpoint_path=job.checkpoint_path,
        status="pending"
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    logger.info(f"Created job {job_id}: {job.name}")
    
    return db_job.to_dict()


@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List all training jobs with optional filtering and pagination
    
    - **status**: Filter by job status (pending, running, completed, failed, retrying)
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page
    """
    query = db.query(TrainingJobModel)
    
    # Apply status filter
    if status_filter:
        query = query.filter(TrainingJobModel.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    jobs = query.order_by(TrainingJobModel.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "jobs": [job.to_dict() for job in jobs],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific training job
    """
    job = db.query(TrainingJobModel).filter(TrainingJobModel.job_id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return job.to_dict()


@app.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, job_update: JobUpdate, db: Session = Depends(get_db)):
    """
    Update a training job
    
    Note: Cannot update jobs that are currently running
    """
    job = db.query(TrainingJobModel).filter(TrainingJobModel.job_id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Prevent updating running jobs
    if job.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update a running job"
        )
    
    # Update fields
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    
    logger.info(f"Updated job {job_id}")
    
    return job.to_dict()


@app.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """
    Delete a training job
    
    Note: Cannot delete jobs that are currently running
    """
    job = db.query(TrainingJobModel).filter(TrainingJobModel.job_id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Prevent deleting running jobs
    if job.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a running job"
        )
    
    db.delete(job)
    db.commit()
    
    logger.info(f"Deleted job {job_id}")
    
    return None


@app.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: str, db: Session = Depends(get_db)):
    """
    Manually retry a failed job
    
    Resets the job to pending status and clears error message
    """
    job = db.query(TrainingJobModel).filter(TrainingJobModel.job_id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Can only retry failed or completed jobs
    if job.status not in ["failed", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Can only retry failed or completed jobs (current status: {job.status})"
        )
    
    # Reset job status
    job.status = "pending"
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    
    db.commit()
    db.refresh(job)
    
    logger.info(f"Manually retrying job {job_id}")
    
    return job.to_dict()


@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """
    Get overall statistics about training jobs
    """
    total_jobs = db.query(TrainingJobModel).count()
    
    stats = {}
    for status_value in ["pending", "running", "completed", "failed", "retrying"]:
        count = db.query(TrainingJobModel).filter(
            TrainingJobModel.status == status_value
        ).count()
        stats[status_value] = count
    
    return {
        "total_jobs": total_jobs,
        "pending": stats.get("pending", 0),
        "running": stats.get("running", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
        "retrying": stats.get("retrying", 0)
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_type": "HTTPException"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error_type": type(exc).__name__}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
