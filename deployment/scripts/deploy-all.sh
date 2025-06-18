#!/bin/bash

# Deploy All Alchemist Services
# Usage: ./deploy-all.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ENVIRONMENT=${1:-"production"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 Deploying All Alchemist Services to ${ENVIRONMENT}${NC}"
echo ""

# Services to deploy (in order of dependencies)
SERVICES=(
    "agent-engine"
    "knowledge-vault"
    "agent-bridge"
    "agent-launcher"
    "tool-forge"
    "agent-studio"
)

# Track deployment results
DEPLOYED_SERVICES=()
FAILED_SERVICES=()

# Function to deploy a service
deploy_service() {
    local service=$1
    echo -e "${BLUE}📦 Deploying ${service}...${NC}"
    
    if "${SCRIPT_DIR}/deploy-service.sh" "$service" "$ENVIRONMENT"; then
        DEPLOYED_SERVICES+=("$service")
        echo -e "${GREEN}✅ ${service} deployed successfully${NC}"
    else
        FAILED_SERVICES+=("$service")
        echo -e "${RED}❌ ${service} deployment failed${NC}"
    fi
    
    echo ""
}

# Main deployment process
main() {
    echo -e "${YELLOW}Starting deployment of ${#SERVICES[@]} services...${NC}"
    echo ""
    
    # Deploy each service
    for service in "${SERVICES[@]}"; do
        deploy_service "$service"
    done
    
    # Summary
    echo -e "${BLUE}=== Deployment Summary ===${NC}"
    echo ""
    
    if [ ${#DEPLOYED_SERVICES[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ Successfully deployed (${#DEPLOYED_SERVICES[@]}):{NC}"
        for service in "${DEPLOYED_SERVICES[@]}"; do
            echo -e "${GREEN}  - ${service}${NC}"
        done
        echo ""
    fi
    
    if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
        echo -e "${RED}❌ Failed deployments (${#FAILED_SERVICES[@]}):${NC}"
        for service in "${FAILED_SERVICES[@]}"; do
            echo -e "${RED}  - ${service}${NC}"
        done
        echo ""
        echo -e "${RED}Some services failed to deploy. Check logs and retry individual deployments.${NC}"
        exit 1
    else
        echo -e "${GREEN}🎉 All services deployed successfully!${NC}"
        echo ""
        
        # Show service URLs
        echo -e "${BLUE}Service URLs:${NC}"
        for service in "${DEPLOYED_SERVICES[@]}"; do
            SERVICE_URL=$(gcloud run services describe "alchemist-${service}" \
                --region=us-central1 \
                --format="value(status.url)" 2>/dev/null || echo "URL not available")
            echo -e "${BLUE}  ${service}: ${SERVICE_URL}${NC}"
        done
    fi
}

# Run main function
main