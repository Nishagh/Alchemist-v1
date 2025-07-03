#!/bin/bash

# Alchemist Deployment Dashboard
# This script provides real-time monitoring and status dashboard for all services
# Author: Alchemist Team
# Version: 1.0.0

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Unicode symbols
CHECK="\u2713"
CROSS="\u2717"
WARNING="\u26A0"
GEAR="\u2699"
ROCKET="\u1F680"
GRAPH="\u1F4CA"

# Default configuration
DEFAULT_PROJECT_ID="alchemist-e69bb"
DEFAULT_REGION="us-central1"
REFRESH_INTERVAL=30

# Service definitions
declare -A SERVICES=(
    ["alchemist-agent-engine"]="Agent Engine"
    ["alchemist-knowledge-vault"]="Knowledge Vault"
    ["alchemist-agent-bridge"]="Agent Bridge"
    ["alchemist-agent-studio"]="Agent Studio"
    ["alchemist-agent-launcher"]="Agent Launcher"
    ["alchemist-tool-forge"]="Tool Forge"
    ["alchemist-sandbox-console"]="Sandbox Console"
    ["alchemist-prompt-engine"]="Prompt Engine"
    ["alchemist-mcp-config-generator"]="MCP Config Generator"
    ["alchemist-banking-api-service"]="Banking API Service"
    ["alchemist-admin-dashboard"]="Admin Dashboard"
)

declare -A SERVICE_TIERS=(
    ["alchemist-agent-engine"]="Core"
    ["alchemist-knowledge-vault"]="Core"
    ["alchemist-agent-bridge"]="Integration"
    ["alchemist-tool-forge"]="Integration"
    ["alchemist-mcp-config-generator"]="Integration"
    ["alchemist-agent-launcher"]="Application"
    ["alchemist-prompt-engine"]="Application"
    ["alchemist-sandbox-console"]="Application"
    ["alchemist-banking-api-service"]="External"
    ["alchemist-agent-studio"]="External"
    ["alchemist-admin-dashboard"]="External"
)

# Global variables
PROJECT_ID=""
REGION=""
WATCH_MODE=""
OUTPUT_FORMAT="table"
SHOW_LOGS=""
SHOW_METRICS=""

# Service status data
declare -A SERVICE_STATUS
declare -A SERVICE_URLS
declare -A SERVICE_HEALTH
declare -A SERVICE_REVISIONS
declare -A SERVICE_TRAFFIC
declare -A SERVICE_INSTANCES

# Clear screen function
clear_screen() {
    if [[ "$WATCH_MODE" == "true" ]]; then
        clear
    fi
}

