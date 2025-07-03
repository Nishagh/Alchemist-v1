#!/bin/bash

# Alchemist Smart Deployment System
# Intelligent change detection and selective deployment with comprehensive management

set -e

# Source all libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
source "${SCRIPT_DIR}/lib/change-detector.sh"
source "${SCRIPT_DIR}/lib/state-manager.sh"
source "${SCRIPT_DIR}/lib/service-deps.sh"

# Global configuration
SCRIPT_VERSION="1.0.0"
DEFAULT_PROJECT_ID="alchemist-e69bb"
DEFAULT_REGION="us-central1"
DEFAULT_ENVIRONMENT="production"
DEFAULT_TIMEOUT="3600s"

# Global variables
PROJECT_ID=""
REGION=""
ENVIRONMENT=""
DEPLOY_MODE=""
SELECTED_SERVICES=()
FORCE_DEPLOY=false
DRY_RUN=false
PARALLEL_DEPLOYMENT=false
MAX_PARALLEL=5
SKIP_HEALTH_CHECK=false
SKIP_CONFIRMATIONS=false

# Deployment tracking
DEPLOYMENT_START_TIME=""
DEPLOYED_SERVICES=()
FAILED_SERVICES=()
SKIPPED_SERVICES=()
declare -A SERVICE_URLS
declare -A SERVICE_ERRORS

