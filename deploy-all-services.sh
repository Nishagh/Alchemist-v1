#!/bin/bash

# Alchemist Platform - Post-Migration Service Deployment Script
# This script deploys all services after the Firestore migration is complete
#
# Usage:
#   ./deploy-all-services.sh              # Interactive mode selection
#   ./deploy-all-services.sh --manual     # Use predefined service lists
#   ./deploy-all-services.sh --auto       # Auto-discover services with deploy.sh
#
# Features:
# - Auto-discovers services with deploy.sh scripts
# - Prioritizes individual service deploy.sh scripts over generic gcloud deploy
# - Manual mode for controlled phased deployment
# - Auto mode for comprehensive deployment of all services
# - Health checks for all deployed services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="alchemist-e69bb"
REGION="us-central1"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚀 Alchemist Platform - Service Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Project: ${PROJECT_ID}"
echo -e "Region: ${REGION}"
echo -e "Migration Status: ✅ Complete"
echo ""

# Deployment mode selection
echo -e "${YELLOW}📋 Deployment Mode Selection:${NC}"
echo -e "1. Use predefined service lists (manual control)"
echo -e "2. Auto-discover all services with deploy.sh scripts"
echo ""

# Check for command line argument
if [ "$1" == "--auto" ]; then
    DEPLOYMENT_MODE="auto"
    echo -e "${GREEN}🤖 Auto-discovery mode selected via --auto flag${NC}"
elif [ "$1" == "--manual" ]; then
    DEPLOYMENT_MODE="manual"
    echo -e "${GREEN}📋 Manual mode selected via --manual flag${NC}"
else
    read -p "Choose deployment mode (1 for manual, 2 for auto): " choice
    case $choice in
        1) DEPLOYMENT_MODE="manual" ;;
        2) DEPLOYMENT_MODE="auto" ;;
        *) 
            echo -e "${YELLOW}Invalid choice, defaulting to manual mode${NC}"
            DEPLOYMENT_MODE="manual"
            ;;
    esac
fi

echo ""

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_path=$2
    
    echo -e "${YELLOW}🔄 Deploying ${service_name}...${NC}"
    
    if [ ! -d "$service_path" ]; then
        echo -e "${RED}❌ Service directory not found: $service_path${NC}"
        return 1
    fi
    
    cd "$service_path"
    
    # Prioritize service-specific deploy.sh script
    if [ -f "deploy.sh" ]; then
        echo -e "   📜 Using service-specific deploy.sh script..."
        chmod +x deploy.sh
        
        # Export environment variables that might be needed
        export PROJECT_ID="$PROJECT_ID"
        export REGION="$REGION"
        
        # Execute the service's own deploy script
        if ./deploy.sh; then
            echo -e "${GREEN}✅ ${service_name} deployed successfully using deploy.sh${NC}"
        else
            echo -e "${RED}❌ ${service_name} deployment failed in deploy.sh${NC}"
            cd - > /dev/null
            return 1
        fi
    elif [ -f "Dockerfile" ]; then
        echo -e "   🐳 No deploy.sh found, using gcloud run deploy with Dockerfile..."
        gcloud run deploy "$service_name" \
            --source . \
            --project "$PROJECT_ID" \
            --region "$REGION" \
            --allow-unauthenticated \
            --memory 2Gi \
            --cpu 2 \
            --timeout 3600 \
            --max-instances 10 \
            --quiet
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ ${service_name} deployed successfully using gcloud${NC}"
        else
            echo -e "${RED}❌ ${service_name} deployment failed with gcloud${NC}"
            cd - > /dev/null
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  No deploy.sh or Dockerfile found in $service_path, skipping...${NC}"
        cd - > /dev/null
        return 0
    fi
    
    cd - > /dev/null
    echo ""
}

