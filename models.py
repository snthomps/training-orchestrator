"""
Database models for training jobs
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base
import json


class TrainingJobModel(Base):
    """
    Database model for training jobs
    """
    __tablename__ = "training_jobs"

    job_id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    image = Column(String, nullable=False)
    command = Column(JSON, nullable=False)  # Store as JSON array
    schedule = Column(String, nullable=False)
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    checkpoint_path = Column(String, nullable=True)
    status = Column(String, default="pending", index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "image": self.image,
            "command": self.command,
            "schedule": self.schedule,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "checkpoint_path": self.checkpoint_path,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
