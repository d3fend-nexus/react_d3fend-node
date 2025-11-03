"""
YARA Scanning Service
REST API for YARA rule management and file scanning
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yara
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
YARA_DB_PATH = os.getenv('YARA_DB_PATH', '/data/yara')
RULES_DIR = os.path.join(YARA_DB_PATH, 'rules')
SAMPLES_DIR = os.path.join(YARA_DB_PATH, 'samples')
CACHE_DIR = os.path.join(YARA_DB_PATH, 'cache')

# Create directories
os.makedirs(RULES_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Store compiled rules in memory
compiled_rules = {}


class YaraManager:
    """YARA rule management and scanning"""
    
    @staticmethod
    def list_rules(category=None):
        """List all YARA rules"""
        rules = []
        
        for root, dirs, files in os.walk(RULES_DIR):
            for file in files:
                if file.endswith('.yar') or file.endswith('.yara'):
                    rel_path = os.path.relpath(os.path.join(root, file), RULES_DIR)
                    cat = rel_path.split(os.sep)[0] if os.sep in rel_path else 'custom'
                    
                    if category and cat != category:
                        continue
                    
                    rules.append({
                        'name': file,
                        'path': rel_path,
                        'category': cat,
                        'size': os.path.getsize(os.path.join(root, file))
                    })
        
        return rules
    
    @staticmethod
    def get_rule(rule_id):
        """Get specific rule content"""
        rule_path = os.path.join(RULES_DIR, rule_id)
        
        if not os.path.exists(rule_path):
            return None
        
        with open(rule_path, 'r') as f:
            content = f.read()
        
        return {
            'name': os.path.basename(rule_path),
            'path': rule_id,
            'content': content,
            'size': os.path.getsize(rule_path)
        }
    
    @staticmethod
    def create_rule(rule_id, content, category='custom'):
        """Create new YARA rule"""
        # Validate rule syntax
        try:
            yara.compile(source=content)
        except yara.Error as e:
            return {'error': f'Invalid YARA syntax: {str(e)}'}
        
        # Create category directory
        cat_dir = os.path.join(RULES_DIR, category)
        os.makedirs(cat_dir, exist_ok=True)
        
        # Save rule
        rule_path = os.path.join(cat_dir, rule_id)
        with open(rule_path, 'w') as f:
            f.write(content)
        
        return {
            'success': True,
            'path': f'{category}/{rule_id}',
            'message': 'Rule created successfully'
        }
    
    @staticmethod
    def update_rule(rule_id, content):
        """Update existing YARA rule"""
        rule_path = os.path.join(RULES_DIR, rule_id)
        
        if not os.path.exists(rule_path):
            return {'error': 'Rule not found'}
        
        # Validate syntax
        try:
            yara.compile(source=content)
        except yara.Error as e:
            return {'error': f'Invalid YARA syntax: {str(e)}'}
        
        # Backup old rule
        backup_path = f"{rule_path}.bak"
        if os.path.exists(rule_path):
            os.rename(rule_path, backup_path)
        
        # Write new rule
        with open(rule_path, 'w') as f:
            f.write(content)
        
        return {
            'success': True,
            'message': 'Rule updated successfully'
        }
    
    @staticmethod
    def delete_rule(rule_id):
        """Delete YARA rule"""
        rule_path = os.path.join(RULES_DIR, rule_id)
        
        if not os.path.exists(rule_path):
            return {'error': 'Rule not found'}
        
        os.remove(rule_path)
        
        return {
            'success': True,
            'message': 'Rule deleted successfully'
        }
    
    @staticmethod
    def validate_rule(content):
        """Validate YARA rule syntax"""
        try:
            yara.compile(source=content)
            return {
                'valid': True,
                'message': 'Valid YARA rule syntax'
            }
        except yara.Error as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def scan_file(file_path, rules_pattern='*'):
        """Scan file with YARA rules"""
        if not os.path.exists(file_path):
            return {'error': 'File not found'}
        
        results = []
        
        # Load and compile all matching rules
        for root, dirs, files in os.walk(RULES_DIR):
            for file in files:
                if file.endswith('.yar') or file.endswith('.yara'):
                    rule_file = os.path.join(root, file)
                    
                    try:
                        rules = yara.compile(filepath=rule_file)
                        matches = rules.match(file_path)
                        
                        if matches:
                            for match in matches:
                                results.append({
                                    'rule': match.rule,
                                    'file': match.strings,
                                    'tags': match.tags
                                })
                    except yara.Error:
                        continue
        
        return {
            'file': file_path,
            'scan_time': datetime.utcnow().isoformat(),
            'matches': len(results),
            'results': results
        }
    
    @staticmethod
    def get_statistics():
        """Get YARA service statistics"""
        rules = YaraManager.list_rules()
        
        stats = {
            'total_rules': len(rules),
            'categories': {},
            'total_size': 0
        }
        
        for rule in rules:
            cat = rule['category']
            if cat not in stats['categories']:
                stats['categories'][cat] = 0
            stats['categories'][cat] += 1
            stats['total_size'] += rule['size']
        
        return stats


# API Routes

@app.route('/api/yara/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'YARA Scanner',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/yara/rules', methods=['GET'])
def list_rules():
    """List all YARA rules"""
    category = request.args.get('category')
    rules = YaraManager.list_rules(category)
    
    return jsonify({
        'success': True,
        'count': len(rules),
        'rules': rules
    })


@app.route('/api/yara/rules/<path:rule_id>', methods=['GET'])
def get_rule(rule_id):
    """Get specific rule"""
    rule = YaraManager.get_rule(rule_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    return jsonify(rule)


@app.route('/api/yara/rules', methods=['POST'])
def create_rule():
    """Create new YARA rule"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'content' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    result = YaraManager.create_rule(
        data['name'],
        data['content'],
        data.get('category', 'custom')
    )
    
    if 'error' in result:
        return jsonify(result), 400
    
    return jsonify(result)


@app.route('/api/yara/rules/<path:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """Update existing rule"""
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content'}), 400
    
    result = YaraManager.update_rule(rule_id, data['content'])
    
    if 'error' in result:
        return jsonify(result), 400
    
    return jsonify(result)


@app.route('/api/yara/rules/<path:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """Delete rule"""
    result = YaraManager.delete_rule(rule_id)
    
    if 'error' in result:
        return jsonify(result), 404
    
    return jsonify(result)


@app.route('/api/yara/validate', methods=['POST'])
def validate_rule():
    """Validate YARA rule syntax"""
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content'}), 400
    
    result = YaraManager.validate_rule(data['content'])
    return jsonify(result)


@app.route('/api/yara/scan', methods=['POST'])
def scan_file():
    """Scan file with YARA rules"""
    data = request.get_json()
    
    if not data or 'file_path' not in data:
        return jsonify({'error': 'Missing file_path'}), 400
    
    result = YaraManager.scan_file(data['file_path'])
    
    if 'error' in result:
        return jsonify(result), 400
    
    return jsonify(result)


@app.route('/api/yara/stats', methods=['GET'])
def get_stats():
    """Get service statistics"""
    stats = YaraManager.get_statistics()
    return jsonify(stats)


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8001))
    app.run(host='0.0.0.0', port=port, debug=False)
