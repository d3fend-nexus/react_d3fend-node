"""
MISP Threat Intelligence Configuration
"""

MISP_CONFIG = {
    "enabled": True,
    "host": "http://misp-core",
    "port": 80,
    "api_timeout": 30,
    "max_results": 100,
    
    "feeds": [
        {
            "name": "CIRCL OSINT Feed",
            "url": "https://www.circl.lu/doc/misp/feed-osint",
            "enabled": True,
            "update_frequency": 86400  # 24 hours
        },
        {
            "name": "AlienVault OTX",
            "url": "https://otx.alienvault.com/api/v1/",
            "enabled": True,
            "update_frequency": 86400
        },
        {
            "name": "Abuse.ch URLhaus",
            "url": "https://urlhaus-api.abuse.ch/v1/",
            "enabled": True,
            "update_frequency": 86400
        },
        {
            "name": "Botvrij.eu",
            "url": "https://www.botvrij.eu/api/",
            "enabled": True,
            "update_frequency": 86400
        }
    ],
    
    "ioc_types": {
        "ipv4": "IP Address",
        "ipv6": "IPv6 Address",
        "domain": "Domain Name",
        "hostname": "Hostname",
        "url": "URL",
        "email": "Email Address",
        "hash": "File Hash",
        "md5": "MD5 Hash",
        "sha1": "SHA1 Hash",
        "sha256": "SHA256 Hash",
        "filename": "Filename"
    },
    
    "threat_levels": {
        "high": {"color": "danger", "icon": "fa-exclamation-circle"},
        "medium": {"color": "warning", "icon": "fa-exclamation-triangle"},
        "low": {"color": "info", "icon": "fa-info-circle"},
        "unknown": {"color": "secondary", "icon": "fa-question-circle"}
    }
}

# IOC Detection Patterns
IOC_PATTERNS = {
    "ipv4": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
    "ipv6": r"^(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$",
    "domain": r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$",
    "url": r"^https?://",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "md5": r"^[a-f0-9]{32}$",
    "sha1": r"^[a-f0-9]{40}$",
    "sha256": r"^[a-f0-9]{64}$"
}