# Show help
show_help() {
    cat << EOF
${WHITE}Alchemist Smart Deployment System v${SCRIPT_VERSION}${NC}

${YELLOW}DESCRIPTION:${NC}
    Intelligent deployment system that automatically detects changes and deploys
    only modified services with comprehensive dependency management and rollback.

${YELLOW}USAGE:${NC}
    $0 [OPTIONS] [MODE] [SERVICES...]

${YELLOW}DEPLOYMENT MODES:${NC}
    ${GREEN}auto${NC}              Auto-detect changed services and deploy them
    ${GREEN}all${NC}               Deploy all services in dependency order
    ${GREEN}group <name>${NC}       Deploy services from a deployment group
    ${GREEN}services <names>${NC}   Deploy specific services
    ${GREEN}status${NC}             Show current deployment status
    ${GREEN}rollback [service]${NC} Rollback service(s) to previous version
    ${GREEN}validate${NC}           Validate deployment configuration
    ${GREEN}diff${NC}               Show what would be deployed (dry run)

${YELLOW}DEPLOYMENT GROUPS:${NC}
    ${GREEN}core${NC}               Core infrastructure services
    ${GREEN}integrations${NC}       External integration services
    ${GREEN}infrastructure${NC}     Platform infrastructure services
    ${GREEN}tools${NC}              Development and management tools
    ${GREEN}frontend${NC}           User interface applications

${YELLOW}OPTIONS:${NC}
    ${CYAN}Configuration:${NC}
    -p, --project-id ID      Google Cloud Project ID
    -r, --region REGION      Deployment region (default: ${DEFAULT_REGION})
    -e, --env ENV            Environment (dev/staging/production)
    
    ${CYAN}Deployment Control:${NC}
    -f, --force              Force deployment of all specified services
    -n, --dry-run            Show what would be deployed without deploying
    --parallel               Enable parallel deployment within tiers
    --max-parallel N         Maximum parallel deployments (default: ${MAX_PARALLEL})
    --skip-health-check      Skip health checks after deployment
    
    ${CYAN}Detection Method:${NC}
    --git                    Use git-based change detection
    --fingerprint            Use file fingerprint change detection
    --auto                   Auto-select best detection method (default)
    
    ${CYAN}Control:${NC}
    -y, --yes                Skip confirmation prompts
    -t, --timeout TIME       Deployment timeout (default: ${DEFAULT_TIMEOUT})
    -d, --debug              Enable debug logging
    -h, --help               Show this help message

${YELLOW}EXAMPLES:${NC}
    ${CYAN}# Auto-deploy changed services${NC}
    $0 auto
    
    ${CYAN}# Deploy specific services${NC}
    $0 services agent-engine knowledge-vault
    
    ${CYAN}# Deploy core services group${NC}
    $0 group core
    
    ${CYAN}# Force deploy all services${NC}
    $0 all --force
    
    ${CYAN}# Dry run to see what would be deployed${NC}
    $0 auto --dry-run
    
    ${CYAN}# Deploy with parallel execution${NC}
    $0 auto --parallel --max-parallel 3
    
    ${CYAN}# Check deployment status${NC}
    $0 status
    
    ${CYAN}# Rollback specific service${NC}
    $0 rollback agent-engine
    
    ${CYAN}# Deploy to staging environment${NC}
    $0 -e staging auto

${YELLOW}ENVIRONMENT VARIABLES:${NC}
    ALCHEMIST_PROJECT_ID     Override project ID
    ALCHEMIST_REGION         Override region
    ALCHEMIST_ENV            Override environment
    DEBUG                    Enable debug mode
    SKIP_CONFIRMATIONS       Skip confirmation prompts

${YELLOW}STATE MANAGEMENT:${NC}
    Deployment state is stored in: ${CYAN}.deployment/state.json${NC}
    Deployment logs in: ${CYAN}.deployment/logs/deployment.log${NC}
    Backups in: ${CYAN}.deployment/backups/${NC}

For detailed documentation, see: ${CYAN}./ALCHEMIST.md${NC}
EOF
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
            -f|--force)
                FORCE_DEPLOY=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            --parallel)
                PARALLEL_DEPLOYMENT=true
                shift
                ;;
            --max-parallel)
                MAX_PARALLEL="$2"
                shift 2
                ;;
            --skip-health-check)
                SKIP_HEALTH_CHECK=true
                shift
                ;;
            --git|--fingerprint|--auto)
                DETECTION_METHOD="${1#--}"
                shift
                ;;
            -y|--yes)
                SKIP_CONFIRMATIONS=true
                shift
                ;;
            -t|--timeout)
                DEFAULT_TIMEOUT="$2"
                shift 2
                ;;
            -d|--debug)
                DEBUG="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            auto|all|status|validate|diff)
                DEPLOY_MODE="$1"
                shift
                ;;
            group)
                DEPLOY_MODE="group"
                if [[ $# -gt 1 && ! "$2" =~ ^- ]]; then
                    SELECTED_SERVICES=("$2")
                    shift
                fi
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
                shift
                # Collect service names for rollback
                while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
                    SELECTED_SERVICES+=("$1")
                    shift
                done
                ;;
            *)
                # Check if it's a valid service name
                if service_exists "$1"; then
                    SELECTED_SERVICES+=("$1")
                else
                    log_error "Unknown option or service: $1"
                    echo ""
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Initialize deployment
init_deployment() {
    # Set defaults from environment variables
    PROJECT_ID="${ALCHEMIST_PROJECT_ID:-${PROJECT_ID:-$DEFAULT_PROJECT_ID}}"
    REGION="${ALCHEMIST_REGION:-${REGION:-$DEFAULT_REGION}}"
    ENVIRONMENT="${ALCHEMIST_ENV:-${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}}"
    SKIP_CONFIRMATIONS="${SKIP_CONFIRMATIONS:-${SKIP_CONFIRMATIONS:-false}}"
    
    # If no mode specified, default to auto
    if [[ -z "$DEPLOY_MODE" ]]; then
        DEPLOY_MODE="auto"
    fi
    
    # Initialize deployment state
    init_deployment_state "$PROJECT_ID" "$REGION" "$ENVIRONMENT"
    
    # Acquire deployment lock
    if ! acquire_lock 300; then
        log_error "Could not acquire deployment lock. Another deployment may be in progress."
        exit 1
    fi
    
    # Record deployment start
    DEPLOYMENT_START_TIME=$(get_unix_timestamp)
    log_info "Starting smart deployment at $(get_timestamp)"
}

# Show deployment configuration
show_deployment_config() {
    echo -e "${BLUE}Deployment Configuration:${NC}"
    echo -e "  Project ID: ${WHITE}$PROJECT_ID${NC}"
    echo -e "  Region: ${WHITE}$REGION${NC}"
    echo -e "  Environment: ${WHITE}$ENVIRONMENT${NC}"
    echo -e "  Mode: ${WHITE}$DEPLOY_MODE${NC}"
    echo -e "  Detection Method: ${WHITE}${DETECTION_METHOD:-auto}${NC}"
    
    if [[ ${#SELECTED_SERVICES[@]} -gt 0 ]]; then
        echo -e "  Services: ${WHITE}${SELECTED_SERVICES[*]}${NC}"
    fi
    
    if [[ "$FORCE_DEPLOY" == "true" ]]; then
        echo -e "  Force Deploy: ${YELLOW}Yes${NC}"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "  Dry Run: ${YELLOW}Yes${NC}"
    fi
    
    if [[ "$PARALLEL_DEPLOYMENT" == "true" ]]; then
        echo -e "  Parallel Deployment: ${GREEN}Yes${NC} (max: $MAX_PARALLEL)"
    fi
    
    echo ""
}

# Deploy single service
deploy_service() {
    local service_name=$1
    local service_config
    
    log_info "Deploying service: $service_name"
    
    # Get service configuration
    service_config=$(get_service_config "$service_name")
    if [[ $? -ne 0 ]]; then
        log_error "Failed to get configuration for service: $service_name"
        return 1
    fi
    
    # Extract configuration values
    local service_path
    service_path=$(echo "$service_config" | yq eval '.path' -)
    local cloud_run_name
    cloud_run_name=$(echo "$service_config" | yq eval '.cloud_run_name' -)
    local dockerfile
    dockerfile=$(echo "$service_config" | yq eval '.dockerfile // "Dockerfile"' -)
    local port
    port=$(echo "$service_config" | yq eval '.port // 8080' -)
    
    # Validate service directory
    local full_service_path="$ROOT_DIR/$service_path"
    if [[ ! -d "$full_service_path" ]]; then
        log_error "Service directory not found: $full_service_path"
        return 1
    fi
    
    # Check for Dockerfile
    if [[ ! -f "$full_service_path/$dockerfile" ]]; then
        log_error "Dockerfile not found: $full_service_path/$dockerfile"
        return 1
    fi
    
    # Build container image
    local image_name="gcr.io/${PROJECT_ID}/${cloud_run_name}"
    log_info "Building container image: $image_name"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Create build configuration
        local build_config
        build_config=$(cat << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', '${service_path}/${dockerfile}', '-t', '${image_name}', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '${image_name}']
images:
- '${image_name}'
timeout: '${DEFAULT_TIMEOUT}'
EOF
)
        
        local build_file="cloudbuild-${service_name}-$(date +%s).yaml"
        echo "$build_config" > "$build_file"
        
        if ! gcloud builds submit --config="$build_file" --timeout="$DEFAULT_TIMEOUT" --quiet; then
            log_error "Failed to build container for: $service_name"
            rm -f "$build_file"
            return 1
        fi
        
        rm -f "$build_file"
    else
        log_info "DRY RUN: Would build $image_name"
    fi
    
    # Deploy to Cloud Run
    log_info "Deploying to Cloud Run: $cloud_run_name"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Get resource configuration
        local memory
        memory=$(echo "$service_config" | yq eval '.resource_config.memory // "1Gi"' -)
        local cpu
        cpu=$(echo "$service_config" | yq eval '.resource_config.cpu // 1' -)
        local max_instances
        max_instances=$(echo "$service_config" | yq eval '.resource_config.max_instances // 3' -)
        local min_instances
        min_instances=$(echo "$service_config" | yq eval '.resource_config.min_instances // 0' -)
        local concurrency
        concurrency=$(echo "$service_config" | yq eval '.resource_config.concurrency // 80' -)
        local timeout
        timeout=$(echo "$service_config" | yq eval '.resource_config.timeout // 900' -)
        
        # Apply environment overrides
        max_instances=$(apply_environment_overrides "$service_name" "$ENVIRONMENT" "max_instances")
        min_instances=$(apply_environment_overrides "$service_name" "$ENVIRONMENT" "min_instances")
        concurrency=$(apply_environment_overrides "$service_name" "$ENVIRONMENT" "concurrency")
        
        # Build environment variables
        local env_vars="ENVIRONMENT=${ENVIRONMENT}"
        local env_var_list
        env_var_list=$(get_service_environment_variables "$service_name")
        
        while IFS= read -r env_var; do
            [[ -z "$env_var" || "$env_var" == "null" ]] && continue
            
            case "$env_var" in
                "FIREBASE_PROJECT_ID"|"REACT_APP_FIREBASE_PROJECT_ID")
                    env_vars="${env_vars},${env_var}=${PROJECT_ID}"
                    ;;
                "AGENT_ENGINE_URL")
                    if [[ -n "${SERVICE_URLS[agent-engine]:-}" ]]; then
                        env_vars="${env_vars},${env_var}=${SERVICE_URLS[agent-engine]}"
                    fi
                    ;;
                "KNOWLEDGE_VAULT_URL"|"REACT_APP_KNOWLEDGE_VAULT_URL")
                    if [[ -n "${SERVICE_URLS[knowledge-vault]:-}" ]]; then
                        env_vars="${env_vars},${env_var}=${SERVICE_URLS[knowledge-vault]}"
                    fi
                    ;;
                "AGENT_BRIDGE_URL")
                    if [[ -n "${SERVICE_URLS[agent-bridge]:-}" ]]; then
                        env_vars="${env_vars},${env_var}=${SERVICE_URLS[agent-bridge]}"
                    fi
                    ;;
                *)
                    # Use default values for other environment variables
                    case "$env_var" in
                        "BANKING_API_KEY") env_vars="${env_vars},${env_var}=banking-api-key-2025" ;;
                        "OPENAI_API_KEY") ;; # Will be set via secrets
                        *) log_debug "Skipping environment variable: $env_var" ;;
                    esac
                    ;;
            esac
        done <<< "$env_var_list"
        
        # Deploy service
        local deploy_cmd="gcloud run deploy $cloud_run_name \
            --image=$image_name \
            --platform=managed \
            --region=$REGION \
            --allow-unauthenticated \
            --port=$port \
            --memory=$memory \
            --cpu=$cpu \
            --max-instances=$max_instances \
            --min-instances=$min_instances \
            --concurrency=$concurrency \
            --timeout=${timeout}s \
            --set-env-vars=\"$env_vars\" \
            --quiet"
        
        # Add secrets for services that need them
        if [[ "$env_var_list" =~ OPENAI_API_KEY ]]; then
            deploy_cmd="${deploy_cmd} --set-secrets=\"OPENAI_API_KEY=openai-api-key:latest\""
        fi
        
        if ! eval "$deploy_cmd"; then
            log_error "Failed to deploy service: $service_name"
            return 1
        fi
        
        # Get service URL
        local service_url
        service_url=$(gcloud run services describe "$cloud_run_name" \
            --region="$REGION" \
            --format="value(status.url)" 2>/dev/null || echo "")
        
        if [[ -n "$service_url" ]]; then
            SERVICE_URLS["$service_name"]="$service_url"
            log_success "$service_name deployed: $service_url"
        else
            log_warning "$service_name deployed but URL not retrieved"
        fi
        
        # Record deployment
        record_service_deployment "$service_name" "success" "$service_url" ""
    else
        log_info "DRY RUN: Would deploy $service_name to $cloud_run_name"
        record_service_deployment "$service_name" "dry-run" "" ""
    fi
    
    return 0
}

