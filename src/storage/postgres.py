#!/usr/bin/env python3
"""
MindMate PostgreSQL Storage
Replaces Redis with PostgreSQL for persistence
"""
import os
import json
from datetime import datetime
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

class PostgresStorage:
    """PostgreSQL storage for MindMate conversations and memory"""
    
    def __init__(self, db_url=None):
        self.db_url = db_url or os.environ.get('DATABASE_URL') or os.environ.get('NEON_MINDMATE_DB_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL or NEON_MINDMATE_DB_URL must be set")
        self.pool = None
    
    def init_db(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_conversations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100),
                    conversation_id VARCHAR(200) UNIQUE NOT NULL,
                    messages JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_user_memory (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) UNIQUE NOT NULL,
                    memory_content TEXT,
                    embedding JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    session_id VARCHAR(200) UNIQUE NOT NULL,
                    mode VARCHAR(20) DEFAULT 'standard',
                    model VARCHAR(50) DEFAULT 'gpt-4',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON mindmate_conversations(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_user_id ON mindmate_user_memory(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON mindmate_sessions(user_id)")
            
            conn.commit()
            print("✓ PostgreSQL tables initialized")
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        if not self.pool:
            self.pool = ThreadedConnectionPool(1, 5, self.db_url)
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    # Conversations
    def get_conversation(self, user_id, conversation_id):
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM mindmate_conversations 
                WHERE user_id = %s AND conversation_id = %s
            """, (user_id, conversation_id))
            result = cursor.fetchone()
            if result:
                result['messages'] = json.dumps(result['messages']) if isinstance(result['messages'], list) else result['messages']
            return result
    
    def save_conversation(self, user_id, conversation_id, messages):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mindmate_conversations (user_id, conversation_id, messages, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (conversation_id) DO UPDATE SET
                    messages = EXCLUDED.messages,
                    updated_at = EXCLUDED.updated_at
            """, (user_id, conversation_id, json.dumps(messages), datetime.now()))
            conn.commit()
    
    def get_user_conversations(self, user_id, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT conversation_id, updated_at 
                FROM mindmate_conversations 
                WHERE user_id = %s 
                ORDER BY updated_at DESC 
                LIMIT %s
            """, (user_id, limit))
            return cursor.fetchall()
    
    # User Memory
    def get_user_memory(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM mindmate_user_memory WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                result['embedding'] = json.dumps(result['embedding']) if result['embedding'] else None
            return result
    
    def save_user_memory(self, user_id, memory_content, embedding=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mindmate_user_memory (user_id, memory_content, embedding, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    memory_content = EXCLUDED.memory_content,
                    embedding = EXCLUDED.embedding,
                    updated_at = EXCLUDED.updated_at
            """, (user_id, memory_content, json.dumps(embedding) if embedding else None, datetime.now()))
            conn.commit()
    
    # Sessions
    def get_session(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM mindmate_sessions 
                WHERE user_id = %s 
                ORDER BY last_active DESC 
                LIMIT 1
            """, (user_id,))
            return cursor.fetchone()
    
    def save_session(self, user_id, session_id, mode='standard', model='gpt-4'):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mindmate_sessions (user_id, session_id, mode, model, last_active)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    mode = EXCLUDED.mode,
                    model = EXCLUDED.model,
                    last_active = EXCLUDED.last_active
            """, (user_id, session_id, mode, model, datetime.now()))
            conn.commit()


if __name__ == "__main__":
    import sys
    storage = PostgresStorage()
    storage.init_db()
    print("✓ MindMate PostgreSQL storage ready")
