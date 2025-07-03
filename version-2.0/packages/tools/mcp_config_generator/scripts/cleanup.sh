#!/bin/bash

# Cleanup Script
# Removes deployed resources and cleans up the project

set -e

# Configuration
SERVICE_NAME="openapi-mcp-converter"
REGION="us-central1"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Function to show what will be deleted
show_resources() {
    print_status "Checking for resources to clean up..."
    
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    echo "Project: $PROJECT_ID"
    echo ""
    
    # Check Cloud Run service
    if gcloud run services describe "$SERVICE_NAME" --region="$REGION" >/dev/null 2>&1; then
        echo "☁️  Cloud Run Service: $SERVICE_NAME (in $REGION)"
    else
        echo "☁️  Cloud Run Service: Not found"
    fi
    
    # Check container images
    IMAGES=$(gcloud container images list --repository="gcr.io/$PROJECT_ID" --filter="name~$SERVICE_NAME" --format="value(name)" 2>/dev/null || echo "")
    if [[ -n "$IMAGES" ]]; then
        echo "🐳 Container Images:"
        for image in $IMAGES; do
            echo "   - $image"
            # Show image tags
            gcloud container images list-tags "$image" --format="table(tags[].list():label=TAGS,timestamp.date():label=CREATED)" --limit=5
        done
    else
        echo "🐳 Container Images: None found"
    fi
    
    # Check Cloud Build history
    BUILD_COUNT=$(gcloud builds list --filter="source.repoSource.repoName~$SERVICE_NAME OR substitutions.REPO_NAME=$SERVICE_NAME" --limit=1 --format="value(id)" 2>/dev/null | wc -l || echo "0")
    if [[ "$BUILD_COUNT" -gt 0 ]]; then
        echo "🏗️  Cloud Build History: $BUILD_COUNT builds found"
    else
        echo "🏗️  Cloud Build History: None found"
    fi
    
    echo ""
}

# Function to delete Cloud Run service
delete_service() {
    if gcloud run services describe "$SERVICE_NAME" --region="$REGION" >/dev/null 2>&1; then
        print_status "Deleting Cloud Run service: $SERVICE_NAME"
        
        if gcloud run services delete "$SERVICE_NAME" --region="$REGION" --quiet; then
            print_success "Cloud Run service deleted successfully"
        else
            print_error "Failed to delete Cloud Run service"
            return 1
        fi
    else
        print_warning "Cloud Run service not found, skipping deletion"
    fi
}

# Function to delete container images
delete_images() {
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    IMAGES=$(gcloud container images list --repository="gcr.io/$PROJECT_ID" --filter="name~$SERVICE_NAME" --format="value(name)" 2>/dev/null || echo "")
    
    if [[ -n "$IMAGES" ]]; then
        print_status "Deleting container images..."
        
        for image in $IMAGES; do
            print_status "Deleting image: $image"
            # Delete all tags for this image
            if gcloud container images delete "$image" --quiet --force-delete-tags 2>/dev/null; then
                print_success "Deleted image: $image"
            else
                print_warning "Failed to delete image: $image (it may not exist)"
            fi
        done
    else
        print_warning "No container images found to delete"
    fi
}

# Function to clean up build artifacts
cleanup_builds() {
    print_status "Cleaning up Cloud Build artifacts..."
    
    # Note: Cloud Build history is kept for project billing and audit purposes
    # We don't delete build history, but we inform the user
    BUILD_COUNT=$(gcloud builds list --filter="source.repoSource.repoName~$SERVICE_NAME OR substitutions.REPO_NAME=$SERVICE_NAME" --limit=10 --format="value(id)" 2>/dev/null | wc -l || echo "0")
    
    if [[ "$BUILD_COUNT" -gt 0 ]]; then
        print_warning "Found $BUILD_COUNT Cloud Build entries. These are kept for audit purposes."
        print_status "If you want to clean up build history manually, you can view builds with:"
        echo "  gcloud builds list --filter=\"source.repoSource.repoName~$SERVICE_NAME\""
    else
        print_status "No build artifacts found"
    fi
}

