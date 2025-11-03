#!/bin/bash
#
# BTPI-REACT Agent Deployment System
# Centralized deployment and management for Velociraptor and Wazuh agents
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
VELO_PORT=${VELO_PORT:-8889}
WAZUH_PORT=${WAZUH_PORT:-1514}
SERVER_IP=${SERVER_IP:-localhost}

log_info "============================================"
log_info "BTPI-REACT Agent Deployment System"
log_info "============================================"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi

# Check if deploying specific service or all
DEPLOY_TYPE=${1:-all}

case $DEPLOY_TYPE in
    velociraptor|velo)
        log_info "Deploying Velociraptor server..."
        cd "${SCRIPT_DIR}/velociraptor/server"
        docker-compose -f docker-compose.yml up -d
        log_success "Velociraptor deployed"
        log_info "Access at: https://${SERVER_IP}:${VELO_PORT}"
        ;;
    wazuh)
        log_info "Deploying Wazuh manager..."
        cd "${SCRIPT_DIR}/wazuh/manager"
        docker-compose -f docker-compose.yml up -d
        log_success "Wazuh deployed"
        log_info "Access at: https://${SERVER_IP}:1515"
        ;;
    all)
        log_info "Deploying all agent systems..."
        
        # Velociraptor
        cd "${SCRIPT_DIR}/velociraptor/server"
        docker-compose -f docker-compose.yml up -d
        log_success "Velociraptor deployed"
        
        # Wazuh
        cd "${SCRIPT_DIR}/wazuh/manager"
        docker-compose -f docker-compose.yml up -d
        log_success "Wazuh deployed"
        ;;
    *)
        log_error "Unknown deployment type: $DEPLOY_TYPE"
        log_info "Usage: $0 [all|velociraptor|wazuh]"
        exit 1
        ;;
esac

log_info "============================================"
log_success "Agent systems deployed successfully!"
log_info "============================================"
log_info ""
log_info "Velociraptor:"
log_info "  URL: https://${SERVER_IP}:${VELO_PORT}"
log_info "  Admin UI: https://${SERVER_IP}:${VELO_PORT}/app"
log_info ""
log_info "Wazuh:"
log_info "  URL: https://${SERVER_IP}:1515"
log_info "  Web UI: https://${SERVER_IP}"
log_info ""
log_info "Next steps:"
log_info "  1. Access the portal at http://${SERVER_IP}:5500"
log_info "  2. Navigate to the Agents tab"
log_info "  3. Generate and deploy agent installers"
log_info "============================================"

exit 0
