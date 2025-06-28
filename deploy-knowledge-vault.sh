#!/bin/bash
# Deployment script for Alchemist Knowledge Vault to Google Cloud Run
# Run from the root Alchemist-v1 directory

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="alchemist-knowledge-vault"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Alchemist Knowledge Vault${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Build Context: $(pwd)"
echo ""

# Verify we're in the right directory
if [ ! -d "knowledge-vault" ] || [ ! -d "shared" ]; then
    echo -e "${RED}❌ Error: Must run from Alchemist-v1 root directory${NC}"
    echo "Expected to find both 'knowledge-vault' and 'shared' directories"
    exit 1
fi

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi


# Check if .env file exists and load it
if [ -f ".env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from .env file...${NC}"
  source .env
elif [ -f "knowledge-vault/.env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from knowledge-vault/.env file...${NC}"
  source knowledge-vault/.env
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

# Create temporary Dockerfile for deployment
echo -e "${YELLOW}📦 Creating deployment Dockerfile...${NC}"
cat > Dockerfile.knowledge-vault << EOF
# Multi-stage Docker build for Knowledge Vault
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
COPY knowledge-vault/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy and install shared libraries
COPY shared /app/shared
RUN cd /app/shared && pip install -e .

# Copy application code
COPY knowledge-vault .

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
CMD exec gunicorn --bind :\${PORT:-8080} --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 300 app.main:app
EOF

# Create deployment-specific .dockerignore
echo -e "${YELLOW}📝 Creating deployment .dockerignore...${NC}"
cat > .dockerignore.knowledge-vault << EOF
# Exclude all other services except knowledge-vault and shared
admin-dashboard/
agent-bridge/
agent-studio/
agent-engine/
agent-tuning-service/
alchemist-monitor-service/
banking-api-service/
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

# Include what we need for knowledge-vault
!knowledge-vault/
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
cp .dockerignore.knowledge-vault .dockerignore

# Build and submit to Cloud Build
echo -e "${YELLOW}🔨 Building and pushing image with Cloud Build...${NC}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create a temporary cloudbuild.yaml for custom Dockerfile
cat > cloudbuild-temp.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.knowledge-vault', '-t', '${IMAGE_NAME}:latest', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:latest']
- name: 'gcr.io/cloud-builders/docker'
  args: ['tag', '${IMAGE_NAME}:latest', '${IMAGE_NAME}:${TIMESTAMP}']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:${TIMESTAMP}']
EOF

gcloud builds submit --config=cloudbuild-temp.yaml .

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"

# Build environment variables from knowledge-vault/.env
ENV_VARS=""
if [ -f "knowledge-vault/.env" ]; then
    echo -e "${BLUE}📋 Loading environment variables from knowledge-vault/.env...${NC}"
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi
        # Skip lines that don't contain =
        if [[ ! "$line" =~ = ]]; then
            continue
        fi
        # Extract key=value pairs
        key=$(echo "$line" | cut -d'=' -f1 | xargs)
        value=$(echo "$line" | cut -d'=' -f2- | xargs)
        # Skip empty values and commented out variables
        if [[ -n "$value" && ! "$line" =~ ^[[:space:]]*# ]]; then
            if [ -n "$ENV_VARS" ]; then
                ENV_VARS="$ENV_VARS,$key=$value"
            else
                ENV_VARS="$key=$value"
            fi
        fi
    done < "knowledge-vault/.env"
fi

# Override with production-specific values
ENV_VARS="$ENV_VARS,ENVIRONMENT=production,FIREBASE_PROJECT_ID=${PROJECT_ID}"

echo -e "${BLUE}🔧 Setting environment variables: $ENV_VARS${NC}"

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 5 \
    --set-env-vars "$ENV_VARS"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

# Cleanup temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f Dockerfile.knowledge-vault .dockerignore.knowledge-vault cloudbuild-temp.yaml

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
echo -e "${GREEN}🎉 Knowledge Vault deployment complete!${NC}"
echo -e "${BLUE}💡 To view logs: gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\"${NC}"
echo -e "${BLUE}💡 To redeploy: ./deploy-knowledge-vault.sh${NC}"