# Show banner
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      📊 ALCHEMIST DEPLOYMENT DASHBOARD 📊                   ║
║                                                              ║
║         Real-time Service Monitoring & Status               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Show help
show_help() {
    cat << EOF
${WHITE}Alchemist Deployment Dashboard${NC}

${YELLOW}USAGE:${NC}
    $0 [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -p, --project-id ID   Google Cloud Project ID
    -r, --region REGION   Deployment region (default: us-central1)
    -w, --watch           Watch mode - refresh every ${REFRESH_INTERVAL}s
    -i, --interval SEC    Refresh interval for watch mode (default: ${REFRESH_INTERVAL})
    -f, --format FORMAT   Output format (table|json|yaml, default: table)
    -l, --logs            Show recent logs for services
    -m, --metrics         Show metrics and resource usage
    -h, --help            Show this help message

${YELLOW}DISPLAY MODES:${NC}
    Default               Show service status table
    --watch              Continuous monitoring with auto-refresh
    --logs               Include recent log entries
    --metrics            Include resource usage metrics

${YELLOW}OUTPUT FORMATS:${NC}
    table                Human-readable table (default)
    json                 JSON format for automation
    yaml                 YAML format for configuration

${YELLOW}EXAMPLES:${NC}
    $0                            # Show current status
    $0 --watch                    # Continuous monitoring
    $0 -p my-project --logs       # Status with logs
    $0 --format json              # JSON output
    $0 --watch --interval 10      # Watch with 10s refresh

${YELLOW}KEYBOARD SHORTCUTS (Watch Mode):${NC}
    q, Ctrl+C            Quit
    r                    Refresh now
    l                    Toggle logs
    m                    Toggle metrics
    h                    Help

EOF
}

# Get service status
get_service_status() {
    local service_name=$1
    
    if gcloud run services describe "$service_name" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --quiet &> /dev/null; then
        
        # Service exists, get details
        local url
        url=$(gcloud run services describe "$service_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)" 2>/dev/null)
        
        local ready_condition
        ready_condition=$(gcloud run services describe "$service_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.conditions[0].status)" 2>/dev/null)
        
        local revision
        revision=$(gcloud run services describe "$service_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.latestReadyRevisionName)" 2>/dev/null)
        
        local traffic
        traffic=$(gcloud run services describe "$service_name" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.traffic[0].percent)" 2>/dev/null)
        
        SERVICE_URLS["$service_name"]="$url"
        SERVICE_REVISIONS["$service_name"]="$revision"
        SERVICE_TRAFFIC["$service_name"]="${traffic:-100}%"
        
        if [[ "$ready_condition" == "True" ]]; then
            SERVICE_STATUS["$service_name"]="Running"
        else
            SERVICE_STATUS["$service_name"]="Deploying"
        fi
    else
        SERVICE_STATUS["$service_name"]="Not Deployed"
        SERVICE_URLS["$service_name"]=""
        SERVICE_REVISIONS["$service_name"]=""
        SERVICE_TRAFFIC["$service_name"]=""
    fi
}

# Check service health
check_service_health() {
    local service_name=$1
    local service_url="${SERVICE_URLS[$service_name]}"
    
    if [[ -z "$service_url" ]]; then
        SERVICE_HEALTH["$service_name"]="Unknown"
        return
    fi
    
    # Quick health check with timeout
    if curl -f -s -m 5 "${service_url}/health" > /dev/null 2>&1; then
        SERVICE_HEALTH["$service_name"]="Healthy"
    elif curl -f -s -m 5 "$service_url" > /dev/null 2>&1; then
        SERVICE_HEALTH["$service_name"]="Responding"
    else
        SERVICE_HEALTH["$service_name"]="Unhealthy"
    fi
}

# Get service metrics
get_service_metrics() {
    local service_name=$1
    
    # Get current instances count
    local instances
    instances=$(gcloud run services describe "$service_name" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.observedGeneration)" 2>/dev/null || echo "0")
    
    SERVICE_INSTANCES["$service_name"]="$instances"
}

# Collect all service data
collect_service_data() {
    echo -e "${BLUE}Collecting service data...${NC}" >&2
    
    for service_name in "${!SERVICES[@]}"; do
        get_service_status "$service_name"
        
        if [[ "${SERVICE_STATUS[$service_name]}" == "Running" ]]; then
            check_service_health "$service_name" &
            get_service_metrics "$service_name" &
        else
            SERVICE_HEALTH["$service_name"]="N/A"
            SERVICE_INSTANCES["$service_name"]="0"
        fi
    done
    
    # Wait for health checks to complete
    wait
}

# Format status indicator
format_status() {
    local status=$1
    case $status in
        "Running")
            echo -e "${GREEN}●${NC} Running"
            ;;
        "Deploying")
            echo -e "${YELLOW}●${NC} Deploying"
            ;;
        "Not Deployed")
            echo -e "${GRAY}●${NC} Not Deployed"
            ;;
        *)
            echo -e "${RED}●${NC} Unknown"
            ;;
    esac
}

# Format health indicator
format_health() {
    local health=$1
    case $health in
        "Healthy")
            echo -e "${GREEN}${CHECK}${NC} Healthy"
            ;;
        "Responding")
            echo -e "${YELLOW}${WARNING}${NC} Responding"
            ;;
        "Unhealthy")
            echo -e "${RED}${CROSS}${NC} Unhealthy"
            ;;
        *)
            echo -e "${GRAY}-${NC} N/A"
            ;;
    esac
}

