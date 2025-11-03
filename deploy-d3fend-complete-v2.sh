#!/bin/bash
#
# D3FEND-Node Complete Deployment Script v2
# Fixed version with proper sudo handling and error reporting
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[*]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
D3FEND_NODE_DIR="../react_d3fend-node"
DEPLOYMENT_LOG="${PROJECT_ROOT}/deployment-v2-$(date +%Y%m%d_%H%M%S).log"

# Counters
DEPLOYMENTS_COMPLETED=0
DEPLOYMENTS_FAILED=0

# Initialize logging
{
    echo "D3FEND-Node Deployment Log v2"
    echo "Started: $(date)"
    echo "Project Root: ${PROJECT_ROOT}"
    echo ""
} > "${DEPLOYMENT_LOG}"

log_to_file() {
    echo "$1" >> "${DEPLOYMENT_LOG}"
}

# Function to deploy service with proper error handling
deploy_service_with_sudo() {
    local service_name=$1
    local deploy_script=$2
    local service_label=$3
    
    log_info "Deploying ${service_label}..."
    
    if [ ! -f "${deploy_script}" ]; then
        log_error "Deploy script not found: ${deploy_script}"
        log_to_file "FAILED: ${service_label} - script not found"
        ((DEPLOYMENTS_FAILED++))
        return 1
    fi
    
    chmod +x "${deploy_script}"
    
    # Execute with proper error handling
    if sudo bash "${deploy_script}" >> "${DEPLOYMENT_LOG}" 2>&1; then
        log_success "${service_label} deployed successfully"
        log_to_file "SUCCESS: ${service_label} deployed"
        ((DEPLOYMENTS_COMPLETED++))
        return 0
    else
        local exit_code=$?
        log_error "${service_label} deployment failed (exit code: $exit_code)"
        log_to_file "FAILED: ${service_label} deployment (exit code: $exit_code)"
        tail -20 "${DEPLOYMENT_LOG}" | grep -E "(ERROR|error|failed)" >> "${DEPLOYMENT_LOG}" || true
        ((DEPLOYMENTS_FAILED++))
        return 1
    fi
}

main() {
    log_section "D3FEND-Node Deployment Started (v2)"
    
    log_to_file "========== Deployment Start v2 =========="
    
    # Port validation (quick)
    log_section "Quick Port Check"
    log_info "Checking critical ports..."
    for port in 5500 7003 8001 8005 3003; do
        if sudo netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            log_warning "Port $port already in use"
        else
            log_success "Port $port available"
        fi
    done
    
    # Sequential deployments
    log_section "Sequential Service Deployment"
    
    cd "${D3FEND_NODE_DIR}"
    
    # Portal
    deploy_service_with_sudo "portal" "./services/portal/deploy.sh" "Portal Service" || true
    sleep 5
    
    # MISP
    deploy_service_with_sudo "misp" "./services/misp/deploy.sh" "MISP Threat Intelligence" || true
    sleep 10
    
    # Detection
    deploy_service_with_sudo "detection" "./services/detection/deploy.sh" "Detection Management" || true
    sleep 5
    
    # Network
    deploy_service_with_sudo "network" "./services/network/deploy.sh" "Network Analysis" || true
    sleep 10
    
    # Agents
    deploy_service_with_sudo "agents" "./services/agents/deploy.sh" "Agent Systems" || true
    sleep 5
    
    # SOAR
    deploy_service_with_sudo "soar" "./services/soar/deploy.sh" "SOAR System" || true
    sleep 5
    
    cd "${PROJECT_ROOT}"
    
    # Summary
    log_section "Deployment Summary"
    log_success "Deployments Completed: ${DEPLOYMENTS_COMPLETED}/6"
    if [ ${DEPLOYMENTS_FAILED} -gt 0 ]; then
        log_warning "Deployments Failed: ${DEPLOYMENTS_FAILED}/6"
    else
        log_success "All deployments completed successfully!"
    fi
    
    # Container status
    log_section "Container Status"
    log_info "Running containers:"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | head -15 || log_warning "Unable to list containers"
    
    log_info "Total containers: $(sudo docker ps -a --format '{{.Names}}' 2>/dev/null | wc -l || echo 'unknown')"
    
    log_to_file "========== Deployment Complete v2 =========="
    log_to_file "Completion Time: $(date)"
    
    log_success "Deployment log saved to: ${DEPLOYMENT_LOG}"
}

main "$@"
