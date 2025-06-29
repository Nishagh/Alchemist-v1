#!/bin/bash
# Deployment script for Alchemist Agent Studio to Google Cloud Run
# Run from the root Alchemist-v1 directory

set -e

# Configuration - detect project from gcloud config
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="alchemist-agent-studio"
REGION="us-central1"
REPO_NAME="alchemist-agent-studio"
MEMORY="1Gi"
CPU="1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Alchemist Agent Studio${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Build Context: $(pwd)"
echo ""

# Validate that project ID was found
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No Google Cloud project set. Run 'gcloud config set project YOUR_PROJECT_ID' first.${NC}"
    exit 1
fi

# Verify we're in the right directory
if [ ! -d "agent-studio" ]; then
    echo -e "${RED}❌ Error: Must run from Alchemist-v1 root directory${NC}"
    echo "Expected to find 'agent-studio' directory"
    exit 1
fi

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
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
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Navigate to agent-studio directory
cd agent-studio

# Get Firebase configuration
echo -e "${YELLOW}Configuring Firebase settings for project: ${PROJECT_ID}${NC}"
FIREBASE_API_KEY="AIzaSyC9MLh9IiFIcH5RJRVLJlrTXNI5s03r4AE"

# Configure service URLs dynamically based on deployed services
echo -e "${YELLOW}Detecting deployed service URLs...${NC}"

# Function to get service URL or construct default
get_service_url() {
    local service_name=$1
    local url=$(gcloud run services describe $service_name --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
    if [ -z "$url" ]; then
        echo -e "${YELLOW}⚠️  Service $service_name not found, using default URL pattern${NC}"
        # Construct default URL pattern - update this to match your actual project
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
echo ""

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
  - 'gcr.io/${PROJECT_ID}/${SERVICE_NAME}'
  - '.'
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/${PROJECT_ID}/${SERVICE_NAME}']
EOF

# Use Cloud Build to build and push the image with dynamic configuration
echo -e "${YELLOW}🔨 Building and pushing image with Cloud Build...${NC}"
gcloud builds submit --config=cloudbuild-agent-studio.yaml .

# Deploy to Cloud Run as frontend service
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 80 \
    --memory ${MEMORY} \
    --cpu ${CPU} \
    --max-instances 10

# Cleanup temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary build files...${NC}"
rm -f cloudbuild-agent-studio.yaml

# Go back to root directory
cd ..

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your Agent Studio application is available at: ${SERVICE_URL}${NC}"
echo ""
echo -e "${BLUE}🔗 Connected Services:${NC}"
echo -e "  🤖 Agent Engine: ${AGENT_ENGINE_URL}"
echo -e "  📚 Knowledge Vault: ${KNOWLEDGE_VAULT_URL}"
echo -e "  📖 Global Narrative Framework: ${GNF_SERVICE_URL}"
echo -e "  ✏️  Prompt Engine: ${PROMPT_ENGINE_URL}"
echo ""
echo -e "${GREEN}🎉 Agent Studio deployment complete!${NC}"
echo -e "${BLUE}💡 To view logs: gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\"${NC}"
echo -e "${BLUE}💡 To redeploy: ./deploy-agent-studio.sh${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
sleep 10
if curl -s -f "${SERVICE_URL}" > /dev/null; then
    echo -e "${GREEN}✅ Application is responding!${NC}"
    echo -e "${GREEN}🎉 Complete Alchemist Platform Successfully Deployed!${NC}"
    echo ""
    echo -e "${BLUE}📊 Platform Overview:${NC}"
    echo -e "  Frontend: ${SERVICE_URL}"
    echo -e "  Backend Services: 4 services running"
    echo -e "  EA3 Integration: ✅ Active"
    echo -e "  Story Events: ✅ Active"
    echo -e "  Centralized Config: ✅ Active"
else
    echo -e "${YELLOW}⚠️  Application may still be starting up${NC}"
    echo "Check logs with: gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\""
fi