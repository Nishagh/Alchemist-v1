#!/bin/bash

# Auto-generated deployment script
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-alchemist-e69bb}"
SERVICE_NAME="agent-bridge"
REGION="${REGION:-us-central1}"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying $SERVICE_NAME...${NC}"

# Configure gcloud
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Ensuring required APIs are enabled...${NC}"
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Copy shared module to local directory for Docker context
echo -e "${YELLOW}📦 Preparing shared module...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi
cp -r ../shared ./shared

# Build using Cloud Build
echo -e "${YELLOW}Building image with Cloud Build...${NC}"
gcloud builds submit --tag=$IMAGE_NAME

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=1Gi \
  --timeout=300

# Cleanup shared directory
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi

echo -e "${GREEN}✅ Deployment completed!${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' 2>/dev/null || echo "Unable to get URL")
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
