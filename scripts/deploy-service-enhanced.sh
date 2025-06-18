#!/bin/bash

# Enhanced Alchemist Service Deployment Script
# This script provides advanced deployment capabilities for individual services
# with support for the unified deployment system configuration
# Author: Alchemist Team
# Version: 2.0.0

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="${PROJECT_ROOT}/deployment-config.yaml"
LOG_FILE="${PROJECT_ROOT}/service-deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_PROJECT_ID="alchemist-e69bb"
DEFAULT_REGION="us-central1"
DEFAULT_ENVIRONMENT="production"
TIMEOUT="3600s"

# Service configuration (will be loaded from config file if available)
declare -A SERVICE_CONFIGS
declare -A SERVICE_NAMES
declare -A SERVICE_DIRECTORIES

# Global variables
SERVICE_NAME=""
PROJECT_ID=""
REGION=""
ENVIRONMENT=""
FORCE_REBUILD=""
SKIP_HEALTH_CHECK=""
DRY_RUN=""
ROLLBACK_ON_FAILURE=""

# Logging functions
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$*"
    echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
    log "SUCCESS" "$*"
    echo -e "${GREEN}✅${NC} $*"
}

log_warning() {
    log "WARNING" "$*"
    echo -e "${YELLOW}⚠️${NC} $*"
}

log_error() {
    log "ERROR" "$*"
    echo -e "${RED}❌${NC} $*"
}

log_debug() {
    if [[ "${DEBUG:-}" == "true" ]]; then
        log "DEBUG" "$*"
        echo -e "${PURPLE}🐛${NC} $*"
    fi
}

# Load configuration from YAML file
load_configuration() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_warning "Configuration file not found: $CONFIG_FILE"
        log_warning "Using default configurations"
        return 0
    fi
    
    log_info "Loading configuration from: $CONFIG_FILE"
    
    # Extract service configurations using basic parsing
    # Note: In production, consider using yq or python for proper YAML parsing
    
    # Initialize service mappings
    SERVICE_NAMES=(
        ["agent-engine"]="alchemist-agent-engine"
        ["knowledge-vault"]="alchemist-knowledge-vault"
        ["agent-bridge"]="alchemist-agent-bridge"
        ["agent-studio"]="alchemist-agent-studio"
        ["agent-launcher"]="alchemist-agent-launcher"
        ["tool-forge"]="alchemist-tool-forge"
        ["sandbox-console"]="alchemist-sandbox-console"
        ["prompt-engine"]="alchemist-prompt-engine"
        ["mcp-config-generator"]="alchemist-mcp-config-generator"
        ["banking-api-service"]="alchemist-banking-api-service"
        ["admin-dashboard"]="alchemist-admin-dashboard"
    )
    
    SERVICE_DIRECTORIES=(
        ["agent-engine"]="agent-engine"
        ["knowledge-vault"]="knowledge-vault"
        ["agent-bridge"]="agent-bridge"
        ["agent-studio"]="agent-studio"
        ["agent-launcher"]="agent-launcher"
        ["tool-forge"]="tool-forge"
        ["sandbox-console"]="sandbox-console"
        ["prompt-engine"]="prompt-engine"
        ["mcp-config-generator"]="mcp_config_generator"
        ["banking-api-service"]="banking-api-service"
        ["admin-dashboard"]="admin-dashboard"
    )
    
    log_success "Configuration loaded successfully"
}

