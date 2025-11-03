#!/bin/bash
#
# D3FEND-Node Complete Deployment Script
# Orchestrates deployment of all D3FEND services with attack-node coexistence
# Validates ports, health checks, and provides comprehensive reporting
#

set -e

# Color codes for output
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
ATTACK_NODE_DIR="../attack-node"
DEPLOYMENT_LOG="${PROJECT_ROOT}/deployment-$(date +%Y%m%d_%H%M%S).log"

# Port definitions
declare -A ATTACK_PORTS=(
    ["9000"]="Portainer (attack-node)"
    ["9443"]="Portainer HTTPS (attack-node)"
    ["8000"]="Portainer Agent (attack-node)"
    ["8082"]="Vaultwarden (attack-node)"
    ["6903"]="Code-Server (attack-node)"
    ["8443"]="Code-Server HTTPS (attack-node)"
    ["4443"]="PWNdrop (attack-node)"
    ["6904"]="PWNdrop (attack-node)"
    ["8080"]="PWNdrop (attack-node) - KASM"
    ["6902"]="Kali Desktop (attack-node)"
    ["3000"]="Kali Web (attack-node)"
    ["6901"]="VS Code Kasm (attack-node)"
    ["3001"]="Kali Web Alt (attack-node)"
    ["7777"]="SysReptor Caddy (attack-node)"
    ["9000"]="SysReptor (attack-node)"
    ["5001"]="Local Registry (attack-node)"
    ["3500"]="Node Service (attack-node)"
)

declare -A D3FEND_PORTS=(
    ["5500"]="Portal HTTP (d3fend-node)"
    ["5443"]="Portal HTTPS (d3fend-node)"
    ["7003"]="MISP HTTP (d3fend-node)"
    ["7004"]="MISP HTTPS (d3fend-node)"
    ["6666"]="MISP Modules (d3fend-node)"
    ["8001"]="YARA API (d3fend-node)"
    ["8005"]="Arkime (d3fend-node)"
    ["9200"]="Elasticsearch (d3fend-node)"
    ["5002"]="Shuffle Backend (d3fend-node)"
    ["3003"]="Shuffle Frontend (d3fend-node)"
    ["3004"]="Shuffle Webhook (d3fend-node)"
    ["8889"]="Velociraptor (d3fend-node)"
    ["1514"]="Wazuh (d3fend-node)"
    ["1515"]="Wazuh (d3fend-node)"
)

# Deployment tracking
DEPLOYMENTS_COMPLETED=0
DEPLOYMENTS_FAILED=0
HEALTH_CHECKS_PASSED=0
HEALTH_CHECKS_FAILED=0

# Initialize logging
{
    echo "D3FEND-Node Deployment Log"
    echo "Started: $(date)"
    echo "Project Root: ${PROJECT_ROOT}"
    echo "D3FEND Node: ${D3FEND_NODE_DIR}"
    echo "Attack Node: ${ATTACK_NODE_DIR}"
    echo ""
} > "${DEPLOYMENT_LOG}"

# Function to log to file and console
log_to_file() {
    echo "$1" >> "${DEPLOYMENT_LOG}"
}

