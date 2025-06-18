FROM python:3.12-slim

WORKDIR /app

# Copy shared libraries first (for better caching)
COPY shared/ /app/shared/

# Install shared libraries
RUN cd /app/shared && pip install -e .

# Copy requirements first for better caching
COPY prompt-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY prompt-engine/ .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=True
ENV ENVIRONMENT=production

# Run the service with uvicorn for ASGI compatibility
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --worker-class uvicorn.workers.UvicornWorker "main:app"
