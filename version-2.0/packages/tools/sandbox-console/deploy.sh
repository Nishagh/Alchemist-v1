#!/bin/bash
# Deployment script for Alchemist Sandbox Console Service
# 
# Usage:
#   ./deploy.sh              # Deploy to Google Cloud Run using Cloud Build (default)
#   ./deploy.sh --local      # Deploy locally
#   ./deploy.sh --docker     # Deploy to Google Cloud Run using local Docker build
#
# This script deploys the standalone agent to Google Cloud Run by default

set -e  # Exit on error

# Configuration variables
KNOWLEDGE_BASE_URL=${KNOWLEDGE_BASE_URL:-"https://alchemist-knowledge-vault-b3hpe34qdq-uc.a.run.app"}
DEFAULT_AGENT_ID=${DEFAULT_AGENT_ID:-"8e18dfe2-1478-4bb3-a9ee-894ff1ac81e7"}
# OPENAI_API_KEY is now managed as a Google Secret (openai-api-key)
GCP_PROJECT_ID=${GCP_PROJECT_ID:-"alchemist-e69bb"}
SERVICE_NAME=${SERVICE_NAME:-"alchemist-sandbox-console"}
REGION=${REGION:-"us-central1"}
IMAGE_NAME=${IMAGE_NAME:-"gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Alchemist Sandbox Console Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Default: Google Cloud Run Deployment${NC}"
echo -e "${GREEN}Use --local for local deployment${NC}"
echo -e "${GREEN}Use --docker for local Docker build${NC}"
echo ""

# Check for required environment variables
check_env_var() {
  local var_name=$1
  local var_value=${!var_name}
  
  if [ -z "$var_value" ]; then
    echo -e "${YELLOW}WARNING: $var_name is not set.${NC}"
    return 1
  else
    echo -e "${GREEN}$var_name is set.${NC}"
    return 0
  fi
}

# Install dependencies
install_dependencies() {
  echo -e "\n${GREEN}Installing dependencies...${NC}"
  pip install -r requirements.txt
  echo -e "${GREEN}Dependencies installed successfully.${NC}"
}

# Create or update .env file
update_env_file() {
  echo -e "\n${GREEN}Updating .env file...${NC}"
  
  # Create .env file if it doesn't exist
  touch .env
  
  # Update environment variables in .env file
  if [ ! -z "$KNOWLEDGE_BASE_URL" ]; then
    grep -q "^KNOWLEDGE_BASE_URL=" .env && sed -i.bak "s|^KNOWLEDGE_BASE_URL=.*|KNOWLEDGE_BASE_URL=$KNOWLEDGE_BASE_URL|" .env || echo "KNOWLEDGE_BASE_URL=$KNOWLEDGE_BASE_URL" >> .env
  fi
  
  if [ ! -z "$DEFAULT_AGENT_ID" ]; then
    grep -q "^DEFAULT_AGENT_ID=" .env && sed -i.bak "s|^DEFAULT_AGENT_ID=.*|DEFAULT_AGENT_ID=$DEFAULT_AGENT_ID|" .env || echo "DEFAULT_AGENT_ID=$DEFAULT_AGENT_ID" >> .env
  fi
  
  
  if [ ! -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    grep -q "^GOOGLE_APPLICATION_CREDENTIALS=" .env && sed -i.bak "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS|" .env || echo "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS" >> .env
  fi
  
  # Clean up backup files created by sed
  rm -f .env.bak
  
  echo -e "${GREEN}.env file updated successfully.${NC}"
}

# Verify Knowledge Base Service connection
verify_knowledge_base() {
  echo -e "\n${GREEN}Verifying Knowledge Base Service connection...${NC}"
  
  # Run the test script
  if python3 test_knowledge_base.py; then
    echo -e "${GREEN}Knowledge Base Service connection verified successfully.${NC}"
    return 0
  else
    echo -e "${RED}Knowledge Base Service connection verification failed.${NC}"
    return 1
  fi
}

# Check if Dockerfile exists
check_dockerfile() {
  echo -e "\n${GREEN}Checking for Dockerfile...${NC}"
  
  if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found in the project.${NC}"
    echo -e "${RED}Please ensure the Dockerfile exists before deploying.${NC}"
    exit 1
  else
    echo -e "${GREEN}Dockerfile found. Using existing Dockerfile for deployment.${NC}"
  fi
}

# Build Docker image
build_docker_image() {
  echo -e "\n${GREEN}Building Docker image...${NC}"
  
  # Check if Dockerfile exists
  check_dockerfile
  
  # Build the image locally
  docker build -t ${SERVICE_NAME} .
  
  echo -e "${GREEN}Docker image built successfully.${NC}"
}

# Push Docker image to Google Container Registry
push_to_gcr() {
  echo -e "\n${GREEN}Pushing Docker image to Google Container Registry...${NC}"
  
  # Tag the image
  docker tag ${SERVICE_NAME} ${IMAGE_NAME}
  
  # Push the image
  docker push ${IMAGE_NAME}
  
  echo -e "${GREEN}Docker image pushed to GCR successfully.${NC}"
}

# Build with Google Cloud Build
gcloud_build() {
  echo -e "\n${GREEN}Building with Google Cloud Build...${NC}"
  
  # Check if Dockerfile exists
  check_dockerfile
  
  # Copy shared module to local directory for Docker context
  echo -e "${YELLOW}📦 Preparing shared module...${NC}"
  if [ -d "./shared" ]; then
      rm -rf ./shared
  fi
  cp -r ../shared ./shared
  
  # Submit the build to Google Cloud Build
  gcloud builds submit --tag ${IMAGE_NAME} .
  
  echo -e "${GREEN}Google Cloud Build completed successfully.${NC}"
}

# Deploy to Google Cloud Run
deploy_to_cloud_run() {
  echo -e "\n${GREEN}Deploying to Google Cloud Run...${NC}"
  
  # Deploy to Cloud Run with secrets
  gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars="KNOWLEDGE_BASE_URL=${KNOWLEDGE_BASE_URL},DEFAULT_AGENT_ID=${DEFAULT_AGENT_ID}" \
    --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest"
  
  echo -e "${GREEN}Deployed to Google Cloud Run successfully.${NC}"
}

# Main deployment function
deploy() {
  echo -e "\n${GREEN}Starting deployment...${NC}"
  
  # Check environment variables
  echo -e "\n${GREEN}Checking environment variables...${NC}"
  check_env_var "KNOWLEDGE_BASE_URL"
  
  if ! check_env_var "DEFAULT_AGENT_ID"; then
    echo -e "${YELLOW}DEFAULT_AGENT_ID is not set. Please provide an agent ID to continue.${NC}"
    read -p "Enter DEFAULT_AGENT_ID: " DEFAULT_AGENT_ID
    export DEFAULT_AGENT_ID=$DEFAULT_AGENT_ID
  fi
  
  # OPENAI_API_KEY is managed as a Google Secret (openai-api-key)
  echo -e "${GREEN}✅ Using existing Google Secret for OPENAI_API_KEY${NC}"
  
  # Check if requirements.txt exists, create if not
  if [ ! -f "requirements.txt" ]; then
    echo -e "\n${YELLOW}requirements.txt not found. Creating...${NC}"
    cat > requirements.txt << EOF
langchain==0.0.247
langchain_openai==0.0.2.post1
openai>=1.0.0
firebase-admin>=6.0.0
python-dotenv>=1.0.0
requests>=2.25.0
EOF
    echo -e "${GREEN}requirements.txt created successfully.${NC}"
  fi
  
  # Deploy to Google Cloud by default
  # Use --local flag to force local deployment: ./deploy.sh --local
  if [[ "$1" == "--local" ]]; then
    echo -e "\n${GREEN}Local deployment mode selected...${NC}"
    
    # Install dependencies
    install_dependencies
    
    # Update .env file
    update_env_file
    
    # Verify Knowledge Base Service connection
    if verify_knowledge_base; then
      echo -e "\n${GREEN}Local deployment completed successfully!${NC}"
      echo -e "${GREEN}The standalone agent is now ready to use with Knowledge Base Service integration.${NC}"
    else
      echo -e "\n${YELLOW}Local deployment completed with warnings.${NC}"
      echo -e "${YELLOW}The Knowledge Base Service connection could not be verified.${NC}"
      echo -e "${YELLOW}Check the connection and try again later.${NC}"
    fi
  else
    # Default: Google Cloud Run deployment
    echo -e "\n${GREEN}Proceeding with Google Cloud Run deployment...${NC}"
    
    # Check GCP project ID
    if ! check_env_var "GCP_PROJECT_ID"; then
      echo -e "${YELLOW}GCP_PROJECT_ID is not set. Please provide a Google Cloud Project ID to continue.${NC}"
      read -p "Enter GCP_PROJECT_ID: " GCP_PROJECT_ID
      export GCP_PROJECT_ID=$GCP_PROJECT_ID
      IMAGE_NAME="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest"
    fi
    
    # Check for gcloud CLI
    if ! command -v gcloud &> /dev/null; then
      echo -e "${RED}Error: gcloud CLI not found. Please install the Google Cloud SDK first.${NC}"
      echo -e "${YELLOW}Visit: https://cloud.google.com/sdk/docs/install${NC}"
      exit 1
    fi
    
    # Check gcloud auth
    echo -e "\n${GREEN}Checking Google Cloud authentication...${NC}"
    if ! gcloud auth print-access-token &> /dev/null; then
      echo -e "${YELLOW}You need to authenticate with Google Cloud.${NC}"
      gcloud auth login
    fi
    
    # Enable required APIs
    echo -e "\n${GREEN}Enabling required APIs...${NC}"
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com
    
    # Use Google Cloud Build by default (use --docker flag for local build)
    if [[ "$1" == "--docker" ]]; then
      echo -e "\n${GREEN}Using local Docker build...${NC}"
      # Local Docker build
      build_docker_image
      push_to_gcr
    else
      echo -e "\n${GREEN}Using Google Cloud Build...${NC}"
      # Google Cloud Build (default)
      gcloud_build
    fi
    
    # Deploy to Cloud Run
    deploy_to_cloud_run
    
    # Cleanup shared directory
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    if [ -d "./shared" ]; then
        rm -rf ./shared
    fi
    
    echo -e "\n${GREEN}Google Cloud Run deployment completed successfully!${NC}"
    echo -e "${GREEN}The standalone agent is now deployed and ready to use.${NC}"
  fi
}

# Execute the deployment
deploy
