#!/bin/bash
# Banking API Service Deployment Script for Google Cloud Run
# This script automates the deployment of the Banking API Service to Google Cloud Run

set -e  # Exit immediately if a command exits with a non-zero status

# Default values
DEFAULT_REGION="us-central1"
DEFAULT_SERVICE_NAME="banking-api-service"
PROJECT_ID="alchemist-e69bb"
API_KEY="banking-api-key-2025"

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BOLD}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       Banking API Service Deployment Tool      ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════╝${NC}"
echo

# Function to display usage information
usage() {
  echo -e "${BOLD}Usage:${NC}"
  echo -e "  ./deploy.sh [options]"
  echo
  echo -e "${BOLD}Options:${NC}"
  echo -e "  -p, --project-id <id>     Google Cloud Project ID (required)"
  echo -e "  -k, --api-key <key>       Banking API key (required)"
  echo -e "  -r, --region <region>     Google Cloud region (default: ${DEFAULT_REGION})"
  echo -e "  -n, --name <name>         Service name (default: ${DEFAULT_SERVICE_NAME})"
  echo -e "  -h, --help                Show this help message"
  echo
  echo -e "${BOLD}Example:${NC}"
  echo -e "  ./deploy.sh -p my-project-id -k my-secret-api-key"
  echo
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -p|--project-id)
      PROJECT_ID="$2"
      shift
      shift
      ;;
    -k|--api-key)
      API_KEY="$2"
      shift
      shift
      ;;
    -r|--region)
      REGION="$2"
      shift
      shift
      ;;
    -n|--name)
      SERVICE_NAME="$2"
      shift
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown option $1${NC}"
      usage
      exit 1
      ;;
  esac
done

# Set default values if not provided
REGION=${REGION:-$DEFAULT_REGION}
SERVICE_NAME=${SERVICE_NAME:-$DEFAULT_SERVICE_NAME}

# Check if required parameters are provided
if [ -z "$PROJECT_ID" ]; then
  echo -e "${RED}Error: Project ID is required${NC}"
  usage
  exit 1
fi

if [ -z "$API_KEY" ]; then
  echo -e "${RED}Error: API key is required${NC}"
  usage
  exit 1
fi

# Check if required tools are installed
echo -e "${BOLD}Checking prerequisites...${NC}"

if ! command_exists gcloud; then
  echo -e "${RED}✗ Google Cloud SDK is not installed${NC}"
  echo -e "${RED}Error: Please install the Google Cloud SDK and try again${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Google Cloud SDK is installed${NC}"
fi

# Check if logged in to Google Cloud
echo -e "${BOLD}Checking Google Cloud authentication...${NC}"
if ! gcloud auth print-access-token &>/dev/null; then
  echo -e "${YELLOW}You are not logged in to Google Cloud. Initiating login...${NC}"
  gcloud auth login
fi

# Set Google Cloud project
echo -e "${BOLD}Setting Google Cloud project...${NC}"
gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}✓ Project set to $PROJECT_ID${NC}"

# Check if Container Registry API is enabled
echo -e "${BOLD}Checking if Container Registry API is enabled...${NC}"
if ! gcloud services list --enabled | grep -q containerregistry.googleapis.com; then
  echo -e "${YELLOW}Container Registry API is not enabled. Enabling...${NC}"
  gcloud services enable containerregistry.googleapis.com
  echo -e "${GREEN}✓ Container Registry API enabled${NC}"
else
  echo -e "${GREEN}✓ Container Registry API already enabled${NC}"
fi

# Check if required APIs are enabled
echo -e "${BOLD}Checking if required APIs are enabled...${NC}"

# Enable Cloud Build API
if ! gcloud services list --enabled | grep -q cloudbuild.googleapis.com; then
  echo -e "${YELLOW}Cloud Build API is not enabled. Enabling...${NC}"
  gcloud services enable cloudbuild.googleapis.com
  echo -e "${GREEN}✓ Cloud Build API enabled${NC}"
else
  echo -e "${GREEN}✓ Cloud Build API already enabled${NC}"
fi

# Enable Container Registry API
if ! gcloud services list --enabled | grep -q containerregistry.googleapis.com; then
  echo -e "${YELLOW}Container Registry API is not enabled. Enabling...${NC}"
  gcloud services enable containerregistry.googleapis.com
  echo -e "${GREEN}✓ Container Registry API enabled${NC}"
else
  echo -e "${GREEN}✓ Container Registry API already enabled${NC}"
fi

# Enable Cloud Run API
if ! gcloud services list --enabled | grep -q run.googleapis.com; then
  echo -e "${YELLOW}Cloud Run API is not enabled. Enabling...${NC}"
  gcloud services enable run.googleapis.com
  echo -e "${GREEN}✓ Cloud Run API enabled${NC}"
else
  echo -e "${GREEN}✓ Cloud Run API already enabled${NC}"
fi

# Set the image path
IMAGE_PATH="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build and push the image using Google Cloud Build
echo -e "${BOLD}Building and pushing image using Google Cloud Build...${NC}"
gcloud builds submit --tag "$IMAGE_PATH" .
echo -e "${GREEN}✓ Image built and pushed to Google Container Registry${NC}"

# Deploy to Cloud Run
echo -e "${BOLD}Deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_PATH" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "BANKING_API_KEY=$API_KEY" \
  --memory 512Mi \
  --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format 'value(status.url)')

echo
echo -e "${BOLD}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║               Deployment Complete!             ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════╝${NC}"
echo
echo -e "${BOLD}Service URL:${NC} $SERVICE_URL"
echo
echo -e "${BOLD}Test your API:${NC}"
echo -e "  curl -H \"Authorization: Bearer $API_KEY\" \"$SERVICE_URL/health\""
echo
echo -e "${BOLD}Update your Alchemist configuration:${NC}"
echo -e "In your banking_customer_support_modular.yaml file, update the API URLs to:"
echo
echo -e "api_integrations:"
echo -e "  balance_inquiry:"
echo -e "    url: \"$SERVICE_URL/accounts/{account_type}/balance\""
echo -e "  transaction_history:"
echo -e "    url: \"$SERVICE_URL/accounts/{account_type}/transactions\""
echo -e "  fund_transfer:"
echo -e "    url: \"$SERVICE_URL/transfers\""
echo

# Make the script executable after creation
chmod +x $0
