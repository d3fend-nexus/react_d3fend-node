#!/bin/bash
#
# BTPI-REACT Detection Management System Deployment
# Centralized YARA and Sigma rule management, deployment, and automation
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

log_info "============================================"
log_info "BTPI-REACT Detection Management System"
log_info "============================================"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi

# Check if deploying specific service or all
DEPLOY_TYPE=${1:-all}

case $DEPLOY_TYPE in
    yara)
        log_info "Deploying YARA scanning service..."
        cd "${SCRIPT_DIR}/yara/scanner"
        docker-compose -f docker-compose.yml up -d
        log_success "YARA scanning service deployed"
        log_info "Access YARA API at: http://localhost:8001/api/yara"
        ;;
    sigma)
        log_info "Deploying Sigma rule service..."
        # Sigma runs as part of portal, no separate container needed
        log_success "Sigma service configured (runs with portal)"
        log_info "Sigma rules served from: /portal/services/sigma"
        ;;
    all)
        log_info "Deploying all detection services..."
        
        # YARA Scanner
        log_info "Starting YARA scanning service..."
        cd "${SCRIPT_DIR}/yara/scanner"
        docker-compose -f docker-compose.yml up -d
        log_success "YARA scanning service deployed"
        
        # Sigma rules are integrated with portal
        log_success "Sigma service configured"
        ;;
    *)
        log_error "Unknown deployment type: $DEPLOY_TYPE"
        log_info "Usage: $0 [all|yara|sigma]"
        exit 1
        ;;
esac

log_info "============================================"
log_success "Detection services deployed successfully!"
log_info "============================================"
log_info ""
log_info "Detection System URLs:"
log_info "  YARA API: http://localhost:8001/api/yara"
log_info "  Portal Detection Tab: http://localhost:5500/app#detection"
log_info ""
log_info "Next steps:"
log_info "  1. Access portal detection management tab"
log_info "  2. Import YARA/Sigma rule libraries"
log_info "  3. Configure MISP IOC integration"
log_info "  4. Deploy rules to agents"
log_info "============================================"

exit 0
