#!/bin/bash

# OpenAPI to MCP Config Converter - Deployment Script
# This script deploys the service to Google Cloud Run

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="openapi-mcp-converter"
REGION="us-central1"
MEMORY="512Mi"
CPU="1"
MAX_INSTANCES="10"
TIMEOUT="300"
PROJECT_ID="alchemist-e69bb"

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command_exists gcloud; then
        print_error "gcloud CLI is not installed. Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if Docker is installed (only for local build)
    if [[ "$BUILD_METHOD" == "local" ]] && ! command_exists docker; then
        print_error "Docker is not installed. Please install it from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check if Go is installed (for testing)
    if ! command_exists go; then
        print_warning "Go is not installed. Skipping local tests."
        SKIP_TESTS=true
    fi
    
    # Check if user is authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "You are not authenticated with gcloud. Please run: gcloud auth login"
        exit 1
    fi
    
    print_success "Prerequisites check completed"
}

# Function to validate project configuration
validate_project() {
    print_status "Validating Google Cloud project configuration..."
    
    print_status "Using project: $PROJECT_ID"
    
    # Check if required APIs are enabled
    print_status "Checking required APIs..."
    
    REQUIRED_APIS=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "containerregistry.googleapis.com"
    )
    
    for api in "${REQUIRED_APIS[@]}"; do
        if ! gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
            print_warning "API $api is not enabled. Enabling it now..."
            gcloud services enable "$api"
        else
            print_status "✓ $api is enabled"
        fi
    done
    
    print_success "Project validation completed"
}

# Function to run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        print_warning "Skipping tests (Go not available)"
        return
    fi
    
    print_status "Running tests..."
    
    if go test -v; then
        print_success "All tests passed"
    else
        print_error "Tests failed. Deployment aborted."
        exit 1
    fi
}

# Function to build and deploy using Cloud Build
deploy_with_cloud_build() {
    print_status "Deploying using Google Cloud Build..."
    
    # Submit build
    if gcloud builds submit --config cloudbuild.yaml; then
        print_success "Cloud Build deployment completed successfully"
    else
        print_error "Cloud Build deployment failed"
        exit 1
    fi
}

# Function to build locally and deploy
deploy_with_local_build() {
    print_status "Building Docker image locally..."
    
    IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$(date +%Y%m%d-%H%M%S)"
    
    # Build the Docker image
    if docker build -t "$IMAGE_NAME" .; then
        print_success "Docker image built successfully: $IMAGE_NAME"
    else
        print_error "Docker build failed"
        exit 1
    fi
    
    # Push the image
    print_status "Pushing image to Container Registry..."
    if docker push "$IMAGE_NAME"; then
        print_success "Image pushed successfully"
    else
        print_error "Failed to push image"
        exit 1
    fi
    
    # Deploy to Cloud Run
    print_status "Deploying to Cloud Run..."
    if gcloud run deploy "$SERVICE_NAME" \
        --image="$IMAGE_NAME" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory="$MEMORY" \
        --cpu="$CPU" \
        --max-instances="$MAX_INSTANCES" \
        --timeout="$TIMEOUT" \
        --port=8080 \
        --set-env-vars="PORT=8080"; then
        print_success "Cloud Run deployment completed successfully"
    else
        print_error "Cloud Run deployment failed"
        exit 1
    fi
}

