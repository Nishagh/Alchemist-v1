#!/bin/bash

# OpenAPI to MCP Converter - Management Script
# Main interface for all deployment and management operations

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              OpenAPI to MCP Config Converter                ║"
    echo "║                    Management Console                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

print_menu() {
    echo -e "${BLUE}Available Commands:${NC}"
    echo ""
    echo "🚀 Deployment Operations:"
    echo "  1) Deploy to Cloud Run (Cloud Build)"
    echo "  2) Deploy with local build"
    echo "  3) Deploy using service.yaml"
    echo "  4) Setup local development environment"
    echo ""
    echo "📊 Monitoring & Management:"
    echo "  5) Check service status"
    echo "  6) View service logs"
    echo "  7) Test all endpoints"
    echo "  8) Update service configuration"
    echo "  9) View service metrics"
    echo ""
    echo "🧹 Cleanup Operations:"
    echo "  10) Full cleanup (service + images)"
    echo "  11) Cleanup service only"
    echo "  12) Cleanup images only"
    echo "  13) Cleanup local artifacts"
    echo ""
    echo "ℹ️  Information:"
    echo "  14) Show service URL"
    echo "  15) Show deployment help"
    echo "  16) Run local tests"
    echo ""
    echo "  0) Exit"
    echo ""
}

wait_for_input() {
    echo ""
    read -p "Press Enter to continue..."
}

execute_deploy() {
    local method=$1
    echo -e "${GREEN}Executing deployment with method: $method${NC}"
    echo ""
    ./deploy.sh --method "$method"
    wait_for_input
}

execute_monitor() {
    local command=$1
    echo -e "${GREEN}Executing monitoring command: $command${NC}"
    echo ""
    ./scripts/monitor.sh "$command"
    wait_for_input
}

execute_cleanup() {
    local option=$1
    echo -e "${YELLOW}Executing cleanup: $option${NC}"
    echo ""
    ./scripts/cleanup.sh "$option"
    wait_for_input
}

show_help() {
    echo -e "${BLUE}Deployment Help${NC}"
    echo "================"
    echo ""
    echo "Prerequisites:"
    echo "• Google Cloud Project with billing enabled"
    echo "• gcloud CLI installed and authenticated"
    echo "• Docker installed (for local builds)"
    echo "• Go installed (for local development)"
    echo ""
    echo "Quick Start:"
    echo "1. Run 'Setup local development environment' first"
    echo "2. Choose a deployment method (Cloud Build recommended)"
    echo "3. Use monitoring commands to check status"
    echo ""
    echo "Deployment Methods:"
    echo "• Cloud Build: Fully managed, recommended for production"
    echo "• Local Build: Build on your machine, deploy to Cloud Run"
    echo "• Service YAML: Use predefined service configuration"
    echo ""
    echo "Cost Information:"
    echo "• Cloud Run: Pay-per-use, generous free tier"
    echo "• Container Registry: Storage costs for images"
    echo "• Cloud Build: Free tier includes 120 build-minutes/day"
    echo ""
    wait_for_input
}

run_local_tests() {
    echo -e "${GREEN}Running local tests...${NC}"
    echo ""
    
    if ! command -v go >/dev/null 2>&1; then
        echo -e "${RED}Go is not installed. Please install Go to run tests.${NC}"
        wait_for_input
        return
    fi
    
    if go test -v; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
    else
        echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
    fi
    
    wait_for_input
}

show_service_url() {
    echo -e "${GREEN}Getting service URL...${NC}"
    echo ""
    
    SERVICE_URL=$(./scripts/monitor.sh url 2>/dev/null || echo "")
    
    if [[ -n "$SERVICE_URL" ]]; then
        echo "🌐 Service URL: $SERVICE_URL"
        echo "🏥 Health Check: $SERVICE_URL/health"
        echo ""
        echo "You can test the service with:"
        echo "curl $SERVICE_URL/health"
    else
        echo "❌ Service not deployed or not accessible"
    fi
    
    wait_for_input
}

# Main menu loop
main() {
    while true; do
        print_header
        print_menu
        
        read -p "Select an option (0-16): " choice
        echo ""
        
        case $choice in
            1)
                execute_deploy "cloudbuild"
                ;;
            2)
                execute_deploy "local"
                ;;
            3)
                execute_deploy "yaml"
                ;;
            4)
                echo -e "${GREEN}Setting up local development environment...${NC}"
                echo ""
                ./scripts/setup-dev.sh
                wait_for_input
                ;;
            5)
                execute_monitor "status"
                ;;
            6)
                echo "How many log lines to show? (default: 50)"
                read -p "Lines: " log_lines
                log_lines=${log_lines:-50}
                execute_monitor "logs $log_lines"
                ;;
            7)
                execute_monitor "test"
                ;;
            8)
                execute_monitor "update"
                ;;
            9)
                execute_monitor "metrics"
                ;;
            10)
                execute_cleanup ""
                ;;
            11)
                execute_cleanup "--service-only"
                ;;
            12)
                execute_cleanup "--images-only"
                ;;
            13)
                execute_cleanup "--local-only"
                ;;
            14)
                show_service_url
                ;;
            15)
                show_help
                ;;
            16)
                run_local_tests
                ;;
            0)
                echo -e "${GREEN}Thanks for using OpenAPI to MCP Converter!${NC}"
                echo "Visit the project repository for updates and documentation."
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option. Please select a number between 0 and 16.${NC}"
                wait_for_input
                ;;
        esac
    done
}

# Check if all required scripts exist
check_dependencies() {
    local missing_scripts=()
    
    if [[ ! -f "deploy.sh" ]]; then
        missing_scripts+=("deploy.sh")
    fi
    
    if [[ ! -f "scripts/setup-dev.sh" ]]; then
        missing_scripts+=("scripts/setup-dev.sh")
    fi
    
    if [[ ! -f "scripts/monitor.sh" ]]; then
        missing_scripts+=("scripts/monitor.sh")
    fi
    
    if [[ ! -f "scripts/cleanup.sh" ]]; then
        missing_scripts+=("scripts/cleanup.sh")
    fi
    
    if [[ ${#missing_scripts[@]} -gt 0 ]]; then
        echo -e "${RED}Error: Missing required scripts:${NC}"
        for script in "${missing_scripts[@]}"; do
            echo "  - $script"
        done
        echo ""
        echo "Please ensure all scripts are present in the project directory."
        exit 1
    fi
}

# Show usage if help is requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "OpenAPI to MCP Converter - Management Console"
    echo ""
    echo "Usage: $0"
    echo ""
    echo "This script provides an interactive menu for managing your"
    echo "OpenAPI to MCP converter deployment on Google Cloud Run."
    echo ""
    echo "Features:"
    echo "• Deploy using multiple methods"
    echo "• Monitor and manage deployed services"
    echo "• Clean up resources"
    echo "• Local development setup"
    echo ""
    echo "Run without arguments to start the interactive menu."
    exit 0
fi

# Check dependencies and start
check_dependencies

# Show quick status if service is already deployed
if ./scripts/monitor.sh status >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Service is currently deployed${NC}"
else
    echo -e "${YELLOW}ℹ️  Service is not currently deployed${NC}"
fi

echo ""
main 