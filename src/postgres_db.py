"""
PostgreSQL Database Module for MindMate Bot
Handles persistent storage - replaces Redis
"""
import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Message data structure"""
    user_id: int
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime
    message_id: str

class PostgresDatabase:
    """PostgreSQL database manager - drop-in replacement for Redis"""
    
    def __init__(self, db_url: str = None, openai_client=None):
        self.db_url = db_url or os.environ.get('NEON_MINDMATE_DB_URL') or os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise ValueError("Database URL not set. Set NEON_MINDMATE_DB_URL or DATABASE_URL")
        
        self.openai_client = openai_client
        self.pool = None
        self.env = os.getenv("ENV", "production")
        self.prefix = f"{self.env}:" if self.env != "production" else ""
        
    def _get_pool(self):
        if not self.pool:
            self.pool = ThreadedConnectionPool(1, 5, self.db_url)
        return self.pool
    
    async def connect(self):
        """Initialize database and create tables"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()
        
        try:
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_messages (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    conversation_id VARCHAR(200) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    message_id VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_user_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    pref_key VARCHAR(100) NOT NULL,
                    pref_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, pref_key)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON mindmate_messages(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON mindmate_messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prefs_user ON mindmate_user_preferences(user_id)")
            
            conn.commit()
            logger.info("✅ PostgreSQL connected successfully")
        finally:
            pool.putconn(conn)
    
    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"
    
    async def store_message(self, message: Message):
        """Store a message in the database"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()
        
        try:
            conversation_id = self._key(f"conversation:{message.user_id}")
            cursor.execute("""
                INSERT INTO mindmate_messages (user_id, conversation_id, role, content, message_id, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (message.user_id, conversation_id, message.role, message.content, message.message_id, message.timestamp))
            conn.commit()
        finally:
            pool.putconn(conn)
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get conversation history for a user"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            conversation_id = self._key(f"conversation:{user_id}")
            cursor.execute("""
                SELECT role, content, message_id, timestamp 
                FROM mindmate_messages 
                WHERE user_id = %s AND conversation_id = %s
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (user_id, conversation_id, limit))
            
            results = cursor.fetchall()
            # Return in chronological order (oldest first)
            return list(reversed([dict(r) for r in results]))
        finally:
            pool.putconn(conn)
    
    async def semantic_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Basic keyword search - vector search requires embedding setup"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            conversation_id = self._key(f"conversation:{user_id}")
            cursor.execute("""
                SELECT role, content, message_id, timestamp 
                FROM mindmate_messages 
                WHERE user_id = %s AND conversation_id = %s AND content ILIKE %s
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (user_id, conversation_id, f"%{query}%", limit))
            
            return [dict(r) for r in cursor.fetchall()]
        finally:
            pool.putconn(conn)
    
    async def store_user_preference(self, user_id: int, key: str, value: Any):
        """Store user preference"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO mindmate_user_preferences (user_id, pref_key, pref_value, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, pref_key) DO UPDATE SET
                    pref_value = EXCLUDED.pref_value,
                    updated_at = EXCLUDED.updated_at
            """, (user_id, key, json.dumps(value), datetime.now()))
            conn.commit()
        finally:
            pool.putconn(conn)
    
    async def get_user_preference(self, user_id: int, key: str) -> Optional[Any]:
        """Get user preference"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT pref_value FROM mindmate_user_preferences 
                WHERE user_id = %s AND pref_key = %s
            """, (user_id, key))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
        finally:
            pool.putconn(conn)
    
    async def clear_conversation(self, user_id: int):
        """Clear conversation history"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()
        
        try:
            conversation_id = self._key(f"conversation:{user_id}")
            cursor.execute("""
                DELETE FROM mindmate_messages 
                WHERE user_id = %s AND conversation_id = %s
            """, (user_id, conversation_id))
            conn.commit()
        finally:
            pool.putconn(conn)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database stats"""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM mindmate_messages")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM mindmate_messages")
            total_users = cursor.fetchone()[0]
            
            return {
                "total_messages": total_messages,
                "total_users": total_users,
                "storage": "postgresql"
            }
        finally:
            pool.putconn(conn)
    
    async def close(self):
        """Close database pool"""
        if self.pool:
            self.pool.closeall()


# Fallback for when DB is unavailable
class InMemoryDatabase:
    """Simple in-memory fallback"""
    
    def __init__(self, db_url=None, openai_client=None):
        self.messages = {}
        self.preferences = {}
    
    async def connect(self):
        logger.info("✅ Using in-memory storage (fallback)")
    
    async def store_message(self, message: Message):
        key = f"{message.user_id}"
        if key not in self.messages:
            self.messages[key] = []
        self.messages[key].append(asdict(message))
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self.messages.get(str(user_id), [])[-limit:]
    
    async def store_user_preference(self, user_id: int, key: str, value: Any):
        k = f"{user_id}:{key}"
        self.preferences[k] = value
    
    async def get_user_preference(self, user_id: int, key: str) -> Optional[Any]:
        return self.preferences.get(f"{user_id}:{key}")
    
    async def clear_conversation(self, user_id: int):
        self.messages.pop(str(user_id), None)
    
    async def get_stats(self):
        return {"storage": "memory", "messages": len(self.messages)}
    
    async def close(self):
        pass
