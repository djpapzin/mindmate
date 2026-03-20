#!/usr/bin/env python3
"""
MindMate Redis Backup Server
Deploy to Render as a simple service to backup Redis data
"""
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

# Get Redis URL from environment
REDIS_URL = os.environ.get('REDIS_URL', 'redis://red-d68oj2bh46gs73fi3j6g:6379')

@app.route('/')
def index():
    return '<a href="/backup">/backup</a> - <a href="/keys">/keys</a>'

@app.route('/keys')
def list_keys():
    r = redis.from_url(REDIS_URL)
    try:
        r.ping()
        keys = r.keys('*')
        return jsonify({
            'count': len(keys),
            'keys': [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/backup')
def backup():
    r = redis.from_url(REDIS_URL)
    try:
        r.ping()
        
        # Get all keys
        keys = r.keys('*')
        
        # Dump all data
        data = {}
        for key in keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            value = r.get(key)
            if value:
                data[key_str] = value.decode('utf-8') if isinstance(value, bytes) else value
        
        # Save to file
        filename = f"mindmate_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'keys_count': len(data),
            'data': data  # Return data in response
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/restore', methods=['POST'])
def restore():
    """Restore data from JSON backup"""
    r = redis.from_url(REDIS_URL)
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        for key, value in data.items():
            r.set(key, value)
        return jsonify({'success': True, 'keys_restored': len(data)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
