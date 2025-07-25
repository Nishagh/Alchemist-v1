#!/bin/bash
# Deployment script for Alchemist Agent Tuning Service to Google Cloud Run
# Run from the root Alchemist-v1 directory

set -e

# Configuration
PROJECT_ID="alchemist-e69bb"
SERVICE_NAME="alchemist-agent-tuning"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Alchemist Agent Tuning Service${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Build Context: $(pwd)"
echo ""

# Verify we're in the right directory
if [ ! -d "agent-tuning-service" ] || [ ! -d "shared" ]; then
    echo -e "${RED}❌ Error: Must run from Alchemist-v1 root directory${NC}"
    echo "Expected to find both 'agent-tuning-service' and 'shared' directories"
    exit 1
fi

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install it first.${NC}"
    exit 1
fi

# Check if .env file exists and load it
if [ -f ".env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from .env file...${NC}"
  source .env
elif [ -f "agent-tuning-service/.env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from agent-tuning-service/.env file...${NC}"
  source agent-tuning-service/.env
else
  echo -e "${YELLOW}⚠️  Warning: .env file not found. Will use default values.${NC}"
fi

# Authenticate with Google Cloud
echo -e "${YELLOW}🔐 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Authenticating with Google Cloud...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}📁 Setting Google Cloud project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Configure Docker for gcr.io
echo -e "${YELLOW}🐳 Configuring Docker for Google Container Registry...${NC}"
gcloud auth configure-docker

# Create temporary Dockerfile for deployment
echo -e "${YELLOW}📦 Creating deployment Dockerfile...${NC}"
cat > Dockerfile.agent-tuning-service << EOF
# Multi-stage Docker build for Agent Tuning Service
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy requirements and install dependencies
COPY agent-tuning-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy and install shared libraries
COPY shared /app/shared
RUN cd /app/shared && pip install -e .

# Copy application code
COPY agent-tuning-service .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:\${PORT:-8080}/health || exit 1

# Expose port
EXPOSE 8080

# Command to run the application
CMD exec gunicorn --bind :\${PORT:-8080} --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 300 main:app
EOF

# Create deployment-specific .dockerignore
echo -e "${YELLOW}📝 Creating deployment .dockerignore...${NC}"
cat > .dockerignore.agent-tuning-service << EOF
# Exclude all other services except agent-tuning-service and shared
admin-dashboard/
agent-bridge/
agent-studio/
agent-engine/
alchemist-monitor-service/
banking-api-service/
knowledge-vault/
mcp_config_generator/
billing-service/
prompt-engine/
sandbox-console/
tool-forge/
user-deployment-monitor/
agent-launcher/
global-narative-framework/

# Exclude documentation and scripts
docs/
scripts/
tools/
deployment/

# Exclude build artifacts and dependencies
**/node_modules/
**/build/
**/dist/
**/.next/
**/coverage/

# Exclude git and version control
.git/
.gitignore
**/.gitkeep

# Exclude temporary and cache files
**/.cache/
**/tmp/
**/temp/
**/*.tmp
**/*.log
**/*.pid
**/*.seed
**/*.pid.lock

# Exclude test files and data
**/tests/
**/*test*/
**/test_*/
**/*.test.js
**/*.spec.js

# Exclude development files
**/.env*
!**/.env.example
**/.vscode/
**/.idea/
**/*.swp
**/*.swo

# Exclude OS files
.DS_Store
Thumbs.db
**/.DS_Store
**/Thumbs.db

# Exclude Python cache and virtual environments
**/__pycache__/
**/*.pyc
**/*.pyo
**/*.pyd
**/venv/
**/env/
**/.venv/
**/test_env/
**/*.egg-info/

# Exclude vector data and large files
**/vector_data*/
**/*.bin
**/*.sqlite3
**/*.db

# Exclude credentials and config files that shouldn't be in container
firebase-credentials.json
**/firebase-credentials.json
gcloud-credentials.json
**/gcloud-credentials.json
service-account-key.json
**/service-account-key.json
**/secrets/
**/credentials/
**/keys/
**/certificates/

# Exclude shared libraries build artifacts
shared/build/
shared/dist/

# Include what we need for agent-tuning-service
!agent-tuning-service/
!shared/

# Exclude deployment configs at root
cloudbuild*.yaml
deploy*.sh
docker-compose*.yml
Makefile
EOF

# Backup original .dockerignore if it exists
if [ -f ".dockerignore" ]; then
    cp .dockerignore .dockerignore.backup
fi

# Use deployment .dockerignore
cp .dockerignore.agent-tuning-service .dockerignore

# Build the Docker image from root directory
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build --platform linux/amd64 -f Dockerfile.agent-tuning-service -t ${IMAGE_NAME}:latest .

# Tag with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${TIMESTAMP}

# Push to Google Container Registry
echo -e "${YELLOW}📤 Pushing image to Google Container Registry...${NC}"
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:${TIMESTAMP}

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 5 \
    --set-env-vars "TUNING_ENVIRONMENT=production" \
    --set-env-vars "TUNING_FIREBASE_PROJECT_ID=${PROJECT_ID}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

# Cleanup temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f Dockerfile.agent-tuning-service .dockerignore.agent-tuning-service

# Restore original .dockerignore if it existed
if [ -f ".dockerignore.backup" ]; then
    mv .dockerignore.backup .dockerignore
else
    rm -f .dockerignore
fi

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}📊 Health Check: ${SERVICE_URL}/health${NC}"
echo -e "${GREEN}📖 API Docs: ${SERVICE_URL}/docs${NC}"
echo ""

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -s -f "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Service may still be starting up. Check logs with:"
    echo "gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\""
fi

echo ""
echo -e "${GREEN}🎉 Agent Tuning Service deployment complete!${NC}"
echo -e "${BLUE}💡 To view logs: gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\"${NC}"
echo -e "${BLUE}💡 To redeploy: ./deploy-agent-tuning-service.sh${NC}"