# Function to clean up local files
cleanup_local() {
    print_status "Cleaning up local build artifacts..."
    
    # Remove built binary
    if [[ -f "converter" ]]; then
        rm -f converter
        print_success "Removed local binary: converter"
    fi
    
    # Remove temporary service file
    if [[ -f "service-temp.yaml" ]]; then
        rm -f service-temp.yaml
        print_success "Removed temporary file: service-temp.yaml"
    fi
    
    # Clean Go build cache
    if command -v go >/dev/null 2>&1; then
        go clean -cache
        print_success "Cleaned Go build cache"
    fi
}

# Function to show cost impact
show_cost_impact() {
    print_status "Cost impact of cleanup..."
    echo ""
    echo "Resources being removed:"
    echo "• Cloud Run service: Stops all running instances and billing"
    echo "• Container images: Frees up Container Registry storage"
    echo "• Local artifacts: Frees up local disk space"
    echo ""
    echo "Resources NOT removed (manual cleanup required if desired):"
    echo "• Cloud Build history: Kept for audit purposes"
    echo "• IAM permissions: Service accounts and roles remain"
    echo "• Enabled APIs: Cloud Run, Cloud Build, Container Registry APIs remain enabled"
    echo ""
}

# Function to confirm deletion
confirm_deletion() {
    echo ""
    print_warning "⚠️  This will permanently delete the following resources:"
    echo "   • Cloud Run service: $SERVICE_NAME"
    echo "   • Container images in gcr.io/$PROJECT_ID"
    echo "   • Local build artifacts"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirmation
    
    if [[ "$confirmation" != "yes" ]]; then
        print_status "Cleanup cancelled"
        exit 0
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --force, -f     Skip confirmation prompt"
    echo "  --service-only  Only delete the Cloud Run service"
    echo "  --images-only   Only delete container images"
    echo "  --local-only    Only clean up local artifacts"
    echo "  --dry-run       Show what would be deleted without actually deleting"
    echo "  --help, -h      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Interactive cleanup with confirmation"
    echo "  $0 --force                  # Cleanup without confirmation"
    echo "  $0 --service-only           # Only delete the Cloud Run service"
    echo "  $0 --dry-run                # Show what would be deleted"
}

# Parse command line arguments
FORCE=false
SERVICE_ONLY=false
IMAGES_ONLY=false
LOCAL_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        --service-only)
            SERVICE_ONLY=true
            shift
            ;;
        --images-only)
            IMAGES_ONLY=true
            shift
            ;;
        --local-only)
            LOCAL_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
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

# Main cleanup flow
main() {
    echo "🧹 OpenAPI to MCP Converter - Cleanup Script"
    echo "============================================="
    echo ""
    
    show_resources
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "Dry run mode - no resources will be deleted"
        show_cost_impact
        exit 0
    fi
    
    show_cost_impact
    
    if [[ "$FORCE" != "true" ]]; then
        confirm_deletion
    fi
    
    echo ""
    print_status "Starting cleanup..."
    
    # Execute cleanup based on options
    if [[ "$LOCAL_ONLY" == "true" ]]; then
        cleanup_local
    elif [[ "$SERVICE_ONLY" == "true" ]]; then
        delete_service
    elif [[ "$IMAGES_ONLY" == "true" ]]; then
        delete_images
    else
        # Full cleanup
        delete_service
        delete_images
        cleanup_builds
        cleanup_local
    fi
    
    echo ""
    print_success "🎉 Cleanup completed!"
    
    if [[ "$SERVICE_ONLY" != "true" && "$IMAGES_ONLY" != "true" && "$LOCAL_ONLY" != "true" ]]; then
        echo ""
        echo "To completely remove all traces:"
        echo "1. Disable APIs if no longer needed:"
        echo "   gcloud services disable run.googleapis.com"
        echo "   gcloud services disable cloudbuild.googleapis.com"
        echo "   gcloud services disable containerregistry.googleapis.com"
        echo ""
        echo "2. Review and clean up IAM roles if desired:"
        echo "   gcloud projects get-iam-policy \$PROJECT_ID"
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 