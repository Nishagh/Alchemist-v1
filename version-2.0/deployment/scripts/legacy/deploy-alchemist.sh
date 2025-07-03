#!/bin/bash
# deploy-alchemist.sh - Complete Alchemist Platform Deployment

set -e

PROJECT_ID=${1:-"alchemist-e69bb"}
REGION=${2:-"us-central1"}

echo "🚀 Deploying Alchemist to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Update project ID in scripts if it's different from default
if [ "$PROJECT_ID" != "alchemist-e69bb" ]; then
    sed -i.bak "s/alchemist-e69bb/$PROJECT_ID/g" deployment/scripts/deploy-service.sh
fi

# Deploy services in order
echo "📦 Deploying core services..."
./deployment/scripts/deploy-service.sh agent-engine production
./deployment/scripts/deploy-service.sh knowledge-vault production
./deployment/scripts/deploy-service.sh agent-bridge production

echo "📦 Deploying supporting services..."
./deployment/scripts/deploy-service.sh agent-launcher production
./deployment/scripts/deploy-service.sh tool-forge production

# Get service URLs
echo "🔗 Getting service URLs..."
AGENT_ENGINE_URL=$(gcloud run services describe alchemist-agent-engine --region=$REGION --format="value(status.url)")
KNOWLEDGE_VAULT_URL=$(gcloud run services describe alchemist-knowledge-vault --region=$REGION --format="value(status.url)")
AGENT_BRIDGE_URL=$(gcloud run services describe alchemist-agent-bridge --region=$REGION --format="value(status.url)")
AGENT_LAUNCHER_URL=$(gcloud run services describe alchemist-agent-launcher --region=$REGION --format="value(status.url)")
TOOL_FORGE_URL=$(gcloud run services describe alchemist-tool-forge --region=$REGION --format="value(status.url)")

# Update Agent Engine with service URLs
echo "🔄 Configuring service URLs..."
gcloud run services update alchemist-agent-engine \
    --region=$REGION \
    --set-env-vars="KNOWLEDGE_VAULT_URL=$KNOWLEDGE_VAULT_URL,AGENT_BRIDGE_URL=$AGENT_BRIDGE_URL,AGENT_LAUNCHER_URL=$AGENT_LAUNCHER_URL,TOOL_FORGE_URL=$TOOL_FORGE_URL"

# Create frontend environment file
echo "🎨 Configuring frontend..."
cat > agent-studio/.env.production << EOF
REACT_APP_ENVIRONMENT=production
REACT_APP_API_BASE_URL=$AGENT_ENGINE_URL
REACT_APP_KNOWLEDGE_BASE_URL=$KNOWLEDGE_VAULT_URL
REACT_APP_WHATSAPP_SERVICE_URL=$AGENT_BRIDGE_URL
REACT_APP_AGENT_DEPLOYMENT_URL=$AGENT_LAUNCHER_URL
REACT_APP_TOOL_FORGE_URL=$TOOL_FORGE_URL
REACT_APP_FIREBASE_PROJECT_ID=$PROJECT_ID
EOF

# Deploy frontend
./deployment/scripts/deploy-service.sh agent-studio production

AGENT_STUDIO_URL=$(gcloud run services describe alchemist-agent-studio --region=$REGION --format="value(status.url)")

# Deploy admin dashboard
echo "📊 Deploying Admin Dashboard..."
cd admin-dashboard && ./deploy.sh $PROJECT_ID $REGION && cd ..

ADMIN_DASHBOARD_URL=$(gcloud run services describe alchemist-admin-dashboard --region=$REGION --format="value(status.url)")

# Update CORS settings
echo "🌐 Updating CORS settings..."
for service in alchemist-agent-engine alchemist-knowledge-vault alchemist-agent-bridge; do
    gcloud run services update $service \
        --region=$REGION \
        --set-env-vars="CORS_ORIGINS=$AGENT_STUDIO_URL"
done

echo "✅ Alchemist deployment completed!"
echo ""
echo "🌟 Service URLs:"
echo "Agent Engine: $AGENT_ENGINE_URL"
echo "Knowledge Vault: $KNOWLEDGE_VAULT_URL"
echo "Agent Bridge: $AGENT_BRIDGE_URL"
echo "Agent Launcher: $AGENT_LAUNCHER_URL"
echo "Tool Forge: $TOOL_FORGE_URL"
echo "Agent Studio: $AGENT_STUDIO_URL"
echo "Admin Dashboard: $ADMIN_DASHBOARD_URL"
echo ""
echo "🧪 Test your deployment:"
echo "curl $AGENT_ENGINE_URL/health"
echo "open $AGENT_STUDIO_URL"
echo "open $ADMIN_DASHBOARD_URL"