# Function to check service health
check_service_health() {
    local service_name=$1
    echo -e "${YELLOW}🏥 Checking ${service_name} health...${NC}"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$service_name" \
        --project "$PROJECT_ID" \
        --region "$REGION" \
        --format "value(status.url)" 2>/dev/null || echo "")
    
    if [ -z "$SERVICE_URL" ]; then
        echo -e "${RED}❌ Could not get service URL for ${service_name}${NC}"
        return 1
    fi
    
    # Check health endpoint
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/" || echo "000")
    
    if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 404 ]; then
        echo -e "${GREEN}✅ ${service_name} is healthy (HTTP $HTTP_STATUS)${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service_name} health check failed (HTTP $HTTP_STATUS)${NC}"
        return 1
    fi
}

# Function to auto-discover services with deploy.sh scripts
discover_services() {
    echo -e "${BLUE}🔍 Auto-discovering services with deploy.sh scripts...${NC}"
    
    DISCOVERED_SERVICES=()
    
    # Find all deploy.sh scripts
    while IFS= read -r -d '' deploy_script; do
        service_dir=$(dirname "$deploy_script")
        service_name=$(basename "$service_dir")
        
        # Skip if it's in a subdirectory we don't want
        if [[ "$service_dir" == *"/universal-deployment-service"* ]]; then
            continue
        fi
        
        echo -e "   📜 Found: ${service_name} (${service_dir})"
        DISCOVERED_SERVICES+=("$service_name:$service_dir")
    done < <(find . -name "deploy.sh" -type f -print0)
    
    echo -e "${GREEN}✅ Discovered ${#DISCOVERED_SERVICES[@]} services with deploy.sh scripts${NC}"
    echo ""
}

# Validate prerequisites
echo -e "${BLUE}🔍 Validating prerequisites...${NC}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check if logged in to gcloud
if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | grep -q "@"; then
    echo -e "${RED}❌ Not authenticated with gcloud. Run: gcloud auth login${NC}"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID" --quiet

echo -e "${GREEN}✅ Prerequisites validated${NC}"
echo ""

# Auto-discover services
discover_services