# Function to deploy using service.yaml
deploy_with_service_yaml() {
    print_status "Deploying using service.yaml configuration..."
    
    # Replace PROJECT_ID placeholder in service.yaml
    IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
    
    # Create a temporary service file with the correct project ID
    TEMP_SERVICE_FILE="service-temp.yaml"
    sed "s/PROJECT_ID/$PROJECT_ID/g" service.yaml > "$TEMP_SERVICE_FILE"
    
    # Build and push the image first
    if [[ "$BUILD_METHOD" == "local" ]]; then
        print_status "Building and pushing Docker image..."
        IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
        
        if docker build -t "$IMAGE_NAME" . && docker push "$IMAGE_NAME"; then
            print_success "Image built and pushed successfully"
        else
            print_error "Failed to build and push image"
            rm -f "$TEMP_SERVICE_FILE"
            exit 1
        fi
    fi
    
    # Deploy the service
    if gcloud run services replace "$TEMP_SERVICE_FILE" --region="$REGION"; then
        print_success "Service deployed successfully using service.yaml"
    else
        print_error "Failed to deploy service using service.yaml"
        rm -f "$TEMP_SERVICE_FILE"
        exit 1
    fi
    
    # Clean up temporary file
    rm -f "$TEMP_SERVICE_FILE"
}

# Function to get service information
get_service_info() {
    print_status "Retrieving service information..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(status.url)" 2>/dev/null || echo "")
    
    if [[ -n "$SERVICE_URL" ]]; then
        print_success "Service deployed successfully!"
        echo ""
        echo "🌐 Service URL: $SERVICE_URL"
        echo "🏥 Health Check: $SERVICE_URL/health"
        echo "📚 API Documentation: See README.md"
        echo ""
        echo "Test the service:"
        echo "curl $SERVICE_URL/health"
        echo ""
        
        # Test health endpoint
        print_status "Testing health endpoint..."
        if curl -s --max-time 10 "$SERVICE_URL/health" | grep -q '"status":"healthy"'; then
            print_success "Health check passed!"
        else
            print_warning "Health check failed or service is still starting up"
        fi
    else
        print_error "Failed to get service URL"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -m, --method METHOD     Deployment method: cloudbuild, local, or yaml (default: cloudbuild)"
    echo "  -r, --region REGION     Google Cloud region (default: us-central1)"
    echo "  -p, --project PROJECT   Google Cloud project ID (optional, uses current project)"
    echo "  -s, --skip-tests        Skip running tests before deployment"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Deployment methods:"
    echo "  cloudbuild - Use Google Cloud Build (recommended)"
    echo "  local      - Build Docker image locally"
    echo "  yaml       - Deploy using service.yaml configuration"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Deploy using Cloud Build"
    echo "  $0 --method local                     # Build locally and deploy"
    echo "  $0 --method yaml --skip-tests         # Deploy using service.yaml, skip tests"
    echo "  $0 --project my-project --region us-west1  # Use specific project and region"
}

# Function to cleanup on exit
cleanup() {
    if [[ -f "service-temp.yaml" ]]; then
        rm -f "service-temp.yaml"
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Parse command line arguments
BUILD_METHOD="cloudbuild"
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--method)
            BUILD_METHOD="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -p|--project)
            gcloud config set project "$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate build method
if [[ "$BUILD_METHOD" != "cloudbuild" && "$BUILD_METHOD" != "local" && "$BUILD_METHOD" != "yaml" ]]; then
    print_error "Invalid build method: $BUILD_METHOD"
    show_usage
    exit 1
fi

# Main deployment flow
main() {
    echo "🚀 OpenAPI to MCP Config Converter - Deployment Script"
    echo "======================================================"
    echo ""
    
    print_status "Deployment method: $BUILD_METHOD"
    print_status "Region: $REGION"
    print_status "Service name: $SERVICE_NAME"
    echo ""
    
    # Run all deployment steps
    check_prerequisites
    validate_project
    
    if [[ "$SKIP_TESTS" != "true" ]]; then
        run_tests
    fi
    
    case $BUILD_METHOD in
        "cloudbuild")
            deploy_with_cloud_build
            ;;
        "local")
            deploy_with_local_build
            ;;
        "yaml")
            deploy_with_service_yaml
            ;;
    esac
    
    get_service_info
    
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Visit the service URL to use the web interface"
    echo "2. Check the logs: gcloud logs read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
    echo "3. Monitor the service: gcloud run services describe $SERVICE_NAME --region=$REGION"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 