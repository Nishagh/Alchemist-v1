#!/bin/bash

# Quick deployment script for post-migration services
# This handles the import path issues and deploys services sequentially

set -e

PROJECT_ID="alchemist-e69bb"
REGION="us-central1"

echo "🚀 Quick Post-Migration Deployment"
echo "=================================="

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_path=$2
    
    echo "📦 Deploying $service_name..."
    
    cd "$service_path"
    
    if gcloud run deploy "$service_name" \
        --source . \
        --project "$PROJECT_ID" \
        --region "$REGION" \
        --allow-unauthenticated \
        --memory 2Gi \
        --timeout 3600 \
        --quiet; then
        echo "✅ $service_name deployed successfully"
    else
        echo "❌ $service_name deployment failed"
        return 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Deploy core services in order
echo "Phase 1: Core Services"
echo "====================="

deploy_service "billing-service" "billing-service"
deploy_service "agent-studio" "agent-studio" 
deploy_service "knowledge-vault" "knowledge-vault"
deploy_service "agent-engine" "agent-engine"
deploy_service "agent-bridge" "agent-bridge"

echo "✅ Core services deployed!"
echo ""

# Quick health check
echo "🏥 Quick Health Check"
echo "===================="

for service in billing-service agent-studio knowledge-vault agent-engine agent-bridge; do
    SERVICE_URL=$(gcloud run services describe "$service" \
        --project "$PROJECT_ID" \
        --region "$REGION" \
        --format "value(status.url)" 2>/dev/null || echo "")
    
    if [ -n "$SERVICE_URL" ]; then
        echo "✅ $service: $SERVICE_URL"
    else
        echo "❌ $service: Failed to get URL"
    fi
done

echo ""
echo "🎉 Quick deployment complete!"
echo "Test the frontend at the agent-studio URL above"