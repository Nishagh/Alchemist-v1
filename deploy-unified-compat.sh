#!/bin/bash

# Alchemist Unified Deployment Script - Compatible Version
# This script provides a comprehensive deployment solution for all Alchemist services
# Compatible with Bash 3.2+ (macOS default)
# Author: Alchemist Team
# Version: 2.0.1

set -e

# Script configuration
SCRIPT_VERSION="2.0.1-compat"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/deployment.log"

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

# Service configuration using arrays instead of associative arrays
# Format: "service:tier:config:cloud_run_name"
SERVICE_CONFIG_DATA=(
    "knowledge-vault:1:--memory=2Gi --cpu=2 --max-instances=5 --concurrency=40:alchemist-knowledge-vault"
    "agent-engine:1:--memory=1Gi --cpu=1 --max-instances=10 --concurrency=80:alchemist-agent-engine"
    "agent-bridge:2:--memory=512Mi --cpu=1 --max-instances=3 --concurrency=100:alchemist-agent-bridge"
    "tool-forge:2:--memory=512Mi --cpu=1 --max-instances=3 --concurrency=50:alchemist-tool-forge"
    "mcp-config-generator:2:--memory=512Mi --cpu=1 --max-instances=2 --concurrency=30:alchemist-mcp-config-generator"
    "agent-launcher:3:--memory=1Gi --cpu=1 --max-instances=3 --concurrency=10:alchemist-agent-launcher"
    "prompt-engine:3:--memory=512Mi --cpu=1 --max-instances=3 --concurrency=50:alchemist-prompt-engine"
    "sandbox-console:3:--memory=1Gi --cpu=1 --max-instances=5 --concurrency=20:alchemist-sandbox-console"
    "banking-api-service:4:--memory=512Mi --cpu=1 --max-instances=3 --concurrency=50:alchemist-banking-api-service"
    "agent-studio:4:--memory=512Mi --cpu=1 --max-instances=5 --concurrency=100:alchemist-agent-studio"
    "admin-dashboard:4:--memory=512Mi --cpu=1 --max-instances=5 --concurrency=100:alchemist-admin-dashboard"
)

# Global variables
PROJECT_ID=""
REGION=""
ENVIRONMENT=""
DEPLOY_MODE=""
SELECTED_SERVICES=()
DEPLOYED_SERVICES=()
FAILED_SERVICES=()

# Helper functions to work with service configuration
get_service_tier() {
    local service_name=$1
    for config in "${SERVICE_CONFIG_DATA[@]}"; do
        IFS=':' read -r name tier config_str cloud_name <<< "$config"
        if [[ "$name" == "$service_name" ]]; then
            echo "$tier"
            return
        fi
    done
    echo "1"  # Default tier
}

get_service_config() {
    local service_name=$1
    for config in "${SERVICE_CONFIG_DATA[@]}"; do
        IFS=':' read -r name tier config_str cloud_name <<< "$config"
        if [[ "$name" == "$service_name" ]]; then
            echo "$config_str"
            return
        fi
    done
    echo "--memory=1Gi --cpu=1 --max-instances=3 --concurrency=80"  # Default config
}

get_cloud_run_name() {
    local service_name=$1
    for config in "${SERVICE_CONFIG_DATA[@]}"; do
        IFS=':' read -r name tier config_str cloud_name <<< "$config"
        if [[ "$name" == "$service_name" ]]; then
            echo "$cloud_name"
            return
        fi
    done
    echo "alchemist-$service_name"  # Default name
}

get_all_services() {
    for config in "${SERVICE_CONFIG_DATA[@]}"; do
        IFS=':' read -r name tier config_str cloud_name <<< "$config"
        echo "$name"
    done
}

get_services_by_tier() {
    local target_tier=$1
    for config in "${SERVICE_CONFIG_DATA[@]}"; do
        IFS=':' read -r name tier config_str cloud_name <<< "$config"
        if [[ "$tier" == "$target_tier" ]]; then
            echo "$name"
        fi
    done
}

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

# Banner function
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🧙‍♂️ ALCHEMIST UNIFIED DEPLOYMENT SYSTEM 🧙‍♂️              ║
║                                                              ║
║     Transforming Deployment Complexity into Simplicity      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo -e "${WHITE}Version: ${SCRIPT_VERSION}${NC}"
    echo -e "${WHITE}Mode: Unified Multi-Tier Deployment (Bash 3.2+ Compatible)${NC}"
    echo ""
}

# Help function
show_help() {
    cat << EOF
${WHITE}Alchemist Unified Deployment Script (Compatible Version)${NC}

${YELLOW}USAGE:${NC}
    $0 [OPTIONS] [MODE] [SERVICES...]

${YELLOW}MODES:${NC}
    all                 Deploy all services in tier order
    core                Deploy core services only (Tier 1)
    services [names]    Deploy specific services
    frontend            Deploy frontend services only
    validate            Validate deployment configuration
    status              Check deployment status
    rollback [service]  Rollback specific service

${YELLOW}OPTIONS:${NC}
    -p, --project-id ID    Google Cloud Project ID (default: ${DEFAULT_PROJECT_ID})
    -r, --region REGION    Deployment region (default: ${DEFAULT_REGION})
    -e, --env ENV          Environment (dev/staging/production, default: ${DEFAULT_ENVIRONMENT})
    -t, --timeout TIME     Deployment timeout (default: ${TIMEOUT})
    -d, --debug            Enable debug logging
    -y, --yes              Skip confirmation prompts
    -h, --help             Show this help message

${YELLOW}SERVICES:${NC}
    ${GREEN}Tier 1 (Core):${NC}        knowledge-vault, agent-engine
    ${BLUE}Tier 2 (Integration):${NC} agent-bridge, tool-forge, mcp-config-generator
    ${PURPLE}Tier 3 (Application):${NC} agent-launcher, prompt-engine, sandbox-console
    ${CYAN}Tier 4 (External):${NC}    banking-api-service, agent-studio, admin-dashboard

${YELLOW}EXAMPLES:${NC}
    $0 all                                    # Deploy all services
    $0 core                                   # Deploy core services only
    $0 services agent-engine knowledge-vault  # Deploy specific services
    $0 -p my-project -r us-west1 all         # Deploy to specific project/region
    $0 -e staging frontend                    # Deploy frontend in staging
    $0 status                                 # Check deployment status

${YELLOW}ENVIRONMENT VARIABLES:${NC}
    ALCHEMIST_PROJECT_ID    Override project ID
    ALCHEMIST_REGION        Override region
    ALCHEMIST_ENV           Override environment
    DEBUG                   Enable debug mode
    SKIP_CONFIRMATIONS      Skip confirmation prompts

For detailed documentation, see: ${CYAN}./UNIFIED_DEPLOYMENT_GUIDE.md${NC}
EOF
}

# Configuration validation
validate_prerequisites() {
    log_info "Validating deployment prerequisites..."
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud SDK (gcloud) is not installed"
        log_error "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with Google Cloud"
        log_error "Run: gcloud auth login"
        exit 1
    fi
    
    # Check Docker (if needed for local builds)
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found - will use Cloud Build only"
    fi
    
    # Validate project access
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Cannot access project: $PROJECT_ID"
        log_error "Check project ID and permissions"
        exit 1
    fi
    
    log_success "Prerequisites validated"
}

# Setup environment
setup_environment() {
    log_info "Setting up deployment environment..."
    
    # Set gcloud project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    local apis=(
        "run.googleapis.com"
        "cloudbuild.googleapis.com" 
        "firestore.googleapis.com"
        "secretmanager.googleapis.com"
        "storage.googleapis.com"
        "artifactregistry.googleapis.com"
        "firebase.googleapis.com"
    )
    
    log_info "Enabling required Google Cloud APIs..."
    for api in "${apis[@]}"; do
        if gcloud services enable "$api" --quiet; then
            log_debug "Enabled API: $api"
        else
            log_warning "Failed to enable API: $api"
        fi
    done
    
    # Create deployment log directory if needed
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_success "Environment setup completed"
}

# Secret management
manage_secrets() {
    log_info "Setting up secret management..."
    
    # Check for OpenAI API key in Secret Manager
    if ! gcloud secrets describe openai-api-key --quiet &> /dev/null; then
        log_warning "OpenAI API key not found in Secret Manager"
        if [[ -z "${OPENAI_API_KEY:-}" ]]; then
            log_error "OPENAI_API_KEY environment variable not set"
            log_error "Set OPENAI_API_KEY or create secret: gcloud secrets create openai-api-key --data-file=-"
            return 1
        else
            log_info "Creating OpenAI API key secret..."
            echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-
        fi
    fi
    
    # Grant service account access to secrets
    local service_account="${PROJECT_ID}@appspot.gserviceaccount.com"
    gcloud secrets add-iam-policy-binding openai-api-key \
        --member="serviceAccount:$service_account" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet || true
    
    log_success "Secret management configured"
}

