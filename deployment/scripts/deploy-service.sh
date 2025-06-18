#!/bin/bash

# Alchemist Service Deployment Script
# Usage: ./deploy-service.sh <service-name> [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME=${1}
ENVIRONMENT=${2:-"production"}
PROJECT_ID=${PROJECT_ID:-"alchemist-e69bb"}
REGION=${REGION:-"us-central1"}
TIMEOUT=${TIMEOUT:-"3600s"}

# Validate inputs
if [ -z "$SERVICE_NAME" ]; then
    echo -e "${RED}Error: Service name is required${NC}"
    echo "Usage: $0 <service-name> [environment]"
    echo "Available services: agent-engine, knowledge-vault, agent-bridge, agent-launcher, agent-studio, tool-forge, sandbox-console"
    exit 1
fi

# Validate service exists
SERVICE_DIR="${SERVICE_NAME}"
if [ ! -d "$SERVICE_DIR" ]; then
    echo -e "${RED}Error: Service '${SERVICE_NAME}' not found in ${SERVICE_DIR}${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Deploying ${SERVICE_NAME} to ${ENVIRONMENT}...${NC}"

# Function to check if gcloud is authenticated
check_gcloud_auth() {
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}Error: Not authenticated with gcloud. Run 'gcloud auth login'${NC}"
        exit 1
    fi
}

# Function to set project
set_project() {
    echo -e "${YELLOW}Setting project to ${PROJECT_ID}...${NC}"
    gcloud config set project $PROJECT_ID
}

# Function to validate deployment configuration
validate_deployment() {
    echo -e "${YELLOW}Validating deployment configuration...${NC}"
    
    if [ ! -f "${SERVICE_DIR}/Dockerfile" ]; then
        echo -e "${RED}Error: No Dockerfile found in ${SERVICE_DIR}${NC}"
        exit 1
    fi
    
    if [ ! -f "${SERVICE_DIR}/cloudbuild.yaml" ] && [ ! -f "cloudbuild.yaml" ]; then
        echo -e "${YELLOW}Warning: No cloudbuild.yaml found, using default build${NC}"
    fi
}

# Function to build and deploy service
deploy_service() {
    local service_name=$1
    local image_name="gcr.io/${PROJECT_ID}/alchemist-${service_name}"
    local service_config=""
    
    echo -e "${YELLOW}Building ${service_name}...${NC}"
    
    # Build from service directory for monitor service, root for others
    if [[ "$service_name" == "alchemist-monitor-service" ]]; then
        # Monitor service has its own build config
        cd "${SERVICE_DIR}"
        gcloud builds submit \
            --config=cloudbuild.yaml \
            --timeout=${TIMEOUT}
        cd ..
        return
    else
        # Build from root directory to include shared dependencies
        # Create a temporary cloudbuild.yaml for this service
        cat > cloudbuild-temp.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', '${SERVICE_DIR}/Dockerfile', '-t', '${image_name}', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${image_name}']
