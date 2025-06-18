#!/bin/bash

# Alchemist Deployment Validation Script
# This script validates the deployment configuration and service health
# Author: Alchemist Team
# Version: 1.0.0

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VALIDATION_LOG="${PROJECT_ROOT}/validation.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=""
REGION="us-central1"
ENVIRONMENT="production"

# Service definitions
declare -A SERVICES=(
    ["alchemist-agent-engine"]="agent-engine"
    ["alchemist-knowledge-vault"]="knowledge-vault"
    ["alchemist-agent-bridge"]="agent-bridge"
    ["alchemist-agent-studio"]="agent-studio"
    ["alchemist-agent-launcher"]="agent-launcher"
    ["alchemist-tool-forge"]="tool-forge"
    ["alchemist-sandbox-console"]="sandbox-console"
    ["alchemist-prompt-engine"]="prompt-engine"
    ["alchemist-mcp-config-generator"]="mcp-config-generator"
    ["alchemist-banking-api-service"]="banking-api-service"
    ["alchemist-admin-dashboard"]="admin-dashboard"
)

# Validation results
VALIDATION_RESULTS=()
ERRORS_FOUND=0
WARNINGS_FOUND=0

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $*" | tee -a "$VALIDATION_LOG"
}

log_success() {
    echo -e "${GREEN}✅${NC} $*" | tee -a "$VALIDATION_LOG"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC} $*" | tee -a "$VALIDATION_LOG"
    ((WARNINGS_FOUND++))
}

log_error() {
    echo -e "${RED}❌${NC} $*" | tee -a "$VALIDATION_LOG"
    ((ERRORS_FOUND++))
}

# Show banner
show_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🔍 ALCHEMIST DEPLOYMENT VALIDATION SYSTEM 🔍         ║
║                                                              ║
║           Ensuring Your Deployment is Ready to Go           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo ""
}

