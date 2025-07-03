#!/bin/bash
# Deployment script for MCP Deployment Job (Cloud Run Jobs)
# Run from the root Alchemist-v1 directory

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
JOB_NAME="mcp-deployment-job"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying MCP Deployment Job${NC}"
echo "Project: ${PROJECT_ID}"
echo "Job: ${JOB_NAME}"
echo "Region: ${REGION}"
echo "Build Context: $(pwd)"
echo ""

# Verify we're in the right directory
if [ ! -d "tool-forge" ] || [ ! -d "shared" ]; then
    echo -e "${RED}❌ Error: Must run from Alchemist-v1 root directory${NC}"
    echo "Expected to find both 'tool-forge' and 'shared' directories"
    exit 1
fi

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
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

# Create temporary Dockerfile for job deployment
echo -e "${YELLOW}📦 Creating job deployment Dockerfile...${NC}"
cat > Dockerfile.mcp-job << EOF
# Dockerfile for MCP Deployment Job (Cloud Run Jobs)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app

# Install system dependencies including gcloud CLI (needed for subprocess calls)
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
RUN groupadd -r jobuser && useradd -r -g jobuser jobuser

WORKDIR /app

# Copy requirements and install dependencies
COPY tool-forge/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install shared libraries
COPY shared /app/shared
RUN cd /app/shared && pip install -e .

# Copy job application code
COPY tool-forge/deploy_job.py .

# Set up gcloud configuration for Cloud Run Jobs  
ENV CLOUDSDK_CONFIG=/tmp/gcloud_config
ENV TMPDIR=/tmp
ENV HOME=/tmp

# Create writable directories for gcloud
RUN mkdir -p /tmp/gcloud_config /tmp/.config/gcloud /tmp/.cache && \
    chmod -R 777 /tmp

# Set ownership (keeping /tmp permissions as set above)
RUN chown -R jobuser:jobuser /app

# Switch to non-root user
USER jobuser

# Default command - will be overridden by Cloud Run Jobs
CMD ["python", "deploy_job.py"]
EOF

# Create deployment-specific .dockerignore for job
echo -e "${YELLOW}📝 Creating job deployment .dockerignore...${NC}"
cat > .dockerignore.mcp-job << EOF
# Exclude all other services except tool-forge and shared
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
agent-launcher/
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

# Include what we need for mcp deployment job
!tool-forge/deploy_job.py
!tool-forge/requirements.txt
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

# Use job deployment .dockerignore
cp .dockerignore.mcp-job .dockerignore

# Build and submit to Cloud Build
echo -e "${YELLOW}🔨 Building and pushing job image with Cloud Build...${NC}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create a temporary cloudbuild.yaml for custom Dockerfile
cat > cloudbuild-job-temp.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.mcp-job', '-t', '${IMAGE_NAME}:latest', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:latest']
- name: 'gcr.io/cloud-builders/docker'
  args: ['tag', '${IMAGE_NAME}:latest', '${IMAGE_NAME}:${TIMESTAMP}']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:${TIMESTAMP}']
EOF

if ! gcloud builds submit --config=cloudbuild-job-temp.yaml .; then
    echo -e "${RED}❌ Build failed! Check the build logs above.${NC}"
    exit 1
fi

# Deploy Cloud Run Job
echo -e "${YELLOW}🚀 Deploying Cloud Run Job...${NC}"

# Build environment variables from tool-forge/.env
ENV_VARS=""
if [ -f "tool-forge/.env" ]; then
    echo -e "${BLUE}📋 Loading environment variables from tool-forge/.env...${NC}"
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
        # Skip empty values, commented out variables, and GOOGLE_APPLICATION_CREDENTIALS for Cloud Run
        if [[ -n "$value" && ! "$line" =~ ^[[:space:]]*# && "$key" != "GOOGLE_APPLICATION_CREDENTIALS" ]]; then
            if [ -n "$ENV_VARS" ]; then
                ENV_VARS="$ENV_VARS,$key=$value"
            else
                ENV_VARS="$key=$value"
            fi
        fi
    done < "tool-forge/.env"
fi

# Override with production-specific values
ENV_VARS="$ENV_VARS,ENVIRONMENT=production,PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}"

# Validate environment variables
if [ -z "$ENV_VARS" ] || [ "$ENV_VARS" = "," ]; then
    echo -e "${YELLOW}⚠️  No environment variables found. Using minimal configuration${NC}"
    ENV_VARS="ENVIRONMENT=production,PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}"
fi

echo -e "${BLUE}🔧 Setting environment variables: $ENV_VARS${NC}"

# Deploy the Cloud Run Job
if ! gcloud run jobs deploy ${JOB_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --memory 2Gi \
    --cpu 2 \
    --max-retries 1 \
    --parallelism 1 \
    --task-timeout 3600 \
    --set-env-vars "$ENV_VARS"; then
    echo -e "${RED}❌ Job deployment failed! Check the deployment logs above.${NC}"
    exit 1
fi

# Clean up temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f Dockerfile.mcp-job cloudbuild-job-temp.yaml .dockerignore.mcp-job

# Restore original .dockerignore if it existed
if [ -f ".dockerignore.backup" ]; then
    mv .dockerignore.backup .dockerignore
else
    rm -f .dockerignore
fi

echo -e "${GREEN}✅ MCP Deployment Job deployed successfully!${NC}"
echo -e "${BLUE}ℹ️  Job Name: ${JOB_NAME}${NC}"
echo -e "${BLUE}ℹ️  Region: ${REGION}${NC}"
echo -e "${BLUE}ℹ️  Image: ${IMAGE_NAME}:latest${NC}"
echo ""
echo -e "${GREEN}🎯 Next steps:${NC}"
echo -e "${BLUE}1. Update Eventarc trigger to target the job${NC}"
echo -e "${BLUE}2. Test deployment by creating a new MCP deployment document${NC}"
echo -e "${BLUE}3. Monitor job executions with: gcloud run jobs list --region=${REGION}${NC}"
echo ""