FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY orchestrator.py .
COPY scheduler.py .
COPY api.py .
COPY cli.py .
COPY config.py .
COPY database.py .
COPY metrics.py .
COPY example_trainer.py .
COPY config.yaml .

# Create necessary directories
RUN mkdir -p /checkpoints /logs

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the orchestrator
CMD ["python", "orchestrator.py"]
