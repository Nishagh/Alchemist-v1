#!/bin/bash

# Agent Launcher Deployment Script
# Usage: ./deploy.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-"production"}
PROJECT_ID=${PROJECT_ID:-"alchemist-e69bb"}
REGION=${REGION:-"us-central1"}
TIMEOUT=${TIMEOUT:-"3600s"}
SERVICE_NAME="alchemist-agent-launcher"
IMAGE_NAME="gcr.io/${PROJECT_ID}/alchemist-agent-launcher"

echo -e "${BLUE}🚀 Deploying Agent Launcher to ${ENVIRONMENT}...${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
echo ""

# Function to check if gcloud is authenticated
check_gcloud_auth() {
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}Error: Not authenticated with gcloud. Run 'gcloud auth login'${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Authenticated with gcloud${NC}"
}

# Function to set project
set_project() {
    echo -e "${YELLOW}Setting project to ${PROJECT_ID}...${NC}"
    if ! gcloud config set project $PROJECT_ID; then
        echo -e "${RED}❌ Failed to set project${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Project set successfully${NC}"
}

# Function to validate deployment files
validate_deployment() {
    echo -e "${YELLOW}Validating deployment files...${NC}"
    
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}Error: No Dockerfile found in current directory${NC}"
        exit 1
    fi
    
    if [ ! -f "universal-deployment-service/main.py" ]; then
        echo -e "${RED}Error: No main.py found in universal-deployment-service${NC}"
        exit 1
    fi
    
    if [ ! -f "universal-deployment-service/requirements.txt" ]; then
        echo -e "${RED}Error: No requirements.txt found in universal-deployment-service${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All required files found${NC}"
}

# Function to build the container image
build_image() {
    echo -e "${YELLOW}Building container image...${NC}"
    
    # Create optimized build context
    BUILD_DIR="../temp-build-agent-launcher"
    echo -e "${YELLOW}Creating optimized build context...${NC}"
    
    # Clean up any existing build directory
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    
    # Copy shared libraries
    if [ -d "../shared" ]; then
        cp -r "../shared" "$BUILD_DIR/"
        echo -e "${GREEN}✅ Copied shared libraries${NC}"
    fi
    
    # Copy agent-launcher files
    mkdir -p "$BUILD_DIR/agent-launcher"
    
    # Copy essential directories
    cp -r "universal-deployment-service" "$BUILD_DIR/agent-launcher/"
    if [ -d "universal-agent-template" ]; then
        cp -r "universal-agent-template" "$BUILD_DIR/agent-launcher/"
    fi
    
    # Copy Dockerfile and other files
    cp "Dockerfile" "$BUILD_DIR/agent-launcher/"
    
    # Copy any Python files, requirements, etc.
    for file in *.py *.txt *.md .env* .dockerignore; do
        if [ -f "$file" ]; then
            cp "$file" "$BUILD_DIR/agent-launcher/"
        fi
    done
    
    # Create optimized .dockerignore
    cat > "$BUILD_DIR/.dockerignore" << 'DOCKERIGNORE_EOF'
# Test files and data
**/tests/
**/*test*
**/test_*/
**/*.test.*
**/*.spec.*

# Vector data and large files
**/vector_data*/
vector_data*/
**/*.bin
**/*.sqlite3
**/*.db

# Python cache
**/__pycache__/
**/*.pyc
**/*.pyo
**/*.pyd
**/venv/
**/env/
**/.venv/
**/*.egg-info/

# Development files
**/.env*
!**/.env.example
**/.vscode/
**/.idea/
**/*.swp
**/*.swo

# Temporary files
**/.cache/
**/tmp/
**/temp/
**/*.tmp
**/*.log
**/*.pid

# OS files
.DS_Store
Thumbs.db
**/.DS_Store
**/Thumbs.db

# Git
.git/
.gitignore

# Large dependencies
**/*.dylib
**/*.so
**/*.dll
**/torch/
**/onnxruntime/
**/chromadb*/
DOCKERIGNORE_EOF
    
    # Create cloudbuild.yaml for the build
    cat > "$BUILD_DIR/cloudbuild.yaml" << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'agent-launcher/Dockerfile', '-t', '${IMAGE_NAME}', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${IMAGE_NAME}']
images:
- '${IMAGE_NAME}'
timeout: '${TIMEOUT}'
options:
  sourceProvenanceHash: ['SHA256']
  logging: CLOUD_LOGGING_ONLY
EOF
    
    # Build the image
    echo -e "${YELLOW}Building Docker image: ${IMAGE_NAME}${NC}"
    if ! gcloud builds submit \
        --config="$BUILD_DIR/cloudbuild.yaml" \
        --timeout="${TIMEOUT}" \
        "$BUILD_DIR"; then
        echo -e "${RED}❌ Image build failed${NC}"
        rm -rf "$BUILD_DIR"
        exit 1
    fi
    
    # Clean up build directory
    rm -rf "$BUILD_DIR"
    echo -e "${GREEN}✅ Image built successfully${NC}"
}