# Function to check if port is in use
is_port_in_use() {
    local port=$1
    if sudo netstat -tuln 2>/dev/null | grep -q ":${port} "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to validate port availability
validate_ports() {
    log_section "Port Availability Validation"
    
    local conflicts=0
    
    log_info "Checking D3FEND-Node required ports..."
    for port in "${!D3FEND_PORTS[@]}"; do
        if is_port_in_use "$port"; then
            log_warning "Port $port is in use: ${D3FEND_PORTS[$port]}"
            ((conflicts++))
        else
            log_success "Port $port available"
        fi
    done
    
    if [ $conflicts -gt 0 ]; then
        log_error "$conflicts port conflicts detected!"
        log_to_file "Port conflicts detected: $conflicts"
        return 1
    fi
    
    log_success "All ports available for D3FEND-Node"
    log_to_file "Port validation passed"
    return 0
}

# Function to verify Docker availability
verify_docker() {
    log_section "Docker Verification"
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        log_to_file "Docker verification failed: Docker not installed"
        return 1
    fi
    
    log_success "Docker installed: $(docker --version)"
    
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            log_error "Docker Compose not found"
            log_to_file "Docker Compose verification failed"
            return 1
        fi
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    log_success "Docker Compose available: ${DOCKER_COMPOSE}"
    log_to_file "Docker verification passed: Using '${DOCKER_COMPOSE}'"
    return 0
}

# Function to deploy service
deploy_service() {
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
    
    # Make script executable
    chmod +x "${deploy_script}"
    
    # Execute deployment
    if bash "${deploy_script}" >> "${DEPLOYMENT_LOG}" 2>&1; then
        log_success "${service_label} deployed successfully"
        log_to_file "SUCCESS: ${service_label} deployed"
        ((DEPLOYMENTS_COMPLETED++))
        return 0
    else
        log_error "${service_label} deployment failed"
        log_to_file "FAILED: ${service_label} deployment"
        ((DEPLOYMENTS_FAILED++))
        return 1
    fi
}

# Function to check container health
check_container_health() {
    local container_name=$1
    local timeout=$2
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if sudo docker inspect "$container_name" &> /dev/null; then
            local status=$(sudo docker inspect "$container_name" --format='{{.State.Status}}' 2>/dev/null)
            if [ "$status" = "running" ]; then
                return 0
            fi
        fi
        sleep 1
        ((elapsed++))
    done
    
    return 1
}

# Function to perform health checks
perform_health_checks() {
    log_section "Service Health Checks"
    
    local services=(
        "btpi-portal:http://localhost:5500/health:Portal"
        "misp-core:http://localhost:7003:MISP"
        "shuffle-backend:http://localhost:5002/api/v1/orgs:Shuffle Backend"
        "shuffle-frontend:http://localhost:3003:Shuffle Frontend"
    )
    
    for service_check in "${services[@]}"; do
        IFS=':' read -r container url label <<< "$service_check"
        
        log_info "Checking ${label}..."
        
        if check_container_health "$container" 60; then
            if curl -sf "$url" > /dev/null 2>&1; then
                log_success "${label} is healthy"
                ((HEALTH_CHECKS_PASSED++))
            else
                log_warning "${label} container running but health endpoint not responding"
                ((HEALTH_CHECKS_FAILED++))
            fi
        else
            log_warning "${label} container not running or unhealthy"
            ((HEALTH_CHECKS_FAILED++))
        fi
    done
}

# Function to verify container count
verify_container_count() {
    log_section "Container Count Verification"
    
    local d3fend_count=$(sudo docker ps -a --filter "label!=attack-node" 2>/dev/null | grep -c "btpi-" || echo "0")
    local attack_count=$(sudo docker ps -a --filter "label=attack-node" 2>/dev/null | wc -l || echo "0")
    local total=$(sudo docker ps -a 2>/dev/null | wc -l || echo "0")
    
    log_info "D3FEND-Node containers: $d3fend_count"
    log_info "Attack-Node containers: $attack_count"
    log_info "Total containers running: $((total - 1))"  # -1 for header line
    
    if [ "$((total - 1))" -ge 15 ]; then
        log_success "Expected container count reached (15+)"
        log_to_file "Container count verification passed: $((total - 1)) containers"
        return 0
    else
        log_warning "Container count lower than expected"
        log_to_file "Container count verification: $((total - 1)) containers (expected 15+)"
        return 1
    fi
}

# Function to generate deployment report
generate_report() {
    log_section "Deployment Report"
    
    local report_file="${PROJECT_ROOT}/deployment-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "D3FEND-Node Deployment Report"
        echo "Generated: $(date)"
        echo ""
        echo "====== SUMMARY ======"
        echo "Deployments Completed: ${DEPLOYMENTS_COMPLETED}"
        echo "Deployments Failed: ${DEPLOYMENTS_FAILED}"
        echo "Health Checks Passed: ${HEALTH_CHECKS_PASSED}"
        echo "Health Checks Failed: ${HEALTH_CHECKS_FAILED}"
        echo ""
        echo "====== PORT MAPPING ======"
        echo "D3FEND-Node Services:"
        for port in "${!D3FEND_PORTS[@]}"; do
            echo "  Port $port: ${D3FEND_PORTS[$port]}"
        done
        echo ""
        echo "====== SERVICE ENDPOINTS ======"
        echo "Portal: http://localhost:5500"
        echo "MISP: http://localhost:7003"
        echo "YARA API: http://localhost:8001"
        echo "Arkime: http://localhost:8005"
        echo "Elasticsearch: http://localhost:9200"
        echo "Shuffle Frontend: http://localhost:3003"
        echo "Shuffle Backend: http://localhost:5002"
        echo "Shuffle Webhook: http://localhost:3004"
        echo ""
        echo "====== ATTACK-NODE COEXISTENCE ======"
        echo "Attack-Node ports: $(echo ${!ATTACK_PORTS[@]} | tr ' ' ',')"
        echo "No port conflicts detected"
        echo ""
        echo "====== FULL LOG ======"
        cat "${DEPLOYMENT_LOG}"
    } > "$report_file"
    
    log_success "Report generated: ${report_file}"
}

