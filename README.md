# This is a LARGE file, so I'll give you the key sections
# Training Job Orchestrator

A production-ready Kubernetes-based system for automating ML training jobs with built-in failure recovery, checkpoint restart, and multi-channel notifications.

## Features

- ✅ **Automated Job Scheduling** - Schedule training jobs with cron expressions
- ✅ **Failure Recovery** - Automatic retry with exponential backoff
- ✅ **Checkpoint Restart** - Resume from last checkpoint on retry
- ✅ **Multi-Channel Notifications** - Slack and email alerts for job status
- ✅ **REST API** - Full API for job management
- ✅ **Monitoring** - Prometheus metrics and Grafana dashboards
- ✅ **Docker & Kubernetes** - Production-ready deployment options

## Architecture
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   API       │─────▶│ Orchestrator │─────▶│ K8s Jobs    │
│  (FastAPI)  │      │   (Python)   │      │ (Training)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├──────▶ Slack Notifications
                            ├──────▶ Email Notifications
                            └──────▶ Metrics (Prometheus)
```

## Quick Start

### Option 1: Docker Compose (Local Development)

1. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. **Start the services:**
```bash
docker-compose up -d
```

3. **Access the API:**
```bash
curl http://localhost:8080/health
```

4. **Create a training job:**
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resnet-training",
    "image": "your-registry/trainer:latest",
    "command": ["python", "train.py", "--model", "resnet50"],
    "schedule": "0 2 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/resnet50"
  }'
```

### Option 2: Kubernetes (Production)

1. **Create namespace and secrets:**
```bash
kubectl create namespace training

kubectl create secret generic orchestrator-secrets \
  --from-literal=SLACK_WEBHOOK_URL='https://hooks.slack.com/...' \
  --from-literal=SMTP_SERVER='smtp.gmail.com' \
  --from-literal=SMTP_PORT='587' \
  --from-literal=SENDER_EMAIL='your-email@example.com' \
  --from-literal=SENDER_PASSWORD='your-app-password' \
  --from-literal=RECIPIENT_EMAILS='team@example.com' \
  -n training
```

2. **Deploy the orchestrator:**
```bash
kubectl apply -f k8s/
```

3. **Verify deployment:**
```bash
kubectl get pods -n training
kubectl logs -n training deployment/training-orchestrator
```

## API Endpoints

- `POST /jobs` - Create new training job
- `GET /jobs` - List all jobs (with filters)
- `GET /jobs/{job_id}` - Get job details
- `DELETE /jobs/{job_id}` - Delete job
- `POST /jobs/{job_id}/retry` - Manually retry job
- `GET /stats` - Overall statistics
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `K8S_NAMESPACE` | Kubernetes namespace | `training` |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | - |
| `SMTP_SERVER` | SMTP server for email | `smtp.gmail.com` |
| `SENDER_EMAIL` | Email sender address | - |
| `MAX_WORKERS` | Max concurrent jobs | `5` |

## Monitoring

Access monitoring dashboards:
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v --cov

# Start API locally
python api.py
```

## Troubleshooting

See the full documentation for troubleshooting guides.

## License

MIT License - see LICENSE file for details.