images:
- '${image_name}'
timeout: '${TIMEOUT}'
EOF
    fi
    
    gcloud builds submit \
        --config=cloudbuild-temp.yaml \
        --timeout=${TIMEOUT}
    
    # Clean up temporary file
    rm -f cloudbuild-temp.yaml
    
    echo -e "${YELLOW}Deploying ${service_name} to Cloud Run...${NC}"
    
    # Service-specific configurations
    case $service_name in
        "agent-engine")
            service_config="--memory=1Gi --cpu=1 --max-instances=10 --concurrency=80"
            ;;
        "knowledge-vault")
            service_config="--memory=2Gi --cpu=2 --max-instances=5 --concurrency=40"
            ;;
        "agent-bridge")
            service_config="--memory=512Mi --cpu=1 --max-instances=3 --concurrency=100"
            ;;
        "agent-studio")
            service_config="--memory=512Mi --cpu=1 --max-instances=5 --concurrency=100"
            ;;
        "agent-launcher")
            service_config="--memory=1Gi --cpu=1 --max-instances=3 --concurrency=10"
            ;;
        "tool-forge")
            service_config="--memory=512Mi --cpu=1 --max-instances=3 --concurrency=50"
            ;;
        "sandbox-console")
            service_config="--memory=1Gi --cpu=1 --max-instances=5 --concurrency=20"
            ;;
        "alchemist-monitor-service")
            service_config="--memory=1Gi --cpu=1 --max-instances=10 --min-instances=1 --concurrency=100"
            ;;
        "admin-dashboard")
            service_config="--memory=512Mi --cpu=1 --max-instances=5 --concurrency=100"
            ;;
        *)
            service_config="--memory=1Gi --cpu=1 --max-instances=3 --concurrency=80"
            ;;
    esac
    
    # Deploy to Cloud Run
    if [[ "$service_name" == "alchemist-monitor-service" ]]; then
        # Special handling for monitor service name
        gcloud run deploy "${service_name}" \
            --image=${image_name} \
            --platform=managed \
            --region=${REGION} \
            --allow-unauthenticated \
            --port=8080 \
            --set-env-vars="ENVIRONMENT=${ENVIRONMENT}" \
            ${service_config}
    else
        gcloud run deploy "alchemist-${service_name}" \
            --image=${image_name} \
            --platform=managed \
            --region=${REGION} \
            --allow-unauthenticated \
            --port=8080 \
            --set-env-vars="ENVIRONMENT=${ENVIRONMENT}" \
            ${service_config}
    fi
    
    # Get service URL
    if [[ "$service_name" == "alchemist-monitor-service" ]]; then
        SERVICE_URL=$(gcloud run services describe "${service_name}" \
            --region=${REGION} \
            --format="value(status.url)")
    else
        SERVICE_URL=$(gcloud run services describe "alchemist-${service_name}" \
            --region=${REGION} \
            --format="value(status.url)")
    fi
    
    echo -e "${GREEN}✅ ${service_name} deployed successfully!${NC}"
    echo -e "${GREEN}URL: ${SERVICE_URL}${NC}"
}

# Function to verify deployment
verify_deployment() {
    local service_name=$1
    local max_attempts=10
    local attempt=1
    
    echo -e "${YELLOW}Verifying deployment...${NC}"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "alchemist-${service_name}" \
        --region=${REGION} \
        --format="value(status.url)" 2>/dev/null || echo "")
    
    if [ -z "$SERVICE_URL" ]; then
        echo -e "${RED}❌ Could not get service URL${NC}"
        return 1
    fi
    
    # Try to reach the health endpoint
    while [ $attempt -le $max_attempts ]; do
        echo -e "${YELLOW}Attempt ${attempt}/${max_attempts}: Checking ${SERVICE_URL}/health${NC}"
        
        if curl -f -s "${SERVICE_URL}/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service is healthy and responding${NC}"
            return 0
        fi
        
        if curl -f -s "${SERVICE_URL}" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service is responding (no health endpoint)${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Service not ready, waiting 30 seconds...${NC}"
        sleep 30
        ((attempt++))
    done
    
    echo -e "${RED}❌ Service verification failed after ${max_attempts} attempts${NC}"
    return 1
}

# Main deployment process
main() {
    echo -e "${BLUE}=== Alchemist Service Deployment ===${NC}"
    echo -e "${BLUE}Service: ${SERVICE_NAME}${NC}"
    echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
    echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
    echo -e "${BLUE}Region: ${REGION}${NC}"
    echo ""
    
    check_gcloud_auth
    set_project
    validate_deployment
    deploy_service $SERVICE_NAME
    
    if verify_deployment $SERVICE_NAME; then
        echo ""
        echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
        echo -e "${GREEN}Service: alchemist-${SERVICE_NAME}${NC}"
        echo -e "${GREEN}URL: ${SERVICE_URL}${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️  Deployment completed but verification failed${NC}"
        echo -e "${YELLOW}Service may still be starting up. Check logs:${NC}"
        echo -e "${YELLOW}gcloud run services logs read alchemist-${SERVICE_NAME} --region=${REGION}${NC}"
    fi
}

# Run main function
main