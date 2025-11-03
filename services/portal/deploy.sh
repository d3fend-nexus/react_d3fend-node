#!/bin/bash
#
# BTPI-REACT Portal Deployment Script
# Deploys the unified SOC dashboard portal
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
PORTAL_DIR="${PROJECT_ROOT}/portal"

# Configuration
PORTAL_PORT=${PORTAL_PORT:-5500}
PORTAL_HTTPS_PORT=${PORTAL_HTTPS_PORT:-5443}
CONTAINER_NAME="btpi-portal"
IMAGE_NAME="btpi-react/portal"
IMAGE_TAG="1.0.0"

log_info "============================================"
log_info "BTPI-REACT Portal Deployment"
log_info "============================================"

# Check if portal directory exists
if [ ! -d "${PORTAL_DIR}" ]; then
    log_error "Portal directory not found at ${PORTAL_DIR}"
    exit 1
fi

log_info "Portal directory: ${PORTAL_DIR}"
log_info "Project root: ${PROJECT_ROOT}"

# Build Docker image
log_info "Building Docker image..."
cd "${PORTAL_DIR}"

if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" . 2>&1 | tail -5; then
    log_success "Docker image built successfully"
else
    log_error "Failed to build Docker image"
    exit 1
fi

# Remove existing container if running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_warning "Found existing container ${CONTAINER_NAME}, removing..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
fi

# Create required networks if they don't exist
log_info "Setting up Docker networks..."
docker network create btpi-core-network 2>/dev/null || true

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p "${PORTAL_DIR}/logs"
mkdir -p "${PORTAL_DIR}/data"

# Run portal container
log_info "Starting portal container..."
docker run -d \
    --name "${CONTAINER_NAME}" \
    --network btpi-core-network \
    -p "${PORTAL_PORT}:5500" \
    -p "${PORTAL_HTTPS_PORT}:5443" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${PORTAL_DIR}/logs:/app/logs" \
    -v "${PORTAL_DIR}/data:/app/data" \
    -e PORTAL_PORT=5500 \
    -e PORTAL_HTTPS_PORT=5443 \
    --restart unless-stopped \
    "${IMAGE_NAME}:${IMAGE_TAG}"

if [ $? -eq 0 ]; then
    log_success "Portal container started successfully"
else
    log_error "Failed to start portal container"
    exit 1
fi

# Wait for portal to be ready
log_info "Waiting for portal to be ready..."
for i in {1..30}; do
    if curl -sf "http://localhost:${PORTAL_PORT}/health" > /dev/null 2>&1; then
        log_success "Portal is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        log_warning "Portal health check timed out (may still be starting)"
        break
    fi
    sleep 1
done

# Display portal information
log_info "============================================"
log_success "Portal deployed successfully!"
log_info "============================================"
log_info "Portal URL: http://localhost:${PORTAL_PORT}"
log_info "Container: ${CONTAINER_NAME}"
log_info "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
log_info ""
log_info "Available endpoints:"
log_info "  - Main Dashboard: http://localhost:${PORTAL_PORT}/"
log_info "  - API Base: http://localhost:${PORTAL_PORT}/api/"
log_info "  - Health Check: http://localhost:${PORTAL_PORT}/health"
log_info ""
log_info "Container logs:"
log_info "  docker logs -f ${CONTAINER_NAME}"
log_info ""
log_info "Stop portal:"
log_info "  docker stop ${CONTAINER_NAME}"
log_info "============================================"

exit 0
