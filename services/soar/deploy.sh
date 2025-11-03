#!/bin/bash
#
# BTPI-REACT SOAR Deployment System
# Shuffle-based incident response automation and case management
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
log_info "BTPI-REACT SOAR System Deployment"
log_info "Shuffle Incident Response Automation"
log_info "============================================"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi

# Check if deploying specific service or all
DEPLOY_TYPE=${1:-all}

case $DEPLOY_TYPE in
    shuffle)
        log_info "Deploying Shuffle SOAR platform..."
        cd "${SCRIPT_DIR}/shuffle"
        docker-compose -f docker-compose.yml up -d
        log_success "Shuffle deployed"
        log_info "Access Shuffle at: http://localhost:3001"
        log_info "Webhook receiver at: http://localhost:3002"
        ;;
    all)
        log_info "Deploying SOAR services..."
        
        # Shuffle
        log_info "Starting Shuffle platform..."
        cd "${SCRIPT_DIR}/shuffle"
        docker-compose -f docker-compose.yml up -d
        log_success "Shuffle deployed"
        ;;
    *)
        log_error "Unknown deployment type: $DEPLOY_TYPE"
        log_info "Usage: $0 [all|shuffle]"
        exit 1
        ;;
esac

log_info "============================================"
log_success "SOAR services deployed successfully!"
log_info "============================================"
log_info ""
log_info "SOAR Platform URLs:"
log_info "  Shuffle UI: http://localhost:3001"
log_info "  Shuffle Webhooks: http://localhost:3002"
log_info "  Portal SOAR Tab: http://localhost:5500/app#soar"
log_info ""
log_info "Next steps:"
log_info "  1. Access Shuffle UI and configure organizations"
log_info "  2. Create app instances for integrations"
log_info "  3. Import pre-built playbooks"
log_info "  4. Configure webhooks for alert ingestion"
log_info "  5. Test incident response workflows"
log_info "============================================"

exit 0
