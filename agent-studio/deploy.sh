#!/bin/bash

# Agent Studio Frontend Deployment Script for Google Cloud Run
# This script deploys the React frontend as a static site using nginx

set -e  # Exit immediately if a command exits with a non-zero status

# Color codes for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration variables - you can modify these as needed
REGION="us-central1"
REPO_NAME="alchemist-agent-studio"
SERVICE_NAME="alchemist-agent-studio"
MEMORY="512Mi"
CPU="1"
PROJECT_ID=alchemist-e69bb

echo -e "${BLUE}=== Agent Studio Frontend Deployment to Google Cloud Run ===${NC}"

# Note: Frontend-only deployment - no server-side Firebase credentials needed
echo -e "${GREEN}Deploying frontend-only React application with nginx...${NC}"

# Ensure gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: Google Cloud SDK (gcloud) is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated with gcloud
echo -e "${YELLOW}Checking Google Cloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}You need to authenticate with Google Cloud.${NC}"
    gcloud auth login
else
    echo -e "${GREEN}Already authenticated with Google Cloud.${NC}"
fi

# Set project ID
echo -e "${YELLOW}Setting Google Cloud project to: ${PROJECT_ID}${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs for frontend deployment
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
echo -e "${GREEN}APIs enabled successfully.${NC}"

# Create Artifact Registry repository if it doesn't exist
echo -e "${YELLOW}Checking for Artifact Registry repository...${NC}"
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION &> /dev/null; then
    echo -e "${YELLOW}Creating Artifact Registry repository: ${REPO_NAME}${NC}"
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for Agent Studio"
else
    echo -e "${GREEN}Repository ${REPO_NAME} already exists.${NC}"
fi

# Skip Secret Manager setup - not needed for frontend-only deployment
echo -e "${YELLOW}Skipping Secret Manager setup (frontend-only deployment)...${NC}"

# Generate a timestamp for unique image versioning
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:$TIMESTAMP"

# Use Cloud Build to build and push the image
echo -e "${YELLOW}Submitting build to Cloud Build...${NC}"
gcloud builds submit --tag $IMAGE_URL

# Deploy to Cloud Run as frontend-only service
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URL \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 80 \
    --memory $MEMORY \
    --cpu $CPU

# Note: Environment variables are baked into the build - no runtime env vars needed for frontend
echo -e "${YELLOW}Environment variables are compiled into the React build during Docker build process.${NC}"

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Your application is available at: ${SERVICE_URL}${NC}"
echo -e "${BLUE}To view logs:${NC}"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\"" 