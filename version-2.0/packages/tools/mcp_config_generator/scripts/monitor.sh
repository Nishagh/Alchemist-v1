#!/bin/bash

# Service Monitoring Script
# Provides monitoring and management utilities for the deployed service

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

# Function to show service status
show_status() {
    print_status "Getting service status..."
    
    if gcloud run services describe "$SERVICE_NAME" --region="$REGION" >/dev/null 2>&1; then
        print_success "Service is deployed"
        
        # Get service details
        echo ""
        echo "Service Details:"
        echo "==============="
        gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="table(
            metadata.name,
            status.url,
            status.latestReadyRevisionName,
            status.conditions[0].status,
            status.conditions[0].type
        )"
        
        # Get service URL
        SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
        echo ""
        echo "🌐 Service URL: $SERVICE_URL"
        echo "🏥 Health Check: $SERVICE_URL/health"
        
    else
        print_error "Service not found or not deployed"
        exit 1
    fi
}

# Function to show logs
show_logs() {
    local lines=${1:-50}
    print_status "Showing last $lines log entries..."
    
    gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
        --limit="$lines" \
        --format="table(timestamp, severity, textPayload)"
}

# Function to show metrics
show_metrics() {
    print_status "Service metrics and configuration..."
    
    gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="yaml(
        spec.template.spec.containers[0].resources,
        spec.template.metadata.annotations,
        status.traffic
    )"
}

# Function to test the service
test_service() {
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)" 2>/dev/null)
    
    if [[ -z "$SERVICE_URL" ]]; then
        print_error "Could not get service URL"
        exit 1
    fi
    
    print_status "Testing service endpoints..."
    
    # Test health endpoint
    echo ""
    echo "Testing health endpoint:"
    if curl -s --max-time 10 "$SERVICE_URL/health" | jq . 2>/dev/null; then
        print_success "Health endpoint is working"
    else
        print_warning "Health endpoint test failed"
    fi
    
    # Test main page
    echo ""
    echo "Testing main page:"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SERVICE_URL/")
    if [[ "$HTTP_CODE" == "200" ]]; then
        print_success "Main page is working (HTTP $HTTP_CODE)"
    else
        print_warning "Main page test failed (HTTP $HTTP_CODE)"
    fi
    
    # Test API endpoint with sample data
    echo ""
    echo "Testing API conversion endpoint:"
    SAMPLE_OPENAPI='{"openapi":"3.0.0","info":{"title":"Test","version":"1.0.0"},"paths":{"/test":{"get":{"responses":{"200":{"description":"OK"}}}}}}'
    
    if curl -s --max-time 30 -X POST "$SERVICE_URL/api/convert" \
        -H "Content-Type: application/json" \
        -d "{\"openapi_spec\":\"$SAMPLE_OPENAPI\",\"server_name\":\"test\"}" | jq .success 2>/dev/null | grep -q true; then
        print_success "API conversion endpoint is working"
    else
        print_warning "API conversion endpoint test failed"
    fi
}

# Function to update service configuration
update_service() {
    print_status "Updating service configuration..."
    
    echo "Current configuration options:"
    echo "1. Update memory allocation"
    echo "2. Update CPU allocation"
    echo "3. Update max instances"
    echo "4. Update environment variables"
    echo "5. Cancel"
    
    read -p "Choose an option (1-5): " choice
    
    case $choice in
        1)
            read -p "Enter new memory limit (e.g., 512Mi, 1Gi): " memory
            gcloud run services update "$SERVICE_NAME" --region="$REGION" --memory="$memory"
            ;;
        2)
            read -p "Enter new CPU limit (e.g., 1, 2): " cpu
            gcloud run services update "$SERVICE_NAME" --region="$REGION" --cpu="$cpu"
            ;;
        3)
            read -p "Enter new max instances: " max_instances
            gcloud run services update "$SERVICE_NAME" --region="$REGION" --max-instances="$max_instances"
            ;;
        4)
            read -p "Enter environment variable (KEY=VALUE): " env_var
            gcloud run services update "$SERVICE_NAME" --region="$REGION" --set-env-vars="$env_var"
            ;;
        5)
            echo "Update cancelled"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
    
    print_success "Service updated successfully"
}

# Function to show traffic allocation
show_traffic() {
    print_status "Current traffic allocation..."
    
    gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="table(
        status.traffic[].revisionName,
        status.traffic[].percent,
        status.traffic[].latestRevision
    )"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status          Show service status and details"
    echo "  logs [LINES]    Show service logs (default: 50 lines)"
    echo "  metrics         Show service metrics and configuration"
    echo "  test            Test all service endpoints"
    echo "  update          Update service configuration"
    echo "  traffic         Show traffic allocation"
    echo "  url             Get service URL"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status                    # Show service status"
    echo "  $0 logs 100                  # Show last 100 log entries"
    echo "  $0 test                      # Test all endpoints"
}

# Parse command
case ${1:-status} in
    "status")
        show_status
        ;;
    "logs")
        show_logs "${2:-50}"
        ;;
    "metrics")
        show_metrics
        ;;
    "test")
        test_service
        ;;
    "update")
        update_service
        ;;
    "traffic")
        show_traffic
        ;;
    "url")
        gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)"
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac 