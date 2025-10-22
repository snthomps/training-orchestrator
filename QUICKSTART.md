# Quick Start Guide

Get the Training Job Orchestrator running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- kubectl (for Kubernetes deployment)

## Option 1: Docker Compose (Fastest)

### 1. Clone and Configure
```bash
git clone https://github.com/yourorg/training-orchestrator
cd training-orchestrator

# Create environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f orchestrator
```

### 3. Access the System

- **API**: http://localhost:8080
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### 4. Create Your First Job
```bash
# Using curl
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-training",
    "image": "python:3.11",
    "command": ["python", "-c", "print(\"Hello from training job!\")"],
    "schedule": "*/5 * * * *",
    "max_retries": 2
  }'

# Using the CLI
pip install -r requirements.txt
python cli.py create \
  --name "my-first-training" \
  --image "python:3.11" \
  --command "python" --command "-c" --command "print('Hello!')" \
  --schedule "*/5 * * * *"
```

### 5. Monitor Your Job
```bash
# List all jobs
python cli.py list

# Watch jobs in real-time
python cli.py watch

# Check specific job
python cli.py get <job-id>
```

## Next Steps

1. **Read the full README** - Detailed documentation
2. **Customize jobs** - Create your own training scripts
3. **Set up monitoring** - Configure Grafana dashboards

Happy Training! 🚀
EOF