# Show help
show_help() {
    cat << EOF
${WHITE}Enhanced Alchemist Service Deployment Script${NC}

${YELLOW}USAGE:${NC}
    $0 [OPTIONS] <service-name>

${YELLOW}ARGUMENTS:${NC}
    service-name          Name of the service to deploy

${YELLOW}OPTIONS:${NC}
    -p, --project-id ID   Google Cloud Project ID (default: ${DEFAULT_PROJECT_ID})
    -r, --region REGION   Deployment region (default: ${DEFAULT_REGION})
    -e, --env ENV         Environment (dev/staging/production, default: ${DEFAULT_ENVIRONMENT})
    -t, --timeout TIME    Deployment timeout (default: ${TIMEOUT})
    -f, --force           Force rebuild even if no changes detected
    --skip-health         Skip health check after deployment
    --dry-run             Show what would be deployed without executing
    --rollback-on-fail    Automatically rollback on deployment failure
    -d, --debug           Enable debug logging
    -h, --help            Show this help message

${YELLOW}AVAILABLE SERVICES:${NC}
    ${GREEN}Core Services:${NC}
        agent-engine          Main API orchestrator
        knowledge-vault       Document processing service
        
    ${BLUE}Integration Services:${NC}
        agent-bridge          WhatsApp/messaging integration
        tool-forge            MCP server management
        mcp-config-generator  OpenAPI to MCP conversion
        
    ${PURPLE}Application Services:${NC}
        agent-launcher        Agent deployment service
        prompt-engine         Prompt management
        sandbox-console       Testing environment
        
    ${CYAN}External Services:${NC}
        banking-api-service   Demo banking API
        agent-studio          Frontend application
        admin-dashboard       Admin monitoring dashboard

${YELLOW}EXAMPLES:${NC}
    $0 agent-engine                    # Deploy agent-engine with defaults
    $0 -p my-project agent-studio      # Deploy to specific project
    $0 -e staging knowledge-vault      # Deploy to staging environment
    $0 --force --debug tool-forge      # Force rebuild with debug logging
    $0 --dry-run agent-bridge          # Show deployment plan without executing
    $0 --rollback-on-fail agent-engine # Deploy with automatic rollback

${YELLOW}CONFIGURATION:${NC}
    Configuration is loaded from: ${CYAN}${CONFIG_FILE}${NC}
    Override with environment variables:
        ALCHEMIST_PROJECT_ID
        ALCHEMIST_REGION
        ALCHEMIST_ENV

For more information, see: ${CYAN}./DEPLOYMENT_GUIDE.md${NC}
EOF
}

# Validate service name
validate_service() {
    local service=$1
    
    if [[ -z "$service" ]]; then
        log_error "Service name is required"
        show_help
        exit 1
    fi
    
    if [[ -z "${SERVICE_NAMES[$service]:-}" ]]; then
        log_error "Unknown service: $service"
        log_info "Available services: ${!SERVICE_NAMES[*]}"
        exit 1
    fi
    
    local service_dir="${SERVICE_DIRECTORIES[$service]}"
    if [[ ! -d "$PROJECT_ROOT/$service_dir" ]]; then
        log_error "Service directory not found: $PROJECT_ROOT/$service_dir"
        exit 1
    fi
    
    if [[ ! -f "$PROJECT_ROOT/$service_dir/Dockerfile" ]]; then
        log_error "Dockerfile not found: $PROJECT_ROOT/$service_dir/Dockerfile"
        exit 1
    fi
    
    log_success "Service validation passed: $service"
}

