#!/bin/bash

# Agent Studio Web Deployment Script for Google Cloud Run
# This script uses Cloud Build to build and deploy to Google Cloud Run

set -e  # Exit immediately if a command exits with a non-zero status

# Color codes for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration variables - you can modify these as needed
REGION="us-central1"
REPO_NAME="agent-studio-web"
SERVICE_NAME="agent-studio-web"
MEMORY="512Mi"
CPU="1"
PROJECT_ID=alchemist-e69bb
FIREBASE_CREDENTIALS="firebase-credentials.json"

echo -e "${BLUE}=== Agent Studio Web Deployment to Google Cloud Run using Cloud Build ===${NC}"

# Check for Firebase credentials
echo -e "${YELLOW}Checking for Firebase credentials file...${NC}"
if [ ! -f "$FIREBASE_CREDENTIALS" ]; then
    echo -e "${RED}Error: Firebase credentials file not found at $FIREBASE_CREDENTIALS${NC}"
    echo "Please ensure your Firebase service account credentials file exists."
    exit 1
else
    echo -e "${GREEN}Firebase credentials found.${NC}"
    # Extract project ID from credentials to ensure consistency
    CREDS_PROJECT_ID=$(grep -o '"project_id": "[^"]*' "$FIREBASE_CREDENTIALS" | cut -d'"' -f4)
    if [ "$CREDS_PROJECT_ID" != "$PROJECT_ID" ]; then
        echo -e "${YELLOW}Warning: Project ID in credentials ($CREDS_PROJECT_ID) doesn't match configured project ID ($PROJECT_ID).${NC}"
        echo -e "${YELLOW}Using project ID from credentials file: $CREDS_PROJECT_ID${NC}"
        PROJECT_ID=$CREDS_PROJECT_ID
    fi
fi

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

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable firebase.googleapis.com
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

# Store Firebase credentials in Secret Manager if not already there
echo -e "${YELLOW}Ensuring Firebase credentials are stored in Secret Manager...${NC}"
SECRET_NAME="firebase-credentials"
if ! gcloud secrets describe $SECRET_NAME &> /dev/null; then
    echo -e "${YELLOW}Creating Firebase credentials secret...${NC}"
    gcloud secrets create $SECRET_NAME --replication-policy="automatic"
    gcloud secrets versions add $SECRET_NAME --data-file="$FIREBASE_CREDENTIALS"
else
    echo -e "${YELLOW}Updating Firebase credentials secret...${NC}"
    gcloud secrets versions add $SECRET_NAME --data-file="$FIREBASE_CREDENTIALS"
fi
echo -e "${GREEN}Firebase credentials stored in Secret Manager.${NC}"

# Get the Cloud Run service account
SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="EMAIL~^${PROJECT_ID}@appspot.gserviceaccount.com" --format="value(EMAIL)")
if [ -z "$SERVICE_ACCOUNT" ]; then
    echo -e "${YELLOW}Creating default service account...${NC}"
    SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
    gcloud iam service-accounts create "${PROJECT_ID}" --display-name="Default service account"
fi
echo -e "${GREEN}Using service account: ${SERVICE_ACCOUNT}${NC}"

# Grant Secret Manager access to Cloud Run service account
echo -e "${YELLOW}Granting Secret Manager access to Cloud Run service account...${NC}"
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
echo -e "${GREEN}Secret Manager access granted.${NC}"

# Generate a timestamp for unique image versioning
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:$TIMESTAMP"

# Use Cloud Build to build and push the image
echo -e "${YELLOW}Submitting build to Cloud Build...${NC}"
gcloud builds submit --tag $IMAGE_URL

# Prepare Firebase-related environment variables
FIREBASE_ENV_VARS="FIREBASE_PROJECT_ID=$PROJECT_ID"

# Deploy to Cloud Run with access to Firebase credentials
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URL \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory $MEMORY \
    --cpu $CPU \
    --set-env-vars "$FIREBASE_ENV_VARS" \
    --update-secrets "/firebase/credentials.json=firebase-credentials:latest" \
    --service-account $SERVICE_ACCOUNT

# Set additional environment variables if .env file exists
if [ -f .env ]; then
    echo -e "${YELLOW}Setting additional environment variables from .env file...${NC}"
    ENV_VARS=""
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines, comments, and Firebase-related vars (handled separately)
        if [[ -z "$line" || "$line" =~ ^# || "$line" =~ ^FIREBASE_ ]]; then
            continue
        fi
        # Add to ENV_VARS with comma if not the first variable
        if [[ -n "$ENV_VARS" ]]; then
            ENV_VARS="$ENV_VARS,$line"
        else
            ENV_VARS="$line"
        fi
    done < .env
    
    if [[ -n "$ENV_VARS" ]]; then
        gcloud run services update $SERVICE_NAME \
            --region $REGION \
            --update-env-vars $ENV_VARS
        echo -e "${GREEN}Environment variables set successfully.${NC}"
    fi
else
    echo -e "${YELLOW}No .env file found. Only Firebase environment variables were set.${NC}"
fi

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Your application is available at: ${SERVICE_URL}${NC}"
echo -e "${BLUE}To view logs:${NC}"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\"" 