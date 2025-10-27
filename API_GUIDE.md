# API Usage Guide

This guide provides examples of how to interact with the Training Job Orchestrator REST API.

## Base URL

- **Local Development:** `http://localhost:8000`
- **Production:** `https://your-domain.com`

## API Documentation

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Authentication

Currently, the API is open by default. To enable authentication, set `ENABLE_API_AUTH=true` in your `.env` file and provide an `API_KEY`.

## Endpoints

### 1. Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2025-10-22T18:00:00",
  "service": "training-orchestrator-api",
  "database_connected": true
}
```

### 2. Create a Training Job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resnet50-training",
    "image": "gcr.io/my-project/trainer:latest",
    "command": ["python", "train.py", "--model", "resnet50", "--epochs", "100"],
    "schedule": "0 2 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/resnet50"
  }'

# Response
{
  "job_id": "train-a1b2c3d4",
  "name": "resnet50-training",
  "image": "gcr.io/my-project/trainer:latest",
  "command": ["python", "train.py", "--model", "resnet50", "--epochs", "100"],
  "schedule": "0 2 * * *",
  "max_retries": 3,
  "retry_count": 0,
  "checkpoint_path": "/checkpoints/resnet50",
  "status": "pending",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "created_at": "2025-10-22T18:00:00",
  "updated_at": "2025-10-22T18:00:00"
}
```

### 3. List All Jobs

```bash
# List all jobs
curl http://localhost:8000/jobs

# Filter by status
curl "http://localhost:8000/jobs?status_filter=completed"

# With pagination
curl "http://localhost:8000/jobs?page=1&page_size=10"

# Response
{
  "jobs": [
    {
      "job_id": "train-a1b2c3d4",
      "name": "resnet50-training",
      "status": "pending",
      ...
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 50
}
```

### 4. Get Job Details

```bash
curl http://localhost:8000/jobs/train-a1b2c3d4

# Response
{
  "job_id": "train-a1b2c3d4",
  "name": "resnet50-training",
  "image": "gcr.io/my-project/trainer:latest",
  "command": ["python", "train.py", "--model", "resnet50"],
  "schedule": "0 2 * * *",
  "status": "completed",
  "started_at": "2025-10-22T02:00:00",
  "completed_at": "2025-10-22T05:30:00",
  ...
}
```

### 5. Update a Job

```bash
curl -X PUT http://localhost:8000/jobs/train-a1b2c3d4 \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": "0 3 * * *",
    "max_retries": 5
  }'

# Response: Updated job details
```

**Note:** Cannot update jobs that are currently running.

### 6. Delete a Job

```bash
curl -X DELETE http://localhost:8000/jobs/train-a1b2c3d4

# Response: 204 No Content
```

**Note:** Cannot delete jobs that are currently running.

### 7. Retry a Failed Job

```bash
curl -X POST http://localhost:8000/jobs/train-a1b2c3d4/retry

# Response: Job details with reset status
{
  "job_id": "train-a1b2c3d4",
  "status": "pending",
  "retry_count": 0,
  "error_message": null,
  ...
}
```

### 8. Get Statistics

```bash
curl http://localhost:8000/stats

# Response
{
  "total_jobs": 25,
  "pending": 5,
  "running": 2,
  "completed": 15,
  "failed": 2,
  "retrying": 1
}
```

## Python Examples

### Using `requests` library

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a job
job_data = {
    "name": "bert-finetuning",
    "image": "gcr.io/my-project/nlp-trainer:latest",
    "command": ["python", "finetune.py", "--model", "bert-base"],
    "schedule": "0 3 * * *",
    "max_retries": 2
}

response = requests.post(f"{BASE_URL}/jobs", json=job_data)
job = response.json()
print(f"Created job: {job['job_id']}")

# List all jobs
response = requests.get(f"{BASE_URL}/jobs")
jobs = response.json()
print(f"Total jobs: {jobs['total']}")

# Get job status
job_id = job['job_id']
response = requests.get(f"{BASE_URL}/jobs/{job_id}")
job_details = response.json()
print(f"Job status: {job_details['status']}")

# Delete job
response = requests.delete(f"{BASE_URL}/jobs/{job_id}")
print(f"Deleted job: {response.status_code == 204}")
```

### Using `httpx` (async)

```python
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient() as client:
        # Create job
        job_data = {
            "name": "gpt-training",
            "image": "gcr.io/my-project/llm-trainer:latest",
            "command": ["python", "train_gpt.py"],
            "schedule": "0 4 * * *"
        }
        
        response = await client.post(f"{BASE_URL}/jobs", json=job_data)
        job = response.json()
        print(f"Created job: {job['job_id']}")
        
        # Get stats
        response = await client.get(f"{BASE_URL}/stats")
        stats = response.json()
        print(f"Stats: {stats}")

asyncio.run(main())
```

## Error Handling

The API returns standard HTTP status codes:

- **200 OK** - Request successful
- **201 Created** - Resource created
- **204 No Content** - Successful deletion
- **400 Bad Request** - Invalid input
- **404 Not Found** - Resource not found
- **409 Conflict** - Conflict (e.g., duplicate name, cannot delete running job)
- **500 Internal Server Error** - Server error

Error response format:

```json
{
  "detail": "Error message here",
  "error_type": "ValueError"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. For production, consider adding rate limiting middleware.

## Webhooks

The orchestrator automatically sends notifications to configured channels (Slack, Email) when job status changes. To receive webhooks from external systems, you'll need to implement custom endpoints.

## Best Practices

1. **Use meaningful job names** - Makes it easier to identify jobs
2. **Set appropriate max_retries** - Balance between reliability and resource usage
3. **Monitor job status** - Regularly check job progress
4. **Clean up completed jobs** - Remove old jobs to keep the database clean
5. **Use checkpoints** - Enable faster recovery from failures

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Train Model
on:
  push:
    branches: [main]

jobs:
  trigger-training:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger training job
        run: |
          curl -X POST ${{ secrets.ORCHESTRATOR_URL }}/jobs \
            -H "Content-Type: application/json" \
            -d '{
              "name": "model-training-${{ github.sha }}",
              "image": "gcr.io/my-project/trainer:${{ github.sha }}",
              "command": ["python", "train.py"],
              "schedule": "*/5 * * * *",
              "max_retries": 3
            }'
```

### Monitoring Script

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def monitor_jobs():
    while True:
        response = requests.get(f"{BASE_URL}/stats")
        stats = response.json()
        
        print(f"Running: {stats['running']}, Failed: {stats['failed']}")
        
        if stats['failed'] > 0:
            # Alert or take action
            print("⚠️  Failed jobs detected!")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor_jobs()
```

## Support

For issues or questions about the API:
- Check the interactive docs at `/docs`
- Review error messages in responses
- Check logs: `docker-compose logs orchestrator`
