#!/bin/bash
#
# BTPI-REACT Network Analysis System Deployment
# Suricata IDS and Arkime PCAP analysis infrastructure
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
log_info "BTPI-REACT Network Analysis System"
log_info "Suricata IDS + Arkime PCAP Analysis"
log_info "============================================"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi

# Check if deploying specific service or all
DEPLOY_TYPE=${1:-all}

case $DEPLOY_TYPE in
    suricata)
        log_info "Deploying Suricata IDS..."
        cd "${SCRIPT_DIR}/suricata"
        docker-compose -f docker-compose.yml up -d
        log_success "Suricata IDS deployed"
        log_info "Suricata listening on: eth0 (configured interface)"
        ;;
    arkime)
        log_info "Deploying Arkime PCAP analysis..."
        cd "${SCRIPT_DIR}/arkime"
        docker-compose -f docker-compose.yml up -d
        log_success "Arkime deployed"
        log_info "Access Arkime at: http://localhost:8005"
        ;;
    all)
        log_info "Deploying all network analysis services..."
        
        # Suricata
        log_info "Starting Suricata IDS..."
        cd "${SCRIPT_DIR}/suricata"
        docker-compose -f docker-compose.yml up -d
        log_success "Suricata deployed"
        
        # Arkime
        log_info "Starting Arkime..."
        cd "${SCRIPT_DIR}/arkime"
        docker-compose -f docker-compose.yml up -d
        log_success "Arkime deployed"
        ;;
    *)
        log_error "Unknown deployment type: $DEPLOY_TYPE"
        log_info "Usage: $0 [all|suricata|arkime]"
        exit 1
        ;;
esac

log_info "============================================"
log_success "Network analysis services deployed!"
log_info "============================================"
log_info ""
log_info "Service URLs:"
log_info "  Suricata: IDS monitoring on configured interface"
log_info "  Arkime: http://localhost:8005"
log_info "  Portal Network Tab: http://localhost:5500/app#network"
log_info ""
log_info "Next steps:"
log_info "  1. Access portal network management tab"
log_info "  2. Configure network interfaces"
log_info "  3. Import detection rules from Phase 3"
log_info "  4. Start PCAP capture"
log_info "============================================"

exit 0
