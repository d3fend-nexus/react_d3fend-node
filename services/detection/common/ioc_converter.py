"""
IOC Conversion Service
Convert MISP IOCs to YARA and Sigma detection rules
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional


class IOCConverter:
    """Convert MISP indicators to detection rules"""
    
    @staticmethod
    def ioc_to_yara(ioc_data: Dict) -> Optional[str]:
        """Convert MISP IOC to YARA rule"""
        
        ioc_type = ioc_data.get('type')
        value = ioc_data.get('value')
        event_id = ioc_data.get('event_id', 'unknown')
        source = ioc_data.get('source', 'MISP')
        
        if ioc_type in ['md5', 'sha1', 'sha256']:
            return IOCConverter._hash_to_yara(
                ioc_type, value, event_id, source
            )
        elif ioc_type == 'filename':
            return IOCConverter._filename_to_yara(value, event_id, source)
        elif ioc_type in ['domain', 'hostname']:
            return IOCConverter._domain_to_yara(value, event_id, source)
        elif ioc_type == 'url':
            return IOCConverter._url_to_yara(value, event_id, source)
        
        return None
    
    @staticmethod
    def _hash_to_yara(hash_type: str, hash_value: str, event_id: str, source: str) -> str:
        """Generate YARA rule from file hash"""
        
        # Normalize hash type for YARA
        hash_func = hash_type.lower().replace('sha', 'sha')
        
        rule_name = f"MISP_IOC_{hash_type.upper()}_{hash_value[:8]}"
        
        return f"""rule {rule_name} {{
    meta:
        description = "Malware detected via {source}"
        misp_event_id = "{event_id}"
        hash_type = "{hash_type}"
        created = "{datetime.utcnow().isoformat()}"
        severity = "high"
    
    condition:
        hash.{hash_func}(0, filesize) == "{hash_value.lower()}"
}}
"""
    
    @staticmethod
    def _filename_to_yara(filename: str, event_id: str, source: str) -> str:
        """Generate YARA rule from filename"""
        
        rule_name = f"MISP_IOC_Filename_{filename.replace('.', '_')[:30]}"
        
        # Escape special characters
        escaped_filename = filename.replace('\\', '\\\\').replace('"', '\\"')
        
        return f"""rule {rule_name} {{
    meta:
        description = "Suspicious file detected via {source}"
        misp_event_id = "{event_id}"
        created = "{datetime.utcnow().isoformat()}"
        severity = "medium"
    
    strings:
        $filename = "{escaped_filename}" nocase
    
    condition:
        $filename
}}
"""
    
    @staticmethod
    def _domain_to_yara(domain: str, event_id: str, source: str) -> str:
        """Generate YARA rule from domain"""
        
        rule_name = f"MISP_IOC_Domain_{domain.replace('.', '_')[:30]}"
        escaped_domain = domain.replace('\\', '\\\\').replace('"', '\\"')
        
        return f"""rule {rule_name} {{
    meta:
        description = "Connection to malicious domain via {source}"
        misp_event_id = "{event_id}"
        created = "{datetime.utcnow().isoformat()}"
        severity = "high"
    
    strings:
        $domain = "{escaped_domain}" nocase
        $dns_query = "dns_query" wide
    
    condition:
        $domain or $dns_query
}}
"""
    
    @staticmethod
    def _url_to_yara(url: str, event_id: str, source: str) -> str:
        """Generate YARA rule from URL"""
        
        rule_name = f"MISP_IOC_URL_{hashlib.md5(url.encode()).hexdigest()[:8]}"
        escaped_url = url.replace('\\', '\\\\').replace('"', '\\"')
        
        return f"""rule {rule_name} {{
    meta:
        description = "Malicious URL detected via {source}"
        misp_event_id = "{event_id}"
        created = "{datetime.utcnow().isoformat()}"
        severity = "high"
    
    strings:
        $url = "{escaped_url}" nocase
    
    condition:
        $url
}}
"""
    
    @staticmethod
    def ioc_to_sigma(ioc_data: Dict) -> Optional[str]:
        """Convert MISP IOC to Sigma rule"""
        
        ioc_type = ioc_data.get('type')
        value = ioc_data.get('value')
        event_id = ioc_data.get('event_id', 'unknown')
        source = ioc_data.get('source', 'MISP')
        
        if ioc_type in ['domain', 'hostname']:
            return IOCConverter._domain_to_sigma(value, event_id, source)
        elif ioc_type == 'url':
            return IOCConverter._url_to_sigma(value, event_id, source)
        elif ioc_type in ['ip_src', 'ip_dst']:
            return IOCConverter._ip_to_sigma(value, ioc_type, event_id, source)
        elif ioc_type == 'filename':
            return IOCConverter._filename_to_sigma(value, event_id, source)
        
        return None
    
    @staticmethod
    def _domain_to_sigma(domain: str, event_id: str, source: str) -> str:
        """Generate Sigma rule from domain"""
        
        rule_id = hashlib.md5(domain.encode()).hexdigest()[:8]
        
        return f"""title: Suspicious Domain Access - {source}