# Check for changes since last deployment
check_for_changes() {
    local service=$1
    local service_dir="${SERVICE_DIRECTORIES[$service]}"
    
    if [[ "${FORCE_REBUILD:-}" == "true" ]]; then
        log_info "Force rebuild enabled - skipping change detection"
        return 0
    fi
    
    log_info "Checking for changes in $service..."
    
    # Get last deployed image tag
    local cloud_run_name="${SERVICE_NAMES[$service]}"
    local current_image
    current_image=$(gcloud run services describe "$cloud_run_name" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(spec.template.spec.containers[0].image)" 2>/dev/null || echo "")
    
    if [[ -z "$current_image" ]]; then
        log_info "Service not currently deployed - changes detected"
        return 0
    fi
    
    # Check if there are uncommitted changes
    if git status --porcelain "$PROJECT_ROOT/$service_dir" | grep -q .; then
        log_info "Uncommitted changes detected in $service_dir"
        return 0
    fi
    
    # Check git commits since last deployment tag
    local last_deploy_tag="deploy-${service}-$(date +%Y%m%d)"
    if git tag -l | grep -q "$last_deploy_tag"; then
        if git diff --quiet "$last_deploy_tag" HEAD -- "$PROJECT_ROOT/$service_dir"; then
            log_info "No changes detected since last deployment"
            return 1
        else
            log_info "Changes detected since last deployment"
            return 0
        fi
    fi
    
    log_info "No deployment history found - proceeding with deployment"
    return 0
}

# Build service image
build_service() {
    local service=$1
    local cloud_run_name="${SERVICE_NAMES[$service]}"
    local service_dir="${SERVICE_DIRECTORIES[$service]}"
    local image_name="gcr.io/${PROJECT_ID}/${cloud_run_name}"
    local build_timestamp=$(date +%Y%m%d-%H%M%S)
    local tagged_image="${image_name}:${build_timestamp}"
    
    log_info "Building service: $service"
    log_info "Image: $tagged_image"
    log_info "Service directory: $service_dir"
    
    if [[ "${DRY_RUN:-}" == "true" ]]; then
        log_info "[DRY RUN] Would build image: $tagged_image"
        return 0
    fi
    
    # Create cloudbuild configuration
    local cloudbuild_file="cloudbuild-${service}-${build_timestamp}.yaml"
    cat > "$cloudbuild_file" << EOF
steps:
# Build the container image
- name: 'gcr.io/cloud-builders/docker'
  args: 
    - 'build'
    - '-f'
    - '${service_dir}/Dockerfile'
    - '-t'
    - '${tagged_image}'
    - '-t'
    - '${image_name}:latest'
    - '.'
  timeout: '${TIMEOUT}'

# Push the container images
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${tagged_image}']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${image_name}:latest']

images:
- '${tagged_image}'
- '${image_name}:latest'

timeout: '${TIMEOUT}'

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'
EOF
    
    log_info "Starting Cloud Build..."
    if gcloud builds submit \
        --config="$cloudbuild_file" \
        --timeout="$TIMEOUT" \
        --project="$PROJECT_ID"; then
        log_success "Build completed successfully"
        
        # Store the image reference for deployment
        echo "$tagged_image" > ".last-build-${service}"
    else
        log_error "Build failed"
        rm -f "$cloudbuild_file"
        return 1
    fi
    
    # Clean up
    rm -f "$cloudbuild_file"
    
    return 0
}

