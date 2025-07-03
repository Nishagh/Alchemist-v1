#!/bin/bash
# Simple Agent deployment trigger: Firestore → Eventarc → agent-launcher
# Triggers agent deployment jobs when documents are created in agent_deployments collection

set -e

PROJECT_ID=$(gcloud config get-value project)
TRIGGER_NAME="agent-deployment-trigger"
SERVICE_NAME="alchemist-agent-launcher"
REGION="us-central1"

echo "🚀 Creating Simple Agent Deployment Trigger"
echo "Firestore → Eventarc → agent-launcher → agent-deployment-job"
echo ""

# Enable required APIs
gcloud services enable eventarc.googleapis.com

# Check if agent-launcher service exists
if ! gcloud run services describe ${SERVICE_NAME} --region=${REGION} &> /dev/null; then
    echo "❌ agent-launcher service not found. Deploy it first with:"
    echo "   ./deploy-agent-launcher.sh"
    exit 1
fi

echo "✅ agent-launcher service found"

# Get service account
SERVICE_ACCOUNT=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(spec.template.spec.serviceAccountName)")
if [ -z "$SERVICE_ACCOUNT" ]; then
    SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"
fi

echo "📋 Using service account: ${SERVICE_ACCOUNT}"

# Grant eventarc.eventReceiver role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/eventarc.eventReceiver" \
    --condition=None \
    --quiet || echo "Role may already be assigned"

# Delete existing trigger if any
gcloud eventarc triggers delete ${TRIGGER_NAME} --location=nam5 --quiet 2>/dev/null || true

# Create Eventarc trigger
echo "🎯 Creating Eventarc trigger..."

gcloud eventarc triggers create ${TRIGGER_NAME} \
    --location=nam5 \
    --destination-run-service=${SERVICE_NAME} \
    --destination-run-region=${REGION} \
    --destination-run-path="/trigger-agent-deployment" \
    --event-filters="type=google.cloud.firestore.document.v1.created" \
    --event-filters="database=(default)" \
    --event-filters-path-pattern="document=agent_deployments/{deployment_id}" \
    --event-data-content-type="application/protobuf" \
    --service-account="${SERVICE_ACCOUNT}"

echo ""
echo "✅ Simple Agent deployment architecture ready!"
echo ""
echo "📋 Components:"
echo "  1. agent-launcher (receives events, triggers job)"
echo "  2. agent-deployment-job (does the deployment work)"
echo "  3. agent-deployment-trigger (connects Firestore to service)"
echo ""
echo "🎯 To test: Create a document in agent_deployments collection"
echo "📊 Monitor: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=alchemist-agent-launcher'"