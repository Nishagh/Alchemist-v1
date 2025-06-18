FROM python:3.12-slim

# Install system dependencies including gcloud CLI
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    gnupg \
    lsb-release \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy shared libraries first (for better caching)
COPY shared/ /app/shared/

# Install shared libraries
RUN cd /app/shared && pip install -e .

# Copy requirements and install Python dependencies
COPY tool-forge/requirements-manager.txt .
RUN pip install --no-cache-dir -r requirements-manager.txt

# Copy application files
COPY tool-forge/ .

# Set environment variables
# Note: GOOGLE_APPLICATION_CREDENTIALS not set - using default service account in Cloud Run
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the manager service
CMD ["python", "mcp_manager_service.py"]