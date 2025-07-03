#!/bin/bash

# Alchemist Admin Dashboard Deployment Script

set -e

PROJECT_ID=${1:-"alchemist-e69bb"}
REGION=${2:-"us-central1"}
SERVICE_NAME="alchemist-admin-dashboard"

echo "🚀 Deploying Alchemist Admin Dashboard..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Build and deploy using Cloud Build
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --project=$PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --port 80 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 5 \
    --min-instances 0 \
    --timeout 3600s \
    --set-env-vars "NODE_ENV=production"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "✅ Deployment completed successfully!"
echo "🌐 Admin Dashboard URL: $SERVICE_URL"
echo ""
echo "🔗 Access your Alchemist Admin Dashboard at:"
echo "   $SERVICE_URL"