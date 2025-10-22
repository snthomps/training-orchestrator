import pytest
import asyncio
from datetime import datetime
from orchestrator import (
    JobOrchestrator, 
    TrainingJob, 
    JobStatus, 
    NotificationService
)


class TestTrainingJob:
    """Test TrainingJob data class"""
    
    def test_job_creation(self):
        job = TrainingJob(
            job_id="test-001",
            name="test-job",
            image="test:latest",
            command=["python", "train.py"],
            schedule="0 * * * *"
        )
        
        assert job.job_id == "test-001"
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 0
        assert job.max_retries == 3
    
    def test_job_with_checkpoint(self):
        job = TrainingJob(
            job_id="test-002",
            name="checkpoint-job",
            image="test:latest",
            command=["python", "train.py"],
            schedule="0 * * * *",
            checkpoint_path="/checkpoints/model"
        )
        
        assert job.checkpoint_path == "/checkpoints/model"


class TestNotificationService:
    """Test notification service"""
    
    @pytest.fixture
    def notification_service(self):
        return NotificationService()
    
    @pytest.fixture
    def sample_job(self):
        return TrainingJob(
            job_id="notif-001",
            name="notification-test",
            image="test:latest",
            command=["echo", "test"],
            schedule="0 * * * *"
        )
    
    def test_slack_notification_no_webhook(self, notification_service, sample_job):
        """Test Slack notification when webhook not configured"""
        # Should not raise error even without webhook
        notification_service.send_slack_notification(sample_job, "Test message")
    
    def test_email_notification_no_config(self, notification_service, sample_job):
        """Test email notification when not configured"""
        # Should not raise error even without email config
        notification_service.send_email_notification(sample_job, "Test message")
    
    def test_notify_all_channels(self, notification_service, sample_job):
        """Test notify method calls all channels"""
        # Should complete without errors
        notification_service.notify(sample_job, "Test notification")


class TestJobOrchestrator:
    """Test JobOrchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        return JobOrchestrator()
    
    @pytest.fixture
    def sample_job(self):
        return TrainingJob(
            job_id="orch-001",
            name="orchestrator-test",
            image="test:latest",
            command=["python", "train.py"],
            schedule="0 * * * *",
            max_retries=2
        )
    
    def test_register_job(self, orchestrator, sample_job):
        """Test job registration"""
        orchestrator.register_job(sample_job)
        
        assert "orch-001" in orchestrator.jobs
        assert orchestrator.jobs["orch-001"].name == "orchestrator-test"
    
    def test_create_k8s_manifest(self, orchestrator, sample_job):
        """Test Kubernetes manifest generation"""
        manifest = orchestrator.create_k8s_job_manifest(sample_job)
        
        assert manifest["kind"] == "Job"
        assert manifest["metadata"]["name"] == f"{sample_job.name}-{sample_job.job_id}"
        assert manifest["spec"]["template"]["spec"]["containers"][0]["image"] == "test:latest"
    
    def test_create_k8s_manifest_with_checkpoint(self, orchestrator):
        """Test manifest with checkpoint recovery"""
        job = TrainingJob(
            job_id="orch-002",
            name="checkpoint-test",
            image="test:latest",
            command=["python", "train.py"],
            schedule="0 * * * *",
            checkpoint_path="/checkpoints/model",
            retry_count=1
        )
        
        manifest = orchestrator.create_k8s_job_manifest(job)
        container_command = manifest["spec"]["template"]["spec"]["containers"][0]["command"]
        
        # Should include checkpoint recovery flag
        assert "--resume-from-checkpoint" in container_command
        assert "/checkpoints/model" in container_command
    
    @pytest.mark.asyncio
    async def test_run_job_success(self, orchestrator, sample_job):
        """Test successful job execution"""
        orchestrator.register_job(sample_job)
        
        # Mock the monitor to return success
        async def mock_monitor(job):
            await asyncio.sleep(0.1)
            return True
        
        orchestrator._monitor_job = mock_monitor
        
        result = await orchestrator.run_job(sample_job)
        
        assert result is True
        assert sample_job.status == JobStatus.COMPLETED
        assert sample_job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_run_job_with_retry(self, orchestrator, sample_job):
        """Test job retry on failure"""
        orchestrator.register_job(sample_job)
        
        # Mock the monitor to fail first time, succeed second time
        call_count = 0
        
        async def mock_monitor(job):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return call_count > 1
        
        orchestrator._monitor_job = mock_monitor
        
        result = await orchestrator.run_job(sample_job)
        
        assert result is True
        assert sample_job.retry_count == 1
        assert sample_job.status == JobStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_run_job_max_retries_exceeded(self, orchestrator, sample_job):
        """Test job fails after max retries"""
        orchestrator.register_job(sample_job)
        
        # Mock the monitor to always fail
        async def mock_monitor(job):
            await asyncio.sleep(0.1)
            return False
        
        orchestrator._monitor_job = mock_monitor
        
        result = await orchestrator.run_job(sample_job)
        
        assert result is False
        assert sample_job.status == JobStatus.FAILED
        assert sample_job.retry_count == sample_job.max_retries


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_job_lifecycle(self):
        """Test complete job lifecycle"""
        orchestrator = JobOrchestrator()
        
        job = TrainingJob(
            job_id="int-001",
            name="integration-test",
            image="test:latest",
            command=["python", "train.py"],
            schedule="0 * * * *",
            max_retries=1
        )
        
        # Mock successful execution
        async def mock_monitor(job):
            await asyncio.sleep(0.1)
            return True
        
        orchestrator._monitor_job = mock_monitor
        orchestrator.register_job(job)
        
        # Run job
        result = await orchestrator.run_job(job)
        
        # Verify lifecycle
        assert result is True
        assert job.status == JobStatus.COMPLETED
        assert job.started_at is not None
        assert job.completed_at is not None
        assert job.retry_count == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_jobs(self):
        """Test running multiple jobs concurrently"""
        orchestrator = JobOrchestrator()
        
        jobs = [
            TrainingJob(
                job_id=f"conc-{i:03d}",
                name=f"concurrent-test-{i}",
                image="test:latest",
                command=["python", "train.py"],
                schedule="0 * * * *"
            )
            for i in range(5)
        ]
        
        async def mock_monitor(job):
            await asyncio.sleep(0.2)
            return True
        
        orchestrator._monitor_job = mock_monitor
        
        # Register all jobs
        for job in jobs:
            orchestrator.register_job(job)
        
        # Run all jobs concurrently
        results = await asyncio.gather(*[
            orchestrator.run_job(job) for job in jobs
        ])
        
        # All should succeed
        assert all(results)
        assert all(job.status == JobStatus.COMPLETED for job in jobs)


# Performance tests
@pytest.mark.performance
class TestPerformance:
    """Performance tests"""
    
    @pytest.mark.asyncio
    async def test_manifest_generation_performance(self):
        """Test manifest generation speed"""
        orchestrator = JobOrchestrator()
        
        job = TrainingJob(
            job_id="perf-001",
            name="performance-test",
            image="test:latest",
            command=["python", "train.py"],
            schedule="0 * * * *"
        )
        
        start = datetime.now()
        for _ in range(1000):
            orchestrator.create_k8s_job_manifest(job)
        duration = (datetime.now() - start).total_seconds()
        
        # Should generate 1000 manifests in less than 1 second
        assert duration < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=orchestrator", "--cov-report=html"])