# Training Job Orchestrator

A production-ready Kubernetes-based system for automating ML training jobs with built-in failure recovery, checkpoint restart, multi-channel notifications, and **REST API for dynamic job management**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## ✨ Features

* ✅ **REST API** - FastAPI endpoints for dynamic job management
* ✅ **Database Persistence** - PostgreSQL storage for jobs and history
* ✅ **Automated Scheduling** - Cron-based job scheduling
* ✅ **Failure Recovery** - Automatic retry with exponential backoff
* ✅ **Checkpoint Restart** - Resume from last checkpoint on retry
* ✅ **Multi-Channel Notifications** - Slack and email alerts
* ✅ **Interactive Docs** - Auto-generated Swagger/ReDoc documentation
* ✅ **Monitoring** - Prometheus metrics and Grafana dashboards
* ✅ **Docker & Kubernetes** - Production-ready deployment

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Training Orchestrator                │
├──────────────────────────────────────────────────────┤
│                                                        │
│  ┌─────────────┐         ┌──────────────┐           │
│  │  FastAPI    │────────▶│ PostgreSQL   │           │
│  │  REST API   │         │  Database    │           │
│  │  (Port 8000)│         └──────────────┘           │
│  └──────┬──────┘                                     │
│         │                                             │
│         ▼                                             │
│  ┌─────────────┐         ┌──────────────┐           │
│  │  Job        │────────▶│  Kubernetes  │           │
│  │ Orchestrator│         │    Jobs      │           │
│  │ (Scheduler) │         └──────────────┘           │
│  └──────┬──────┘                                     │
│         │                                             │
│         ├──────────────▶ Slack Notifications         │
│         ├──────────────▶ Email Notifications         │
│         └──────────────▶ Prometheus Metrics          │
│                                                        │
│  ┌─────────────┐                                     │
│  │   Health    │         (Port 8080)                 │
│  │   Check API │                                     │
│  └─────────────┘                                     │
└──────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (20.10+)
- **Gmail account** with [App Password](https://support.google.com/accounts/answer/185833)
- **Slack workspace** with [incoming webhook](https://api.slack.com/messaging/webhooks) (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/snthomps/training-orchestrator.git
cd training-orchestrator

# Set up environment variables
cp .env.example .env
nano .env  # Edit with your credentials

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Access the Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI Docs** | http://localhost:8000/docs | - |
| **Health Check** | http://localhost:8080/health | - |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |

## 📖 Usage

### Two Ways to Use the Orchestrator

#### 1. REST API (Recommended) 🔥

**Create jobs dynamically** without code changes:

```bash
# Create a training job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resnet50-training",
    "image": "gcr.io/my-project/trainer:latest",
    "command": ["python", "train.py", "--model", "resnet50"],
    "schedule": "0 2 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/resnet50"
  }'

# List all jobs
curl http://localhost:8000/jobs

# Get job status
curl http://localhost:8000/jobs/{job_id}

# Delete a job
curl -X DELETE http://localhost:8000/jobs/{job_id}
```

**See full API documentation:** [API_GUIDE.md](API_GUIDE.md)

#### 2. Code-Defined Jobs (Simple Mode)

**Define jobs in code** for predictable workloads:

```python
# In orchestrator.py
job = TrainingJob(
    job_id="train-001",
    name="resnet50-training",
    image="gcr.io/my-project/trainer:latest",
    command=["python", "train.py", "--model", "resnet50"],
    schedule="0 2 * * *",
    max_retries=3
)

orchestrator.register_job(job)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/training_orchestrator

# Email Notifications (Gmail)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-gmail-app-password
RECIPIENT_EMAILS=recipient@example.com

# SMTP Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Slack Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Kubernetes
K8S_NAMESPACE=default
```

> **⚠️ Important:** For Gmail, you must use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password!

### Gmail App Password Setup

1. Enable **2-Step Verification** on your Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Select **"Mail"** → **"Other (Custom name)"**
4. Enter "Training Orchestrator" and click **Generate**
5. Copy the 16-character password to your `.env` file

## 📊 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/docs` | GET | Interactive API documentation |
| `/health` | GET | Health check |
| `/jobs` | POST | Create new training job |
| `/jobs` | GET | List all jobs (with filters) |
| `/jobs/{job_id}` | GET | Get job details |
| `/jobs/{job_id}` | PUT | Update job |
| `/jobs/{job_id}` | DELETE | Delete job |
| `/jobs/{job_id}/retry` | POST | Retry failed job |
| `/stats` | GET | Get statistics |

### Example: Create a Job with Python

```python
import requests

response = requests.post("http://localhost:8000/jobs", json={
    "name": "bert-finetuning",
    "image": "gcr.io/my-project/nlp-trainer:latest",
    "command": ["python", "finetune.py", "--model", "bert-base"],
    "schedule": "0 3 * * *",
    "max_retries": 2
})

job = response.json()
print(f"Created job: {job['job_id']}")
```

## 📈 Monitoring

### Prometheus Metrics

Available metrics:
- `training_jobs_total` - Total jobs created
- `training_jobs_completed` - Completed jobs
- `training_jobs_failed` - Failed jobs
- `training_jobs_duration_seconds` - Job duration histogram
- `notification_sent_total` - Notifications sent
- `notification_failures_total` - Notification failures

Access at: http://localhost:9090

### Grafana Dashboards

Pre-configured dashboards for:
- Job success/failure rates
- Execution durations
- Notification status
- System health

Access at: http://localhost:3000 (admin/admin)

## 🐳 Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
# Create namespace
kubectl create namespace training

# Create secrets
kubectl create secret generic orchestrator-secrets \
  --from-env-file=.env \
  -n training

# Deploy
kubectl apply -f k8s/ -n training

# Verify
kubectl get pods -n training
```

## 🔍 Troubleshooting

### Container keeps restarting

```bash
# Check logs
docker-compose logs orchestrator --tail 50

# Common issues:
# - Missing dependencies → Rebuild: docker-compose build
# - Database not ready → Wait 30 seconds
# - Environment variables missing → Check .env
```

### Email notifications failing

**Error:** `535 Username and Password not accepted`

**Solution:** Use Gmail App Password (see setup above)

### API not accessible

```bash
# Test health endpoint
curl http://localhost:8000/health

# Check if port is exposed
docker-compose ps

# View API logs
docker-compose logs orchestrator | grep "FastAPI"
```

### Database connection issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker exec -it training-postgres psql -U postgres -d training_orchestrator
```

**Full troubleshooting guide:** [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## 🛠️ Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -c "from database import init_db; init_db()"

# Start services separately
python start.py  # Runs both API and orchestrator
```

### Running Tests

```bash
pytest tests/ -v --cov
```

### Project Structure

```
training-orchestrator/
├── api.py                    # FastAPI REST API
├── orchestrator.py           # Job scheduler and executor
├── database.py              # Database configuration
├── models.py                # SQLAlchemy models
├── schemas.py               # Pydantic schemas
├── metrics.py               # Prometheus metrics
├── start.py                 # Startup script
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-service stack
├── .env                    # Environment config (gitignored)
├── .env.example           # Environment template
├── API_GUIDE.md           # Complete API documentation
├── MIGRATION_GUIDE.md     # Upgrade instructions
└── k8s/                   # Kubernetes manifests
    ├── deployment.yaml
    ├── service.yaml
    └── configmap.yaml
```

## 📚 Documentation

- **API Guide:** Complete REST API documentation → [API_GUIDE.md](API_GUIDE.md)
- **Migration Guide:** Upgrading from simple mode → [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **Interactive Docs:** http://localhost:8000/docs

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙋 Support

- 🐛 [Report bugs](https://github.com/snthomps/training-orchestrator/issues)
- 💬 [Discussions](https://github.com/snthomps/training-orchestrator/discussions)
- 📧 Email: [your-email@example.com]

## 🌟 Acknowledgments

- Built with **FastAPI** for high-performance REST API
- **PostgreSQL** for robust data persistence
- **Prometheus** and **Grafana** for comprehensive monitoring
- **Kubernetes** for scalable job orchestration
- **aiohttp** for efficient async health checks

---

**⭐ Star this repo if you find it helpful!**

**Made with ❤️ for the ML community**
