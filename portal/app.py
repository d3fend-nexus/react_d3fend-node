#!/usr/bin/env python3
"""
BTPI-REACT Portal - Unified SOC Management Interface
Flask-based backend for centralized access to all security tools
"""

import os
import json
import subprocess
import logging
import threading
import time
import signal
import sys
import requests
import re
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/portal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Import configuration
from config.tools import BTPI_TOOLS, TOOL_CATEGORIES, PORTAL_CONFIG
from config.intel_config import MISP_CONFIG, IOC_PATTERNS

# Configuration from environment
PORT = int(os.environ.get('PORTAL_PORT', PORTAL_CONFIG['port']))
HTTPS_PORT = int(os.environ.get('PORTAL_HTTPS_PORT', PORTAL_CONFIG['https_port']))
CHANGELOG_FILE = PORTAL_CONFIG['changelog_file']
CONTAINER_STATUS_FILE = PORTAL_CONFIG['container_status_file']

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class ChangelogManager:
    """Manages changelog entries for all system activities"""

    def __init__(self, changelog_file):
        self.changelog_file = changelog_file
        self.load_changelog()

    def load_changelog(self):
        """Load existing changelog from file"""
        try:
            if os.path.exists(self.changelog_file):
                with open(self.changelog_file, 'r') as f:
                    self.changelog = json.load(f)
            else:
                self.changelog = {
                    "entries": [],
                    "metadata": {
                        "created": datetime.now().isoformat(),
                        "version": "1.0.0",
                        "total_entries": 0
                    }
                }
                self.save_changelog()
        except Exception as e:
            logger.error(f"Error loading changelog: {e}")
            self.changelog = {
                "entries": [],
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "total_entries": 0
                }
            }

    def save_changelog(self):
        """Save changelog to file"""
        try:
            os.makedirs(os.path.dirname(self.changelog_file), exist_ok=True)
            with open(self.changelog_file, 'w') as f:
                json.dump(self.changelog, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving changelog: {e}")

    def add_entry(self, action, details, user="system", level="info"):
        """Add a new changelog entry"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "user": user,
            "level": level,
            "id": len(self.changelog["entries"]) + 1
        }

        self.changelog["entries"].append(entry)
        self.changelog["metadata"]["total_entries"] = len(self.changelog["entries"])
        self.save_changelog()

        logger.info(f"Changelog entry added: {action} - {details}")
        return entry

    def get_entries(self, limit=None, level=None):
        """Get changelog entries with optional filtering"""
        entries = self.changelog["entries"]

        if level:
            entries = [e for e in entries if e["level"] == level]

        if limit:
            entries = entries[-limit:]

        return entries

    def get_stats(self):
        """Get changelog statistics"""
        entries = self.changelog["entries"]
        stats = {
            "total_entries": len(entries),
            "by_level": {},
            "by_action": {},
            "recent_activity": len([e for e in entries if self._is_recent(e["timestamp"])])
        }

        for entry in entries:
            level = entry["level"]
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

            action = entry["action"]
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1

        return stats

    def _is_recent(self, timestamp, hours=24):
        """Check if timestamp is within recent hours"""
        try:
            entry_time = datetime.fromisoformat(timestamp)
            return (datetime.now() - entry_time).total_seconds() < hours * 3600
        except:
            return False


class ContainerMonitor:
    """Monitors Docker container status for BTPI-REACT tools"""

    def __init__(self, changelog_manager):
        self.changelog = changelog_manager
        self.container_status = {}
        self.previous_status = {}
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start container monitoring in background thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Container monitoring started")

    def stop_monitoring(self):
        """Stop container monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Container monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                current_status = self.get_all_container_status()
                self._check_status_changes(current_status)
                self.container_status = current_status
                self.previous_status = {
                    name: status["status"] for name, status in current_status.items()
                }
                time.sleep(PORTAL_CONFIG['monitoring_interval'])
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)

    def _check_status_changes(self, current_status):
        """Check for container status changes and log them"""
        current_containers = {name: status["status"] for name, status in current_status.items()}

        for name, status_info in current_status.items():
            if name not in self.previous_status:
                self.changelog.add_entry(
                    "container_started",
                    f"Container '{name}' started with status: {status_info['status']}",
                    level="info"
                )
            elif self.previous_status[name] != status_info["status"]:
                self.changelog.add_entry(
                    "container_status_changed",
                    f"Container '{name}' status changed from '{self.previous_status[name]}' to '{status_info['status']}'",
                    level="warning"
                )

        for name in self.previous_status:
            if name not in current_containers:
                self.changelog.add_entry(
                    "container_stopped",
                    f"Container '{name}' stopped",
                    level="warning"
                )

    def get_container_count(self):
        """Get running container count"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', 'table {{.Names}}'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                return len(lines) - 1 if len(lines) > 1 else 0
            return 0
        except Exception as e:
            logger.error(f"Error getting container count: {e}")
            return 0

    def get_all_container_status(self):
        """Get detailed status for all containers"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}\t{{.Size}}'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                containers = {}

                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            name = parts[0].strip()
                            status = parts[1].strip()
                            ports = parts[2].strip()
                            image = parts[3].strip()
                            size = parts[4].strip()

                            # Determine status type
                            if "Up" in status:
                                status_type = "running"
                                status_color = "success"
                            elif "Exited" in status:
                                status_type = "stopped"
                                status_color = "danger"
                            elif "Created" in status:
                                status_type = "created"
                                status_color = "warning"
                            else:
                                status_type = "unknown"
                                status_color = "secondary"

                            containers[name] = {
                                "name": name,
                                "status": status_type,
                                "status_text": status,
                                "color": status_color,
                                "ports": ports,
                                "image": image,
                                "size": size,
                                "last_updated": datetime.now().isoformat()
                            }

                return containers
            return {}
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return {}

    def get_tool_container_status(self):
        """Get status for BTPI-REACT tools"""
        all_containers = self.get_all_container_status()
        tool_containers = {}

        for tool_id, tool_info in BTPI_TOOLS.items():
            found = False
            for container_name in tool_info.get("container_names", []):
                if container_name in all_containers:
                    tool_containers[tool_id] = all_containers[container_name]
                    found = True
                    break

            if not found:
                tool_containers[tool_id] = {
                    "name": tool_info["name"],
                    "status": "not_found",
                    "status_text": "Container not running",
                    "color": "secondary",
                    "description": tool_info.get("description", "")
                }

        return tool_containers

    def start_container(self, container_name):
        """Start a specific container"""
        try:
            result = subprocess.run(
                ['docker', 'start', container_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.changelog.add_entry(
                    "container_started",
                    f"Container '{container_name}' started manually",
                    level="info"
                )
                return {"success": True, "message": f"Container {container_name} started successfully"}
            else:
                return {"success": False, "message": f"Failed to start container: {result.stderr}"}
        except Exception as e:
            logger.error(f"Error starting container {container_name}: {e}")
            return {"success": False, "message": f"Error starting container: {str(e)}"}

    def stop_container(self, container_name):
        """Stop a specific container"""
        try:
            result = subprocess.run(
                ['docker', 'stop', container_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.changelog.add_entry(
                    "container_stopped",
                    f"Container '{container_name}' stopped manually",
                    level="info"
                )
                return {"success": True, "message": f"Container {container_name} stopped successfully"}
            else:
                return {"success": False, "message": f"Failed to stop container: {result.stderr}"}
        except Exception as e:
            logger.error(f"Error stopping container {container_name}: {e}")
            return {"success": False, "message": f"Error stopping container: {str(e)}"}

    def restart_container(self, container_name):
        """Restart a specific container"""
        try:
            result = subprocess.run(
                ['docker', 'restart', container_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.changelog.add_entry(
                    "container_restarted",
                    f"Container '{container_name}' restarted manually",
                    level="info"
                )
                return {"success": True, "message": f"Container {container_name} restarted successfully"}
            else:
                return {"success": False, "message": f"Failed to restart container: {result.stderr}"}
        except Exception as e:
            logger.error(f"Error restarting container {container_name}: {e}")
            return {"success": False, "message": f"Error restarting container: {str(e)}"}


# Initialize managers
changelog_manager = ChangelogManager(CHANGELOG_FILE)
container_monitor = ContainerMonitor(changelog_manager)


# ============================================================================
# ROUTES - Main Pages
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    changelog_manager.add_entry(
        action="portal_access",
        details="Portal accessed",
        user="anonymous",
        level="info"
    )
    return render_template('index.html', tools=BTPI_TOOLS, categories=TOOL_CATEGORIES)


# ============================================================================
# API - Container Management
# ============================================================================

@app.route('/api/containers/count')
def get_container_count():
    """Get container count"""
    try:
        count = container_monitor.get_container_count()
        return jsonify({"count": count, "success": True})
    except Exception as e:
        logger.error(f"Error in container count API: {e}")
        return jsonify({"count": 0, "error": str(e), "success": False}), 500


@app.route('/api/containers/status')
def get_containers_status():
    """Get detailed container status"""
    try:
        containers = container_monitor.get_all_container_status()
        return jsonify({
            "containers": containers,
            "count": len(containers),
            "success": True
        })
    except Exception as e:
        logger.error(f"Error in container status API: {e}")
        return jsonify({"containers": {}, "error": str(e), "success": False}), 500


@app.route('/api/tools/status')
def get_tools_status():
    """Get BTPI-REACT tool status"""
    try:
        tool_containers = container_monitor.get_tool_container_status()
        changelog_manager.add_entry("api_call", f"Tool status requested: {len(tool_containers)} tools")
        return jsonify({"tools": tool_containers, "success": True})
    except Exception as e:
        logger.error(f"Error in tool status API: {e}")
        return jsonify({"tools": {}, "error": str(e), "success": False}), 500


@app.route('/api/containers/<container_name>/start', methods=['POST'])
def start_container(container_name):
    """Start a specific container"""
    try:
        result = container_monitor.start_container(container_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting container {container_name}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route('/api/containers/<container_name>/stop', methods=['POST'])
def stop_container(container_name):
    """Stop a specific container"""
    try:
        result = container_monitor.stop_container(container_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping container {container_name}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route('/api/containers/<container_name>/restart', methods=['POST'])
def restart_container(container_name):
    """Restart a specific container"""
    try:
        result = container_monitor.restart_container(container_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error restarting container {container_name}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


# ============================================================================
# API - Dashboard & System Info
# ============================================================================

@app.route('/api/dashboard/metrics')
def get_dashboard_metrics():
    """Get comprehensive dashboard metrics"""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        all_containers = container_monitor.get_all_container_status()
        tool_containers = container_monitor.get_tool_container_status()
        
        running_containers = len([c for c in all_containers.values() if c["status"] == "running"])
        stopped_containers = len([c for c in all_containers.values() if c["status"] == "stopped"])
        total_containers = len(all_containers)

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": round(disk.percent, 1),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            },
            "containers": {
                "total": total_containers,
                "running": running_containers,
                "stopped": stopped_containers,
                "health_percentage": round((running_containers / total_containers * 100) if total_containers > 0 else 0, 1)
            },
            "tools": {
                "total": len(tool_containers),
                "running": len([t for t in tool_containers.values() if t.get("status") == "running"]),
                "stopped": len([t for t in tool_containers.values() if t.get("status") == "stopped"])
            },
            "success": True
        }
        
        changelog_manager.add_entry("api_call", "Dashboard metrics requested")
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/server-info')
def get_server_info():
    """Get server information"""
    try:
        import socket
        
        hostname = socket.gethostname()
        server_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'localhost'))
        
        return jsonify({
            "hostname": hostname,
            "server_ip": server_ip,
            "port": PORT,
            "portal_url": f"http://{server_ip}:{PORT}",
            "timestamp": datetime.now().isoformat(),
            "success": True
        })
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/changelog')
def get_changelog():
    """Get changelog entries"""
    try:
        limit = request.args.get('limit', type=int)
        level = request.args.get('level')
        entries = changelog_manager.get_entries(limit=limit, level=level)
        return jsonify({"entries": entries, "success": True})
    except Exception as e:
        logger.error(f"Error in changelog API: {e}")
        return jsonify({"entries": [], "error": str(e), "success": False}), 500


@app.route('/api/changelog/stats')
def get_changelog_stats():
    """Get changelog statistics"""
    try:
        stats = changelog_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in changelog stats API: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        container_count = container_monitor.get_container_count()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "container_count": container_count,
            "success": True
        })
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/tools')
def get_tools():
    """Get available tools"""
    try:
        tools_list = []
        for tool_id, tool_info in BTPI_TOOLS.items():
            tool_data = {
                "id": tool_id,
                **tool_info
            }
            tools_list.append(tool_data)
        
        return jsonify({"tools": tools_list, "categories": TOOL_CATEGORIES, "success": True})
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        return jsonify({"tools": [], "error": str(e), "success": False}), 500


# ============================================================================
# API - Threat Intelligence (MISP)
# ============================================================================

def detect_ioc_type(value):
    """Auto-detect IOC type"""
    value = value.strip()
    
    for ioc_type, pattern in IOC_PATTERNS.items():
        if re.match(pattern, value):
            return ioc_type
    
    return "unknown"


@app.route('/api/misp/search', methods=['POST'])
def search_misp():
    """Search MISP for IOC"""
    try:
        data = request.get_json()
        ioc_value = data.get('value', '').strip()
        ioc_type = data.get('type', 'auto')
        
        if not ioc_value:
            return jsonify({"success": False, "error": "No IOC value provided"}), 400
        
        # Auto-detect type if needed
        if ioc_type == 'auto':
            ioc_type = detect_ioc_type(ioc_value)
        
        # Query MISP
        misp_url = MISP_CONFIG.get('host', 'http://misp-core')
        misp_port = MISP_CONFIG.get('port', 80)
        
        try:
            response = requests.post(
                f"{misp_url}:{misp_port if misp_port != 80 else ''}/attributes/restSearch",
                headers={'Authorization': 'test-api-key'},
                json={'value': ioc_value},
                timeout=MISP_CONFIG.get('api_timeout', 30),
                verify=False
            )
            
            results = response.json() if response.ok else {}
            
            changelog_manager.add_entry(
                "misp_search",
                f"IOC search performed: {ioc_type}={ioc_value}",
                level="info"
            )
            
            return jsonify({
                "success": True,
                "ioc_type": ioc_type,
                "value": ioc_value,
                "results": results.get('Attribute', []),
                "timestamp": datetime.now().isoformat()
            })
        except requests.exceptions.ConnectionError:
            return jsonify({
                "success": False,
                "error": "Cannot connect to MISP service",
                "ioc_type": ioc_type,
                "value": ioc_value
            }), 503
    except Exception as e:
        logger.error(f"Error searching MISP: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/misp/stats')
def get_misp_stats():
    """Get MISP statistics"""
    try:
        misp_url = MISP_CONFIG.get('host', 'http://misp-core')
        misp_port = MISP_CONFIG.get('port', 80)
        
        try:
            response = requests.get(
                f"{misp_url}:{misp_port if misp_port != 80 else ''}/stats",
                headers={'Authorization': 'test-api-key'},
                timeout=MISP_CONFIG.get('api_timeout', 30),
                verify=False
            )
            
            stats = response.json() if response.ok else {}
            
            return jsonify({
                "success": True,
                "events": stats.get('event_count', 0),
                "attributes": stats.get('attribute_count', 0),
                "feeds": len(MISP_CONFIG.get('feeds', [])),
                "timestamp": datetime.now().isoformat()
            })
        except requests.exceptions.ConnectionError:
            return jsonify({
                "success": False,
                "error": "Cannot connect to MISP service",
                "events": 0,
                "attributes": 0,
                "feeds": len(MISP_CONFIG.get('feeds', []))
            }), 503
    except Exception as e:
        logger.error(f"Error getting MISP stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/misp/feeds')
def get_misp_feeds():
    """Get configured threat feeds"""
    try:
        feeds = MISP_CONFIG.get('feeds', [])
        
        return jsonify({
            "success": True,
            "feeds": feeds,
            "count": len(feeds),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting MISP feeds: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/misp/sync-feeds', methods=['POST'])
def sync_misp_feeds():
    """Trigger MISP feed synchronization"""
    try:
        misp_url = MISP_CONFIG.get('host', 'http://misp-core')
        misp_port = MISP_CONFIG.get('port', 80)
        
        try:
            response = requests.post(
                f"{misp_url}:{misp_port if misp_port != 80 else ''}/feeds/fetchFeeds",
                headers={'Authorization': 'test-api-key'},
                timeout=MISP_CONFIG.get('api_timeout', 30),
                verify=False
            )
            
            changelog_manager.add_entry(
                "misp_feed_sync",
                "Manual feed synchronization triggered",
                level="info"
            )
            
            return jsonify({
                "success": response.ok,
                "message": "Feed synchronization initiated",
                "timestamp": datetime.now().isoformat()
            })
        except requests.exceptions.ConnectionError:
            return jsonify({
                "success": False,
                "error": "Cannot connect to MISP service"
            }), 503
    except Exception as e:
        logger.error(f"Error syncing MISP feeds: {e}")
        changelog_manager.add_entry("misp_feed_sync_error", f"Feed sync error: {e}", level="error")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 Starting BTPI-REACT Portal")
    logger.info("=" * 60)
    logger.info(f"🌐 Portal running on http://localhost:{PORT}")
    logger.info(f"📚 API endpoints available at http://localhost:{PORT}/api/")
    logger.info("=" * 60)

    try:
        # Create required directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)

        # Log initial startup
        changelog_manager.add_entry(
            "system_startup",
            "BTPI-REACT Portal started successfully",
            level="info"
        )

        # Start container monitoring in background
        def start_monitoring_async():
            try:
                container_monitor.start_monitoring()
            except Exception as e:
                logger.error(f"Error starting container monitoring: {e}")

        monitoring_thread = threading.Thread(target=start_monitoring_async, daemon=True)
        monitoring_thread.start()

        # Start Flask app
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)

    except KeyboardInterrupt:
        logger.info("Shutting down BTPI-REACT Portal...")
        changelog_manager.add_entry("system_shutdown", "Portal shut down gracefully")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        changelog_manager.add_entry("system_error", f"Server startup error: {e}", level="error")
        time.sleep(5)
        sys.exit(1)
