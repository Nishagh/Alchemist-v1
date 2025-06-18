#!/bin/bash
# Manual deployment script for the Prompt Engineer Service
# This script builds a new container image using Cloud Build and deploys it to Cloud Run

# Exit on error
set -e

# Configuration
PROJECT_ID="alchemist-e69bb"
SERVICE_NAME="prompt-engineer-service"
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
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Build using Cloud Build
echo -e "${BLUE}Building image with Cloud Build...${NC}"
gcloud builds submit --tag=$IMAGE_NAME

# Deploy to Cloud Run with environment variables
echo -e "${BLUE}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=1Gi \
  --timeout=300 \
  --service-account="$SERVICE_NAME-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --set-env-vars="ENVIRONMENT=production,OPENAI_API_KEY=$OPENAI_API_KEY,FIREBASE_CREDENTIALS_BASE64=$FIREBASE_CREDS_BASE64"

echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${GREEN}Your service should be available at:${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo -e "${GREEN}$SERVICE_URL${NC}"
echo -e "${BLUE}To test the service health:${NC}"
echo -e "${BLUE}./test_service_health.sh${NC}" 