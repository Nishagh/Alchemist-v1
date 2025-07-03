#!/bin/bash

# Agent Tuning Service Deployment Script

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
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Agent Tuning Service${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install it first.${NC}"
    exit 1
fi

# Authenticate with Google Cloud
echo -e "${YELLOW}🔐 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Authenticating with Google Cloud...${NC}"
    gcloud auth login
fi

# Set project
gcloud config set project ${PROJECT_ID}

# Configure Docker for gcr.io
echo -e "${YELLOW}🐳 Configuring Docker for Google Container Registry...${NC}"
gcloud auth configure-docker

# Copy shared module to local directory for Docker context
echo -e "${YELLOW}📦 Preparing shared module...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi
cp -r ../shared ./shared

# Build the Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

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

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}📊 Health Check: ${SERVICE_URL}/health/${NC}"
echo -e "${GREEN}📖 API Docs: ${SERVICE_URL}/docs${NC}"
echo ""

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -s -f "${SERVICE_URL}/health/" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Service may still be starting up. Check logs with:"
    echo "gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\""
fi

echo ""
echo -e "${GREEN}🎉 Agent Tuning Service deployment complete!${NC}"