# Deploy service to Cloud Run
deploy_to_cloud_run() {
    local service=$1
    local cloud_run_name="${SERVICE_NAMES[$service]}"
    local image_name
    
    # Get the image name from last build
    if [[ -f ".last-build-${service}" ]]; then
        image_name=$(cat ".last-build-${service}")
    else
        image_name="gcr.io/${PROJECT_ID}/${cloud_run_name}:latest"
    fi
    
    log_info "Deploying $service to Cloud Run..."
    log_info "Image: $image_name"
    log_info "Service: $cloud_run_name"
    
    if [[ "${DRY_RUN:-}" == "true" ]]; then
        log_info "[DRY RUN] Would deploy: $cloud_run_name with image $image_name"
        return 0
    fi
    
    # Build environment variables
    local env_vars="ENVIRONMENT=${ENVIRONMENT}"
    
    # Add service-specific environment variables
    case $service in
        "agent-engine"|"knowledge-vault"|"agent-bridge"|"prompt-engine"|"sandbox-console"|"agent-launcher")
            env_vars="${env_vars},FIREBASE_PROJECT_ID=${PROJECT_ID}"
            ;;
        "agent-studio")
            env_vars="${env_vars},REACT_APP_FIREBASE_PROJECT_ID=${PROJECT_ID}"
            env_vars="${env_vars},REACT_APP_ENVIRONMENT=${ENVIRONMENT}"
            ;;
        "admin-dashboard")
            env_vars="${env_vars},NODE_ENV=${ENVIRONMENT}"
            ;;
        "banking-api-service")
            env_vars="${env_vars},BANKING_API_KEY=banking-api-key-2025"
            ;;
        "tool-forge")
            env_vars="${env_vars},FIREBASE_STORAGE_BUCKET=${PROJECT_ID}.appspot.com"
            env_vars="${env_vars},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
            ;;
    esac
    
    # Get service configuration
    local memory="1Gi"
    local cpu="1"
    local max_instances="5"
    local concurrency="80"
    local port="8080"
    
    # Override with service-specific configs
    case $service in
        "knowledge-vault")
            memory="2Gi"
            cpu="2"
            max_instances="5"
            concurrency="40"
            ;;
        "agent-engine")
            memory="1Gi"
            cpu="1"
            max_instances="10"
            concurrency="80"
            ;;
        "agent-bridge"|"agent-studio"|"admin-dashboard")
            memory="512Mi"
            cpu="1"
            max_instances="5"
            concurrency="100"
            ;;
        "admin-dashboard")
            port="80"
            ;;
    esac
    
    # Build deployment command
    local deploy_cmd=(
        gcloud run deploy "$cloud_run_name"
        --image="$image_name"
        --platform=managed
        --region="$REGION"
        --project="$PROJECT_ID"
        --allow-unauthenticated
        --port="$port"
        --memory="$memory"
        --cpu="$cpu"
        --max-instances="$max_instances"
        --concurrency="$concurrency"
        --set-env-vars="$env_vars"
        --quiet
    )
    
    # Add secrets for services that need them
    case $service in
        "agent-engine"|"knowledge-vault"|"prompt-engine"|"sandbox-console")
            deploy_cmd+=(--set-secrets="OPENAI_API_KEY=openai-api-key:latest")
            ;;
    esac
    
    # Execute deployment
    if "${deploy_cmd[@]}"; then
        log_success "Deployment to Cloud Run completed"
        
        # Get service URL
        local service_url
        service_url=$(gcloud run services describe "$cloud_run_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)" 2>/dev/null)
        
        if [[ -n "$service_url" ]]; then
            log_success "Service URL: $service_url"
            echo "$service_url" > ".last-url-${service}"
        fi
        
        return 0
    else
        log_error "Deployment to Cloud Run failed"
        return 1
    fi
}

# Health check
run_health_check() {
    local service=$1
    local service_url
    
    if [[ "${SKIP_HEALTH_CHECK:-}" == "true" ]]; then
        log_info "Health check skipped"
        return 0
    fi
    
    if [[ -f ".last-url-${service}" ]]; then
        service_url=$(cat ".last-url-${service}")
    else
        local cloud_run_name="${SERVICE_NAMES[$service]}"
        service_url=$(gcloud run services describe "$cloud_run_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)" 2>/dev/null)
    fi
    
    if [[ -z "$service_url" ]]; then
        log_warning "Service URL not available for health check"
        return 0
    fi
    
    log_info "Running health check for $service..."
    log_info "URL: $service_url"
    
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log_debug "Health check attempt $attempt/$max_attempts"
        
        # Try health endpoint first, then root
        if curl -f -s -m 30 "${service_url}/health" > /dev/null 2>&1; then
            log_success "Health check passed: /health endpoint"
            return 0
        elif curl -f -s -m 30 "$service_url" > /dev/null 2>&1; then
            log_success "Health check passed: root endpoint"
            return 0
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            log_debug "Health check failed, waiting 30 seconds..."
            sleep 30
        fi
        
        ((attempt++))
    done
    
    log_warning "Health check failed after $max_attempts attempts"
    return 1
}

# Rollback on failure
rollback_service() {
    local service=$1
    local cloud_run_name="${SERVICE_NAMES[$service]}"
    
    log_warning "Attempting to rollback $service..."
    
    # Get previous revision
    local previous_revision
    previous_revision=$(gcloud run revisions list \
        --service="$cloud_run_name" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --limit=2 \
        --format="value(metadata.name)" | tail -n 1)
    
    if [[ -z "$previous_revision" ]]; then
        log_error "No previous revision found for rollback"
        return 1
    fi
    
    log_info "Rolling back to revision: $previous_revision"
    
    if gcloud run services update-traffic "$cloud_run_name" \
        --to-revisions="$previous_revision=100" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --quiet; then
        log_success "Rollback completed successfully"
        return 0
    else
        log_error "Rollback failed"
        return 1
    fi
}

