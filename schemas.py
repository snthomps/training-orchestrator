"""
Pydantic schemas for API validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class JobCreate(BaseModel):
    """Schema for creating a new training job"""
    name: str = Field(..., description="Unique name for the training job")
    image: str = Field(..., description="Docker image for training")
    command: List[str] = Field(..., description="Command to run in the container")
    schedule: str = Field(..., description="Cron expression for scheduling")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    checkpoint_path: Optional[str] = Field(None, description="Path to checkpoint directory")

    @validator('name')
    def validate_name(cls, v):
        """Validate job name"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Job name cannot be empty')
        if len(v) > 100:
            raise ValueError('Job name too long (max 100 characters)')
        return v.strip()

    @validator('command')
    def validate_command(cls, v):
        """Validate command is not empty"""
        if not v or len(v) == 0:
            raise ValueError('Command cannot be empty')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "resnet50-training",
                "image": "gcr.io/my-project/trainer:latest",
                "command": ["python", "train.py", "--model", "resnet50"],
                "schedule": "0 2 * * *",
                "max_retries": 3,
                "checkpoint_path": "/checkpoints/resnet50"
            }
        }


class JobUpdate(BaseModel):
    """Schema for updating a training job"""
    name: Optional[str] = None
    image: Optional[str] = None
    command: Optional[List[str]] = None
    schedule: Optional[str] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    checkpoint_path: Optional[str] = None


class JobResponse(BaseModel):
    """Schema for job response"""
    job_id: str
    name: str
    image: str
    command: List[str]
    schedule: str
    max_retries: int
    retry_count: int
    checkpoint_path: Optional[str]
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for listing jobs"""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


class StatsResponse(BaseModel):
    """Schema for statistics response"""
    total_jobs: int
    pending: int
    running: int
    completed: int
    failed: int
    retrying: int


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: str
    service: str
    database_connected: bool


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    error_type: Optional[str] = None
