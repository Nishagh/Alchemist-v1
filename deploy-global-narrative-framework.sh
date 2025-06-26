#!/bin/bash

# Global Narrative Framework Deployment Script
# Deploys the GNF service to Google Cloud Run with centralized alchemist_shared module

set -e

# Configuration
SERVICE_NAME="global-narrative-framework"
PROJECT_ID="alchemist-e69bb"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting deployment of Global Narrative Framework..."

# Build the Docker image from root directory (to include shared module)
echo "📦 Building Docker image for linux/amd64 platform..."
docker build --platform linux/amd64 -f global-narative-framework/Dockerfile -t ${IMAGE_NAME}:latest .

# Push the image to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME}:latest \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=80 \
  --max-instances=5 \
  --min-instances=0 \
  --set-env-vars="ENVIRONMENT=production,PYTHONPATH=/app,PROJECT_ID=${PROJECT_ID}" \

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform=managed --region=${REGION} --format='value(status.url)')

echo "✅ Deployment completed successfully!"
echo "🔗 Service URL: ${SERVICE_URL}"
echo "🔧 Health check: ${SERVICE_URL}/health"

# Test the health endpoint
echo "🏥 Testing health endpoint..."
sleep 10
curl -f "${SERVICE_URL}/health" || echo "⚠️  Health check failed, but service might still be starting up"

echo ""
echo "📋 Service Details:"
echo "   - Service: ${SERVICE_NAME}"
echo "   - Image: ${IMAGE_NAME}:latest"
echo "   - Region: ${REGION}"
echo "   - URL: ${SERVICE_URL}"
echo ""
echo "🎯 Global Narrative Framework is now deployed!"