# Service deployment function
deploy_service() {
    local service_name=$1
    local cloud_run_name=$(get_cloud_run_name "$service_name")
    local image_name="gcr.io/${PROJECT_ID}/${cloud_run_name}"
    local service_dir="${service_name}"
    
    # Handle special cases for service directories
    case $service_name in
        "admin-dashboard")
            service_dir="admin-dashboard"
            ;;
        "mcp-config-generator") 
            service_dir="mcp_config_generator"
            ;;
        "banking-api-service")
            service_dir="banking-api-service"
            ;;
    esac
    
    log_info "Deploying service: $service_name ($cloud_run_name)"
    
    # Validate service directory exists
    if [[ ! -d "$service_dir" ]]; then
        log_error "Service directory not found: $service_dir"
        return 1
    fi
    
    # Check for Dockerfile
    if [[ ! -f "$service_dir/Dockerfile" ]]; then
        log_error "Dockerfile not found in $service_dir"
        return 1
    fi
    
    # Build and deploy using Cloud Build
    log_info "Building container image for $service_name..."
    
    # Create temporary cloudbuild.yaml for this service
    local cloudbuild_file="cloudbuild-${service_name}-temp.yaml"
    cat > "$cloudbuild_file" << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', '${service_dir}/Dockerfile', '-t', '${image_name}', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${image_name}']
images:
- '${image_name}'
timeout: '${TIMEOUT}'
EOF
    
    if ! gcloud builds submit --config="$cloudbuild_file" --timeout="$TIMEOUT" --quiet; then
        log_error "Failed to build $service_name"
        rm -f "$cloudbuild_file"
        return 1
    fi
    
    # Clean up temporary file
    rm -f "$cloudbuild_file"
    
    # Deploy to Cloud Run
    log_info "Deploying $service_name to Cloud Run..."
    
    local service_config=$(get_service_config "$service_name")
    local env_vars="ENVIRONMENT=${ENVIRONMENT}"
    
    # Add service-specific environment variables
    case $service_name in
        "agent-engine"|"knowledge-vault"|"agent-bridge"|"prompt-engine"|"sandbox-console")
            env_vars="${env_vars},FIREBASE_PROJECT_ID=${PROJECT_ID}"
            ;;
        "agent-studio")
            env_vars="${env_vars},REACT_APP_FIREBASE_PROJECT_ID=${PROJECT_ID}"
            ;;
        "banking-api-service")
            env_vars="${env_vars},BANKING_API_KEY=banking-api-key-2025"
            ;;
    esac
    
    if ! gcloud run deploy "$cloud_run_name" \
        --image="$image_name" \
        --platform=managed \
        --region="$REGION" \
        --allow-unauthenticated \
        --port=8080 \
        --set-env-vars="$env_vars" \
        --set-secrets="OPENAI_API_KEY=openai-api-key:latest" \
        --quiet \
        $service_config; then
        log_error "Failed to deploy $service_name to Cloud Run"
        return 1
    fi
    
    # Get service URL
    local service_url
    service_url=$(gcloud run services describe "$cloud_run_name" \
        --region="$REGION" \
        --format="value(status.url)" 2>/dev/null || echo "")
    
    if [[ -n "$service_url" ]]; then
        log_success "$service_name deployed successfully: $service_url"
    else
        log_warning "$service_name deployed but URL not retrieved"
    fi
    
    return 0
}

# Service health check
verify_service_health() {
    local service_name=$1
    local cloud_run_name=$(get_cloud_run_name "$service_name")
    local service_url
    service_url=$(gcloud run services describe "$cloud_run_name" \
        --region="$REGION" \
        --format="value(status.url)" 2>/dev/null || echo "")
    local max_attempts=10
    local attempt=1
    
    if [[ -z "$service_url" ]]; then
        log_warning "No URL available for $service_name health check"
        return 1
    fi
    
    log_info "Verifying health of $service_name..."
    
    while [[ $attempt -le $max_attempts ]]; do
        log_debug "Health check attempt $attempt/$max_attempts for $service_name"
        
        # Try health endpoint first, then root endpoint
        if curl -f -s "${service_url}/health" > /dev/null 2>&1 || \
           curl -f -s "${service_url}" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        log_debug "Health check failed, waiting 30 seconds..."
        sleep 30
        ((attempt++))
    done
    
    log_warning "$service_name health check failed after $max_attempts attempts"
    return 1
}

