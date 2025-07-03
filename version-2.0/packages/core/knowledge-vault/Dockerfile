FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy shared libraries first (for better caching)
COPY shared/ /app/shared/

# Install shared libraries
RUN pip install -e /app/shared/

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Note: GOOGLE_APPLICATION_CREDENTIALS not set - using default service account in Cloud Run

# Run the application with Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app -k uvicorn.workers.UvicornWorker