# Function to deploy to Cloud Run
deploy_to_cloud_run() {
    echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
    
    # Deploy the service
    if ! gcloud run deploy "${SERVICE_NAME}" \
        --image="${IMAGE_NAME}" \
        --platform=managed \
        --region="${REGION}" \
        --allow-unauthenticated \
        --port=8080 \
        --memory=1Gi \
        --cpu=1 \
        --max-instances=3 \
        --concurrency=10 \
        --set-env-vars="ENVIRONMENT=${ENVIRONMENT}" \
        --timeout=3600; then
        echo -e "${RED}❌ Cloud Run deployment failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Service deployed to Cloud Run${NC}"
}

# Function to check revision health
check_revision_health() {
    echo -e "${YELLOW}Checking revision health...${NC}"
    
    # Wait a moment for deployment to register
    sleep 5
    
    # Get the latest revision
    echo -e "${YELLOW}Getting latest revision...${NC}"
    latest_revision=$(gcloud run revisions list \
        --service="${SERVICE_NAME}" \
        --region="${REGION}" \
        --limit=1 \
        --format="value(metadata.name)")
    
    if [ -z "$latest_revision" ]; then
        echo -e "${RED}❌ Could not get latest revision${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Latest revision: ${latest_revision}${NC}"
    
    # Check revision status with timeout
    max_wait=600  # 10 minutes
    wait_time=0
    check_interval=15
    
    echo -e "${YELLOW}Waiting for revision to become ready...${NC}"
    
    while [ $wait_time -lt $max_wait ]; do
        # Get revision status
        revision_info=$(gcloud run revisions describe "$latest_revision" \
            --region="${REGION}" \
            --format="json" 2>/dev/null || echo '{}')
        
        # Extract status and condition
        revision_status=$(echo "$revision_info" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    conditions = data.get('status', {}).get('conditions', [])
    ready_condition = next((c for c in conditions if c.get('type') == 'Ready'), {})
    print(ready_condition.get('status', 'Unknown'))
except:
    print('Unknown')
" 2>/dev/null || echo "Unknown")
        
        case "$revision_status" in
            "True")
                echo -e "${GREEN}✅ Revision ${latest_revision} is ready and healthy!${NC}"
                return 0
                ;;
            "False")
                echo -e "${RED}❌ Revision ${latest_revision} failed to start${NC}"
                
                # Get detailed error message
                error_msg=$(echo "$revision_info" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    conditions = data.get('status', {}).get('conditions', [])
    ready_condition = next((c for c in conditions if c.get('type') == 'Ready'), {})
    print(ready_condition.get('message', 'No error message available'))
except:
    print('Could not get error message')
" 2>/dev/null || echo "Could not get error message")
                
                echo -e "${RED}Error details: ${error_msg}${NC}"
                echo ""
                echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
                echo -e "${YELLOW}• Check logs: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}${NC}"
                echo -e "${YELLOW}• Verify Dockerfile exposes port 8080${NC}"
                echo -e "${YELLOW}• Ensure main.py listens on PORT environment variable${NC}"
                echo -e "${YELLOW}• Check for missing dependencies or configuration${NC}"
                exit 1
                ;;
            "Unknown"|"")
                echo -e "${YELLOW}Revision status unknown, waiting... (${wait_time}s/${max_wait}s)${NC}"
                ;;
            *)
                echo -e "${YELLOW}Revision status: ${revision_status}, waiting... (${wait_time}s/${max_wait}s)${NC}"
                ;;
        esac
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
    done
    
    echo -e "${RED}❌ Timeout waiting for revision to become ready after ${max_wait} seconds${NC}"
    echo -e "${YELLOW}Check the logs for more details: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}${NC}"
    exit 1
}

# Function to get service info
get_service_info() {
    echo -e "${YELLOW}Getting service information...${NC}"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
        --region="${REGION}" \
        --format="value(status.url)" 2>/dev/null || echo "")
    
    if [ -z "$SERVICE_URL" ]; then
        echo -e "${RED}❌ Could not get service URL${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Service deployed successfully!${NC}"
    echo -e "${GREEN}Service Name: ${SERVICE_NAME}${NC}"
    echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
    echo ""
    
    # Test health endpoint
    echo -e "${YELLOW}Testing health endpoint...${NC}"
    if curl -f -s "${SERVICE_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    elif curl -f -s "${SERVICE_URL}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Service may still be starting up${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🎉 Deployment completed successfully!${NC}"
    echo -e "${BLUE}Monitor logs: gcloud run services logs read ${SERVICE_NAME} --region=${REGION} --follow${NC}"
}

# Main deployment process
main() {
    echo -e "${BLUE}=== Agent Launcher Deployment ===${NC}"
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    check_gcloud_auth
    set_project
    validate_deployment
    build_image
    deploy_to_cloud_run
    check_revision_health
    get_service_info
}

# Run main function
main "$@"