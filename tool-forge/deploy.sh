#!/bin/bash

# MCP Manager Service Deployment Script

set -e

# Configuration
PROJECT_ID="alchemist-e69bb"
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
FIREBASE_BUCKET=${FIREBASE_STORAGE_BUCKET:-"alchemist-e69bb.firebasestorage.app"}

echo "🚀 Deploying Alchemist Tool Forge Service"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Firebase Bucket: $FIREBASE_BUCKET"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    echo "   gcloud auth application-default login"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    firebase.googleapis.com \
    firestore.googleapis.com \
    storage.googleapis.com

# Create Firebase Storage bucket if it doesn't exist
echo "🪣 Checking Firebase Storage bucket..."
if ! gsutil ls -b gs://$FIREBASE_BUCKET &>/dev/null; then
    echo "Creating Firebase Storage bucket: $FIREBASE_BUCKET"
    gsutil mb gs://$FIREBASE_BUCKET
else
    echo "Firebase Storage bucket exists: $FIREBASE_BUCKET"
fi

# Copy shared module to local directory for Docker context
echo "📦 Preparing shared module..."
if [ -d "./shared" ]; then
    rm -rf ./shared
fi
cp -r ../shared ./shared

# Deploy using Cloud Build
echo "🏗️  Building and deploying Alchemist Tool Forge Service..."
gcloud builds submit \
    --config=cloudbuild-manager.yaml \
    --substitutions=_REGION=$REGION,_FIREBASE_STORAGE_BUCKET=$FIREBASE_BUCKET \
    .

# Cleanup shared directory
echo "🧹 Cleaning up..."
if [ -d "./shared" ]; then
    rm -rf ./shared
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe alchemist-tool-forge \
    --region=$REGION \
    --format="value(status.url)")

echo "✅ Deployment completed!"
echo "🌐 Alchemist Tool Forge Service URL: $SERVICE_URL"
echo ""
echo "📋 API Endpoints:"
echo "   Health Check: $SERVICE_URL/health"
echo "   List Servers: $SERVICE_URL/servers"
echo "   Deploy Server: $SERVICE_URL/deploy-from-file"
echo ""
echo "🔧 Environment Variables Set:"
echo "   GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
echo "   GOOGLE_CLOUD_REGION=$REGION"
echo "   FIREBASE_STORAGE_BUCKET=$FIREBASE_BUCKET"
echo ""
echo "📖 Usage Example:"
echo "   curl -X POST $SERVICE_URL/deploy-from-file \\"
echo "     -F 'agent_id=my-agent-001' \\"
echo "     -F 'description=My Banking Agent' \\"
echo "     -F 'config_file=@mcp_config.yaml'" 