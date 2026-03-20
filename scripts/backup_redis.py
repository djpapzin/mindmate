#!/usr/bin/env python3
"""
MindMate Redis Backup Script
Dumps all data from Render Redis to local JSON backup
"""
import redis
import json
import os
from datetime import datetime

# Render Redis connection (from render.yaml)
RENDER_REDIS_URL = "redis://red-c2qgq9b321ks73c6p7g0:6379"

# Local backup settings
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")
BACKUP_FILE = os.path.join(BACKUP_DIR, f"mindmate_redis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

def backup_redis():
    # Create backup directory
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Connect to Render Redis
    r = redis.from_url(RENDER_REDIS_URL)
    
    try:
        # Test connection
        r.ping()
        print("✓ Connected to Render Redis")
    except redis.ConnectionError as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    # Get all keys
    keys = r.keys("*")
    print(f"Found {len(keys)} keys")
    
    # Dump all data
    backup_data = {}
    for key in keys:
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        value = r.get(key)
        if value:
            backup_data[key_str] = value.decode('utf-8') if isinstance(value, bytes) else value
        else:
            # Try list type
            list_val = r.lrange(key, 0, -1)
            if list_val:
                backup_data[key_str] = [v.decode('utf-8') if isinstance(v, bytes) else v for v in list_val]
    
    # Save to JSON
    with open(BACKUP_FILE, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✓ Backup saved to: {BACKUP_FILE}")
    print(f"✓ Backed up {len(backup_data)} keys")
    
    return True

if __name__ == "__main__":
    backup_redis()
