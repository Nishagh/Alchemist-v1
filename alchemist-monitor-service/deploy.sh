#!/bin/bash

# Deploy Alchemist Monitor Service
# This script deploys the monitoring service using the Alchemist deployment system

set -e

# Default values
PROJECT_ID=${PROJECT_ID:-"alchemist-e69bb"}
REGION=${REGION:-"us-central1"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

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

# Check if we're in the correct directory
if [[ ! -f "main.py" ]] || [[ ! -f "Dockerfile" ]]; then
    print_error "This script must be run from the alchemist-monitor-service directory"
    exit 1
fi

print_status "🚀 Deploying Alchemist Monitor Service..."
print_status "Project: $PROJECT_ID"
print_status "Region: $REGION"
print_status "Environment: $ENVIRONMENT"

# Build and deploy using Cloud Build
print_status "📦 Building and deploying with Cloud Build..."

gcloud builds submit \
    --config=cloudbuild.yaml \
    --timeout=1200s \
    --project=$PROJECT_ID

if [[ $? -eq 0 ]]; then
    print_success "✅ Cloud Build completed successfully!"
else
    print_error "❌ Cloud Build failed!"
    exit 1
fi

# Wait a moment for deployment to complete
sleep 10

# Get service URL
print_status "🌐 Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe alchemist-monitor-service \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)" 2>/dev/null)

if [[ -n "$SERVICE_URL" ]]; then
    print_success "Service URL: $SERVICE_URL"
else
    print_warning "Could not retrieve service URL"
fi

# Perform health check
print_status "🏥 Performing health check..."
if [[ -n "$SERVICE_URL" ]]; then
    HEALTH_URL="$SERVICE_URL/health"
    
    # Wait up to 2 minutes for service to be ready
    MAX_ATTEMPTS=12
    ATTEMPT=1
    
    while [[ $ATTEMPT -le $MAX_ATTEMPTS ]]; do
        print_status "Health check attempt $ATTEMPT/$MAX_ATTEMPTS..."
        
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
        
        if [[ "$HTTP_STATUS" == "200" ]]; then
            print_success "✅ Health check passed! Service is healthy."
            
            # Get additional service info
            print_status "📊 Service information:"
            HEALTH_RESPONSE=$(curl -s "$HEALTH_URL" || echo "{}")
            echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
            break
        else
            print_warning "Health check failed with status: $HTTP_STATUS"
            if [[ $ATTEMPT -eq $MAX_ATTEMPTS ]]; then
                print_error "❌ Health check failed after $MAX_ATTEMPTS attempts"
                print_error "Service may not be responding correctly"
                exit 1
            fi
            sleep 10
        fi
        
        ((ATTEMPT++))
    done
else
    print_warning "⚠️  Skipping health check - service URL not available"
fi

# Show deployment summary
print_status "📋 Deployment Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Service: alchemist-monitor-service"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
[[ -n "$SERVICE_URL" ]] && echo "URL: $SERVICE_URL"
echo "Health Check: $HEALTH_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

print_success "🎉 Alchemist Monitor Service deployment completed!"

# Optional: Test monitoring endpoints
if [[ "$1" == "--test" ]]; then
    print_status "🧪 Testing monitoring endpoints..."
    
    if [[ -n "$SERVICE_URL" ]]; then
        ENDPOINTS=(
            "/api/monitoring/health"
            "/api/monitoring/services"
            "/api/scheduler/status"
        )
        
        for endpoint in "${ENDPOINTS[@]}"; do
            test_url="$SERVICE_URL$endpoint"
            print_status "Testing: $endpoint"
            
            response=$(curl -s -w "HTTP_STATUS:%{http_code}" "$test_url" || echo "HTTP_STATUS:000")
            http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
            
            if [[ "$http_status" == "200" ]]; then
                print_success "✅ $endpoint - OK"
            else
                print_warning "⚠️  $endpoint - Status: $http_status"
            fi
        done
    fi
fi

print_success "🚀 Monitor service is ready to monitor all Alchemist services!"