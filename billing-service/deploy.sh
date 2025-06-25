#!/bin/bash

# Alchemist Billing Service Deployment Script
# Deploys the billing service to Google Cloud Run

set -e

# Configuration
PROJECT_ID="alchemist-e69bb"
SERVICE_NAME="billing-service"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of Alchemist Billing Service...${NC}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}Setting Google Cloud project...${NC}"
gcloud config set project ${PROJECT_ID}

# Navigate to parent directory for build context (needed for shared module access)
cd ..

# Validate deployment security - ensure no credential files in build context
echo -e "${YELLOW}Validating deployment security...${NC}"
if [ -f "billing-service/firebase-credentials.json" ] || [ -f "billing-service/gcloud-credentials.json" ] || [ -f "billing-service/service-account-key.json" ]; then
    echo -e "${RED}Security Error: Credential files found in deployment directory!${NC}"
    echo -e "${RED}Firebase credentials should not be included in cloud deployments.${NC}"
    echo -e "${RED}Please ensure .dockerignore excludes: firebase-credentials.json, gcloud-credentials.json, service-account-key.json${NC}"
    exit 1
fi

# Build the Docker image with current directory as context (parent of billing-service)
echo -e "${YELLOW}Building Docker image...${NC}"
docker build --platform linux/amd64 -t ${IMAGE_NAME} -f billing-service/Dockerfile .

# Tag the image with latest
docker tag ${IMAGE_NAME} ${IMAGE_NAME}:latest

# Push the image to Google Container Registry
echo -e "${YELLOW}Pushing image to GCR...${NC}"
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 100 \
    --set-env-vars "FIREBASE_PROJECT_ID=${PROJECT_ID}" \
    --set-env-vars "DEBUG=false" \
    --set-env-vars "LOG_LEVEL=INFO" \
    --set-env-vars "RAZORPAY_KEY_ID=rzp_test_k5THxV7SS2yIH2" \
    --set-env-vars "RAZORPAY_KEY_SECRET=go3WDjIae5q5wFLUzL61eYkN" \
    --set-env-vars "RAZORPAY_WEBHOOK_SECRET=Alchemist@29"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}Health check: ${SERVICE_URL}/api/v1/health${NC}"

# Test the deployment
echo -e "${YELLOW}Testing deployment...${NC}"
if curl -f "${SERVICE_URL}/api/v1/health" > /dev/null 2>&1; then
    echo -e "${GREEN}Health check passed! Service is running.${NC}"
else
    echo -e "${RED}Health check failed. Please check the logs.${NC}"
    gcloud run services logs read ${SERVICE_NAME} --region ${REGION} --limit 50
fi