if [ "$DEPLOYMENT_MODE" == "auto" ]; then
    # Auto-discovery mode: deploy all discovered services
    echo -e "${BLUE}🤖 Auto-Discovery Mode: Deploying All Services${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    for service_info in "${DISCOVERED_SERVICES[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_info"
        deploy_service "$service_name" "$service_path"
        
        # Brief pause between deployments
        sleep 3
    done
    
    echo -e "${GREEN}✅ Auto-Discovery Complete - All Services Deployed${NC}"
    echo ""
    
else
    # Manual mode: use predefined service lists
    echo -e "${BLUE}📋 Manual Mode: Deploying Services in Phases${NC}"
    echo ""
    
    # Phase 1: Deploy Core Services (Critical)
    echo -e "${BLUE}📦 Phase 1: Deploying Core Services${NC}"
    echo -e "${BLUE}======================================${NC}"
    
    CORE_SERVICES=(
        "billing-service:billing-service"
        "agent-studio:agent-studio" 
        "knowledge-vault:knowledge-vault"
        "agent-engine:agent-engine"
        "agent-bridge:agent-bridge"
    )
    
    for service_info in "${CORE_SERVICES[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_info"
        deploy_service "$service_name" "$service_path"
        
        # Brief pause between core deployments
        sleep 5
    done
    
    echo -e "${GREEN}✅ Phase 1 Complete - Core Services Deployed${NC}"
    echo ""
    
    # Phase 2: Deploy Supporting Services
    echo -e "${BLUE}📦 Phase 2: Deploying Supporting Services${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    SUPPORTING_SERVICES=(
        "agent-tuning-service:agent-tuning-service"
        "agent-launcher:agent-launcher"
        "alchemist-sandbox-console:sandbox-console"
        "prompt-engine:prompt-engine"
    )
    
    for service_info in "${SUPPORTING_SERVICES[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_info"
        deploy_service "$service_name" "$service_path"
    done

    echo -e "${GREEN}✅ Phase 2 Complete - Supporting Services Deployed${NC}"
    echo ""
    
    # Phase 3: Deploy Additional Services
    echo -e "${BLUE}📦 Phase 3: Deploying Additional Services${NC}"
    echo -e "${BLUE}=========================================${NC}"
    
    ADDITIONAL_SERVICES=(
        "alchemist-tool-forge:tool-forge"
        "alchemist-monitor-service:alchemist-monitor-service"
    )
    
    for service_info in "${ADDITIONAL_SERVICES[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_info"
        deploy_service "$service_name" "$service_path"
    done
    
    echo -e "${GREEN}✅ Phase 3 Complete - Additional Services Deployed${NC}"
    echo ""
fi

# Health Checks
echo -e "${BLUE}🏥 Running Health Checks${NC}"
echo -e "${BLUE}========================${NC}"

# Build service list based on deployment mode
if [ "$DEPLOYMENT_MODE" == "auto" ]; then
    # Use discovered services for health checks
    ALL_SERVICES=()
    for service_info in "${DISCOVERED_SERVICES[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_info"
        ALL_SERVICES+=("$service_name")
    done
else
    # Use predefined service list
    ALL_SERVICES=(
        "billing-service"
        "agent-studio"
        "knowledge-vault" 
        "agent-engine"
        "agent-bridge"
        "alchemist-agent-tuning"
        "agent-launcher"
        "alchemist-sandbox-console"
        "prompt-engine"
        "alchemist-tool-forge"
        "alchemist-monitor-service"
    )
fi

HEALTHY_SERVICES=0
TOTAL_SERVICES=${#ALL_SERVICES[@]}

for service_name in "${ALL_SERVICES[@]}"; do
    if check_service_health "$service_name"; then
        ((HEALTHY_SERVICES++))
    fi
    sleep 2
done

echo ""
echo -e "${BLUE}📊 Deployment Summary${NC}"
echo -e "${BLUE}====================${NC}"
echo -e "Total Services: $TOTAL_SERVICES"
echo -e "Healthy Services: $HEALTHY_SERVICES"
echo -e "Health Rate: $((HEALTHY_SERVICES * 100 / TOTAL_SERVICES))%"

if [ $HEALTHY_SERVICES -eq $TOTAL_SERVICES ]; then
    echo -e "${GREEN}🎉 All services deployed and healthy!${NC}"
    echo -e "${GREEN}✅ Post-migration deployment completed successfully${NC}"
    
    echo ""
    echo -e "${BLUE}🔗 Service URLs:${NC}"
    for service_name in "${ALL_SERVICES[@]}"; do
        SERVICE_URL=$(gcloud run services describe "$service_name" \
            --project "$PROJECT_ID" \
            --region "$REGION" \
            --format "value(status.url)" 2>/dev/null || echo "Not available")
        echo -e "   $service_name: $SERVICE_URL"
    done
    
else
    echo -e "${YELLOW}⚠️  Some services may need attention${NC}"
    echo -e "${YELLOW}Check the logs for any failed services${NC}"
fi

echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo -e "1. Test the frontend application"
echo -e "2. Verify agent creation and management"
echo -e "3. Test knowledge base uploads"
echo -e "4. Verify billing/credits functionality"
echo -e "5. Check service logs for any errors"

echo ""
echo -e "${BLUE}💡 Deployment Tips:${NC}"
echo -e "• Use --auto flag for future deployments to auto-discover all services"
echo -e "• Use --manual flag for controlled phased deployments"
echo -e "• Each service's deploy.sh script is prioritized over generic gcloud deploy"
echo -e "• Check individual service deploy.sh scripts for service-specific configurations"

echo ""
echo -e "${GREEN}🚀 Alchemist Platform deployment complete! (Mode: $DEPLOYMENT_MODE)${NC}"