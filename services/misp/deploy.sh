#!/bin/bash
#
# BTPI-REACT MISP Threat Intelligence Deployment Script
# Deploys MISP and configures threat feeds
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
MISP_DIR="${SCRIPT_DIR}"

# Configuration
SERVER_IP=${SERVER_IP:-localhost}
MISP_ADMIN_EMAIL=${MISP_ADMIN_EMAIL:-admin@btpi-react.local}
MISP_ADMIN_PASSWORD=${MISP_ADMIN_PASSWORD:-$(openssl rand -base64 12)}
MISP_DB_PASSWORD=${MISP_DB_PASSWORD:-$(openssl rand -base64 12)}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-$(openssl rand -base64 12)}

log_info "============================================"
log_info "BTPI-REACT MISP Deployment"
log_info "============================================"

# Check if docker and docker-compose are available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_warning "docker-compose not found, checking for docker compose..."
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available"
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

log_info "Using: ${DOCKER_COMPOSE}"

# Create config directory
log_info "Setting up configuration..."
mkdir -p "${MISP_DIR}/config"

# Create feed settings JSON
cat > "${MISP_DIR}/config/feed-settings.json" << 'EOF'
{
  "feeds": [
    {
      "name": "CIRCL OSINT Feed",
      "url": "https://www.circl.lu/doc/misp/feed-osint",
      "enabled": true,
      "cache_file": "circl_osint.json"
    },
    {
      "name": "AlienVault OTX",
      "url": "https://otx.alienvault.com/api/v1/",
      "enabled": true,
      "cache_file": "otx.json"
    },
    {
      "name": "Abuse.ch URLhaus",
      "url": "https://urlhaus-api.abuse.ch/v1/",
      "enabled": true,
      "cache_file": "urlhaus.json"
    },
    {
      "name": "Botvrij.eu",
      "url": "https://www.botvrij.eu/api/",
      "enabled": true,
      "cache_file": "botvrij.json"
    }
  ],
  "sync_interval": 86400,
  "timeout": 300
}
EOF

log_success "Configuration created"

# Set environment variables for docker-compose
export SERVER_IP
export MISP_ADMIN_EMAIL
export MISP_ADMIN_PASSWORD
export MISP_DB_PASSWORD
export MYSQL_ROOT_PASSWORD

# Create required networks if they don't exist
log_info "Setting up Docker networks..."
docker network create btpi-core-network 2>/dev/null || true

# Deploy MISP stack
log_info "Deploying MISP stack..."
cd "${MISP_DIR}"

if $DOCKER_COMPOSE -f docker-compose.misp.yml up -d 2>&1 | tail -10; then
    log_success "MISP stack deployed"
else
    log_error "Failed to deploy MISP stack"
    exit 1
fi

# Wait for services to be ready
log_info "Waiting for MISP services to be ready..."
for i in {1..60}; do
    if docker exec misp-db mysqladmin ping -h localhost -u misp -p"${MISP_DB_PASSWORD}" &> /dev/null; then
        log_success "Database is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        log_warning "Database startup timeout"
    fi
    sleep 1
done

# Wait for MISP core to be ready
log_info "Waiting for MISP core to be ready..."
for i in {1..120}; do
    if curl -sf http://localhost:7003 > /dev/null 2>&1; then
        log_success "MISP core is ready"
        break
    fi
    if [ $i -eq 120 ]; then
        log_warning "MISP core startup timeout (may still be initializing)"
    fi
    sleep 1
done

# Save credentials to file
log_info "Saving credentials..."
cat > "${MISP_DIR}/.misp-credentials" << EOF
MISP_ADMIN_EMAIL=${MISP_ADMIN_EMAIL}
MISP_ADMIN_PASSWORD=${MISP_ADMIN_PASSWORD}
MISP_DB_PASSWORD=${MISP_DB_PASSWORD}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
SERVER_IP=${SERVER_IP}
EOF

chmod 600 "${MISP_DIR}/.misp-credentials"
log_success "Credentials saved to .misp-credentials"

# Display deployment information
log_info "============================================"
log_success "MISP deployed successfully!"
log_info "============================================"
log_info ""
log_info "Access Information:"
log_info "  URL: http://${SERVER_IP}:7003"
log_info "  Email: ${MISP_ADMIN_EMAIL}"
log_info "  Password: ${MISP_ADMIN_PASSWORD}"
log_info "  (Saved in .misp-credentials)"
log_info ""
log_info "Containers:"
log_info "  - misp-db (MySQL Database)"
log_info "  - misp-redis (Redis Cache)"
log_info "  - misp-core (MISP Application)"
log_info "  - misp-modules (Analysis Modules)"
log_info ""
log_info "Useful Commands:"
log_info "  View logs: $DOCKER_COMPOSE -f docker-compose.misp.yml logs -f"
log_info "  Stop: $DOCKER_COMPOSE -f docker-compose.misp.yml down"
log_info "  Restart: $DOCKER_COMPOSE -f docker-compose.misp.yml restart"
log_info ""
log_info "Initial Setup Steps:"
log_info "  1. Access http://${SERVER_IP}:7003"
log_info "  2. Login with credentials above"
log_info "  3. Configure Organization details"
log_info "  4. Set up threat feeds (Admin > Feeds)"
log_info "  5. Configure API keys for integrations"
log_info ""
log_info "============================================"

exit 0
