#!/bin/bash

# Knowledge Base Service Cloud Run Deployment Script
# This script builds and deploys the Knowledge Base Service to Google Cloud Run

# Exit on error
set -e

# Configuration - detect project from gcloud config
PROJECT_ID=$(gcloud config get-value project)
IMAGE_NAME="alchemist-knowledge-vault"
REGION="us-central1"  # Change as needed

# Validate that project ID was found
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No Google Cloud project set. Run 'gcloud config set project YOUR_PROJECT_ID' first.${NC}"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying Knowledge Base Service v2.0.0 to Google Cloud Run...${NC}"
echo -e "${YELLOW}Using project: ${PROJECT_ID}${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null
then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Ensure user is logged in to gcloud
echo -e "${YELLOW}Checking gcloud authentication...${NC}"
gcloud auth print-access-token &> /dev/null || (echo -e "${RED}Not logged in to gcloud. Run 'gcloud auth login' first.${NC}" && exit 1)

# Set the Google Cloud project
echo -e "${YELLOW}Setting Google Cloud project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}Ensuring required APIs are enabled...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable spanner.googleapis.com

# Copy shared module to local directory for Docker context
echo -e "${YELLOW}📦 Preparing shared module...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi
cp -r ../shared ./shared

# Build the Docker image using Cloud Build
echo -e "${YELLOW}Building and pushing Docker image with Cloud Build...${NC}"
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${IMAGE_NAME} .

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"

# Extract environment variables from .env file for cloud deployment
# Note: PORT is automatically set by Cloud Run
# Knowledge vault uses hardcoded embeddings model (text-embedding-3-small)
# Auto-generate Firebase storage bucket based on current project
FIREBASE_STORAGE_BUCKET="${PROJECT_ID}.appspot.com"

gcloud run deploy ${IMAGE_NAME} \
  --image gcr.io/${PROJECT_ID}/${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --timeout 300 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars="FIREBASE_STORAGE_BUCKET=${FIREBASE_STORAGE_BUCKET},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},SPANNER_INSTANCE_ID=alchemist-graph,SPANNER_DATABASE_ID=agent-stories,ENVIRONMENT=production" \
  --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest \
  --min-instances=0

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${IMAGE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "Service URL: ${SERVICE_URL}"
echo -e "API Documentation: ${SERVICE_URL}/docs"
echo -e "${GREEN}Knowledge Base Service v2.0.0 is now running with EA3 integration!${NC}"

echo ""
echo -e "${YELLOW}⚠️  If you encounter Pub/Sub errors, ensure the Cloud Run service account has:${NC}"
echo -e "${YELLOW}   - Pub/Sub Publisher${NC}"
echo -e "${YELLOW}   - Pub/Sub Subscriber${NC}"
echo -e "${YELLOW}   - Cloud Spanner Database User${NC}"
echo -e "${YELLOW}   - Firebase Admin${NC}"