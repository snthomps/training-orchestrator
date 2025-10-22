-- Initialize database schema for training job orchestrator

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    image VARCHAR(500) NOT NULL,
    command JSONB NOT NULL,
    schedule VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_count INTEGER NOT NULL DEFAULT 0,
    checkpoint_path VARCHAR(500),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job executions history
CREATE TABLE IF NOT EXISTS job_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    execution_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    error_message TEXT,
    checkpoint_used VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications log
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) NOT NULL,
    channel VARCHAR(50) NOT NULL, -- 'slack', 'email'
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'sent', 'failed'
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_started_at ON job_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_job_id ON notifications(job_id);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_job_id ON metrics(job_id);
CREATE INDEX IF NOT EXISTS idx_metrics_recorded_at ON metrics(recorded_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for job statistics
CREATE OR REPLACE VIEW job_statistics AS
SELECT 
    j.job_id,
    j.name,
    j.status,
    COUNT(je.id) as total_executions,
    AVG(je.duration_seconds) as avg_duration_seconds,
    MIN(je.duration_seconds) as min_duration_seconds,
    MAX(je.duration_seconds) as max_duration_seconds,
    SUM(CASE WHEN je.status = 'completed' THEN 1 ELSE 0 END) as successful_executions,
    SUM(CASE WHEN je.status = 'failed' THEN 1 ELSE 0 END) as failed_executions,
    j.created_at,
    MAX(je.completed_at) as last_execution_at
FROM jobs j
LEFT JOIN job_executions je ON j.job_id = je.job_id
GROUP BY j.job_id, j.name, j.status, j.created_at;

-- View for recent failures
CREATE OR REPLACE VIEW recent_failures AS
SELECT 
    j.job_id,
    j.name,
    je.execution_number,
    je.error_message,
    je.started_at,
    je.completed_at,
    je.duration_seconds
FROM job_executions je
JOIN jobs j ON j.job_id = je.job_id
WHERE je.status = 'failed'
ORDER BY je.started_at DESC
LIMIT 100;

-- Insert sample data (optional, for testing)
-- Uncomment if you want initial test data

-- INSERT INTO jobs (job_id, name, image, command, schedule) VALUES
-- ('test-001', 'test-training', 'trainer:latest', '["python", "train.py"]', '0 2 * * *'),
-- ('test-002', 'test-inference', 'inference:latest', '["python", "infer.py"]', '0 3 * * *');

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO orchestrator;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO orchestrator;

-- Print confirmation
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully';
END $$;