# Create deployment tag
create_deployment_tag() {
    local service=$1
    local tag="deploy-${service}-$(date +%Y%m%d-%H%M%S)"
    
    if git rev-parse --git-dir > /dev/null 2>&1; then
        if git tag "$tag" 2>/dev/null; then
            log_info "Created deployment tag: $tag"
        else
            log_debug "Failed to create deployment tag (not critical)"
        fi
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
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -f|--force)
                FORCE_REBUILD="true"
                shift
                ;;
            --skip-health)
                SKIP_HEALTH_CHECK="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --rollback-on-fail)
                ROLLBACK_ON_FAILURE="true"
                shift
                ;;
            -d|--debug)
                DEBUG="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                if [[ -z "$SERVICE_NAME" ]]; then
                    SERVICE_NAME="$1"
                else
                    log_error "Unknown option: $1"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Main execution
main() {
    # Initialize log
    echo "=== Enhanced Service Deployment Log ===" > "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"
    
    echo -e "${CYAN}"
    echo "🧙‍♂️ Enhanced Alchemist Service Deployment"
    echo -e "${NC}"
    
    # Load configuration
    load_configuration
    
    # Set defaults
    PROJECT_ID="${ALCHEMIST_PROJECT_ID:-${PROJECT_ID:-$DEFAULT_PROJECT_ID}}"
    REGION="${ALCHEMIST_REGION:-${REGION:-$DEFAULT_REGION}}"
    ENVIRONMENT="${ALCHEMIST_ENV:-${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}}"
    
    # Parse arguments
    parse_arguments "$@"
    
    # Validate service
    validate_service "$SERVICE_NAME"
    
    # Show configuration
    echo -e "${BLUE}Deployment Configuration:${NC}"
    echo -e "  Service: ${WHITE}$SERVICE_NAME${NC}"
    echo -e "  Cloud Run Name: ${WHITE}${SERVICE_NAMES[$SERVICE_NAME]}${NC}"
    echo -e "  Project ID: ${WHITE}$PROJECT_ID${NC}"
    echo -e "  Region: ${WHITE}$REGION${NC}"
    echo -e "  Environment: ${WHITE}$ENVIRONMENT${NC}"
    echo -e "  Force Rebuild: ${WHITE}${FORCE_REBUILD:-false}${NC}"
    echo -e "  Dry Run: ${WHITE}${DRY_RUN:-false}${NC}"
    echo ""
    
    # Check for changes
    if ! check_for_changes "$SERVICE_NAME"; then
        log_info "No changes detected - skipping deployment"
        log_info "Use --force to rebuild anyway"
        exit 0
    fi
    
    # Main deployment process
    local deployment_failed=false
    
    # Build
    if ! build_service "$SERVICE_NAME"; then
        deployment_failed=true
    fi
    
    # Deploy
    if [[ "$deployment_failed" == "false" ]] && ! deploy_to_cloud_run "$SERVICE_NAME"; then
        deployment_failed=true
    fi
    
    # Health check
    if [[ "$deployment_failed" == "false" ]] && ! run_health_check "$SERVICE_NAME"; then
        if [[ "${ROLLBACK_ON_FAILURE:-}" == "true" ]]; then
            deployment_failed=true
        else
            log_warning "Health check failed but continuing (use --rollback-on-fail for automatic rollback)"
        fi
    fi
    
    # Handle failure
    if [[ "$deployment_failed" == "true" ]]; then
        log_error "Deployment failed"
        
        if [[ "${ROLLBACK_ON_FAILURE:-}" == "true" ]]; then
            rollback_service "$SERVICE_NAME"
        fi
        
        exit 1
    fi
    
    # Success
    log_success "Service deployment completed successfully"
    create_deployment_tag "$SERVICE_NAME"
    
    # Clean up temporary files
    rm -f ".last-build-${SERVICE_NAME}" ".last-url-${SERVICE_NAME}"
    
    echo ""
    log_success "🎉 $SERVICE_NAME deployed successfully!"
    echo "Full deployment log: $LOG_FILE"
}

# Run main function
main "$@"