id: misp-ioc-{rule_id}
description: Connection attempt to known malicious domain
status: experimental
logsource:
    category: network_connection
    product: windows
detection:
    selection:
        DestinationHostname|contains:
            - '{domain}'
    filter_dns:
        ProcessName|endswith:
            - 'svchost.exe'
    condition: selection and not filter_dns
fields:
    - ComputerName
    - Image
    - DestinationHostname
    - DestinationPort
falsepositives:
    - Legitimate traffic
level: high
tags:
    - misp
    - misp_event_id_{event_id}
"""
    
    @staticmethod
    def _url_to_sigma(url: str, event_id: str, source: str) -> str:
        """Generate Sigma rule from URL"""
        
        rule_id = hashlib.md5(url.encode()).hexdigest()[:8]
        
        return f"""title: Suspicious URL Access - {source}
id: misp-ioc-{rule_id}
description: HTTP request to malicious URL
status: experimental
logsource:
    category: web_application_firewall
detection:
    selection:
        url|contains: '{url}'
    condition: selection
fields:
    - src_ip
    - dest_ip
    - url
    - user_agent
falsepositives:
    - Legitimate traffic
level: high
tags:
    - misp
    - misp_event_id_{event_id}
"""
    
    @staticmethod
    def _ip_to_sigma(ip_addr: str, ip_type: str, event_id: str, source: str) -> str:
        """Generate Sigma rule from IP address"""
        
        rule_id = hashlib.md5(ip_addr.encode()).hexdigest()[:8]
        direction = 'DestinationIp' if ip_type == 'ip_dst' else 'SourceIp'
        
        return f"""title: Suspicious IP Connection - {source}
id: misp-ioc-{rule_id}
description: Connection to/from known malicious IP
status: experimental
logsource:
    category: network_connection
    product: windows
detection:
    selection:
        {direction}: '{ip_addr}'
    filter_whitelist:
        ProcessName|endswith:
            - 'svchost.exe'
            - 'lsass.exe'
    condition: selection and not filter_whitelist
fields:
    - ComputerName
    - Image
    - {direction}
    - DestinationPort
falsepositives:
    - Legitimate traffic
    - Corporate proxies
level: high
tags:
    - misp
    - misp_event_id_{event_id}
"""
    
    @staticmethod
    def _filename_to_sigma(filename: str, event_id: str, source: str) -> str:
        """Generate Sigma rule from filename"""
        
        rule_id = hashlib.md5(filename.encode()).hexdigest()[:8]
        
        return f"""title: Suspicious File Execution - {source}
id: misp-ioc-{rule_id}
description: Execution of known malicious filename
status: experimental
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '{filename}'
    condition: selection
fields:
    - ComputerName
    - Image
    - CommandLine
    - ParentImage
falsepositives:
    - Legitimate software
level: medium
tags:
    - misp
    - misp_event_id_{event_id}
"""
    
    @staticmethod
    def batch_convert_iocs(iocs: List[Dict], rule_type: str = 'yara') -> List[str]:
        """Convert multiple IOCs to rules"""
        
        rules = []
        
        for ioc in iocs:
            if rule_type == 'yara':
                rule = IOCConverter.ioc_to_yara(ioc)
            else:
                rule = IOCConverter.ioc_to_sigma(ioc)
            
            if rule:
                rules.append(rule)
        
        return rules
    
    @staticmethod
    def get_supported_ioc_types() -> Dict[str, str]:
        """Get supported IOC types and their target rule systems"""
        
        return {
            'md5': 'yara',
            'sha1': 'yara',
            'sha256': 'yara',
            'filename': 'both',
            'domain': 'sigma',
            'hostname': 'sigma',
            'url': 'sigma',
            'ip_src': 'sigma',
            'ip_dst': 'sigma'
        }