# Health check service
verify_service_health() {
    local service_name=$1
    
    if [[ "$SKIP_HEALTH_CHECK" == "true" || "$DRY_RUN" == "true" ]]; then
        log_info "Skipping health check for $service_name"
        return 0
    fi
    
    local service_url="${SERVICE_URLS[$service_name]}"
    if [[ -z "$service_url" ]]; then
        log_warning "No URL available for health check: $service_name"
        return 1
    fi
    
    # Get health check configuration
    local health_config
    health_config=$(get_service_health_check "$service_name")
    local health_path
    health_path=$(echo "$health_config" | yq eval '.path // "/health"' -)
    local health_timeout
    health_timeout=$(echo "$health_config" | yq eval '.timeout // 30' -)
    local health_retries
    health_retries=$(echo "$health_config" | yq eval '.retries // 3' -)
    
    log_info "Verifying health of $service_name..."
    
    local attempt=1
    while [[ $attempt -le $health_retries ]]; do
        log_debug "Health check attempt $attempt/$health_retries for $service_name"
        
        if check_url "${service_url}${health_path}" "$health_timeout" || \
           check_url "${service_url}/" "$health_timeout"; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        if [[ $attempt -lt $health_retries ]]; then
            log_debug "Health check failed, waiting 30 seconds..."
            sleep 30
        fi
        ((attempt++))
    done
    
    log_warning "$service_name health check failed after $health_retries attempts"
    return 1
}

