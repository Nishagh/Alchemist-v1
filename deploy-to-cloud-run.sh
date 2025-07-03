#!/bin/bash

# Deploy Accountable AI Agent to Google Cloud Run
# This script builds, tags, pushes, and deploys the agent to Cloud Run

set -e

# Configuration
AGENT_ID="9cb4e76c-28bf-45d6-a7c0-e67607675457"
PROJECT_ID="alchemist-e69bb"
REGION="us-central1"
SERVICE_NAME="accountable-agent-${AGENT_ID}"
IMAGE_NAME="accountable-agent"
REPOSITORY="gcr.io/${PROJECT_ID}/${IMAGE_NAME}"
TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check prerequisites
check_prerequisites() {
    print_status "🔍 Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "docker not found. Please install Docker"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "agent-launcher/agent-template/main.py" ]; then
        print_error "Please run this script from the Alchemist-v1 directory"
        exit 1
    fi
    
    # Check if alchemist-shared exists
    if [ ! -d "shared" ]; then
        print_error "alchemist-shared not found at ./shared"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to configure gcloud
configure_gcloud() {
    print_status "⚙️ Configuring gcloud..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker
    
    print_success "gcloud configured successfully"
}

# Function to build Docker image
build_image() {
    print_status "🔨 Building Docker image..."
    
    # Build from current directory to include alchemist-shared
    docker build -t $IMAGE_NAME:$TAG -f agent-launcher/agent-template/Dockerfile .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Function to tag and push image
push_image() {
    print_status "🚀 Tagging and pushing image to Google Container Registry..."
    
    # Tag image for GCR
    docker tag $IMAGE_NAME:$TAG $REPOSITORY:$TAG
    
    # Push to GCR
    docker push $REPOSITORY:$TAG
    
    if [ $? -eq 0 ]; then
        print_success "Image pushed to GCR successfully"
    else
        print_error "Failed to push image to GCR"
        exit 1
    fi
}

# Function to deploy to Cloud Run
deploy_to_cloud_run() {
    print_status "☁️ Deploying to Google Cloud Run..."
    
    gcloud run deploy $SERVICE_NAME \
        --image=$REPOSITORY:$TAG \
        --platform=managed \
        --region=$REGION \
        --allow-unauthenticated \
        --set-env-vars="AGENT_ID=$AGENT_ID,ENVIRONMENT=production,USE_ALCHEMIST_SHARED=true,ENABLE_GNF=true,DEBUG=false" \
        --memory=2Gi \
        --cpu=2 \
        --max-instances=10 \
        --min-instances=1 \
        --port=8000 \
        --timeout=300 \
        --concurrency=80
    
    if [ $? -eq 0 ]; then
        print_success "Deployment to Cloud Run successful"
    else
        print_error "Failed to deploy to Cloud Run"
        exit 1
    fi
}

# Function to get service URL
get_service_url() {
    print_status "🔗 Getting service URL..."
    
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform=managed --region=$REGION --format="value(status.url)")
    
    if [ ! -z "$SERVICE_URL" ]; then
        print_success "Service URL: $SERVICE_URL"
        return 0
    else
        print_error "Failed to get service URL"
        return 1
    fi
}

# Function to test deployment
test_deployment() {
    print_status "🧪 Testing deployment..."
    
    if [ -z "$SERVICE_URL" ]; then
        print_error "Service URL not available for testing"
        return 1
    fi
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    for i in {1..30}; do
        if curl -s -f "$SERVICE_URL/health" > /dev/null; then
            print_success "Health endpoint responding"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Health endpoint not responding after 30 attempts"
            return 1
        fi
        sleep 10
    done
    
    # Get health information
    print_status "Getting health information..."
    health_response=$(curl -s "$SERVICE_URL/health")
    echo "$health_response" | python3 -m json.tool
    
    # Test agent info
    print_status "Testing agent info endpoint..."
    agent_info=$(curl -s "$SERVICE_URL/agent/info")
    echo "$agent_info" | python3 -m json.tool
    
    print_success "Deployment test completed successfully"
}

# Function to show deployment info
show_deployment_info() {
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Deployment Information:"
    echo "  - Agent ID: $AGENT_ID"
    echo "  - Project ID: $PROJECT_ID"
    echo "  - Region: $REGION"
    echo "  - Service Name: $SERVICE_NAME"
    echo "  - Image: $REPOSITORY:$TAG"
    if [ ! -z "$SERVICE_URL" ]; then
        echo "  - Service URL: $SERVICE_URL"
        echo ""
        echo "🔗 Endpoints:"
        echo "  - Health: $SERVICE_URL/health"
        echo "  - Agent Info: $SERVICE_URL/agent/info"
        echo "  - Chat: $SERVICE_URL/chat"
        echo "  - Accountability: $SERVICE_URL/agent/accountability"
    fi
    echo ""
    echo "🛠️ Management Commands:"
    echo "  - View logs: gcloud run services logs read $SERVICE_NAME --region=$REGION"
    echo "  - Update service: gcloud run services update $SERVICE_NAME --region=$REGION"
    echo "  - Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"
    echo "  - Service details: gcloud run services describe $SERVICE_NAME --region=$REGION"
}

# Main function
main() {
    print_status "🚀 Deploying Accountable AI Agent to Google Cloud Run"
    echo "============================================================"
    echo "Agent ID: $AGENT_ID"
    echo "Project: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service: $SERVICE_NAME"
    echo "============================================================"
    
    # Run deployment steps
    check_prerequisites
    configure_gcloud
    build_image
    push_image
    deploy_to_cloud_run
    get_service_url
    test_deployment
    show_deployment_info
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent-id)
            AGENT_ID="$2"
            SERVICE_NAME="accountable-agent-${AGENT_ID}"
            shift 2
            ;;
        --project)
            PROJECT_ID="$2"
            REPOSITORY="gcr.io/${PROJECT_ID}/${IMAGE_NAME}"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --agent-id AGENT_ID    Agent ID to deploy (default: $AGENT_ID)"
            echo "  --project PROJECT_ID   GCP project ID (default: $PROJECT_ID)"
            echo "  --region REGION        GCP region (default: $REGION)"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"