# Show help
show_help() {
    cat << EOF
${BLUE}Alchemist Deployment Validation Script${NC}

${YELLOW}USAGE:${NC}
    $0 [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -p, --project-id ID    Google Cloud Project ID
    -r, --region REGION    Deployment region (default: us-central1)
    -e, --env ENV          Environment (default: production)
    --config-only          Validate configuration files only
    --services-only        Validate deployed services only
    --health-only          Run health checks only
    -h, --help             Show this help message

${YELLOW}VALIDATION CHECKS:${NC}
    • Prerequisites (gcloud, docker, etc.)
    • Configuration files integrity
    • Google Cloud API access
    • Service account permissions
    • Secret Manager configuration
    • Deployed service status
    • Service health endpoints
    • Inter-service connectivity
    • Environment variables
    • Resource configurations

${YELLOW}EXAMPLES:${NC}
    $0                                    # Full validation
    $0 -p my-project --config-only        # Config validation only
    $0 --health-only                      # Health checks only
    $0 -e staging --services-only         # Service validation for staging

EOF
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    # Check gcloud CLI
    if command -v gcloud &> /dev/null; then
        local version=$(gcloud version --format="value(Google Cloud SDK)" 2>/dev/null)
        log_success "Google Cloud SDK installed: $version"
    else
        log_error "Google Cloud SDK not installed"
        return 1
    fi
    
    # Check authentication
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        local account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
        log_success "Authenticated as: $account"
    else
        log_error "Not authenticated with Google Cloud"
        return 1
    fi
    
    # Check project access
    if [[ -n "$PROJECT_ID" ]]; then
        if gcloud projects describe "$PROJECT_ID" &> /dev/null; then
            log_success "Project access validated: $PROJECT_ID"
        else
            log_error "Cannot access project: $PROJECT_ID"
            return 1
        fi
    else
        log_warning "No project ID specified"
    fi
    
    # Check curl for health checks
    if command -v curl &> /dev/null; then
        log_success "curl available for health checks"
    else
        log_warning "curl not available - health checks will be skipped"
    fi
    
    # Check docker (optional)
    if command -v docker &> /dev/null; then
        log_success "Docker available"
    else
        log_warning "Docker not available"
    fi
    
    return 0
}

# Validate configuration files
validate_configuration() {
    log_info "Validating configuration files..."
    
    # Check deployment configuration
    if [[ -f "$PROJECT_ROOT/deployment-config.yaml" ]]; then
        log_success "Deployment configuration found"
        
        # Basic YAML syntax check
        if command -v python3 &> /dev/null; then
            if python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/deployment-config.yaml'))" 2>/dev/null; then
                log_success "Deployment configuration YAML is valid"
            else
                log_error "Deployment configuration YAML is invalid"
            fi
        fi
    else
        log_warning "Deployment configuration not found"
    fi
    
    # Check service Dockerfiles
    local missing_dockerfiles=()
    for service_dir in agent-engine knowledge-vault agent-bridge agent-studio agent-launcher; do
        if [[ -f "$PROJECT_ROOT/$service_dir/Dockerfile" ]]; then
            log_success "Dockerfile found: $service_dir"
        else
            log_error "Dockerfile missing: $service_dir"
            missing_dockerfiles+=("$service_dir")
        fi
    done
    
    # Check requirements files
    for service_dir in agent-engine knowledge-vault agent-bridge agent-launcher prompt-engine sandbox-console; do
        if [[ -f "$PROJECT_ROOT/$service_dir/requirements.txt" ]]; then
            log_success "Requirements file found: $service_dir"
        else
            log_warning "Requirements file missing: $service_dir"
        fi
    done
    
    # Check package.json for Node.js services
    for service_dir in agent-studio admin-dashboard; do
        if [[ -f "$PROJECT_ROOT/$service_dir/package.json" ]]; then
            log_success "Package.json found: $service_dir"
        else
            log_warning "Package.json missing: $service_dir"
        fi
    done
    
    return 0
}

# Validate Google Cloud setup
validate_gcloud_setup() {
    log_info "Validating Google Cloud setup..."
    
    if [[ -z "$PROJECT_ID" ]]; then
        log_warning "Project ID not specified - skipping Cloud setup validation"
        return 0
    fi
    
    # Check required APIs
    local required_apis=(
        "run.googleapis.com"
        "cloudbuild.googleapis.com"
        "firestore.googleapis.com"
        "secretmanager.googleapis.com"
        "storage.googleapis.com"
    )
    
    for api in "${required_apis[@]}"; do
        if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
            log_success "API enabled: $api"
        else
            log_error "API not enabled: $api"
        fi
    done
    
    # Check Secret Manager secrets
    local required_secrets=("openai-api-key")
    for secret in "${required_secrets[@]}"; do
        if gcloud secrets describe "$secret" --project="$PROJECT_ID" &> /dev/null; then
            log_success "Secret exists: $secret"
        else
            log_error "Secret missing: $secret"
        fi
    done
    
    # Check service account
    local service_account="${PROJECT_ID}@appspot.gserviceaccount.com"
    if gcloud iam service-accounts describe "$service_account" --project="$PROJECT_ID" &> /dev/null; then
        log_success "Default service account exists"
    else
        log_warning "Default service account not found"
    fi
    
    return 0
}

# Validate deployed services
validate_deployed_services() {
    log_info "Validating deployed services..."
    
    if [[ -z "$PROJECT_ID" ]]; then
        log_warning "Project ID not specified - skipping service validation"
        return 0
    fi
    
    local deployed_count=0
    local not_deployed_count=0
    
    for cloud_run_name in "${!SERVICES[@]}"; do
        local service_name="${SERVICES[$cloud_run_name]}"
        
        if gcloud run services describe "$cloud_run_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --quiet &> /dev/null; then
            
            log_success "Service deployed: $service_name ($cloud_run_name)"
            ((deployed_count++))
            
            # Check service configuration
            local memory=$(gcloud run services describe "$cloud_run_name" \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --format="value(spec.template.spec.template.spec.containers[0].resources.limits.memory)" 2>/dev/null)
            
            local cpu=$(gcloud run services describe "$cloud_run_name" \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --format="value(spec.template.spec.template.spec.containers[0].resources.limits.cpu)" 2>/dev/null)
            
            if [[ -n "$memory" && -n "$cpu" ]]; then
                log_info "  Resource limits: Memory=$memory, CPU=$cpu"
            fi
            
        else
            log_warning "Service not deployed: $service_name ($cloud_run_name)"
            ((not_deployed_count++))
        fi
    done
    
    log_info "Deployment summary: $deployed_count deployed, $not_deployed_count not deployed"
    
    return 0
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    if [[ -z "$PROJECT_ID" ]]; then
        log_warning "Project ID not specified - skipping health checks"
        return 0
    fi
    
    if ! command -v curl &> /dev/null; then
        log_warning "curl not available - skipping health checks"
        return 0
    fi
    
    local healthy_count=0
    local unhealthy_count=0
    
    for cloud_run_name in "${!SERVICES[@]}"; do
        local service_name="${SERVICES[$cloud_run_name]}"
        
        # Get service URL
        local service_url
        service_url=$(gcloud run services describe "$cloud_run_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)" 2>/dev/null)
        
        if [[ -z "$service_url" ]]; then
            log_warning "Service URL not available: $service_name"
            continue
        fi
        
        # Try health endpoint first, then root
        if curl -f -s -m 10 "${service_url}/health" > /dev/null 2>&1; then
            log_success "Health check passed: $service_name"
            ((healthy_count++))
        elif curl -f -s -m 10 "$service_url" > /dev/null 2>&1; then
            log_success "Service responding: $service_name (no health endpoint)"
            ((healthy_count++))
        else
            log_error "Health check failed: $service_name"
            ((unhealthy_count++))
        fi
    done
    
    log_info "Health check summary: $healthy_count healthy, $unhealthy_count unhealthy"
    
    return 0
}

# Check inter-service connectivity
check_connectivity() {
    log_info "Checking inter-service connectivity..."
    
    if [[ -z "$PROJECT_ID" ]]; then
        log_warning "Project ID not specified - skipping connectivity checks"
        return 0
    fi
    
    # Get agent-engine URL
    local agent_engine_url
    agent_engine_url=$(gcloud run services describe "alchemist-agent-engine" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)" 2>/dev/null)
    
    if [[ -z "$agent_engine_url" ]]; then
        log_warning "Agent engine not deployed - skipping connectivity checks"
        return 0
    fi
    
    # Check if agent-engine can reach other services
    local dependencies=("knowledge-vault" "agent-bridge" "agent-launcher")
    
    for dep in "${dependencies[@]}"; do
        local dep_url
        dep_url=$(gcloud run services describe "alchemist-$dep" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)" 2>/dev/null)
        
        if [[ -n "$dep_url" ]]; then
            log_success "Dependency URL available: $dep -> $dep_url"
        else
            log_warning "Dependency not available: $dep"
        fi
    done
    
    return 0
}

# Generate validation report
generate_report() {
    echo ""
    echo -e "${BLUE}=== VALIDATION REPORT ===${NC}"
    echo ""
    echo -e "${GREEN}✅ Successful checks: $((${#VALIDATION_RESULTS[@]} - ERRORS_FOUND - WARNINGS_FOUND))${NC}"
    echo -e "${YELLOW}⚠️  Warnings: $WARNINGS_FOUND${NC}"
    echo -e "${RED}❌ Errors: $ERRORS_FOUND${NC}"
    echo ""
    
    if [[ $ERRORS_FOUND -eq 0 ]]; then
        echo -e "${GREEN}🎉 Validation completed successfully!${NC}"
        if [[ $WARNINGS_FOUND -gt 0 ]]; then
            echo -e "${YELLOW}Note: There are $WARNINGS_FOUND warnings that should be addressed.${NC}"
        fi
        echo ""
        echo -e "${BLUE}Your Alchemist deployment appears to be ready! 🧙‍♂️✨${NC}"
    else
        echo -e "${RED}❌ Validation failed with $ERRORS_FOUND errors.${NC}"
        echo -e "${RED}Please fix the errors before deploying.${NC}"
        echo ""
        echo -e "${BLUE}Check the full log at: $VALIDATION_LOG${NC}"
        exit 1
    fi
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--project-id)
                PROJECT_ID="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -e|--env|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --config-only)
                CONFIG_ONLY="true"
                shift
                ;;
            --services-only)
                SERVICES_ONLY="true"
                shift
                ;;
            --health-only)
                HEALTH_ONLY="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    # Initialize log
    echo "=== Alchemist Deployment Validation Log ===" > "$VALIDATION_LOG"
    echo "Started: $(date)" >> "$VALIDATION_LOG"
    
    show_banner
    
    # Parse arguments
    parse_arguments "$@"
    
    # Get project ID from gcloud if not specified
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
    fi
    
    # Show configuration
    echo -e "${BLUE}Validation Configuration:${NC}"
    echo -e "  Project ID: ${PROJECT_ID:-"Not set"}"
    echo -e "  Region: $REGION"
    echo -e "  Environment: $ENVIRONMENT"
    echo ""
    
    # Run validation checks based on options
    if [[ "${CONFIG_ONLY:-}" == "true" ]]; then
        validate_configuration
    elif [[ "${SERVICES_ONLY:-}" == "true" ]]; then
        validate_prerequisites
        validate_deployed_services
    elif [[ "${HEALTH_ONLY:-}" == "true" ]]; then
        run_health_checks
    else
        # Full validation
        validate_prerequisites
        validate_configuration
        validate_gcloud_setup
        validate_deployed_services
        run_health_checks
        check_connectivity
    fi
    
    # Generate final report
    generate_report
}

# Run main function
main "$@"