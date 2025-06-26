#!/bin/bash

# Script to fix shared library deployment issues across services
# This script checks which services need shared library copying and fixes their deploy scripts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Checking services for shared library deployment issues...${NC}"
echo ""

# Services that need shared library and their status
SERVICES_WITH_SHARED=(
    "agent-tuning-service:✅"
    "knowledge-vault:✅"
    "prompt-engine:✅"
    "agent-launcher:?"
    "tool-forge:?"
    "agent-bridge:❌"
)

echo -e "${YELLOW}Services with shared library dependency:${NC}"
for service_info in "${SERVICES_WITH_SHARED[@]}"; do
    IFS=':' read -r service_name status <<< "$service_info"
    echo -e "  $service_name: $status"
done

echo ""
echo -e "${BLUE}Legend:${NC}"
echo -e "  ✅ = Has proper shared library copying in deploy.sh"
echo -e "  ❌ = Missing deploy.sh script"
echo -e "  ? = Needs to be checked"

echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "1. Create deploy.sh scripts for services missing them"
echo -e "2. Add shared library copying to deploy scripts that need it"
echo -e "3. Test deployments"

# Function to create a deploy script template for services missing one
create_deploy_script_template() {
    local service_name=$1
    local service_path=$2
    
    echo -e "${BLUE}Creating deploy.sh template for $service_name...${NC}"
    
    cat > "$service_path/deploy.sh" << 'EOF'
#!/bin/bash

# Auto-generated deployment script
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-alchemist-e69bb}"
SERVICE_NAME="SERVICE_NAME_PLACEHOLDER"
REGION="${REGION:-us-central1}"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying $SERVICE_NAME...${NC}"

# Configure gcloud
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Ensuring required APIs are enabled...${NC}"
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Copy shared module to local directory for Docker context
echo -e "${YELLOW}📦 Preparing shared module...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi
cp -r ../shared ./shared

# Build using Cloud Build
echo -e "${YELLOW}Building image with Cloud Build...${NC}"
gcloud builds submit --tag=$IMAGE_NAME

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=1Gi \
  --timeout=300

# Cleanup shared directory
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
if [ -d "./shared" ]; then
    rm -rf ./shared
fi

echo -e "${GREEN}✅ Deployment completed!${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' 2>/dev/null || echo "Unable to get URL")
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
EOF

    # Replace placeholder with actual service name
    sed -i.bak "s/SERVICE_NAME_PLACEHOLDER/$service_name/g" "$service_path/deploy.sh"
    rm "$service_path/deploy.sh.bak" 2>/dev/null || true
    
    # Make executable
    chmod +x "$service_path/deploy.sh"
    
    echo -e "${GREEN}✅ Created deploy.sh for $service_name${NC}"
}

# Check and fix agent-bridge
if [ -d "agent-bridge" ] && [ ! -f "agent-bridge/deploy.sh" ]; then
    echo -e "${YELLOW}Creating deploy.sh for agent-bridge...${NC}"
    create_deploy_script_template "agent-bridge" "agent-bridge"
fi

# Check tool-forge
if [ -d "tool-forge" ]; then
    if [ ! -f "tool-forge/deploy.sh" ]; then
        echo -e "${YELLOW}Creating deploy.sh for tool-forge...${NC}"
        create_deploy_script_template "tool-forge" "tool-forge"
    else
        echo -e "${BLUE}Checking tool-forge deploy.sh for shared library copying...${NC}"
        if ! grep -q "cp -r.*shared" "tool-forge/deploy.sh"; then
            echo -e "${YELLOW}⚠️  tool-forge deploy.sh needs shared library copying added${NC}"
        else
            echo -e "${GREEN}✅ tool-forge deploy.sh already has shared library copying${NC}"
        fi
    fi
fi

# Check agent-launcher
if [ -d "agent-launcher" ]; then
    if [ -f "agent-launcher/deploy.sh" ]; then
        echo -e "${BLUE}Checking agent-launcher deploy.sh for shared library copying...${NC}"
        if ! grep -q "cp -r.*shared" "agent-launcher/deploy.sh"; then
            echo -e "${YELLOW}⚠️  agent-launcher deploy.sh needs shared library copying added${NC}"
        else
            echo -e "${GREEN}✅ agent-launcher deploy.sh already has shared library copying${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}🎉 Shared library deployment fixes complete!${NC}"
echo -e "${BLUE}Now you can run: ./deploy-all-services.sh --auto${NC}"