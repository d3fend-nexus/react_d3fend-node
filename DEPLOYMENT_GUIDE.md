# BTPI-REACT Deployment Guide

Complete step-by-step deployment instructions for the BTPI-REACT purple team infrastructure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Phase-by-Phase Deployment](#phase-by-phase-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Configuration Guide](#configuration-guide)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## Prerequisites

### Required Software

1. **Docker** (v20.10 or later)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Verify installation
   docker --version
   ```

2. **Docker Compose** (v1.29 or later)
   ```bash
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Verify installation
   docker-compose --version
   ```

3. **Git** (for cloning repository)
   ```bash
   sudo apt-get install git
   ```

### System Requirements

| Component | CPU | RAM | Disk | Network |
|-----------|-----|-----|------|---------|
| **Minimum** | 4 cores | 8GB | 50GB | 1Gbps |
| **Recommended** | 8+ cores | 16GB+ | 100GB+ | 1Gbps+ |
| **Production** | 16+ cores | 32GB+ | 200GB+ | 10Gbps |

### Port Requirements

Ensure these ports are available and not blocked by firewall:

| Service | Port | Protocol | Required |
|---------|------|----------|----------|
| Portal | 5500 | HTTP/HTTPS | Yes |
| MISP | 8080 | HTTP | Yes |
| YARA API | 8001 | HTTP | Yes |
| Arkime | 8005 | HTTP | Yes |
| Elasticsearch | 9200 | HTTP | Yes |
| Shuffle Backend | 5001 | HTTP | Yes |
| Shuffle Frontend | 3001 | HTTP | Yes |
| Shuffle Webhook | 3002 | HTTP | Yes |
| Velociraptor | 8889 | HTTPS | Optional |
| Wazuh | 443 | HTTPS | Optional |

### Network Configuration

```bash
# Check available ports
sudo netstat -tuln | grep -E "5500|8080|8001|8005|9200|5001|3001|3002"

# Open required ports (if using UFW)
sudo ufw allow 5500/tcp
sudo ufw allow 8080/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 8005/tcp
sudo ufw allow 9200/tcp
sudo ufw allow 5001/tcp
sudo ufw allow 3001/tcp
sudo ufw allow 3002/tcp
```

---

## System Requirements

### Linux Distribution Support

**Recommended:**
- Ubuntu 20.04 LTS or later
- CentOS 8 or later
- Debian 11 or later

### Kernel & System Libraries

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required libraries
sudo apt-get install -y \
  curl \
  wget \
  git \
  net-tools \
  htop \
  jq \
  vim \
  python3-pip
```

### Docker Resource Limits (Optional)

Configure Docker daemon for optimal performance:

```json
{
  "/etc/docker/daemon.json":{
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    },
    "memory": "16g",
    "cpus": "8.0"
  }
}
```

---

## Pre-Deployment Checklist

Before deployment, verify:

- [ ] Docker installed and running (`docker --version`)
- [ ] Docker Compose installed (`docker-compose --version`)
- [ ] Sufficient disk space (`df -h / | tail -1`)
- [ ] Required ports available (`netstat -tuln`)
- [ ] Network connectivity (`ping 8.8.8.8`)
- [ ] Git installed (`git --version`)
- [ ] Python 3.8+ available (`python3 --version`)
- [ ] Project directory created and accessible
- [ ] User added to docker group (`sudo usermod -aG docker $USER`)
- [ ] SSH keys configured (if pulling private repos)

**Verify all checks pass before proceeding.**

---

## Phase-by-Phase Deployment

### Step 1: Clone & Initialize

```bash
# Clone repository (or use existing)
cd /home/demo/code
git clone https://github.com/yourorg/react_d3fend-node.git
cd react_d3fend-node

# Create necessary directories
mkdir -p services/{portal,misp,detection,network,agents,soar}
mkdir -p portal/{config,templates,static/{css,js}}
mkdir -p data/{misp,yara,suricata,arkime,elasticsearch}

# Set permissions
chmod -R 755 services/
chmod -R 755 portal/
```

### Phase 1: Portal & Dashboard Deployment

**Duration:** 5-10 minutes

```bash
# Navigate to portal service
cd services/portal

# Deploy portal
./deploy.sh

# Verify deployment
docker ps | grep portal
sleep 30

# Test portal health
curl http://localhost:5500/api/health

# Access portal
# URL: http://localhost:5500
# Default credentials: admin/admin
```

**Expected Output:**
```
[✓] Portal deployed
[✓] Flask application running
[✓] API responding on :5500
```

### Phase 2: Threat Intelligence (MISP) Deployment

**Duration:** 10-15 minutes

```bash
# Navigate to MISP service
cd ../misp

# Deploy MISP
./deploy.sh

# Wait for services to initialize
echo "Waiting for MISP to initialize..."
sleep 60

# Test MISP API
curl http://localhost:8080/api/servers/getVersion

# Access MISP
# URL: http://localhost:8080
# Default credentials: admin@misp.local / misp
```

**Expected Output:**
```
[✓] MISP deployed
[✓] MySQL database initialized
[✓] Redis cache running
[✓] MISP API responding on :8080
```

**Post-Deployment Configuration:**
```bash
# Login and set up organization
# 1. Access MISP admin panel
# 2. Create organization
# 3. Add users
# 4. Configure feeds
```

### Phase 3: Detection Management (YARA/Sigma) Deployment

**Duration:** 5-10 minutes

```bash
# Navigate to detection service
cd ../detection

# Deploy detection engine
./deploy.sh

# Verify YARA scanner is running
docker ps | grep yara

# Test YARA API
curl http://localhost:8001/api/yara/health

# List available rules
curl http://localhost:8001/api/yara/rules
```

**Expected Output:**
```
[✓] YARA scanner deployed
[✓] Sigma rule engine running
[✓] IOC converter service active
[✓] API responding on :8001
```

### Phase 4: Network Analysis (Suricata/Arkime) Deployment

**Duration:** 15-20 minutes

```bash
# Navigate to network service
cd ../network

# Deploy network analysis
./deploy.sh

# Verify services are running
docker ps | grep -E "suricata|arkime|elasticsearch"

# Test Suricata connectivity
curl http://localhost:5500/api/network/suricata/health

# Access Arkime
# URL: http://localhost:8005
# Default credentials: admin / admin

# Wait for Elasticsearch to initialize
echo "Waiting for Elasticsearch..."
sleep 30

# Verify Elasticsearch
curl http://localhost:9200/_cluster/health
```

**Expected Output:**
```
[✓] Suricata IDS deployed
[✓] Arkime capture running
[✓] Elasticsearch initialized
[✓] PCAP storage configured
```

### Phase 5: SOAR Automation (Shuffle) Deployment

**Duration:** 10-15 minutes

```bash
# Navigate to SOAR service
cd ../soar

# Deploy Shuffle SOAR
./deploy.sh

# Verify Shuffle services
docker ps | grep shuffle

# Test Shuffle backend
curl http://localhost:5001/api/v1/orgs

# Access Shuffle UI
# URL: http://localhost:3001

# Test webhook receiver
curl http://localhost:3002/healthz

# Wait for full initialization
sleep 30
```

**Expected Output:**
```
[✓] Shuffle backend deployed
[✓] Shuffle frontend running
[✓] Orborus execution engine active
[✓] Webhook receiver listening on :3002
[✓] UI accessible on :3001
```

**Post-Deployment Configuration:**
```bash
# 1. Create organization in Shuffle
# 2. Add app instances (MISP, YARA, Suricata, Agents)
# 3. Import pre-built playbooks
# 4. Configure webhooks
```

### Phase 6: Agent Deployment (Velociraptor/Wazuh) Deployment

**Duration:** 15-20 minutes (optional)

```bash
# Navigate to agents service
cd ../agents

# Deploy agent infrastructure
./deploy.sh

# Verify Velociraptor
docker ps | grep velociraptor
curl https://localhost:8889/api/v1/users -k

# Verify Wazuh
docker ps | grep wazuh
curl https://localhost/api/overview -k

# Note: Agent deployment requires additional configuration
# See agents-config.py for details
```

**Expected Output:**
```
[✓] Velociraptor server deployed
[✓] Wazuh manager initialized
[✓] Agents ready for deployment
```

---

## Post-Deployment Verification

### Quick Health Check

```bash
#!/bin/bash
# Save as health-check.sh

echo "=== BTPI-REACT Health Check ==="
echo ""

# Portal
echo "[Portal] Testing..."
PORTAL=$(curl -s http://localhost:5500/api/health | jq -r '.status' 2>/dev/null)
echo "Portal: $PORTAL"

# MISP
echo "[MISP] Testing..."
MISP=$(curl -s http://localhost:8080/api/servers/getVersion 2>/dev/null | jq -r '.version' 2>/dev/null)
echo "MISP: $MISP"

# YARA
echo "[YARA] Testing..."
YARA=$(curl -s http://localhost:8001/api/yara/health | jq -r '.status' 2>/dev/null)
echo "YARA: $YARA"

# Suricata
echo "[Suricata] Testing..."
SURICATA=$(curl -s http://localhost:5500/api/network/suricata/health | jq -r '.status' 2>/dev/null)
echo "Suricata: $SURICATA"

# Shuffle
echo "[Shuffle] Testing..."
SHUFFLE=$(curl -s http://localhost:5001/api/v1/orgs 2>/dev/null | jq -r '.success' 2>/dev/null)
echo "Shuffle: $SHUFFLE"

echo ""
echo "=== Service Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Verify All Services

```bash
# Check running containers
docker ps

# Expected: 8-12 containers running (depending on configuration)

# Check network connectivity
docker network ls | grep -E "btpi|misp|detection|network|soar"

# Check volumes
docker volume ls | grep -E "misp|yara|arkime|elasticsearch|shuffle"
```

### Test Core Workflows

#### 1. Intelligence Ingestion
```bash
# Test adding IOC to MISP
curl -X POST http://localhost:8080/api/attributes/add \
  -H "Authorization: Automation token" \
  -H "Content-Type: application/json" \
  -d '{"Attribute": {"type": "md5", "value": "abc123"}}'
```

#### 2. Detection Rule Creation
```bash
# Convert IOC to YARA rule
curl -X POST http://localhost:8001/api/yara/convert \
  -H "Content-Type: application/json" \
  -d '{"ioc_type": "md5", "ioc_value": "abc123"}'
```

#### 3. Alert Forwarding
```bash
# Send test alert to Shuffle
curl -X POST http://localhost:3002/webhook \
  -H "Content-Type: application/json" \
  -d '{"alert_type": "test", "severity": "high"}'
```

---

## Configuration Guide

### Portal Configuration

**File:** `portal/config/tools.py`

```python
# API configuration
API_HOST = "0.0.0.0"
API_PORT = 5500
API_DEBUG = False

# Database
DB_PATH = "/data/portal.db"

# Security
SECRET_KEY = "generate-secure-random-key"
JWT_EXPIRATION = 3600
```

### MISP Configuration

**File:** `portal/config/intel-config.py`

```python
MISP_CONFIG = {
    "enabled": True,
    "host": "misp-platform",
    "port": 80,
    "api_key": "YOUR_MISP_API_KEY",
    "verify_ssl": False,
    
    "auto_tagging": {
        "enabled": True,
        "tag_pattern": "detection-{type}",
    }
}
```

### Detection Configuration

**File:** `portal/config/detection-config.py`

```python
DETECTION_CONFIG = {
    "yara": {
        "enabled": True,
        "host": "yara-scanner",
        "port": 8001,
        "rules_dir": "/data/yara/rules"
    },
    "sigma": {
        "enabled": True,
        "backend_dir": "/data/sigma/backends"
    }
}
```

### Network Configuration

**File:** `portal/config/network-config.py`

```python
NETWORK_CONFIG = {
    "suricata": {
        "enabled": True,
        "interface": "eth0",
        "rule_sources": ["et_open", "detection_rules"]
    },
    "arkime": {
        "enabled": True,
        "retention_days": 30
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Problem:** `Error: bind: address already in use`

**Solution:**
```bash
# Find process using port
lsof -i :5500

# Kill process
sudo kill -9 <PID>

# Or use different port
export PORT=5501
```

#### 2. Insufficient Disk Space

**Problem:** `Error: no space left on device`

**Solution:**
```bash
# Check disk space
df -h

# Clean Docker data
docker system prune -a

# Increase volume size or mount additional storage
```

#### 3. Database Connection Issues

**Problem:** `Error: could not connect to database`

**Solution:**
```bash
# Check database container
docker logs misp-db

# Restart database
docker restart misp-db

# Wait for database to initialize
sleep 30
```

#### 4. API Timeout

**Problem:** `Error: connection timeout`

**Solution:**
```bash
# Check service logs
docker logs service-name

# Increase timeout in configuration
API_TIMEOUT = 60  # seconds

# Restart service
docker restart service-name
```

#### 5. Memory Issues

**Problem:** `Error: OOMKilled` or container restarts

**Solution:**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Edit /etc/docker/daemon.json:
{
  "memory": "32g",
  "swap": "8g"
}

# Restart Docker
sudo systemctl restart docker
```

### Diagnostics

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker logs service-name

# Check service health
docker inspect service-name | jq '.State.Health'

# Test connectivity between containers
docker exec container1 curl http://container2:port

# Check network
docker network inspect btpi-network
```

---

## Maintenance

### Regular Tasks

#### Daily
- Monitor disk space: `df -h`
- Check service status: `docker ps`
- Review error logs: `docker logs`

#### Weekly
- Backup databases: `docker exec db mysqldump`
- Update images: `docker pull`
- Review alerts and metrics

#### Monthly
- Full system backup
- Update security patches
- Review and optimize configuration

### Backup & Recovery

```bash
# Backup all data
docker run --rm \
  -v misp-db:/source \
  -v /backup:/dest \
  alpine cp -r /source /dest/misp-db-backup

# Backup YARA rules
cp -r portal/config/detection-config.py /backup/detection-config.py

# Restore from backup
docker run --rm \
  -v misp-db:/dest \
  -v /backup:/source \
  alpine cp -r /source/misp-db-backup /dest
```

### Scaling Considerations

**Horizontal Scaling:**
- Deploy multiple Portal instances behind load balancer
- Scale YARA workers independently
- Add Suricata sensors on multiple interfaces

**Vertical Scaling:**
- Increase Docker memory allocation
- Add CPU cores to Docker daemon
- Upgrade underlying hardware

---

## Next Steps

After successful deployment:

1. **Configure Intelligence Sources**
   - Add MISP feeds
   - Import threat feeds
   - Configure organizations

2. **Create Detection Rules**
   - Develop YARA signatures
   - Import Sigma rules
   - Test rule effectiveness

3. **Setup Network Monitoring**
   - Configure Suricata rules
   - Setup Arkime retention
   - Define alert thresholds

4. **Integrate Agents**
   - Deploy Velociraptor
   - Register Wazuh agents
   - Configure agent groups

5. **Automate Responses**
   - Create SOAR playbooks
   - Setup webhook triggers
   - Test end-to-end workflows

---

## Support & Resources

- **Documentation:** See README.md
- **API Reference:** portal/docs/api.md
- **Configuration Examples:** portal/config/examples/
- **Community:** GitHub Issues

---

**Last Updated:** October 2025  
**Version:** 1.0.0  
**Status:** Production Ready
