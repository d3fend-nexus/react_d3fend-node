"""
Network Analysis Configuration
Suricata IDS and Arkime PCAP analysis settings
"""

NETWORK_CONFIG = {
    "enabled": True,
    "monitoring_interval": 30,  # seconds
    
    # Suricata IDS Configuration
    "suricata": {
        "enabled": True,
        "host": "suricata",
        "port": 5000,
        "api_port": 5000,
        "api_timeout": 30,
        
        "monitoring": {
            "interface": "eth0",
            "pcap_snaplen": 65535,
            "buffer_size": 32768,
            "threads": 4
        },
        
        "detection": {
            "rule_sources": [
                "phase3_detection",
                "et_open",
                "custom"
            ],
            "emerging_threats": {
                "enabled": True,
                "update_interval": 3600
            }
        },
        
        "logging": {
            "eve_log": True,
            "dns_log": True,
            "http_log": True,
            "tls_log": True,
            "alert_log": True
        },
        
        "alert_thresholds": {
            "critical": 1,
            "high": 5,
            "medium": 20,
            "low": 100
        }
    },
    
    # Arkime Configuration
    "arkime": {
        "enabled": True,
        "host": "arkime",
        "port": 8005,
        "elasticsearch_host": "elasticsearch",
        "elasticsearch_port": 9200,
        
        "capture": {
            "enabled": True,
            "interface": "eth0",
            "snaplen": 65535,
            "buffer_size": 32768,
            "max_file_size": 268435456  # 256 MB
        },
        
        "storage": {
            "pcap_dir": "/data/pcap",
            "index_dir": "/data/indices",
            "retention_days": 30,
            "compression": "none"
        },
        
        "indexing": {
            "interval": 300,  # seconds
            "max_packet_queue": 1000000,
            "max_es_request_size": 536870912  # 512 MB
        }
    },
    
    # Network Interfaces
    "interfaces": {
        "eth0": {
            "name": "Primary Interface",
            "description": "Default monitoring interface",
            "enabled": True,
            "suricata": True,
            "arkime": True,
            "pcap_rotation": 3600
        },
        "eth1": {
            "name": "Secondary Interface",
            "description": "Optional second monitoring interface",
            "enabled": False,
            "suricata": False,
            "arkime": False,
            "pcap_rotation": 3600
        }
    },
    
    # Protocol Analysis
    "protocols": {
        "dns": {
            "enabled": True,
            "track_queries": True,
            "track_responses": True,
            "suspicious_domains": []
        },
        
        "http": {
            "enabled": True,
            "track_requests": True,
            "track_responses": True,
            "track_cookies": True,
            "suspicious_useragents": []
        },
        
        "tls": {
            "enabled": True,
            "track_certificates": True,
            "track_handshakes": True,
            "expired_cert_alert": True,
            "self_signed_alert": False
        },
        
        "ssh": {
            "enabled": True,
            "track_attempts": True,
            "track_versions": True,
            "brute_force_threshold": 10
        },
        
        "smtp": {
            "enabled": True,
            "track_emails": True,
            "suspicious_recipients": []
        },
        
        "ftp": {
            "enabled": True,
            "track_logins": True,
            "brute_force_threshold": 5
        }
    },
    
    # Threat Intelligence Integration
    "threat_intelligence": {
        "enabled": True,
        "misp_integration": True,
        "auto_import_iocs": True,
        "ioc_types": {
            "ip": True,
            "domain": True,
            "url": True,
            "hash": False
        },
        "update_interval": 300  # 5 minutes
    },
    
    # Alert Settings
    "alerts": {
        "enabled": True,
        "email_alerts": False,
        "slack_alerts": False,
        "threshold_based": True,
        "correlation": True,
        
        "rules": {
            "suspicious_dns": True,
            "c2_detection": True,
            "data_exfiltration": True,
            "malware_signatures": True,
            "brute_force": True,
            "port_scanning": True
        }
    }
}

# Default Suricata Rules Categories
SURICATA_RULE_CATEGORIES = {
    "malware": {
        "name": "Malware Detection",
        "description": "Malware signatures and behavioral patterns"
    },
    "c2": {
        "name": "Command & Control",
        "description": "C2 communication detection"
    },
    "exfiltration": {
        "name": "Data Exfiltration",
        "description": "Data exfiltration detection"
    },
    "reconnaissance": {
        "name": "Reconnaissance",
        "description": "Network reconnaissance activity"
    },
    "exploitation": {
        "name": "Exploitation",
        "description": "Known exploit signatures"
    },
    "dos": {
        "name": "Denial of Service",
        "description": "DoS attack patterns"
    }
}

# Network Flow Types
NETWORK_FLOW_TYPES = {
    "client_server": {
        "name": "Client-Server",
        "icon": "fas fa-arrows-h",
        "description": "Typical client-server communication"
    },
    "peer_to_peer": {
        "name": "Peer-to-Peer",
        "icon": "fas fa-project-diagram",
        "description": "P2P communication patterns"
    },
    "broadcast": {
        "name": "Broadcast",
        "icon": "fas fa-broadcast-tower",
        "description": "Broadcast or multicast traffic"
    },
    "lateral_movement": {
        "name": "Lateral Movement",
        "icon": "fas fa-arrows-alt",
        "description": "Suspected lateral movement"
    }
}

# Suspicious Pattern Definitions
SUSPICIOUS_PATTERNS = {
    "fast_flux": {
        "description": "Fast flux DNS activity",
        "indicators": ["DNS_RAPID_CHANGE", "IP_RAPID_CHANGE"]
    },
    "dns_tunnel": {
        "description": "DNS tunneling activity",
        "indicators": ["DNS_QUERY_SIZE", "DNS_RESPONSE_SIZE"]
    },
    "http_tunnel": {
        "description": "HTTP tunneling activity",
        "indicators": ["HTTP_LONG_BODY", "HTTP_ABNORMAL_METHOD"]
    },
    "data_exfil": {
        "description": "Data exfiltration patterns",
        "indicators": ["OUTBOUND_VOLUME", "PROTOCOL_MISMATCH"]
    }
}
