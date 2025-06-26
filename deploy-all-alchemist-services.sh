#!/bin/bash
# Master deployment script for all Alchemist services using alchemist_shared
# Run from the root Alchemist-v1 directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Services that use alchemist_shared
SERVICES=(
    "agent-engine"
    "billing-service" 
    "prompt-engine"
    "sandbox-console"
    "agent-tuning-service"
    "knowledge-vault"
)

echo -e "${CYAN}🎯 Alchemist Services Deployment Manager${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# Function to display usage
show_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [SERVICE_NAME]           # Deploy specific service"
    echo "  $0 all                      # Deploy all services"
    echo "  $0 --list                   # List available services"
    echo "  $0 --help                   # Show this help"
    echo ""
    echo -e "${YELLOW}Available Services:${NC}"
    for service in "${SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 agent-engine             # Deploy only agent-engine"
    echo "  $0 all                      # Deploy all services"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Verify we're in the right directory
    if [ ! -d "shared" ]; then
        echo -e "${RED}❌ Error: Must run from Alchemist-v1 root directory${NC}"
        echo "Expected to find 'shared' directory"
        exit 1
    fi
    
    # Check if required tools are installed
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
    echo ""
}

# Function to deploy a specific service
deploy_service() {
    local service=$1
    local script_name="deploy-${service}.sh"
    
    echo -e "${CYAN}🚀 Deploying ${service}...${NC}"
    echo -e "${CYAN}========================${NC}"
    
    if [ ! -f "$script_name" ]; then
        echo -e "${RED}❌ Deployment script not found: $script_name${NC}"
        return 1
    fi
    
    if [ ! -x "$script_name" ]; then
        echo -e "${YELLOW}📝 Making deployment script executable...${NC}"
        chmod +x "$script_name"
    fi
    
    echo -e "${BLUE}▶️  Executing: ./$script_name${NC}"
    echo ""
    
    if ./"$script_name"; then
        echo ""
        echo -e "${GREEN}✅ ${service} deployment completed successfully!${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}❌ ${service} deployment failed!${NC}"
        return 1
    fi
}

# Function to deploy all services
deploy_all_services() {
    local failed_services=()
    local successful_services=()
    
    echo -e "${CYAN}🚀 Deploying all Alchemist services...${NC}"
    echo -e "${CYAN}====================================${NC}"
    echo ""
    
    for service in "${SERVICES[@]}"; do
        echo -e "${YELLOW}📦 Starting deployment of $service...${NC}"
        
        if deploy_service "$service"; then
            successful_services+=("$service")
        else
            failed_services+=("$service")
        fi
        
        echo ""
        echo -e "${BLUE}⏳ Waiting 10 seconds before next deployment...${NC}"
        sleep 10
        echo ""
    done
    
    # Summary
    echo -e "${CYAN}📊 Deployment Summary${NC}"
    echo -e "${CYAN}===================${NC}"
    echo ""
    
    if [ ${#successful_services[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ Successfully deployed (${#successful_services[@]}):${NC}"
        for service in "${successful_services[@]}"; do
            echo -e "   ${GREEN}✓${NC} $service"
        done
        echo ""
    fi
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        echo -e "${RED}❌ Failed deployments (${#failed_services[@]}):${NC}"
        for service in "${failed_services[@]}"; do
            echo -e "   ${RED}✗${NC} $service"
        done
        echo ""
        echo -e "${YELLOW}💡 You can retry failed deployments individually:${NC}"
        for service in "${failed_services[@]}"; do
            echo "   ./deploy-all-alchemist-services.sh $service"
        done
        echo ""
        return 1
    else
        echo -e "${GREEN}🎉 All services deployed successfully!${NC}"
        return 0
    fi
}

# Function to list available services
list_services() {
    echo -e "${YELLOW}Available Alchemist Services:${NC}"
    echo ""
    for service in "${SERVICES[@]}"; do
        local script_name="deploy-${service}.sh"
        if [ -f "$script_name" ]; then
            echo -e "  ${GREEN}✓${NC} $service (script: $script_name)"
        else
            echo -e "  ${RED}✗${NC} $service (script missing: $script_name)"
        fi
    done
    echo ""
}

# Main script logic
main() {
    case "${1:-}" in
        "")
            show_usage
            ;;
        "--help" | "-h")
            show_usage
            ;;
        "--list" | "-l")
            list_services
            ;;
        "all")
            check_prerequisites
            deploy_all_services
            ;;
        *)
            # Check if the specified service is valid
            local service="$1"
            local valid_service=false
            
            for valid in "${SERVICES[@]}"; do
                if [ "$valid" = "$service" ]; then
                    valid_service=true
                    break
                fi
            done
            
            if [ "$valid_service" = false ]; then
                echo -e "${RED}❌ Invalid service: $service${NC}"
                echo ""
                show_usage
                exit 1
            fi
            
            check_prerequisites
            deploy_service "$service"
            ;;
    esac
}

# Run main function with all arguments
main "$@"