# Deploy services in order
deploy_services() {
    local services=("$@")
    
    if [[ ${#services[@]} -eq 0 ]]; then
        log_info "No services to deploy"
        return 0
    fi
    
    log_info "Deploying ${#services[@]} services..."
    
    # Get deployment order
    local deployment_order
    deployment_order=$(get_deployment_order "${services[@]}")
    
    if [[ $? -ne 0 ]]; then
        log_error "Failed to determine deployment order"
        return 1
    fi
    
    local total_services
    total_services=$(echo "$deployment_order" | wc -l)
    local current_service=0
    
    while IFS= read -r service; do
        [[ -z "$service" ]] && continue
        
        ((current_service++))
        show_progress "$current_service" "$total_services" "Deploying $service"
        
        if deploy_service "$service"; then
            DEPLOYED_SERVICES+=("$service")
            
            # Verify health for critical services
            local tier
            tier=$(get_service_tier "$service")
            if [[ $tier -le 2 ]]; then
                verify_service_health "$service" || true
            fi
        else
            FAILED_SERVICES+=("$service")
            SERVICE_ERRORS["$service"]="Deployment failed"
            log_error "Failed to deploy $service"
            
            # Record failure
            record_service_deployment "$service" "failed" "" "Deployment failed"
            
            # Check if we should continue or abort
            if [[ "$tier" -le 2 ]]; then
                log_error "Critical service deployment failed. Aborting deployment."
                return 1
            fi
        fi
        
        # Brief pause between deployments
        if [[ $current_service -lt $total_services && "$DRY_RUN" != "true" ]]; then
            sleep 5
        fi
    done <<< "$deployment_order"
    
    return 0
}

# Show deployment summary
show_deployment_summary() {
    local deployment_duration=$(($(get_unix_timestamp) - DEPLOYMENT_START_TIME))
    
    echo ""
    echo -e "${WHITE}=== DEPLOYMENT SUMMARY ===${NC}"
    echo ""
    echo -e "Duration: ${CYAN}${deployment_duration}s${NC}"
    echo ""
    
    if [[ ${#DEPLOYED_SERVICES[@]} -gt 0 ]]; then
        echo -e "${GREEN}✅ Successfully deployed (${#DEPLOYED_SERVICES[@]}):${NC}"
        for service in "${DEPLOYED_SERVICES[@]}"; do
            local url="${SERVICE_URLS[$service]:-"URL not available"}"
            printf "  ${GREEN}%-25s${NC} %s\n" "$service" "$url"
        done
        echo ""
    fi
    
    if [[ ${#SKIPPED_SERVICES[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⏭️  Skipped (no changes) (${#SKIPPED_SERVICES[@]}):${NC}"
        for service in "${SKIPPED_SERVICES[@]}"; do
            echo -e "  ${YELLOW}- $service${NC}"
        done
        echo ""
    fi
    
    if [[ ${#FAILED_SERVICES[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Failed deployments (${#FAILED_SERVICES[@]}):${NC}"
        for service in "${FAILED_SERVICES[@]}"; do
            local error="${SERVICE_ERRORS[$service]:-"Unknown error"}"
            echo -e "  ${RED}- $service${NC}: $error"
        done
        echo ""
    fi
    
    # Calculate success rate
    local total_attempted=$((${#DEPLOYED_SERVICES[@]} + ${#FAILED_SERVICES[@]}))
    if [[ $total_attempted -gt 0 ]]; then
        local success_rate=$((${#DEPLOYED_SERVICES[@]} * 100 / total_attempted))
        echo -e "Success Rate: ${CYAN}${success_rate}%${NC}"
        echo ""
    fi
    
    # Show next steps
    if [[ ${#DEPLOYED_SERVICES[@]} -gt 0 && ${#FAILED_SERVICES[@]} -eq 0 ]]; then
        echo -e "${GREEN}🎉 All services deployed successfully!${NC}"
        echo ""
        if [[ "$DRY_RUN" != "true" ]]; then
            echo -e "${CYAN}🔗 Test your deployment:${NC}"
            if [[ -n "${SERVICE_URLS[agent-engine]:-}" ]]; then
                echo -e "  curl ${SERVICE_URLS[agent-engine]}/health"
            fi
            if [[ -n "${SERVICE_URLS[agent-studio]:-}" ]]; then
                echo -e "  open ${SERVICE_URLS[agent-studio]}"
            fi
        fi
    elif [[ ${#FAILED_SERVICES[@]} -gt 0 ]]; then
        echo -e "${RED}⚠️  Some services failed to deploy.${NC}"
        echo -e "Check logs: ${CYAN}${LOG_DIR}/deployment.log${NC}"
        echo -e "Consider rollback: ${CYAN}$0 rollback <service>${NC}"
    fi
}

# Execute deployment based on mode
execute_deployment() {
    case "$DEPLOY_MODE" in
        "auto")
            log_info "Auto-detecting changed services..."
            local changed_services
            changed_services=$(detect_changed_services "${DETECTION_METHOD:-auto}")
            
            if [[ -z "$changed_services" ]]; then
                log_success "No changes detected. All services are up to date."
                return 0
            fi
            
            local changed_array
            readarray -t changed_array <<< "$changed_services"
            
            log_info "Detected ${#changed_array[@]} changed services: ${changed_array[*]}"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "\n${YELLOW}DRY RUN - Would deploy:${NC}"
                printf "%s\n" "${changed_array[@]}"
                return 0
            fi
            
            deploy_services "${changed_array[@]}"
            ;;
            
        "all")
            log_info "Deploying all services..."
            local all_services
            all_services=($(get_all_configured_services))
            
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "\n${YELLOW}DRY RUN - Would deploy all ${#all_services[@]} services:${NC}"
                printf "%s\n" "${all_services[@]}"
                return 0
            fi
            
            deploy_services "${all_services[@]}"
            ;;
            
        "group")
            if [[ ${#SELECTED_SERVICES[@]} -eq 0 ]]; then
                log_error "No deployment group specified"
                return 1
            fi
            
            local group_name="${SELECTED_SERVICES[0]}"
            local group_services
            group_services=($(get_deployment_group_services "$group_name"))
            
            if [[ ${#group_services[@]} -eq 0 ]]; then
                log_error "No services found in group: $group_name"
                return 1
            fi
            
            log_info "Deploying group '$group_name' (${#group_services[@]} services)"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "\n${YELLOW}DRY RUN - Would deploy group '$group_name':${NC}"
                printf "%s\n" "${group_services[@]}"
                return 0
            fi
            
            deploy_services "${group_services[@]}"
            ;;
            
        "services")
            if [[ ${#SELECTED_SERVICES[@]} -eq 0 ]]; then
                log_error "No services specified"
                return 1
            fi
            
            log_info "Deploying specified services: ${SELECTED_SERVICES[*]}"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "\n${YELLOW}DRY RUN - Would deploy:${NC}"
                printf "%s\n" "${SELECTED_SERVICES[@]}"
                return 0
            fi
            
            deploy_services "${SELECTED_SERVICES[@]}"
            ;;
            
        "status")
            show_deployment_status "table"
            return 0
            ;;
            
        "validate")
            log_info "Validating deployment configuration..."
            validate_prerequisites
            load_service_config
            local all_services
            all_services=($(get_all_configured_services))
            validate_dependencies "${all_services[@]}"
            detect_circular_dependencies "${all_services[@]}"
            log_success "Deployment configuration is valid"
            return 0
            ;;
            
        "diff")
            log_info "Showing deployment diff..."
            local changed_services
            changed_services=$(detect_changed_services "${DETECTION_METHOD:-auto}")
            
            if [[ -z "$changed_services" ]]; then
                echo -e "${GREEN}No changes detected${NC}"
            else
                echo -e "${YELLOW}Services that would be deployed:${NC}"
                echo "$changed_services"
            fi
            return 0
            ;;
            
        "rollback")
            log_error "Rollback functionality not yet implemented"
            return 1
            ;;
            
        *)
            log_error "Unknown deployment mode: $DEPLOY_MODE"
            return 1
            ;;
    esac
}

# Main execution function
main() {
    show_banner
    
    # Parse arguments
    parse_arguments "$@"
    
    # Initialize deployment
    init_deployment
    
    # Show configuration
    show_deployment_config
    
    # Confirm deployment unless skipped
    if [[ "$SKIP_CONFIRMATIONS" != "true" && "$DEPLOY_MODE" =~ ^(auto|all|group|services)$ ]]; then
        if [[ "$DRY_RUN" != "true" ]]; then
            read -p "Continue with deployment? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Deployment cancelled by user"
                exit 0
            fi
        fi
    fi
    
    # Validate prerequisites for deployment modes
    if [[ "$DEPLOY_MODE" =~ ^(auto|all|group|services)$ ]]; then
        validate_prerequisites
        validate_project_access "$PROJECT_ID"
        
        # Create deployment backup
        if [[ "$DRY_RUN" != "true" ]]; then
            create_deployment_backup "pre-deployment-$(date +%Y%m%d-%H%M%S)"
        fi
        
        # Update deployment metadata
        update_deployment_metadata "$PROJECT_ID" "$REGION" "$ENVIRONMENT"
    fi
    
    # Execute deployment
    if execute_deployment; then
        if [[ "$DEPLOY_MODE" =~ ^(auto|all|group|services)$ ]]; then
            show_deployment_summary
        fi
        
        # Clean old backups
        clean_old_backups 10
        
        log_success "Deployment completed successfully"
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Run main function
main "$@"