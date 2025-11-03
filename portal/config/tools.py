"""
BTPI-REACT Tool Configuration
Maps all security tools to portal interface
"""

BTPI_TOOLS = {
    "velociraptor": {
        "name": "Velociraptor",
        "description": "Digital Forensics and Incident Response platform for live endpoint forensics and threat hunting.",
        "category": "dfir",
        "port": 8889,
        "icon": "fas fa-search",
        "protocols": ["https"],
        "credentials": {
            "username": "admin",
            "password": "admin"
        },
        "container_names": ["velociraptor", "btpi-velociraptor", "cyber-blue-test-velociraptor-1"],
        "access_url": "https://{server_ip}:8889",
        "status": "running"
    },
    "wazuh-dashboard": {
        "name": "Wazuh Dashboard",
        "description": "SIEM dashboard for log analysis, alerting, and security monitoring with Kibana-style interface.",
        "category": "siem",
        "port": 5601,
        "icon": "fas fa-chart-line",
        "protocols": ["https"],
        "credentials": {
            "username": "admin",
            "password": "SecretPassword"
        },
        "container_names": ["wazuh-dashboard", "wazuh.dashboard", "cyber-blue-test-wazuh.dashboard-1"],
        "access_url": "https://{server_ip}:5601",
        "status": "running"
    },
    "wazuh-manager": {
        "name": "Wazuh Manager",
        "description": "Wazuh Manager API for agent management and SIEM configuration.",
        "category": "siem",
        "port": 55000,
        "icon": "fas fa-shield-alt",
        "protocols": ["https"],
        "credentials": {
            "username": "wazuh",
            "password": "${WAZUH_API_PASSWORD}"
        },
        "container_names": ["wazuh-manager", "wazuh.manager", "cyber-blue-test-wazuh.manager-1"],
        "access_url": "https://{server_ip}:55000",
        "status": "running"
    },
    "elasticsearch": {
        "name": "Elasticsearch",
        "description": "Search and analytics engine for log storage and retrieval.",
        "category": "data",
        "port": 9200,
        "icon": "fas fa-database",
        "protocols": ["https"],
        "credentials": {
            "username": "elastic",
            "password": "${ELASTIC_PASSWORD}"
        },
        "container_names": ["elasticsearch", "btpi-elasticsearch", "cyber-blue-test-elasticsearch-1"],
        "access_url": "https://{server_ip}:9200",
        "status": "running"
    },
    "portainer": {
        "name": "Portainer",
        "description": "Web-based container management interface for Docker and Kubernetes.",
        "category": "management",
        "port": 9443,
        "icon": "fas fa-ship",
        "protocols": ["https"],
        "credentials": {
            "username": "admin",
            "password": "cyberblue123"
        },
        "container_names": ["portainer", "btpi-portainer", "cyber-blue-test-portainer-1"],
        "access_url": "https://{server_ip}:9443",
        "status": "running"
    },
    "kasm": {
        "name": "Kasm Workspaces",
        "description": "Secure browser-based virtual desktop environment for malware analysis and web-based investigations.",
        "category": "utility",
        "port": 6443,
        "icon": "fas fa-desktop",
        "protocols": ["https"],
        "credentials": {
            "username": "admin@kasm.local",
            "password": "admin"
        },
        "container_names": ["kasm-server", "kasm_kasm_1", "cyber-blue-test-kasm-1"],
        "access_url": "https://{server_ip}:6443",
        "status": "running"
    },
    "cassandra": {
        "name": "Cassandra",
        "description": "NoSQL database backend for distributed data storage.",
        "category": "data",
        "port": 9042,
        "icon": "fas fa-database",
        "protocols": ["tcp"],
        "credentials": {
            "note": "Database backend - no direct access needed"
        },
        "container_names": ["cassandra", "btpi-cassandra", "cyber-blue-test-cassandra-1"],
        "status": "backend"
    }
}

# Tool categories
TOOL_CATEGORIES = {
    "dfir": {
        "name": "Digital Forensics & Incident Response",
        "icon": "fas fa-magnifying-glass",
        "color": "primary"
    },
    "siem": {
        "name": "SIEM & Log Analysis",
        "icon": "fas fa-chart-line",
        "color": "success"
    },
    "data": {
        "name": "Data Storage & Search",
        "icon": "fas fa-database",
        "color": "info"
    },
    "management": {
        "name": "Container Management",
        "icon": "fas fa-cogs",
        "color": "warning"
    },
    "utility": {
        "name": "Utilities",
        "icon": "fas fa-toolbox",
        "color": "secondary"
    }
}

# Portal configuration
PORTAL_CONFIG = {
    "name": "BTPI-REACT",
    "title": "Blue Team Portable Infrastructure - Rapid Emergency Analysis & Counter-Threat",
    "version": "1.0.0",
    "port": 5500,
    "https_port": 5443,
    "enable_https": True,
    "log_file": "logs/portal.log",
    "changelog_file": "data/changelog.json",
    "container_status_file": "data/container_status.json",
    "monitoring_interval": 30,  # seconds
    "refresh_interval": 5000,  # milliseconds for frontend
}
