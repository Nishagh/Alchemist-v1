#!/bin/bash
# Deployment script for Agent Deployment Job (Cloud Run Jobs)
# Run from the root Alchemist-v1 directory

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
JOB_NAME="agent-deployment-job"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Agent Deployment Job${NC}"
echo "Project: ${PROJECT_ID}"
echo "Job: ${JOB_NAME}"
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
cat > Dockerfile.agent-job << EOF
# Dockerfile for Agent Deployment Job (Cloud Run Jobs)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app

# Install system dependencies including gcloud CLI and Docker (needed for subprocess calls)
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    apt-transport-https \\
    ca-certificates \\
    gnupg \\
    docker.io \\
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \\
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \\
    && apt-get update && apt-get install -y google-cloud-cli \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r jobuser && useradd -r -g jobuser jobuser

WORKDIR /app

# Copy requirements and install dependencies
COPY agent-launcher/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set up directory structure that deploy-ai-agent.sh expects (Alchemist-v1 root structure)
# Copy and install shared libraries first for better caching
COPY shared /app/shared
RUN cd /app/shared && pip install -e .

# Copy agent-launcher directory (needed by deploy-ai-agent.sh)
COPY agent-launcher /app/agent-launcher

# Copy deployment script to root (deploy-ai-agent.sh expects to run from root)
COPY deploy-ai-agent.sh /app/
RUN chmod +x /app/deploy-ai-agent.sh

# Copy the job script to the working directory
COPY agent-launcher/deploy_job.py /app/

# Set up gcloud configuration for Cloud Run Jobs  
ENV CLOUDSDK_CONFIG=/tmp/gcloud_config
ENV TMPDIR=/tmp
ENV HOME=/tmp

# Create writable directories for gcloud
RUN mkdir -p /tmp/gcloud_config /tmp/.config/gcloud /tmp/.cache && \\
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
cat > .dockerignore.agent-job << EOF
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

# Include what we need for agent deployment job
!agent-launcher/deploy_job.py
!agent-launcher/requirements.txt
!agent-launcher/agent-template/
!shared/
!deploy-ai-agent.sh

# Exclude deployment configs at root (but not deploy-ai-agent.sh)
cloudbuild*.yaml
deploy-agent-job.sh
deploy-to-cloud-run.sh
docker-compose*.yml
Makefile
EOF

# Backup original .dockerignore if it exists
if [ -f ".dockerignore" ]; then
    cp .dockerignore .dockerignore.backup
fi

# Use job deployment .dockerignore
cp .dockerignore.agent-job .dockerignore

# Build and submit to Cloud Build
echo -e "${YELLOW}🔨 Building and pushing job image with Cloud Build...${NC}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create build directory with all required files
BUILD_DIR="/tmp/agent-job-build"
rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}

# Copy all required files to build directory
echo -e "${BLUE}📁 Copying files to build directory...${NC}"

# Verify files exist before copying
if [ ! -f "deploy-ai-agent.sh" ]; then
    echo -e "${RED}❌ deploy-ai-agent.sh not found in current directory${NC}"
    echo "Current directory: $(pwd)"
    ls -la deploy*.sh
    exit 1
fi

cp -r agent-launcher ${BUILD_DIR}/
cp -r shared ${BUILD_DIR}/
cp deploy-ai-agent.sh ${BUILD_DIR}/
cp Dockerfile.agent-job ${BUILD_DIR}/Dockerfile
cp .dockerignore.agent-job ${BUILD_DIR}/.dockerignore

# Debug: List files in build directory
echo -e "${BLUE}📋 Build directory contents:${NC}"
ls -la ${BUILD_DIR}/

# Create cloudbuild.yaml in the build directory
cat > ${BUILD_DIR}/cloudbuild.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '${IMAGE_NAME}:latest', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:latest']
- name: 'gcr.io/cloud-builders/docker'
  args: ['tag', '${IMAGE_NAME}:latest', '${IMAGE_NAME}:${TIMESTAMP}']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}:${TIMESTAMP}']
EOF

if ! gcloud builds submit --config=${BUILD_DIR}/cloudbuild.yaml ${BUILD_DIR}; then
    echo -e "${RED}❌ Build failed! Check the build logs above.${NC}"
    exit 1
fi

# Deploy Cloud Run Job
echo -e "${YELLOW}🚀 Deploying Cloud Run Job...${NC}"

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
rm -f Dockerfile.agent-job .dockerignore.agent-job
rm -rf ${BUILD_DIR}

# Restore original .dockerignore if it existed
if [ -f ".dockerignore.backup" ]; then
    mv .dockerignore.backup .dockerignore
else
    rm -f .dockerignore
fi

echo -e "${GREEN}✅ Agent Deployment Job deployed successfully!${NC}"
echo -e "${BLUE}ℹ️  Job Name: ${JOB_NAME}${NC}"
echo -e "${BLUE}ℹ️  Region: ${REGION}${NC}"
echo -e "${BLUE}ℹ️  Image: ${IMAGE_NAME}:latest${NC}"
echo ""
echo -e "${GREEN}🎯 Next steps:${NC}"
echo -e "${BLUE}1. Update Eventarc trigger to target the job${NC}"
echo -e "${BLUE}2. Test deployment by creating a new agent deployment document${NC}"
echo -e "${BLUE}3. Monitor job executions with: gcloud run jobs list --region=${REGION}${NC}"
echo ""