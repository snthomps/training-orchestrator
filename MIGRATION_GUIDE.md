# Migration Guide: Adding FastAPI to Your Orchestrator

This guide will help you upgrade your training orchestrator to include the FastAPI REST API for dynamic job management.

## What's New?

### Before (Simple Mode)
- Jobs defined in code
- Manual code changes to add/remove jobs
- Container restart required for changes

### After (API Mode)
- ✅ **REST API** for creating/managing jobs dynamically
- ✅ **Database persistence** - jobs survive restarts
- ✅ **Swagger documentation** at `/docs`
- ✅ **Both modes work** - backward compatible!

## Files You'll Receive

1. **database.py** - Database configuration
2. **models.py** - SQLAlchemy database models
3. **schemas.py** - Pydantic validation schemas
4. **api.py** - FastAPI REST API
5. **orchestrator_v2.py** - Updated orchestrator with database integration
6. **start.py** - Startup script for both services
7. **requirements.txt** - Updated dependencies
8. **docker-compose.yml** - Updated with database
9. **Dockerfile** - Updated container definition
10. **.env.example** - Environment variable template
11. **API_GUIDE.md** - Complete API usage guide

## Step-by-Step Migration

### Step 1: Backup Current Setup

```bash
cd ~/Git_Repo/training-orchestrator

# Create backup
cp orchestrator.py orchestrator_backup.py
cp requirements.txt requirements_backup.txt
cp docker-compose.yml docker-compose_backup.yml
```

### Step 2: Download New Files

Download all the files I provided and place them in your project directory:

- database.py
- models.py  
- schemas.py
- api.py
- orchestrator_v2.py → **rename to orchestrator.py** (replaces old one)
- start.py
- requirements.txt (replaces old one)
- docker-compose.yml (replaces old one)
- Dockerfile (update if you have a custom one)
- .env.example

### Step 3: Update Environment Variables

```bash
# Copy and update your .env file
cp .env.example .env

# Edit .env with your actual values
nano .env
```

Make sure you have all these variables:

```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/training_orchestrator
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-gmail-app-password
RECIPIENT_EMAILS=recipient@example.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
K8S_NAMESPACE=default
```

### Step 4: Stop Current Services

```bash
docker-compose down
```

### Step 5: Rebuild with New Code

```bash
# Rebuild the container with new dependencies
docker-compose build orchestrator

# Start all services
docker-compose up -d
```

### Step 6: Verify Everything Works

```bash
# Check all containers are running
docker-compose ps

# Should see:
# - training-orchestrator (healthy)
# - training-postgres (healthy)
# - training-redis (healthy)
# - training-prometheus
# - training-grafana
# - training-loki

# Test health endpoints
curl http://localhost:8080/health  # Orchestrator health
curl http://localhost:8000/health  # API health

# Check API documentation
open http://localhost:8000/docs
```

### Step 7: Create Your First Job via API

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-api-job",
    "image": "gcr.io/my-project/trainer:latest",
    "command": ["python", "train.py"],
    "schedule": "0 2 * * *",
    "max_retries": 3
  }'
```

## Troubleshooting

### Issue: Container keeps restarting

**Check logs:**
```bash
docker-compose logs orchestrator
```

**Common causes:**
- Missing dependencies (rebuild: `docker-compose build`)
- Database not ready (wait 30 seconds and check again)
- Missing environment variables (check `.env`)

### Issue: Database connection errors

```bash
# Check if postgres is running
docker-compose ps postgres

# Test database connection
docker exec -it training-postgres psql -U postgres -d training_orchestrator

# Inside postgres:
\dt  # List tables
\q   # Quit
```

### Issue: API not accessible

```bash
# Check if port 8000 is exposed
docker-compose ps orchestrator

# Check API logs specifically
docker-compose logs orchestrator | grep "FastAPI"

# Test from inside container
docker exec training-orchestrator curl http://localhost:8000/health
```

### Issue: Jobs not running

```bash
# Check orchestrator is scheduling jobs
docker-compose logs orchestrator | grep "Scheduling"

# Check database has jobs
docker exec -it training-postgres psql -U postgres -d training_orchestrator -c "SELECT * FROM training_jobs;"

# Manually trigger scheduler
docker-compose restart orchestrator
```

## Rollback Instructions

If you need to rollback to the simple version:

```bash
# Stop services
docker-compose down

# Restore backups
cp orchestrator_backup.py orchestrator.py
cp requirements_backup.txt requirements.txt
cp docker-compose_backup.yml docker-compose.yml

# Rebuild and restart
docker-compose build orchestrator
docker-compose up -d
```

## Next Steps

1. **Read the API Guide** - See `API_GUIDE.md` for usage examples
2. **Create jobs via API** - Start using dynamic job creation
3. **Set up monitoring** - Configure Grafana dashboards
4. **Add authentication** - Enable API key auth for production

## Key Differences

### Port Changes

| Service | Old Port | New Port | Purpose |
|---------|----------|----------|---------|
| Orchestrator Health | 8080 | 8080 | Health checks (unchanged) |
| FastAPI | - | 8000 | **NEW** REST API |
| PostgreSQL | 5432 | 5432 | Database |

### Database

The new version uses PostgreSQL to store jobs. Benefits:
- Jobs persist across restarts
- Can query job history
- Supports API-based job management

### Backward Compatibility

The orchestrator still works in "standalone mode" if database is unavailable:
- Falls back to example jobs defined in code
- No API functionality, but health checks work
- Useful for development/testing

## Getting Help

- Check API docs: http://localhost:8000/docs
- Review logs: `docker-compose logs -f orchestrator`
- Check database: `docker exec -it training-postgres psql -U postgres -d training_orchestrator`
- Issues: https://github.com/snthomps/training-orchestrator/issues

## Summary

You now have:
✅ REST API for dynamic job management  
✅ Database persistence  
✅ Swagger documentation  
✅ Backward compatibility  
✅ Production-ready setup  

Enjoy your upgraded Training Orchestrator! 🚀
