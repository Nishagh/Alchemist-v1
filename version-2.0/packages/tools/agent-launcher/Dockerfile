FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Cloud SDK and deployment tools
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Copy and install shared libraries first
COPY ../../shared/ /app/shared/
RUN cd /app/shared && pip install -e .

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy deployment service application code
COPY main.py .
COPY agent_deployer.py .
COPY config_loader.py .
COPY mcp_tool.py .
COPY embedded_vector_search.py .
COPY knowledge_service.py .

# Copy the entire universal-agent template directory
COPY universal-agent-template ./universal-agent

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Run the application
CMD ["python", "main.py"]