# Deploy services by tier
deploy_by_tier() {
    local max_tier=${1:-4}
    
    for tier in $(seq 1 $max_tier); do
        log_info "Deploying Tier $tier services..."
        
        local tier_services
        tier_services=($(get_services_by_tier "$tier"))
        
        if [[ ${#tier_services[@]} -eq 0 ]]; then
            log_info "No services in Tier $tier"
            continue
        fi
        
        log_info "Tier $tier services: ${tier_services[*]}"
        
        # Deploy services in this tier
        for service in "${tier_services[@]}"; do
            if deploy_service "$service"; then
                DEPLOYED_SERVICES+=("$service")
                
                # Verify health for critical services
                if [[ $tier -le 2 ]]; then
                    verify_service_health "$service" || true
                fi
            else
                FAILED_SERVICES+=("$service")
                log_error "Failed to deploy $service in Tier $tier"
            fi
        done
        
        # Wait between tiers for services to stabilize
        if [[ $tier -lt $max_tier ]]; then
            log_info "Waiting 60 seconds before next tier..."
            sleep 60
        fi
    done
}

# Configure inter-service communication
configure_services() {
    log_info "Configuring inter-service communication..."
    
    # Get service URLs
    local agent_engine_url=""
    local knowledge_vault_url=""
    local agent_bridge_url=""
    local agent_launcher_url=""
    local tool_forge_url=""
    local agent_studio_url=""
    
    for service in agent-engine knowledge-vault agent-bridge agent-launcher tool-forge agent-studio; do
        local cloud_run_name=$(get_cloud_run_name "$service")
        local url=$(gcloud run services describe "$cloud_run_name" \
            --region="$REGION" \
            --format="value(status.url)" 2>/dev/null || echo "")
        
        case $service in
            "agent-engine") agent_engine_url="$url" ;;
            "knowledge-vault") knowledge_vault_url="$url" ;;
            "agent-bridge") agent_bridge_url="$url" ;;
            "agent-launcher") agent_launcher_url="$url" ;;
            "tool-forge") tool_forge_url="$url" ;;
            "agent-studio") agent_studio_url="$url" ;;
        esac
    done
    
    # Update agent-engine with service URLs
    if [[ -n "$agent_engine_url" ]]; then
        local env_vars="ENVIRONMENT=${ENVIRONMENT},FIREBASE_PROJECT_ID=${PROJECT_ID}"
        
        if [[ -n "$knowledge_vault_url" ]]; then
            env_vars="${env_vars},KNOWLEDGE_VAULT_URL=${knowledge_vault_url}"
        fi
        if [[ -n "$agent_bridge_url" ]]; then
            env_vars="${env_vars},AGENT_BRIDGE_URL=${agent_bridge_url}"
        fi
        if [[ -n "$agent_launcher_url" ]]; then
            env_vars="${env_vars},AGENT_LAUNCHER_URL=${agent_launcher_url}"
        fi
        if [[ -n "$tool_forge_url" ]]; then
            env_vars="${env_vars},TOOL_FORGE_URL=${tool_forge_url}"
        fi
        
        gcloud run services update "$(get_cloud_run_name "agent-engine")" \
            --region="$REGION" \
            --set-env-vars="$env_vars" \
            --quiet || log_warning "Failed to update agent-engine configuration"
    fi
    
    # Configure CORS for frontend access
    if [[ -n "$agent_studio_url" ]]; then
        for service in agent-engine knowledge-vault agent-bridge; do
            local cloud_run_name=$(get_cloud_run_name "$service")
            gcloud run services update "$cloud_run_name" \
                --region="$REGION" \
                --set-env-vars="CORS_ORIGINS=$agent_studio_url" \
                --quiet || log_warning "Failed to update CORS for $service"
        done
    fi
    
    log_success "Service configuration completed"
}

