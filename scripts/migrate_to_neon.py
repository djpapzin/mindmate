#!/usr/bin/env python3
"""
MindMate Redis to Neon PostgreSQL Migration Script
Migrates conversation history and memory from Redis to Neon PostgreSQL
"""
import redis
import json
import os
import psycopg2
from datetime import datetime

# Source: Render Redis
RENDER_REDIS_URL = "redis://red-c2qgq9b321ks73c6p7g0:6379"

# Destination: Neon PostgreSQL
NEON_DB_URL = os.environ.get('NEON_MINDMATE_DB_URL')  # Set this env var

def get_neon_connection():
    """Connect to Neon PostgreSQL"""
    if not NEON_DB_URL:
        print("NEON_MINDMATE_DB_URL not set")
        return None
    
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        return conn
    except Exception as e:
        print(f"Failed to connect to Neon: {e}")
        return None

def init_neon_tables(conn):
    """Create tables in Neon for storing conversation data"""
    cursor = conn.cursor()
    
    # Create conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100),
            conversation_id VARCHAR(100) UNIQUE,
            messages JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create user memory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) UNIQUE,
            memory_content TEXT,
            embedding vector(384),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    print("✓ Neon tables initialized")

def migrate_redis_to_neon():
    """Main migration function"""
    # Connect to Redis
    r = redis.from_url(RENDER_REDIS_URL)
    try:
        r.ping()
        print("✓ Connected to Render Redis")
    except redis.ConnectionError as e:
        print(f"✗ Redis connection failed: {e}")
        return False
    
    # Connect to Neon
    conn = get_neon_connection()
    if not conn:
        print("Set NEON_MINDMATE_DB_URL environment variable first")
        return False
    
    print("✓ Connected to Neon PostgreSQL")
    init_neon_tables(conn)
    
    # Get all keys from Redis
    keys = r.keys("*")
    print(f"Migrating {len(keys)} keys...")
    
    cursor = conn.cursor()
    migrated_count = 0
    
    for key in keys:
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        
        # Parse key to determine type
        if key_str.startswith("conversation:"):
            user_id = key_str.split(":")[1] if ":" in key_str else "unknown"
            value = r.get(key)
            if value:
                messages = value.decode('utf-8') if isinstance(value, bytes) else value
                try:
                    messages_json = json.loads(messages)
                except:
                    messages_json = [{"content": messages}]
                
                cursor.execute("""
                    INSERT INTO conversations (user_id, conversation_id, messages)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (conversation_id) DO UPDATE SET
                        messages = EXCLUDED.messages,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, key_str, json.dumps(messages_json)))
                migrated_count += 1
        
        elif key_str.startswith("memory:"):
            user_id = key_str.split(":")[1] if ":" in key_str else "unknown"
            value = r.get(key)
            if value:
                memory_content = value.decode('utf-8') if isinstance(value, bytes) else value
                cursor.execute("""
                    INSERT INTO user_memory (user_id, memory_content)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        memory_content = EXCLUDED.memory_content,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, memory_content))
                migrated_count += 1
    
    conn.commit()
    print(f"✓ Migration complete: {migrated_count} records migrated")
    
    # Create local backup before clearing Redis
    backup_file = f"mindmate_pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    keys_data = {k: r.get(k) for k in keys}
    with open(backup_file, 'w') as f:
        json.dump({k.decode('utf-8') if isinstance(k, bytes) else k: 
                   v.decode('utf-8') if isinstance(v, bytes) else v 
                   for k, v in keys_data.items()}, f)
    print(f"✓ Local backup created: {backup_file}")
    
    cursor.close()
    conn.close()
    return True

if __name__ == "__main__":
    migrate_redis_to_neon()
