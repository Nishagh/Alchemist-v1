#!/bin/bash
# Manual deployment script for the Prompt Engineer Service
# This script builds a new container image using Cloud Build and deploys it to Cloud Run

# Exit on error
set -e

# Configuration
PROJECT_ID="alchemist-e69bb"
SERVICE_NAME="alchemist-prompt-engine"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Run the Python script to fix imports
#echo -e "${BLUE}Running import fixes...${NC}"
#python3 fix_imports.py

# Ensure .env file exists
if [ ! -f ".env" ]; then
  echo -e "${RED}Error: .env file not found.${NC}"
  exit 1
fi

# Configure gcloud to use the current project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}Ensuring required APIs are enabled...${NC}"
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# Copy shared module to local directory for Docker context
echo -e "${BLUE}📦 Preparing shared module...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi
cp -r ../shared ./shared

# Create or update OpenAI API key secret
echo -e "${BLUE}🔐 Managing OpenAI API key secret...${NC}"
SECRET_NAME="OPENAI_API_KEY"

# Check if secret exists
if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    echo -e "   Secret $SECRET_NAME already exists"
else
    echo -e "   Creating secret $SECRET_NAME..."
    gcloud secrets create $SECRET_NAME --project=$PROJECT_ID
fi

# Update secret value if OPENAI_API_KEY is set
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo -e "   Updating secret value..."
    echo -n "$OPENAI_API_KEY" | gcloud secrets versions add $SECRET_NAME --data-file=- --project=$PROJECT_ID
else
    echo -e "   ⚠️  OPENAI_API_KEY not set in environment - using existing secret value"
fi

# Build using Cloud Build
echo -e "${BLUE}Building image with Cloud Build...${NC}"
gcloud builds submit --tag=$IMAGE_NAME

# Deploy to Cloud Run with secrets
echo -e "${BLUE}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=1Gi \
  --timeout=300 \
  --set-env-vars="ENVIRONMENT=production" \
  --set-secrets="OPENAI_API_KEY=${SECRET_NAME}:latest"

# Cleanup shared directory
echo -e "${BLUE}🧹 Cleaning up...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi

echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${GREEN}Your service should be available at:${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo -e "${GREEN}$SERVICE_URL${NC}"
echo -e "${BLUE}To test the service health:${NC}"
echo -e "${BLUE}./test_service_health.sh${NC}" 