# Status checking
check_deployment_status() {
    log_info "Checking deployment status..."
    
    echo -e "\n${WHITE}=== DEPLOYMENT STATUS ===${NC}\n"
    
    local all_services
    all_services=($(get_all_services))
    
    for service in "${all_services[@]}"; do
        local cloud_run_name=$(get_cloud_run_name "$service")
        local status="Unknown"
        local url=""
        
        if gcloud run services describe "$cloud_run_name" --region="$REGION" --quiet &> /dev/null; then
            status="Deployed"
            url=$(gcloud run services describe "$cloud_run_name" \
                --region="$REGION" \
                --format="value(status.url)" 2>/dev/null || echo "URL not available")
        else
            status="Not Deployed"
        fi
        
        printf "%-25s %-15s %s\n" "$service" "$status" "$url"
    done
    
    echo ""
}

# Rollback function
rollback_service() {
    local service_name=$1
    local cloud_run_name=$(get_cloud_run_name "$service_name")
    
    if [[ -z "$cloud_run_name" ]]; then
        log_error "Unknown service: $service_name"
        return 1
    fi
    
    log_info "Rolling back service: $service_name"
    
    # Get previous revision
    local previous_revision
    previous_revision=$(gcloud run revisions list \
        --service="$cloud_run_name" \
        --region="$REGION" \
        --limit=2 \
        --format="value(metadata.name)" | tail -n 1)
    
    if [[ -z "$previous_revision" ]]; then
        log_error "No previous revision found for $service_name"
        return 1
    fi
    
    # Update traffic to previous revision
    if gcloud run services update-traffic "$cloud_run_name" \
        --to-revisions="$previous_revision=100" \
        --region="$REGION" \
        --quiet; then
        log_success "Rolled back $service_name to revision: $previous_revision"
    else
        log_error "Failed to rollback $service_name"
        return 1
    fi
}

