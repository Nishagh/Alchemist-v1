#!/bin/bash
# Deployment script for Global Narrative Framework to Google Cloud Run
# Uses gcloud build and properly integrates alchemist-shared like other modules

set -e

# Configuration - detect project from gcloud config
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="global-narrative-framework"
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

echo -e "${GREEN}🚀 Deploying Global Narrative Framework${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if .env file exists and load it
if [ -f "global-narative-framework/.env" ]; then
  echo -e "${BLUE}📋 Loading environment variables from .env file...${NC}"
  source global-narative-framework/.env
else
  echo -e "${YELLOW}⚠️  Warning: .env file not found in global-narative-framework/. Will use default values.${NC}"
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

# Copy shared module to local directory for Docker context
echo -e "${BLUE}📦 Preparing shared module...${NC}"
cd global-narative-framework
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

# Verify required files exist
echo -e "${YELLOW}📦 Verifying project structure...${NC}"
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found in global-narative-framework directory${NC}"
    exit 1
fi
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found in global-narative-framework directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Project structure verified${NC}"

# Create deployment-specific .dockerignore
echo -e "${YELLOW}📝 Creating deployment .dockerignore...${NC}"
cat > .dockerignore.deploy << EOF
# Development files
.env*
!.env.example
.vscode/
.idea/
*.swp
*.swo

# Git and version control
.git/
.gitignore
.gitkeep

# Python cache and virtual environments
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
env/
.venv/
test_env/
*.egg-info/

# Testing and coverage
tests/
*test*/
test_*/
*.test.py
*.spec.py
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# OS files
.DS_Store
Thumbs.db

# Temporary and cache files
.cache/
tmp/
temp/
*.tmp
*.log
*.pid
*.seed
*.pid.lock

# Documentation and scripts
docs/
scripts/
deploy*.sh
cloudbuild*.yaml
Makefile

# Credentials and secrets
firebase-credentials.json
gcloud-credentials.json
service-account-key.json
secrets/
credentials/
keys/
certificates/

# Build artifacts
build/
dist/

# Vector data and large files
vector_data*/
*.bin
*.sqlite3
*.db

# Include what we need
!main.py
!gnf/
!shared/
!requirements.txt
!firebase.json
!firestore.rules
!firestore.indexes.json
EOF

# Backup original .dockerignore if it exists
if [ -f ".dockerignore" ]; then
    cp .dockerignore .dockerignore.backup
fi

# Use deployment .dockerignore
cp .dockerignore.deploy .dockerignore

# Build using Cloud Build
echo -e "${BLUE}🔨 Building image with Cloud Build...${NC}"
gcloud builds submit --tag=$IMAGE_NAME

# Deploy to Cloud Run with secrets
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=80 \
  --max-instances=5 \
  --min-instances=0 \
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},FIREBASE_PROJECT_ID=${PROJECT_ID},SPANNER_INSTANCE_ID=alchemist-graph,SPANNER_DATABASE_ID=agent-stories,PYTHONPATH=/app" \
  --set-secrets="OPENAI_API_KEY=${SECRET_NAME}:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

# Cleanup temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f .dockerignore.deploy

# Restore original .dockerignore if it existed
if [ -f ".dockerignore.backup" ]; then
    mv .dockerignore.backup .dockerignore
else
    rm -f .dockerignore
fi

# Cleanup shared directory
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
sleep 10
if curl -s -f "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Service may still be starting up. Check logs with:"
    echo "gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\""
fi

echo ""
echo -e "${GREEN}🎉 Global Narrative Framework deployment complete!${NC}"
echo -e "${BLUE}💡 To view logs: gcloud logs read --project=${PROJECT_ID} --filter=\"resource.labels.service_name=${SERVICE_NAME}\"${NC}"
echo -e "${BLUE}💡 To redeploy: ./deploy-global-narrative-framework.sh${NC}"