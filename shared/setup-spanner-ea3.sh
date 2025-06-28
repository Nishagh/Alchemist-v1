#!/bin/bash

# Alchemist eA³ (Epistemic Autonomy) - Google Cloud Spanner Setup Script
# This script sets up Google Cloud Spanner Graph for agent life-stories

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get current project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    print_error "No active Google Cloud project found. Please run 'gcloud auth login' and 'gcloud config set project PROJECT_ID'"
    exit 1
fi

print_status "Using Google Cloud Project: $PROJECT_ID"

# Configuration
INSTANCE_ID="alchemist-graph"
DATABASE_ID="agent-stories"
SERVICE_ACCOUNT_NAME="alchemist-spanner"
REGION="us-central1"
KEY_FILE="./spanner-key.json"

print_status "Starting Alchemist eA³ Spanner setup..."

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    print_error "Not authenticated with Google Cloud. Please run 'gcloud auth login'"
    exit 1
fi

# Enable required APIs
print_status "Enabling required Google Cloud APIs..."
gcloud services enable spanner.googleapis.com --project=$PROJECT_ID
gcloud services enable iam.googleapis.com --project=$PROJECT_ID

# Create Spanner instance (if it doesn't exist)
print_status "Creating Spanner instance: $INSTANCE_ID"
if gcloud spanner instances describe $INSTANCE_ID --project=$PROJECT_ID &>/dev/null; then
    print_warning "Spanner instance $INSTANCE_ID already exists"
else
    gcloud spanner instances create $INSTANCE_ID \
        --config=regional-$REGION \
        --description="Alchemist Agent Life-Stories Graph Database" \
        --nodes=1 \
        --project=$PROJECT_ID
    print_success "Created Spanner instance: $INSTANCE_ID"
fi

# Create database (if it doesn't exist)
print_status "Creating Spanner database: $DATABASE_ID"
if gcloud spanner databases describe $DATABASE_ID --instance=$INSTANCE_ID --project=$PROJECT_ID &>/dev/null; then
    print_warning "Spanner database $DATABASE_ID already exists"
else
    gcloud spanner databases create $DATABASE_ID \
        --instance=$INSTANCE_ID \
        --database-dialect=GOOGLE_STANDARD_SQL \
        --project=$PROJECT_ID
    print_success "Created Spanner database: $DATABASE_ID"
fi

# Create service account (if it doesn't exist)
print_status "Creating service account: $SERVICE_ACCOUNT_NAME"
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID &>/dev/null; then
    print_warning "Service account $SERVICE_ACCOUNT_NAME already exists"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --description="Alchemist Spanner Graph Service Account" \
        --display-name="Alchemist Spanner" \
        --project=$PROJECT_ID
    print_success "Created service account: $SERVICE_ACCOUNT_NAME"
fi

# Grant IAM roles
print_status "Granting IAM roles to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseUser" \
    --condition=None \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseReader" \
    --condition=None \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseAdmin" \
    --condition=None \
    --quiet

print_success "Granted Spanner permissions to service account"

# Create service account key
print_status "Creating service account key: $KEY_FILE"
if [ -f "$KEY_FILE" ]; then
    print_warning "Service account key already exists at $KEY_FILE"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Skipping key creation"
    else
        gcloud iam service-accounts keys create $KEY_FILE \
            --iam-account=$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
            --project=$PROJECT_ID
        print_success "Created new service account key: $KEY_FILE"
    fi
else
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
        --project=$PROJECT_ID
    print_success "Created service account key: $KEY_FILE"
fi

# Set up environment variables
print_status "Setting up environment variables..."

ENV_FILE=".env.spanner"
cat > $ENV_FILE << EOF
# Alchemist eA³ (Epistemic Autonomy) Environment Variables
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
SPANNER_INSTANCE_ID=$INSTANCE_ID
SPANNER_DATABASE_ID=$DATABASE_ID
GOOGLE_APPLICATION_CREDENTIALS=$PWD/$KEY_FILE
EOF

print_success "Created environment file: $ENV_FILE"

# Create Cloud Run secret
print_status "Creating Cloud Run secret for service account key..."
if gcloud secrets describe spanner-service-account-key --project=$PROJECT_ID &>/dev/null; then
    print_warning "Secret spanner-service-account-key already exists"
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud secrets versions add spanner-service-account-key \
            --data-file=$KEY_FILE \
            --project=$PROJECT_ID
        print_success "Updated secret: spanner-service-account-key"
    fi
else
    gcloud secrets create spanner-service-account-key \
        --data-file=$KEY_FILE \
        --project=$PROJECT_ID
    print_success "Created secret: spanner-service-account-key"
fi

# Display setup summary
echo
print_success "🎉 Alchemist eA³ Spanner setup completed successfully!"
echo
echo -e "${BLUE}Setup Summary:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Spanner Instance: $INSTANCE_ID"
echo "  Database: $DATABASE_ID"
echo "  Service Account: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
echo "  Key File: $KEY_FILE"
echo "  Environment File: $ENV_FILE"
echo
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Add these environment variables to your deployment:"
echo "   export GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
echo "   export SPANNER_INSTANCE_ID=$INSTANCE_ID"
echo "   export SPANNER_DATABASE_ID=$DATABASE_ID"
echo "   export GOOGLE_APPLICATION_CREDENTIALS=$PWD/$KEY_FILE"
echo
echo "2. For Cloud Run deployment, the secret 'spanner-service-account-key' is ready to use"
echo
echo "3. Install required Python packages:"
echo "   pip install google-cloud-spanner>=3.47.0"
echo
echo "4. The eA³ system will automatically create database tables on first use"
echo
print_status "Your agents can now maintain coherent life-stories with full epistemic autonomy! 🧠✨"