#!/bin/bash

# Alchemist Platform - Post-Migration Service Deployment Script
# This script deploys all services after the Firestore migration is complete

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
    
    # Check if service has a deploy script
    if [ -f "deploy.sh" ]; then
        echo -e "   Using service-specific deploy script..."
        chmod +x deploy.sh
        ./deploy.sh
    elif [ -f "Dockerfile" ]; then
        echo -e "   Deploying with gcloud run deploy..."
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
    else
        echo -e "${YELLOW}⚠️  No Dockerfile or deploy script found, skipping...${NC}"
        return 0
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${service_name} deployed successfully${NC}"
    else
        echo -e "${RED}❌ ${service_name} deployment failed${NC}"
        return 1
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
    "alchemist-agent-tuning:alchemist-agent-tuning"
    "agent-launcher:agent-launcher/universal-deployment-service"
    "sandbox-console:sandbox-console"
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
    "tool-forge:tool-forge"
    "alchemist-monitor-service:alchemist-monitor-service"
)

for service_info in "${ADDITIONAL_SERVICES[@]}"; do
    IFS=':' read -r service_name service_path <<< "$service_info"
    deploy_service "$service_name" "$service_path"
done

echo -e "${GREEN}✅ Phase 3 Complete - Additional Services Deployed${NC}"
echo ""

# Health Checks
echo -e "${BLUE}🏥 Running Health Checks${NC}"
echo -e "${BLUE}========================${NC}"

ALL_SERVICES=(
    "billing-service"
    "agent-studio"
    "knowledge-vault" 
    "agent-engine"
    "agent-bridge"
    "alchemist-agent-tuning"
    "agent-launcher"
    "sandbox-console"
    "prompt-engine"
    "tool-forge"
    "alchemist-monitor-service"
)

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
echo -e "${GREEN}🚀 Alchemist Platform deployment complete!${NC}"