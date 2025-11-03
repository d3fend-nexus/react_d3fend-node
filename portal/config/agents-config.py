"""
Agent Management Configuration
Centralized configuration for Velociraptor and Wazuh agent deployment
"""

AGENTS_CONFIG = {
    "enabled": True,
    "monitoring_interval": 30,  # seconds
    
    # Velociraptor Configuration
    "velociraptor": {
        "enabled": True,
        "host": "https://velociraptor-server",
        "port": 8889,
        "api_port": 8889,
        "api_timeout": 30,
        
        "server_settings": {
            "frontend_certificate": "/etc/velociraptor/server.crt",
            "frontend_key": "/etc/velociraptor/server.key",
            "client_certificate": "/etc/velociraptor/client.crt",
            "client_key": "/etc/velociraptor/client.key"
        },
        
        "deployment": {
            "windows": {
                "installer_type": "msi",
                "arch": ["x86_64", "x86"],
                "template": "velociraptor_windows.msi.j2"
            },
            "linux": {
                "installer_type": ["deb", "rpm"],
                "arch": ["x86_64", "arm64"],
                "template": "velociraptor_linux.pkg.j2"
            },
            "macos": {
                "installer_type": "pkg",
                "arch": ["x86_64", "arm64"],
                "template": "velociraptor_macos.pkg.j2"
            }
        }
    },
    
    # Wazuh Configuration
    "wazuh": {
        "enabled": True,
        "host": "wazuh-manager",
        "port": 55000,  # API port
        "agent_port": 1514,
        "api_timeout": 30,
        
        "credentials": {
            "username": "wazuh",
            "password": "SecurePassword123"
        },
        
        "deployment": {
            "windows": {
                "installer_type": "msi",
                "arch": ["x86_64", "x86"],
                "default_group": "windows"
            },
            "linux": {
                "installer_type": ["deb", "rpm"],
                "arch": ["x86_64", "arm64"],
                "default_group": "linux"
            },
            "macos": {
                "installer_type": "pkg",
                "arch": ["x86_64", "arm64"],
                "default_group": "macos"
            }
        },
        
        "agent_groups": {
            "windows": {
                "description": "Windows Endpoints",
                "config": {
                    "localfile": {
                        "log_format": "eventchannel",
                        "location": "Security,System,Application"
                    }
                }
            },
            "linux": {
                "description": "Linux Servers",
                "config": {
                    "localfile": {
                        "log_format": "syslog",
                        "location": "/var/log/auth.log"
                    }
                }
            },
            "macos": {
                "description": "macOS Endpoints",
                "config": {
                    "localfile": {
                        "log_format": "syslog",
                        "location": "/var/log/system.log"
                    }
                }
            }
        }
    },
    
    # Deployment Methods
    "deployment_methods": {
        "web_download": {
            "name": "Web Download Portal",
            "description": "Download installer from web interface",
            "supported": ["windows", "linux", "macos"]
        },
        "powershell_oneliner": {
            "name": "PowerShell One-Liner",
            "description": "Windows PowerShell single command deployment",
            "supported": ["windows"]
        },
        "bash_oneliner": {
            "name": "Bash One-Liner",
            "description": "Linux/macOS single command deployment",
            "supported": ["linux", "macos"]
        },
        "docker": {
            "name": "Docker Container",
            "description": "Deploy as containerized agent",
            "supported": ["windows", "linux", "macos"]
        },
        "ansible": {
            "name": "Ansible Playbook",
            "description": "Deploy using Ansible automation",
            "supported": ["linux"]
        },
        "gpo": {
            "name": "Group Policy",
            "description": "Deploy via Active Directory GPO",
            "supported": ["windows"]
        }
    },
    
    # One-Liner Templates
    "oneliner_templates": {
        "velociraptor_windows": 'iex (iwr -Uri "https://{server}:{port}/api/agents/deploy/windows/velociraptor").Content',
        "velociraptor_linux": 'bash <(curl -sSL https://{server}:{port}/api/agents/deploy/linux/velociraptor)',
        
        "wazuh_windows": 'iex (iwr -Uri "https://{server}:{port}/api/agents/deploy/windows/wazuh").Content',
        "wazuh_linux": 'bash <(curl -sSL https://{server}:{port}/api/agents/deploy/linux/wazuh)',
    }
}

# Supported Platforms
SUPPORTED_PLATFORMS = {
    "windows": {
        "name": "Windows",
        "icon": "fab fa-windows",
        "versions": ["7", "8", "8.1", "10", "11", "Server 2012+"],
        "arch": ["x86_64", "x86"]
    },
    "linux": {
        "name": "Linux",
        "icon": "fab fa-linux",
        "distributions": ["Ubuntu", "Debian", "CentOS", "RedHat", "Fedora", "Alpine"],
        "arch": ["x86_64", "arm64", "armv7"]
    },
    "macos": {
        "name": "macOS",
        "icon": "fab fa-apple",
        "versions": ["10.13+", "11", "12", "13"],
        "arch": ["x86_64", "arm64"]
    }
}

# Agent Health Status Thresholds
HEALTH_THRESHOLDS = {
    "online_timeout": 300,  # 5 minutes
    "warning_timeout": 600,  # 10 minutes
    "critical_timeout": 1800  # 30 minutes
}
