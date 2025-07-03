#!/bin/bash
# Deployment script for Alchemist Prompt Engine to Google Cloud Run
# Run from the root Alchemist-v1 directory

set -e

# Configuration - detect project from gcloud config
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="alchemist-prompt-engine"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Validate that project ID was found
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No Google Cloud project set. Run 'gcloud config set project YOUR_PROJECT_ID' first.${NC}"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Alchemist Prompt Engine${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Build Context: $(pwd)"
echo ""

# Verify we're in the right directory
if [ ! -d "prompt-engine" ] || [ ! -d "shared" ]; then
    echo -e "${RED}❌ Error: Must run from Alchemist-v1 root directory${NC}"
    echo "Expected to find both 'prompt-engine' and 'shared' directories"
    exit 1
fi

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if .env file exists and load it
if [ -f ".env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from .env file...${NC}"
  source .env
elif [ -f "prompt-engine/.env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from prompt-engine/.env file...${NC}"
  source prompt-engine/.env
else
  echo -e "${YELLOW}⚠️  Warning: .env file not found. Will use default values.${NC}"
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

# Enable required APIs
echo -e "${BLUE}🔧 Ensuring required APIs are enabled...${NC}"
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com pubsub.googleapis.com spanner.googleapis.com


# Navigate to prompt-engine directory and use existing Dockerfile
echo -e "${YELLOW}📦 Preparing prompt-engine for deployment...${NC}"
cd prompt-engine

# Copy shared module to local directory for Docker context
echo -e "${BLUE}📦 Preparing shared module...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi
cp -r ../shared ./shared

# Verify required files exist
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found in prompt-engine directory${NC}"
    exit 1
fi
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found in prompt-engine directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Prompt engine structure verified${NC}"

# Build using existing Dockerfile and gcloud builds submit
echo -e "${YELLOW}🔨 Building and pushing image with Cloud Build...${NC}"
gcloud builds submit --tag=${IMAGE_NAME}

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"

# Build environment variables from .env file if it exists
ENV_VARS=""
if [ -f ".env" ]; then
    echo -e "${BLUE}📋 Loading environment variables from .env...${NC}"
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
        # Skip empty values, commented out variables, and sensitive keys that should use secrets
        if [[ -n "$value" && ! "$line" =~ ^[[:space:]]*# && "$key" != "OPENAI_API_KEY" ]]; then
            if [ -n "$ENV_VARS" ]; then
                ENV_VARS="$ENV_VARS,$key=$value"
            else
                ENV_VARS="$key=$value"
            fi
        fi
    done < ".env"
fi

# Override with production-specific values for EA3 integration
ENV_VARS="$ENV_VARS,ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},FIREBASE_PROJECT_ID=${PROJECT_ID},SPANNER_INSTANCE_ID=alchemist-graph,SPANNER_DATABASE_ID=agent-stories"

echo -e "${BLUE}🔧 Setting environment variables: $ENV_VARS${NC}"

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 5 \
    --set-env-vars "$ENV_VARS" \
    --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

# Cleanup shared directory
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi

# Go back to root directory
cd ..

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}📊 Health Check: ${SERVICE_URL}/health${NC}"
echo -e "${GREEN}📖 API Docs: ${SERVICE_URL}/docs${NC}"
echo ""

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -s -f "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Service may still be starting up. Check logs with:"
    echo "gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\""
fi

echo ""
echo -e "${GREEN}🎉 Prompt Engine deployment complete!${NC}"
echo -e "${BLUE}💡 To view logs: gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\"${NC}"
echo -e "${BLUE}💡 To redeploy: ./deploy-prompt-engine.sh${NC}"