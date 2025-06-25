# Global Narrative Framework - Backend Service for Cloud Run
FROM python:3.12-slim

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gnf/ ./gnf/
COPY firebase.json firestore.rules firestore.indexes.json ./

# Create non-root user for security
RUN groupadd -r gnfuser && useradd -r -g gnfuser gnfuser
RUN chown -R gnfuser:gnfuser /app
USER gnfuser

# Expose port for Cloud Run
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run FastAPI backend service
CMD ["python", "-m", "uvicorn", "gnf.api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]