# Deployment summary
show_deployment_summary() {
    echo -e "\n${WHITE}=== DEPLOYMENT SUMMARY ===${NC}\n"
    
    if [[ ${#DEPLOYED_SERVICES[@]} -gt 0 ]]; then
        echo -e "${GREEN}✅ Successfully deployed (${#DEPLOYED_SERVICES[@]}):${NC}"
        for service in "${DEPLOYED_SERVICES[@]}"; do
            local cloud_run_name=$(get_cloud_run_name "$service")
            local url=$(gcloud run services describe "$cloud_run_name" \
                --region="$REGION" \
                --format="value(status.url)" 2>/dev/null || echo "URL not available")
            printf "  ${GREEN}%-25s${NC} %s\n" "$service" "$url"
        done
        echo ""
    fi
    
    if [[ ${#FAILED_SERVICES[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Failed deployments (${#FAILED_SERVICES[@]}):${NC}"
        for service in "${FAILED_SERVICES[@]}"; do
            echo -e "  ${RED}- $service${NC}"
        done
        echo ""
        echo -e "${RED}Some services failed to deploy. Check logs: $LOG_FILE${NC}"
    fi
    
    if [[ ${#DEPLOYED_SERVICES[@]} -gt 0 && ${#FAILED_SERVICES[@]} -eq 0 ]]; then
        echo -e "${GREEN}🎉 All services deployed successfully!${NC}"
        echo ""
        echo -e "${CYAN}🧪 Test your deployment:${NC}"
        local agent_engine_url=$(gcloud run services describe "$(get_cloud_run_name "agent-engine")" \
            --region="$REGION" \
            --format="value(status.url)" 2>/dev/null || echo "")
        local agent_studio_url=$(gcloud run services describe "$(get_cloud_run_name "agent-studio")" \
            --region="$REGION" \
            --format="value(status.url)" 2>/dev/null || echo "")
        
        if [[ -n "$agent_engine_url" ]]; then
            echo -e "  curl ${agent_engine_url}/health"
        fi
        if [[ -n "$agent_studio_url" ]]; then
            echo -e "  open ${agent_studio_url}"
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
            -d|--debug)
                DEBUG="true"
                shift
                ;;
            -y|--yes)
                SKIP_CONFIRMATIONS="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            all|core|frontend|validate|status)
                DEPLOY_MODE="$1"
                shift
                ;;
            services)
                DEPLOY_MODE="services"
                shift
                # Collect service names
                while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
                    SELECTED_SERVICES+=("$1")
                    shift
                done
                ;;
            rollback)
                DEPLOY_MODE="rollback"
                if [[ $# -gt 1 && ! "$2" =~ ^- ]]; then
                    SELECTED_SERVICES+=("$2")
                    shift
                fi
                shift
                ;;
            *)
                # Check if it's a valid service name
                local valid_service=false
                local all_services
                all_services=($(get_all_services))
                for service in "${all_services[@]}"; do
                    if [[ "$1" == "$service" ]]; then
                        valid_service=true
                        break
                    fi
                done
                
                if [[ "$valid_service" == "true" ]]; then
                    SELECTED_SERVICES+=("$1")
                else
                    log_error "Unknown option or service: $1"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Main execution function
main() {
    # Initialize log file
    echo "=== Alchemist Unified Deployment Log ===" > "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"
    
    show_banner
    
    # Set defaults from environment variables or use defaults
    PROJECT_ID="${ALCHEMIST_PROJECT_ID:-${PROJECT_ID:-$DEFAULT_PROJECT_ID}}"
    REGION="${ALCHEMIST_REGION:-${REGION:-$DEFAULT_REGION}}"
    ENVIRONMENT="${ALCHEMIST_ENV:-${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}}"
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # If no mode specified, show help
    if [[ -z "$DEPLOY_MODE" ]]; then
        show_help
        exit 0
    fi
    
    # Show configuration
    echo -e "${BLUE}Configuration:${NC}"
    echo -e "  Project ID: ${WHITE}$PROJECT_ID${NC}"
    echo -e "  Region: ${WHITE}$REGION${NC}"  
    echo -e "  Environment: ${WHITE}$ENVIRONMENT${NC}"
    echo -e "  Mode: ${WHITE}$DEPLOY_MODE${NC}"
    if [[ ${#SELECTED_SERVICES[@]} -gt 0 ]]; then
        echo -e "  Services: ${WHITE}${SELECTED_SERVICES[*]}${NC}"
    fi
    echo ""
    
    # Confirm deployment unless skipped
    if [[ "${SKIP_CONFIRMATIONS:-}" != "true" ]] && [[ "$DEPLOY_MODE" != "validate" ]] && [[ "$DEPLOY_MODE" != "status" ]]; then
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    # Execute based on mode
    case $DEPLOY_MODE in
        "validate")
            validate_prerequisites
            log_success "Validation completed successfully"
            ;;
        "status")
            check_deployment_status
            ;;
        "rollback")
            if [[ ${#SELECTED_SERVICES[@]} -eq 0 ]]; then
                log_error "No service specified for rollback"
                exit 1
            fi
            validate_prerequisites
            for service in "${SELECTED_SERVICES[@]}"; do
                rollback_service "$service"
            done
            ;;
        "all")
            validate_prerequisites
            setup_environment
            manage_secrets
            deploy_by_tier 4
            configure_services
            show_deployment_summary
            ;;
        "core")
            validate_prerequisites
            setup_environment
            manage_secrets
            deploy_by_tier 1
            configure_services
            show_deployment_summary
            ;;
        "frontend")
            validate_prerequisites
            setup_environment
            # Deploy frontend services (agent-studio, admin-dashboard)
            for service in agent-studio admin-dashboard; do
                if deploy_service "$service"; then
                    DEPLOYED_SERVICES+=("$service")
                else
                    FAILED_SERVICES+=("$service")
                fi
            done
            show_deployment_summary
            ;;
        "services")
            if [[ ${#SELECTED_SERVICES[@]} -eq 0 ]]; then
                log_error "No services specified"
                exit 1
            fi
            validate_prerequisites
            setup_environment
            manage_secrets
            
            # Deploy selected services
            for service in "${SELECTED_SERVICES[@]}"; do
                local all_services
                all_services=($(get_all_services))
                local valid_service=false
                for valid in "${all_services[@]}"; do
                    if [[ "$service" == "$valid" ]]; then
                        valid_service=true
                        break
                    fi
                done
                
                if [[ "$valid_service" != "true" ]]; then
                    log_error "Unknown service: $service"
                    FAILED_SERVICES+=("$service")
                    continue
                fi
                
                if deploy_service "$service"; then
                    DEPLOYED_SERVICES+=("$service")
                    verify_service_health "$service" || true
                else
                    FAILED_SERVICES+=("$service")
                fi
            done
            configure_services
            show_deployment_summary
            ;;
        *)
            log_error "Unknown deployment mode: $DEPLOY_MODE"
            show_help
            exit 1
            ;;
    esac
    
    log_info "Deployment script completed"
    echo "Full deployment log available at: $LOG_FILE"
}

# Script entry point
main "$@"