#!/bin/bash
# Deployment script for Alchemist Agent Launcher to Google Cloud Run
# Run from the root Alchemist-v1 directory

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="alchemist-agent-launcher"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Alchemist Agent Launcher${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Build Context: $(pwd)"
echo ""

# Verify we're in the right directory
if [ ! -d "agent-launcher" ] || [ ! -d "shared" ]; then
    echo -e "${RED}❌ Error: Must run from Alchemist-v1 root directory${NC}"
    echo "Expected to find both 'agent-launcher' and 'shared' directories"
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
elif [ -f "agent-launcher/.env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from agent-launcher/.env file...${NC}"
  source agent-launcher/.env
else
  echo -e "${YELLOW}⚠️  Warning: .env file not found. Will use default values.${NC}"
fi

# For Cloud Run deployment, we use the default service account
echo -e "${GREEN}✅ Using Cloud Run default service account for production deployment${NC}"
echo -e "${BLUE}ℹ️  Ensure your Cloud Run service account has proper permissions:${NC}"
echo -e "${BLUE}   - Firebase Admin${NC}"
echo -e "${BLUE}   - Cloud Storage Admin${NC}"
echo -e "${BLUE}   - Cloud Run Admin (for triggering jobs via API)${NC}"
echo -e "${BLUE}   - Cloud Run Jobs Admin${NC}"
echo -e "${BLUE}   - Cloud Build Service Account${NC}"

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
cat > Dockerfile.agent-launcher << EOF
# Multi-stage Docker build for Agent Launcher
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app

# Install system dependencies including gcloud CLI (needed for job creation)
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    apt-transport-https \\
    ca-certificates \\
    gnupg \\
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \\
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \\
    && apt-get update && apt-get install -y google-cloud-cli \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy requirements and install dependencies
COPY agent-launcher/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy and install shared libraries
COPY shared /app/shared
RUN cd /app/shared && pip install -e .

# Copy application code
COPY agent-launcher .

# Set up gcloud configuration for Cloud Run service
ENV CLOUDSDK_CONFIG=/tmp/gcloud_config
ENV TMPDIR=/tmp
ENV HOME=/tmp

# Create writable directories for gcloud
RUN mkdir -p /tmp/gcloud_config /tmp/.config/gcloud /tmp/.cache && \\
    chmod -R 777 /tmp

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
cat > .dockerignore.agent-launcher << EOF
# Exclude all other services except agent-launcher and shared
admin-dashboard/
agent-bridge/
agent-studio/
agent-engine/
agent-tuning-service/
alchemist-monitor-service/
banking-api-service/
knowledge-vault/
mcp_config_generator/
prompt-engine/
sandbox-console/
user-deployment-monitor/
tool-forge/
billing-service/
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

# Exclude all credentials - Cloud Run uses default service account
firebase-credentials.json
**/firebase-credentials.json
gcloud-credentials.json
**/gcloud-credentials.json
service-account-key.json
**/service-account-key.json
shared/spanner-key.json
**/secrets/
**/credentials/
**/keys/
**/certificates/

# Exclude shared libraries build artifacts
shared/build/
shared/dist/

# Include what we need for agent-launcher
!agent-launcher/
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
cp .dockerignore.agent-launcher .dockerignore

# Build and submit to Cloud Build
echo -e "${YELLOW}🔨 Building and pushing image with Cloud Build...${NC}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create a temporary cloudbuild.yaml for custom Dockerfile
cat > cloudbuild-temp.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.agent-launcher', '-t', '${IMAGE_NAME}:latest', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:latest']
- name: 'gcr.io/cloud-builders/docker'
  args: ['tag', '${IMAGE_NAME}:latest', '${IMAGE_NAME}:${TIMESTAMP}']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:${TIMESTAMP}']
EOF

if ! gcloud builds submit --config=cloudbuild-temp.yaml .; then
    echo -e "${RED}❌ Build failed! Check the build logs above.${NC}"
    exit 1
fi

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"

# Build environment variables from agent-launcher/.env
ENV_VARS=""
if [ -f "agent-launcher/.env" ]; then
    echo -e "${BLUE}📋 Loading environment variables from agent-launcher/.env...${NC}"
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
        # Skip empty values, commented out variables, and reserved Cloud Run variables
        if [[ -n "$value" && ! "$line" =~ ^[[:space:]]*# && "$key" != "GOOGLE_APPLICATION_CREDENTIALS" && "$key" != "PORT" ]]; then
            if [ -n "$ENV_VARS" ]; then
                ENV_VARS="$ENV_VARS,$key=$value"
            else
                ENV_VARS="$key=$value"
            fi
        fi
    done < "agent-launcher/.env"
fi

# Override with production-specific values
ENV_VARS="$ENV_VARS,ENVIRONMENT=production,PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}"

# Cloud Run will use default service account - no GOOGLE_APPLICATION_CREDENTIALS needed

# Validate environment variables
if [ -z "$ENV_VARS" ] || [ "$ENV_VARS" = "," ]; then
    echo -e "${YELLOW}⚠️  No environment variables found. Using minimal configuration${NC}"
    ENV_VARS="ENVIRONMENT=production,PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}"
fi

echo -e "${BLUE}🔧 Setting environment variables: $ENV_VARS${NC}"

if ! gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 5 \
    --set-env-vars "$ENV_VARS"; then
    echo -e "${RED}❌ Deployment failed! Check the deployment logs above.${NC}"
    exit 1
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

# Clean up temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f Dockerfile.agent-launcher cloudbuild-temp.yaml .dockerignore.agent-launcher

# Restore original .dockerignore if it existed
if [ -f ".dockerignore.backup" ]; then
    mv .dockerignore.backup .dockerignore
else
    rm -f .dockerignore
fi

echo ""
echo -e "${GREEN}🎉 Agent Launcher deployment complete!${NC}"
echo -e "${GREEN}📝 Service URL: ${SERVICE_URL}${NC}"
echo ""

# Health check
echo -e "${YELLOW}🏥 Running health check...${NC}"
if curl -f -s "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Service may still be starting up. Check logs with:"
    echo "gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\""
fi

echo ""
echo -e "${GREEN}🎉 Agent Launcher deployment complete!${NC}"
echo ""
echo -e "${BLUE}📋 Cloud Run Configuration:${NC}"
echo -e "${GREEN}✅ Using Cloud Run default service account${NC}"
echo -e "${BLUE}ℹ️  Ensure your service account has these roles:${NC}"
echo -e "${BLUE}   - Firebase Admin${NC}"
echo -e "${BLUE}   - Cloud Storage Admin${NC}"
echo -e "${BLUE}   - Cloud Run Admin (for triggering deployment jobs)${NC}"
echo -e "${BLUE}   - Cloud Run Jobs Admin${NC}"
echo -e "${BLUE}   - Cloud Build Service Account${NC}"
echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo -e "${BLUE}1. Deploy the agent deployment job: ./deploy-agent-job.sh${NC}"
echo -e "${BLUE}2. Set up Firestore trigger: ./deploy-agent-deployment-trigger.sh${NC}"
echo -e "${BLUE}3. Test deployment by creating a document in agent_deployments collection${NC}"
echo ""
echo -e "${BLUE}💡 Useful commands:${NC}"
echo -e "${BLUE}💡 View logs: gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\" --limit=50${NC}"
echo -e "${BLUE}💡 Stream logs: gcloud logs tail --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\"${NC}"
echo -e "${BLUE}💡 Redeploy: ./deploy-agent-launcher.sh${NC}"
echo -e "${BLUE}💡 Scale down: gcloud run services update ${SERVICE_NAME} --region=${REGION} --max-instances=0${NC}"