# Display table format
display_table() {
    echo -e "${WHITE}=== ALCHEMIST DEPLOYMENT STATUS ===${NC}"
    echo -e "${GRAY}Project: $PROJECT_ID | Region: $REGION | $(date)${NC}"
    echo ""
    
    # Header
    printf "%-35s %-12s %-15s %-12s %-50s\n" "SERVICE" "TIER" "STATUS" "HEALTH" "URL"
    printf "%-35s %-12s %-15s %-12s %-50s\n" "$(printf '%.0s-' {1..35})" "$(printf '%.0s-' {1..12})" "$(printf '%.0s-' {1..15})" "$(printf '%.0s-' {1..12})" "$(printf '%.0s-' {1..50})"
    
    # Sort services by tier and name
    local sorted_services=()
    
    # Core services first
    for service_name in "${!SERVICES[@]}"; do
        if [[ "${SERVICE_TIERS[$service_name]}" == "Core" ]]; then
            sorted_services+=("$service_name")
        fi
    done
    
    # Integration services
    for service_name in "${!SERVICES[@]}"; do
        if [[ "${SERVICE_TIERS[$service_name]}" == "Integration" ]]; then
            sorted_services+=("$service_name")
        fi
    done
    
    # Application services
    for service_name in "${!SERVICES[@]}"; do
        if [[ "${SERVICE_TIERS[$service_name]}" == "Application" ]]; then
            sorted_services+=("$service_name")
        fi
    done
    
    # External services
    for service_name in "${!SERVICES[@]}"; do
        if [[ "${SERVICE_TIERS[$service_name]}" == "External" ]]; then
            sorted_services+=("$service_name")
        fi
    done
    
    # Display services
    for service_name in "${sorted_services[@]}"; do
        local display_name="${SERVICES[$service_name]}"
        local tier="${SERVICE_TIERS[$service_name]}"
        local status=$(format_status "${SERVICE_STATUS[$service_name]}")
        local health=$(format_health "${SERVICE_HEALTH[$service_name]}")
        local url="${SERVICE_URLS[$service_name]:-"N/A"}"
        
        printf "%-35s %-12s %-25s %-20s %-50s\n" \
            "$display_name" \
            "$tier" \
            "$status" \
            "$health" \
            "${url:0:50}"
    done
    
    echo ""
    
    # Summary
    local total_services=${#SERVICES[@]}
    local running_count=0
    local healthy_count=0
    
    for service_name in "${!SERVICES[@]}"; do
        if [[ "${SERVICE_STATUS[$service_name]}" == "Running" ]]; then
            ((running_count++))
        fi
        if [[ "${SERVICE_HEALTH[$service_name]}" == "Healthy" ]]; then
            ((healthy_count++))
        fi
    done
    
    echo -e "${WHITE}SUMMARY:${NC}"
    echo -e "  Total Services: $total_services"
    echo -e "  Running: ${GREEN}$running_count${NC}"
    echo -e "  Healthy: ${GREEN}$healthy_count${NC}"
    echo -e "  Not Deployed: ${GRAY}$((total_services - running_count))${NC}"
    
    if [[ "$SHOW_LOGS" == "true" ]]; then
        show_recent_logs
    fi
    
    if [[ "$SHOW_METRICS" == "true" ]]; then
        show_metrics_summary
    fi
}

# Display JSON format
display_json() {
    echo "{"
    echo "  \"timestamp\": \"$(date -Iseconds)\","
    echo "  \"project_id\": \"$PROJECT_ID\","
    echo "  \"region\": \"$REGION\","
    echo "  \"services\": {"
    
    local first=true
    for service_name in "${!SERVICES[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi
        
        echo -n "    \"$service_name\": {"
        echo -n "\"name\": \"${SERVICES[$service_name]}\", "
        echo -n "\"tier\": \"${SERVICE_TIERS[$service_name]}\", "
        echo -n "\"status\": \"${SERVICE_STATUS[$service_name]}\", "
        echo -n "\"health\": \"${SERVICE_HEALTH[$service_name]}\", "
        echo -n "\"url\": \"${SERVICE_URLS[$service_name]}\", "
        echo -n "\"revision\": \"${SERVICE_REVISIONS[$service_name]}\", "
        echo -n "\"traffic\": \"${SERVICE_TRAFFIC[$service_name]}\""
        echo -n "}"
    done
    
    echo ""
    echo "  }"
    echo "}"
}

# Display YAML format
display_yaml() {
    echo "timestamp: $(date -Iseconds)"
    echo "project_id: $PROJECT_ID"
    echo "region: $REGION"
    echo "services:"
    
    for service_name in "${!SERVICES[@]}"; do
        echo "  $service_name:"
        echo "    name: \"${SERVICES[$service_name]}\""
        echo "    tier: \"${SERVICE_TIERS[$service_name]}\""
        echo "    status: \"${SERVICE_STATUS[$service_name]}\""
        echo "    health: \"${SERVICE_HEALTH[$service_name]}\""
        echo "    url: \"${SERVICE_URLS[$service_name]}\""
        echo "    revision: \"${SERVICE_REVISIONS[$service_name]}\""
        echo "    traffic: \"${SERVICE_TRAFFIC[$service_name]}\""
    done
}

# Show recent logs
show_recent_logs() {
    echo ""
    echo -e "${WHITE}=== RECENT LOGS ===${NC}"
    
    for service_name in "${!SERVICES[@]}"; do
        if [[ "${SERVICE_STATUS[$service_name]}" == "Running" ]]; then
            echo -e "${BLUE}${SERVICES[$service_name]}:${NC}"
            gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$service_name" \
                --limit=3 \
                --format="value(timestamp,severity,textPayload)" \
                --project="$PROJECT_ID" 2>/dev/null | head -3 || echo "  No recent logs"
            echo ""
        fi
    done
}

# Show metrics summary
show_metrics_summary() {
    echo ""
    echo -e "${WHITE}=== METRICS SUMMARY ===${NC}"
    
    echo -e "${BLUE}Resource Usage:${NC}"
    for service_name in "${!SERVICES[@]}"; do
        if [[ "${SERVICE_STATUS[$service_name]}" == "Running" ]]; then
            echo -e "  ${SERVICES[$service_name]}: ${SERVICE_INSTANCES[$service_name]} instances"
        fi
    done
}

# Watch mode
run_watch_mode() {
    echo -e "${CYAN}Starting watch mode (refresh every ${REFRESH_INTERVAL}s)${NC}"
    echo -e "${GRAY}Press 'q' to quit, 'r' to refresh, 'l' to toggle logs, 'm' to toggle metrics${NC}"
    echo ""
    
    while true; do
        clear_screen
        show_banner
        collect_service_data
        
        case $OUTPUT_FORMAT in
            "json")
                display_json
                ;;
            "yaml")
                display_yaml
                ;;
            *)
                display_table
                ;;
        esac
        
        # Wait for refresh interval or user input
        if read -t $REFRESH_INTERVAL -n 1 key; then
            case $key in
                'q'|'Q')
                    echo ""
                    echo "Exiting dashboard..."
                    exit 0
                    ;;
                'r'|'R')
                    continue
                    ;;
                'l'|'L')
                    if [[ "$SHOW_LOGS" == "true" ]]; then
                        SHOW_LOGS=""
                    else
                        SHOW_LOGS="true"
                    fi
                    ;;
                'm'|'M')
                    if [[ "$SHOW_METRICS" == "true" ]]; then
                        SHOW_METRICS=""
                    else
                        SHOW_METRICS="true"
                    fi
                    ;;
                'h'|'H')
                    show_help
                    read -p "Press Enter to continue..."
                    ;;
            esac
        fi
    done
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
            -w|--watch)
                WATCH_MODE="true"
                shift
                ;;
            -i|--interval)
                REFRESH_INTERVAL="$2"
                shift 2
                ;;
            -f|--format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            -l|--logs)
                SHOW_LOGS="true"
                shift
                ;;
            -m|--metrics)
                SHOW_METRICS="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    # Set defaults
    PROJECT_ID="${ALCHEMIST_PROJECT_ID:-${PROJECT_ID:-$DEFAULT_PROJECT_ID}}"
    REGION="${ALCHEMIST_REGION:-${REGION:-$DEFAULT_REGION}}"
    
    # Parse arguments
    parse_arguments "$@"
    
    # Get project ID from gcloud if not specified
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
    fi
    
    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}Error: Project ID not specified${NC}"
        echo "Use -p option or set ALCHEMIST_PROJECT_ID environment variable"
        exit 1
    fi
    
    # Validate gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}Error: Not authenticated with Google Cloud${NC}"
        echo "Run: gcloud auth login"
        exit 1
    fi
    
    # Show banner for non-watch mode
    if [[ "$WATCH_MODE" != "true" ]]; then
        show_banner
    fi
    
    # Main execution
    if [[ "$WATCH_MODE" == "true" ]]; then
        # Trap for clean exit
        trap 'echo ""; echo "Dashboard stopped."; exit 0' INT TERM
        run_watch_mode
    else
        collect_service_data
        
        case $OUTPUT_FORMAT in
            "json")
                display_json
                ;;
            "yaml")
                display_yaml
                ;;
            *)
                display_table
                ;;
        esac
    fi
}

# Run main function
main "$@"