# Multi-stage Docker build for Agent Engine
FROM python:3.12-slim AS base

# Set environment variables (non-sensitive only)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy requirements and install dependencies
COPY agent-engine/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy and install shared libraries
COPY shared /app/shared
RUN cd /app/shared && pip install -e .

# Copy application code
COPY agent-engine .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["sh", "-c", "exec gunicorn --bind :${PORT:-8080} --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 300 main:app"]
