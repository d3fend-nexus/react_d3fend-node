"""
Detection Management Configuration
YARA and Sigma rule management, deployment, and automation
"""

DETECTION_CONFIG = {
    "enabled": True,
    "auto_import_misp": True,
    "monitoring_interval": 60,  # seconds
    
    # YARA Configuration
    "yara": {
        "enabled": True,
        "service_host": "localhost",
        "service_port": 8001,
        "api_endpoint": "/api/yara",
        "api_timeout": 30,
        
        "rule_directories": {
            "custom": "/var/lib/yara/rules/custom/",
            "auto_generated": "/var/lib/yara/rules/auto_generated/",
            "community": "/var/lib/yara/rules/community/",
            "malware": "/var/lib/yara/rules/malware/",
            "apt": "/var/lib/yara/rules/apt/"
        },
        
        "deployment": {
            "velociraptor": {
                "enabled": True,
                "artifact_name": "YARA/ProcessScan",
                "schedule_interval": 3600  # 1 hour
            }
        },
        
        "rule_templates": {
            "hash_detection": """
rule MISP_Malware_{hash_type}_{hash_value} {{
    meta:
        description = "Malware detected via MISP"
        misp_event_id = "{misp_event_id}"
        misp_source = "{misp_source}"
        created = "{created_date}"
        severity = "{severity}"
    
    condition:
        hash.{hash_type}(0, filesize) == "{hash_value_lower}"
}}
""",
            
            "malware_family": """
rule APT_{family_name}_Indicators {{
    meta:
        description = "Detection for {family_name} malware"
        author = "{author}"
        date = "{created_date}"
        mitre_technique = "{mitre_technique}"
    
    strings:
        $str1 = "{indicator1}" ascii wide
        $str2 = "{indicator2}" ascii
        $str3 = "{indicator3}" hex
    
    condition:
        uint16(0) == 0x5a4d and any of them
}}
"""
        }
    },
    
    # Sigma Configuration
    "sigma": {
        "enabled": True,
        "rule_directories": {
            "windows": "/var/lib/sigma/rules/windows/",
            "linux": "/var/lib/sigma/rules/linux/",
            "network": "/var/lib/sigma/rules/network/",
            "custom": "/var/lib/sigma/rules/custom/"
        },
        
        "backends": {
            "wazuh": {
                "enabled": True,
                "manager_host": "wazuh-manager",
                "manager_port": 55000,
                "converter": "sigma_to_wazuh",
                "deployment_group": "sigma_rules"
            },
            "elasticsearch": {
                "enabled": False,
                "host": "elasticsearch",
                "port": 9200,
                "converter": "sigma_to_elasticsearch"
            }
        },
        
        "community_library": {
            "enabled": True,
            "update_interval": 86400,  # 24 hours
            "repository": "https://github.com/SigmaHQ/sigma/raw/main/rules/"
        }
    },
    
    # IOC Conversion & Automation
    "ioc_conversion": {
        "enabled": True,
        "auto_generate_on_misp_update": True,
        "supported_types": {
            "md5": "yara",
            "sha1": "yara",
            "sha256": "yara",
            "file_path": "sigma",
            "filename": "sigma",
            "domain": "sigma",
            "url": "sigma",
            "ip_src": "sigma",
            "ip_dst": "sigma"
        },
        
        "misp_integration": {
            "enabled": True,
            "host": "http://misp-platform",
            "port": 80,
            "api_endpoint": "/api/v2",
            "sync_interval": 300,  # 5 minutes
            "auto_tag": True
        }
    },
    
    # Rule Performance Tracking
    "performance_tracking": {
        "enabled": True,
        "metrics": {
            "track_hits": True,
            "track_execution_time": True,
            "track_false_positives": True,
            "track_coverage": True
        },
        
        "alert_thresholds": {
            "false_positive_rate": 0.05,  # 5%
            "execution_time_warning": 1000,  # ms
            "execution_time_critical": 5000  # ms
        }
    },
    
    # Deployment Settings
    "deployment": {
        "auto_deploy_on_creation": False,
        "require_validation": True,
        "require_approval": False,
        "approval_role": "analyst",
        
        "rollback_enabled": True,
        "rollback_keep_versions": 10,
        
        "deployment_schedule": {
            "enabled": False,
            "schedule_time": "02:00"  # 2 AM UTC
        }
    }
}

# Pre-loaded Community YARA Rules
COMMUNITY_YARA_RULES = {
    "malware_families": [
        "emotet.yar",
        "trickbot.yar",
        "wannacry.yar",
        "locky.yar",
        "cryptolocker.yar",
        "petya.yar",
        "mirai.yar",
        "zeus.yar",
        "conficker.yar",
        "stuxnet.yar"
    ],
    
    "apt_groups": [
        "apt1_comment_crew.yar",
        "apt28_fancy_bear.yar",
        "apt29_cozy_bear.yar",
        "lazarus_nk.yar",
        "equation_group.yar"
    ],
    
    "fileless": [
        "powershell_obfuscation.yar",
        "wmi_execution.yar",
        "registry_modification.yar",
        "scheduled_task.yar"
    ]
}

# Pre-loaded Community Sigma Rules
COMMUNITY_SIGMA_RULES = {
    "windows": {
        "process_creation": 8,
        "image_load": 5,
        "file_access": 4,
        "registry": 3
    },
    
    "linux": {
        "process_execution": 6,
        "file_access": 4,
        "user_management": 3,
        "network": 2
    },
    
    "network": {
        "dns": 4,
        "http": 5,
        "ssh": 3,
        "rdp": 2
    }
}

# Default Rule Groups
DEFAULT_RULE_GROUPS = {
    "windows": {
        "description": "Windows endpoint detection",
        "rules": ["process_creation", "registry", "image_load"],
        "agents": ["windows_group"]
    },
    
    "linux": {
        "description": "Linux server detection",
        "rules": ["process_execution", "file_access", "user_management"],
        "agents": ["linux_group"]
    },
    
    "network": {
        "description": "Network-based detection",
        "rules": ["dns", "http", "ssh", "rdp"],
        "agents": ["network_sensors"]
    },
    
    "critical": {
        "description": "High-priority detection rules",
        "rules": ["ransomware", "apt_indicators", "fileless_execution"],
        "agents": ["all"]
    }
}
