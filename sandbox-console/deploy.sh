#!/bin/bash
# Deployment script for Standalone Agent with Knowledge Base Service integration
# This script sets up the environment and deploys the standalone agent to Google Cloud Run

set -e  # Exit on error

# Configuration variables
KNOWLEDGE_BASE_URL=${KNOWLEDGE_BASE_URL:-"https://knowledge-base-service-b3hpe34qdq-uc.a.run.app"}
DEFAULT_AGENT_ID=${DEFAULT_AGENT_ID:-"8e18dfe2-1478-4bb3-a9ee-894ff1ac81e7"}
OPENAI_API_KEY=${OPENAI_API_KEY:-"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"}
GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-"firebase-credentials.json"}
GCP_PROJECT_ID=${GCP_PROJECT_ID:-"alchemist-e69bb"}
SERVICE_NAME=${SERVICE_NAME:-"standalone-agent"}
REGION=${REGION:-"us-central1"}
IMAGE_NAME=${IMAGE_NAME:-"gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}Standalone Agent Deployment Script${NC}"
echo -e "${GREEN}=================================${NC}"

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
  
  if [ ! -z "$OPENAI_API_KEY" ]; then
    grep -q "^OPENAI_API_KEY=" .env && sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|" .env || echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env
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
  
  # Submit the build to Google Cloud Build
  gcloud builds submit --tag ${IMAGE_NAME} .
  
  echo -e "${GREEN}Google Cloud Build completed successfully.${NC}"
}

# Deploy to Google Cloud Run
deploy_to_cloud_run() {
  echo -e "\n${GREEN}Deploying to Google Cloud Run...${NC}"
  
  # Deploy to Cloud Run
  gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars="KNOWLEDGE_BASE_URL=${KNOWLEDGE_BASE_URL},DEFAULT_AGENT_ID=${DEFAULT_AGENT_ID},OPENAI_API_KEY=${OPENAI_API_KEY}"
  
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
  
  if ! check_env_var "OPENAI_API_KEY"; then
    echo -e "${YELLOW}OPENAI_API_KEY is not set. Please provide an OpenAI API key to continue.${NC}"
    read -p "Enter OPENAI_API_KEY: " OPENAI_API_KEY
    export OPENAI_API_KEY=$OPENAI_API_KEY
  fi
  
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
  
  # Determine deployment type
  echo -e "\n${GREEN}Select deployment type:${NC}"
  echo "1) Local deployment"
  echo "2) Google Cloud Run deployment"
  read -p "Enter your choice (1/2): " deployment_choice
  
  case $deployment_choice in
    1)
      # Local deployment
      echo -e "\n${GREEN}Proceeding with local deployment...${NC}"
      
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
      ;;
    2)
      # Cloud deployment
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
      
      # Select build method
      echo -e "\n${GREEN}Select build method:${NC}"
      echo "1) Local Docker build and push to GCR"
      echo "2) Google Cloud Build (build in the cloud)"
      read -p "Enter your choice (1/2): " build_choice
      
      case $build_choice in
        1)
          # Local Docker build
          build_docker_image
          push_to_gcr
          ;;
        2)
          # Google Cloud Build
          gcloud_build
          ;;
        *)
          echo -e "${RED}Invalid choice. Using Google Cloud Build.${NC}"
          gcloud_build
          ;;
      esac
      
      # Deploy to Cloud Run
      deploy_to_cloud_run
      
      echo -e "\n${GREEN}Google Cloud Run deployment completed successfully!${NC}"
      echo -e "${GREEN}The standalone agent is now deployed and ready to use.${NC}"
      ;;
    *)
      echo -e "${RED}Invalid choice. Exiting.${NC}"
      exit 1
      ;;
  esac
}

# Execute the deployment
deploy
