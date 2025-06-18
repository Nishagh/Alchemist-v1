#!/bin/bash

# Deploy Universal Agent Deployment Service to Cloud Run

set -e

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "⚠️ .env file not found, using environment variables"
fi

# Configuration
SERVICE_NAME="alchemist-deployment-service"
REGION="${REGION:-us-central1}"
PROJECT_ID="${PROJECT_ID}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Universal Agent Deployment Service"
echo "📍 Project: ${PROJECT_ID}"
echo "🌍 Region: ${REGION}"
echo "🏷️  Image: ${IMAGE_NAME}"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please authenticate with Google Cloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project "${PROJECT_ID}"

echo "🔨 Building container image..."
gcloud builds submit --tag "${IMAGE_NAME}" .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --concurrency=10 \
    --min-instances=0 \
    --max-instances=5 \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},OPENAI_API_KEY=${OPENAI_API_KEY}" \
    --format=json > deployment-result.json

# Extract service URL
SERVICE_URL=$(cat deployment-result.json | python3 -c "import sys, json; print(json.load(sys.stdin)['status']['url'])")

echo ""
echo "✅ Deployment successful!"
echo "🔗 Service URL: ${SERVICE_URL}"
echo "📋 Health check: ${SERVICE_URL}/healthz"
echo "📖 API docs: ${SERVICE_URL}/docs"
echo ""
echo "📝 Example API calls:"
echo "   # Deploy an agent"
echo "   curl -X POST \"${SERVICE_URL}/api/deploy\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"agent_id\": \"your-agent-id\"}'"
echo ""
echo "   # Check deployment status"
echo "   curl \"${SERVICE_URL}/api/deployment/{deployment_id}/status\""
echo ""
echo "   # List deployments"
echo "   curl \"${SERVICE_URL}/api/deployments\""

# Clean up
rm -f deployment-result.json