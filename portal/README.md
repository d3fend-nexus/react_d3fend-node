# BTPI-REACT Portal

Unified SOC Management Dashboard for BTPI-REACT

## Overview

The BTPI-REACT Portal provides a centralized web-based interface for managing all security tools within the BTPI-REACT infrastructure. Built with Flask and modern JavaScript, it offers real-time monitoring, container management, and quick access to all integrated security platforms.

## Features

### Dashboard
- **System Metrics**: Real-time CPU, memory, and disk usage monitoring
- **Container Health**: Overview of running/stopped containers
- **Tool Status**: Live status of all integrated security tools
- **Activity Log**: Timeline of system events and changes

### Tool Management
- **Quick Access**: One-click access to all security tools
- **Container Control**: Start, stop, and restart containers
- **Status Monitoring**: Real-time tool availability
- **Categorization**: Tools organized by function (DFIR, SIEM, CTI, etc.)

### System Monitoring
- **Real-time Updates**: Auto-refresh metrics every 5 seconds
- **Health Indicators**: Visual indicators for tool status
- **Activity Timeline**: Comprehensive event logging
- **Resource Tracking**: System and container performance metrics

## Architecture

```
Frontend (JavaScript/HTML/CSS)
          ↓
API Client (Fetch wrapper)
          ↓
Flask Backend (Python)
          ↓
Docker Socket API
          ↓
Container Management
```

## Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Modern web browser

### Quick Start

1. **Clone/Navigate to portal directory**:
   ```bash
   cd react_d3fend-node/portal
   ```

2. **Deploy using script**:
   ```bash
   chmod +x ../services/portal/deploy.sh
   ../services/portal/deploy.sh
   ```

   Or manually with Docker:
   ```bash
   docker build -t btpi-react/portal:1.0.0 .
   docker run -d \
     --name btpi-portal \
     --network btpi-core-network \
     -p 5500:5500 \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/data:/app/data \
     btpi-react/portal:1.0.0
   ```

3. **Access Portal**:
   - Open browser to `http://localhost:5500`
   - Dashboard loads automatically

## Configuration

### Environment Variables

```bash
PORTAL_PORT=5500              # HTTP port (default: 5500)
PORTAL_HTTPS_PORT=5443        # HTTPS port (default: 5443)
```

### Tool Configuration

Edit `config/tools.py` to customize tool information:

```python
"velociraptor": {
    "name": "Velociraptor",
    "port": 8889,
    "icon": "fas fa-search",
    "category": "dfir",
    "container_names": ["velociraptor"],
    ...
}
```

## API Endpoints

### Container Management
- `GET /api/containers/count` - Get container count
- `GET /api/containers/status` - Get all container status
- `POST /api/containers/<name>/start` - Start container
- `POST /api/containers/<name>/stop` - Stop container
- `POST /api/containers/<name>/restart` - Restart container

### Tools
- `GET /api/tools/status` - Get tool status
- `GET /api/tools` - Get tool configuration

### Dashboard
- `GET /api/dashboard/metrics` - Get system metrics
- `GET /api/server-info` - Get server information
- `GET /health` - Health check

### Activity Log
- `GET /api/changelog` - Get changelog entries
- `GET /api/changelog/stats` - Get changelog statistics

## Development

### Local Setup

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run development server**:
   ```bash
   python app.py
   ```

4. **Access at**:
   - `http://localhost:5500`

### Directory Structure

```
portal/
├── app.py                    # Flask backend
├── config/
│   └── tools.py             # Tool configuration
├── templates/
│   └── index.html           # Main dashboard
├── static/
│   ├── css/
│   │   └── main.css        # Styles
│   └── js/
│       ├── api-client.js   # API wrapper
│       └── dashboard.js    # Dashboard logic
├── data/
│   └── changelog.json      # Activity log
├── logs/
│   └── portal.log          # Application log
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

## Docker Integration

### Add to docker-compose.yml

```yaml
services:
  portal:
    build:
      context: ./portal
      dockerfile: Dockerfile
    container_name: btpi-portal
    ports:
      - "5500:5500"
      - "5443:5443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./portal/logs:/app/logs
      - ./portal/data:/app/data
    networks:
      - btpi-core-network
    restart: unless-stopped
    environment:
      PORTAL_PORT: 5500
      PORTAL_HTTPS_PORT: 5443

networks:
  btpi-core-network:
    driver: bridge
```

## Troubleshooting

### Portal not accessible

```bash
# Check container is running
docker ps | grep btpi-portal

# Check container logs
docker logs btpi-portal

# Test health endpoint
curl http://localhost:5500/health
```

### Tools not showing

1. Verify container names match `config/tools.py`
2. Check Docker network connectivity
3. Review application logs: `docker logs btpi-portal`

### High resource usage

- Reduce refresh interval in `dashboard.js`
- Adjust monitoring interval in `config/tools.py`
- Limit changelog entries in `app.py`

## Performance

- Auto-refresh: 5 seconds
- Monitoring interval: 30 seconds
- Changelog limit: 100 entries
- Dashboard updates: Parallel loading

## Security

⚠️ **Security Notes**:
- Portal requires Docker socket access
- Run behind firewall in production
- Consider reverse proxy with authentication
- Use HTTPS in production
- Implement proper access controls

## Logs

Application logs are stored in `logs/portal.log`:

```bash
# View logs
tail -f logs/portal.log

# View from container
docker logs -f btpi-portal
```

## Changelog

System activity is logged to `data/changelog.json`:

```bash
# View activity
tail -f data/changelog.json

# Or via API
curl http://localhost:5500/api/changelog
```

## Version

- **Portal Version**: 1.0.0
- **Python**: 3.11+
- **Flask**: 3.0.0
- **Python Requirements**: See requirements.txt

## Support & Issues

For issues or feature requests:
1. Check troubleshooting section above
2. Review application logs
3. Check Docker container status
4. Verify tool configuration

## License

MIT License - See LICENSE file in project root

## Contributing

Contributions welcome! Areas for enhancement:
- Advanced metrics and graphing
- Real-time alerts
- User authentication
- Custom themes
- Additional tool integrations

---

**BTPI-REACT Portal** - Centralized SOC Management
