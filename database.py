"""
Database operations for the Training Job Orchestrator
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from config import get_config

logger = logging.getLogger(__name__)

Base = declarative_base()


class JobRecord(Base):
    """Job database model"""
    __tablename__ = 'jobs'
    
    id = Column(String, primary_key=True)
    job_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=False)
    command = Column(JSON, nullable=False)
    schedule = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    checkpoint_path = Column(String)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobExecutionRecord(Base):
    """Job execution history model"""
    __tablename__ = 'job_executions'
    
    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False, index=True)
    execution_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    checkpoint_used = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationRecord(Base):
    """Notification history model"""
    __tablename__ = 'notifications'
    
    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)


class DatabaseManager:
    """Database manager for job persistence"""
    
    def __init__(self):
        config = get_config()
        db_config = config.get('database', {})
        
        # Build connection string
        self.connection_string = (
            f"postgresql://{db_config.get('user')}:{db_config.get('password')}"
            f"@{db_config.get('host')}:{db_config.get('port')}/{db_config.get('name')}"
        )
        
        self.engine = create_engine(
            self.connection_string,
            pool_size=db_config.get('max_connections', 20),
            pool_pre_ping=True,
            echo=False
        )
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def save_job(self, job_data: Dict):
        """Save or update job"""
        with self.get_session() as session:
            job = session.query(JobRecord).filter_by(job_id=job_data['job_id']).first()
            
            if job:
                # Update existing
                for key, value in job_data.items():
                    setattr(job, key, value)
            else:
                # Create new
                job = JobRecord(id=job_data['job_id'], **job_data)
                session.add(job)
            
            session.commit()
            logger.debug(f"Saved job {job_data['job_id']}")
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        with self.get_session() as session:
            job = session.query(JobRecord).filter_by(job_id=job_id).first()
            if job:
                return self._job_to_dict(job)
            return None
    
    def get_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get jobs with optional status filter"""
        with self.get_session() as session:
            query = session.query(JobRecord)
            
            if status:
                query = query.filter_by(status=status)
            
            jobs = query.order_by(JobRecord.created_at.desc()).limit(limit).all()
            return [self._job_to_dict(job) for job in jobs]
    
    def delete_job(self, job_id: str):
        """Delete job"""
        with self.get_session() as session:
            job = session.query(JobRecord).filter_by(job_id=job_id).first()
            if job:
                session.delete(job)
                session.commit()
                logger.info(f"Deleted job {job_id}")
    
    def save_execution(self, execution_data: Dict):
        """Save job execution record"""
        with self.get_session() as session:
            execution = JobExecutionRecord(**execution_data)
            session.add(execution)
            session.commit()
    
    def get_executions(self, job_id: str) -> List[Dict]:
        """Get execution history for a job"""
        with self.get_session() as session:
            executions = session.query(JobExecutionRecord)\
                .filter_by(job_id=job_id)\
                .order_by(JobExecutionRecord.started_at.desc())\
                .all()
            return [self._execution_to_dict(exec) for exec in executions]
    
    def save_notification(self, notification_data: Dict):
        """Save notification record"""
        with self.get_session() as session:
            notification = NotificationRecord(**notification_data)
            session.add(notification)
            session.commit()
    
    def get_stats(self) -> Dict:
        """Get overall statistics"""
        with self.get_session() as session:
            total = session.query(JobRecord).count()
            pending = session.query(JobRecord).filter_by(status='pending').count()
            running = session.query(JobRecord).filter_by(status='running').count()
            completed = session.query(JobRecord).filter_by(status='completed').count()
            failed = session.query(JobRecord).filter_by(status='failed').count()
            retrying = session.query(JobRecord).filter_by(status='retrying').count()
            
            return {
                'total_jobs': total,
                'pending': pending,
                'running': running,
                'completed': completed,
                'failed': failed,
                'retrying': retrying
            }
    
    @staticmethod
    def _job_to_dict(job: JobRecord) -> Dict:
        """Convert job record to dictionary"""
        return {
            'job_id': job.job_id,
            'name': job.name,
            'image': job.image,
            'command': job.command,
            'schedule': job.schedule,
            'status': job.status,
            'max_retries': job.max_retries,
            'retry_count': job.retry_count,
            'checkpoint_path': job.checkpoint_path,
            'error_message': job.error_message,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'updated_at': job.updated_at.isoformat() if job.updated_at else None
        }
    
    @staticmethod
    def _execution_to_dict(execution: JobExecutionRecord) -> Dict:
        """Convert execution record to dictionary"""
        return {
            'id': execution.id,
            'job_id': execution.job_id,
            'execution_number': execution.execution_number,
            'status': execution.status,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration_seconds': execution.duration_seconds,
            'error_message': execution.error_message,
            'checkpoint_used': execution.checkpoint_used
        }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager