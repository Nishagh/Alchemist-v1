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

# Configuration variables - detect project from gcloud config
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="alchemist-agent-studio"
SERVICE_NAME="alchemist-agent-studio"
MEMORY="512Mi"
CPU="1"

# Validate that project ID was found
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No Google Cloud project set. Run 'gcloud config set project YOUR_PROJECT_ID' first.${NC}"
    exit 1
fi

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

# Generate a timestamp for unique image versioning
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:$TIMESTAMP"

# Get Firebase configuration from project
echo -e "${YELLOW}Configuring Firebase settings for project: ${PROJECT_ID}${NC}"
FIREBASE_API_KEY=$(gcloud services list --filter="name:firebase.googleapis.com" --format="value(name)" --project=$PROJECT_ID > /dev/null 2>&1 && echo "AIzaSyC9MLh9IiFIcH5RJRVLJlrTXNI5s03r4AE" || echo "AIzaSyC9MLh9IiFIcH5RJRVLJlrTXNI5s03r4AE")

# Configure service URLs dynamically based on current project
# Try to get actual service URLs, fallback to default pattern if services exist
echo -e "${YELLOW}Detecting deployed service URLs...${NC}"

# Function to get service URL or construct default
get_service_url() {
    local service_name=$1
    local url=$(gcloud run services describe $service_name --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
    if [ -z "$url" ]; then
        # Construct default URL pattern
        echo "https://$service_name-851487020021.us-central1.run.app"
    else
        echo "$url"
    fi
}

AGENT_ENGINE_URL=$(get_service_url "alchemist-agent-engine")
KNOWLEDGE_VAULT_URL=$(get_service_url "alchemist-knowledge-vault")
GNF_SERVICE_URL=$(get_service_url "global-narrative-framework")
PROMPT_ENGINE_URL=$(get_service_url "alchemist-prompt-engine")
TOOL_FORGE_URL=$(get_service_url "alchemist-tool-forge")
BILLING_SERVICE_URL=$(get_service_url "billing-service")

echo -e "${BLUE}Service URLs configured:${NC}"
echo -e "  Agent Engine: ${AGENT_ENGINE_URL}"
echo -e "  Knowledge Vault: ${KNOWLEDGE_VAULT_URL}"
echo -e "  Global Narrative Framework: ${GNF_SERVICE_URL}"
echo -e "  Prompt Engine: ${PROMPT_ENGINE_URL}"

# Create a cloudbuild.yaml with build args for dynamic configuration
echo -e "${YELLOW}Creating dynamic build configuration...${NC}"
cat > cloudbuild-agent-studio.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: 
  - 'build'
  - '--build-arg'
  - 'PROJECT_ID=${PROJECT_ID}'
  - '--build-arg'
  - 'REACT_APP_FIREBASE_API_KEY=${FIREBASE_API_KEY}'
  - '--build-arg'
  - 'REACT_APP_FIREBASE_AUTH_DOMAIN=${PROJECT_ID}.firebaseapp.com'
  - '--build-arg'
  - 'REACT_APP_FIREBASE_PROJECT_ID=${PROJECT_ID}'
  - '--build-arg'
  - 'REACT_APP_FIREBASE_STORAGE_BUCKET=${PROJECT_ID}.appspot.com'
  - '--build-arg'
  - 'REACT_APP_FIREBASE_MESSAGING_SENDER_ID=851487020021'
  - '--build-arg'
  - 'REACT_APP_FIREBASE_APP_ID=1:851487020021:web:527efbdbe1ded9aa2686bc'
  - '--build-arg'
  - 'REACT_APP_AGENT_ENGINE_URL=${AGENT_ENGINE_URL}'
  - '--build-arg'
  - 'REACT_APP_KNOWLEDGE_VAULT_URL=${KNOWLEDGE_VAULT_URL}'
  - '--build-arg'
  - 'REACT_APP_GNF_SERVICE_URL=${GNF_SERVICE_URL}'
  - '--build-arg'
  - 'REACT_APP_PROMPT_ENGINE_URL=${PROMPT_ENGINE_URL}'
  - '--build-arg'
  - 'REACT_APP_TOOL_FORGE_URL=${TOOL_FORGE_URL}'
  - '--build-arg'
  - 'REACT_APP_BILLING_SERVICE_URL=${BILLING_SERVICE_URL}'
  - '-t'
  - '${IMAGE_URL}'
  - '.'
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_URL}']
EOF

# Use Cloud Build to build and push the image with dynamic configuration
echo -e "${YELLOW}Submitting build to Cloud Build with dynamic configuration...${NC}"
gcloud builds submit --config=cloudbuild-agent-studio.yaml .

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

# Cleanup temporary files
echo -e "${YELLOW}Cleaning up temporary build files...${NC}"
rm -f cloudbuild-agent-studio.yaml

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Your Agent Studio application is available at: ${SERVICE_URL}${NC}"
echo -e "${BLUE}Connected Services:${NC}"
echo -e "  Agent Engine: ${AGENT_ENGINE_URL}"
echo -e "  Knowledge Vault: ${KNOWLEDGE_VAULT_URL}"
echo -e "  Global Narrative Framework: ${GNF_SERVICE_URL}"
echo -e "  Prompt Engine: ${PROMPT_ENGINE_URL}"
echo ""
echo -e "${BLUE}To view logs:${NC}"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\"" 