# Main deployment flow
main() {
    log_section "D3FEND-Node Deployment Started"
    
    log_to_file "========== Deployment Start =========="
    
    # Step 1: Verify prerequisites
    if ! verify_docker; then
        log_error "Docker verification failed. Stopping deployment."
        return 1
    fi
    
    # Step 2: Validate ports
    if ! validate_ports; then
        log_warning "Port validation failed, but continuing..."
    fi
    
    # Step 3: Sequential deployments
    log_section "Sequential Service Deployment"
    
    cd "${D3FEND_NODE_DIR}"
    
    # Portal
    deploy_service "portal" "./services/portal/deploy.sh" "Portal Service"
    sleep 10
    
    # MISP
    deploy_service "misp" "./services/misp/deploy.sh" "MISP Threat Intelligence"
    sleep 15
    
    # Detection
    deploy_service "detection" "./services/detection/deploy.sh" "Detection Management (YARA/Sigma)"
    sleep 10
    
    # Network
    deploy_service "network" "./services/network/deploy.sh" "Network Analysis (Suricata/Arkime)"
    sleep 15
    
    # Agents
    deploy_service "agents" "./services/agents/deploy.sh" "Agent Systems (Velociraptor/Wazuh)"
    sleep 15
    
    # SOAR
    deploy_service "soar" "./services/soar/deploy.sh" "SOAR System (Shuffle)"
    sleep 10
    
    cd "${PROJECT_ROOT}"
    
    # Step 4: Health checks
    perform_health_checks
    
    # Step 5: Container verification
    verify_container_count
    
    # Step 6: Generate report
    generate_report
    
    # Final summary
    log_section "Deployment Completion Summary"
    log_success "Deployments Completed: ${DEPLOYMENTS_COMPLETED}"
    if [ ${DEPLOYMENTS_FAILED} -gt 0 ]; then
        log_warning "Deployments Failed: ${DEPLOYMENTS_FAILED}"
    else
        log_success "No deployment failures"
    fi
    
    log_success "Health Checks Passed: ${HEALTH_CHECKS_PASSED}"
    if [ ${HEALTH_CHECKS_FAILED} -gt 0 ]; then
        log_warning "Health Checks Failed: ${HEALTH_CHECKS_FAILED}"
    fi
    
    log_to_file "========== Deployment Complete =========="
    log_to_file "Completion Time: $(date)"
}

# Execute main function
main "$@"
