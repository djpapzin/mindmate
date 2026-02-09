"""
MindMate Database Module
PostgreSQL connection and data models for persistent conversation storage.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import asyncpg
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# =============================================================================
# Database Configuration
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.warning("DATABASE_URL not configured - using in-memory fallback")

# =============================================================================
# Pydantic Models
# =============================================================================

class User(BaseModel):
    """User profile model"""
    telegram_id: int
    name: Optional[str] = None
    focus_areas: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    """Message model for conversation history"""
    id: Optional[int] = None
    user_id: int
    role: str  # 'user', 'assistant', 'system'
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseModel):
    """Conversation session model"""
    id: Optional[int] = None
    user_id: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    summary: Optional[str] = None

# =============================================================================
# Database Connection
# =============================================================================

class Database:
    """PostgreSQL database manager for MindMate"""
    
    def __init__(self):
        self.pool = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Initialize database connection pool"""
        if not DATABASE_URL:
            logger.warning("No DATABASE_URL - running in memory-only mode")
            return False
            
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            self.connected = True
            logger.info("✅ PostgreSQL connected successfully")
            await self.create_tables()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            logger.info("🔄 Falling back to in-memory storage")
            return False
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.connected = False
            logger.info("Database connection closed")
    
    async def create_tables(self):
        """Create database tables if they don't exist"""
        if not self.connected:
            return
            
        # Create users table
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                name TEXT,
                focus_areas TEXT[],
                preferences JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create conversations table
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                summary TEXT
            )
        """)
        
        # Create messages table
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                conversation_id INTEGER,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        await self.pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_user_created 
            ON messages(user_id, created_at DESC)
        """)
        
        await self.pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user 
            ON conversations(user_id, last_message_at DESC)
        """)
        
        logger.info("✅ Database tables ready")
    
    # =============================================================================
    # User Management
    # =============================================================================
    
    async def get_or_create_user(self, telegram_id: int, name: str = None) -> User:
        """Get existing user or create new one"""
        if not self.connected:
            return User(telegram_id=telegram_id, name=name)
            
        # Try to get existing user
        row = await self.pool.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            telegram_id
        )
        
        if row:
            user = User(
                telegram_id=row['telegram_id'],
                name=row['name'],
                focus_areas=row['focus_areas'] or [],
                preferences=row['preferences'] or {},
                created_at=row['created_at'],
                last_active=row['last_active']
            )
            
            # Update last active time
            await self.pool.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE telegram_id = $1",
                telegram_id
            )
            return user
        else:
            # Create new user
            user = User(telegram_id=telegram_id, name=name)
            await self.pool.execute(
                """
                INSERT INTO users (telegram_id, name, focus_areas, preferences)
                VALUES ($1, $2, $3, $4)
                """,
                user.telegram_id, user.name, user.focus_areas, user.preferences
            )
            logger.info(f"Created new user: {telegram_id}")
            return user
    
    async def update_user_preferences(self, telegram_id: int, preferences: Dict[str, Any]):
        """Update user preferences"""
        if not self.connected:
            return
            
        await self.pool.execute(
            "UPDATE users SET preferences = $1, last_active = CURRENT_TIMESTAMP WHERE telegram_id = $2",
            preferences, telegram_id
        )
    
    # =============================================================================
    # Conversation Management
    # =============================================================================
    
    async def get_or_create_conversation(self, user_id: int) -> Conversation:
        """Get active conversation or create new one"""
        if not self.connected:
            return Conversation(user_id=user_id)
            
        # Get most recent conversation (within last 24 hours)
        row = await self.pool.fetchrow("""
            SELECT * FROM conversations 
            WHERE user_id = $1 AND last_message_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            ORDER BY last_message_at DESC LIMIT 1
        """, user_id)
        
        if row:
            return Conversation(
                id=row['id'],
                user_id=row['user_id'],
                started_at=row['started_at'],
                last_message_at=row['last_message_at'],
                message_count=row['message_count'],
                summary=row['summary']
            )
        else:
            # Create new conversation
            conv = Conversation(user_id=user_id)
            await self.pool.execute(
                """
                INSERT INTO conversations (user_id, started_at, last_message_at, message_count)
                VALUES ($1, $2, $3, $4)
                """,
                conv.user_id, conv.started_at, conv.last_message_at, conv.message_count
            )
            logger.info(f"Created new conversation for user {user_id}")
            return conv
    
    async def add_message(self, user_id: int, conversation_id: int, role: str, content: str) -> Message:
        """Add a message to conversation"""
        if not self.connected:
            return Message(user_id=user_id, role=role, content=content)
            
        message = Message(user_id=user_id, role=role, content=content)
        
        # Insert message
        message_id = await self.pool.fetchval(
            """
            INSERT INTO messages (user_id, conversation_id, role, content)
            VALUES ($1, $2, $3, $4) RETURNING id
            """,
            user_id, conversation_id, role, content
        )
        message.id = message_id
        
        # Update conversation stats (if conversation_id is not None)
        if conversation_id:
            await self.pool.execute(
                """
                UPDATE conversations 
                SET message_count = message_count + 1, 
                    last_message_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                conversation_id
            )
        
        return message
    
    async def get_conversation_history(self, user_id: int, limit: int = 50) -> List[Message]:
        """Get conversation history for a user"""
        if not self.connected:
            return []
            
        rows = await self.pool.fetch("""
            SELECT m.* FROM messages m
            WHERE m.user_id = $1
            ORDER BY m.created_at DESC
            LIMIT $2
        """, user_id, limit)
        
        return [
            Message(
                id=row['id'],
                user_id=row['user_id'],
                role=row['role'],
                content=row['content'],
                created_at=row['created_at']
            )
            for row in rows
        ]
    
    async def get_recent_messages(self, user_id: int, limit: int = 10) -> List[Message]:
        """Get most recent messages for context"""
        if not self.connected:
            return []
            
        rows = await self.pool.fetch("""
            SELECT m.* FROM messages m
            WHERE m.user_id = $1
            ORDER BY m.created_at DESC
            LIMIT $2
        """, user_id, limit)
        
        messages = [
            Message(
                id=row['id'],
                user_id=row['user_id'],
                role=row['role'],
                content=row['content'],
                created_at=row['created_at']
            )
            for row in rows
        ]
        
        # Return in chronological order (oldest first)
        return list(reversed(messages))

# =============================================================================
# Global Database Instance
# =============================================================================

db = Database()

# =============================================================================
# Graceful Fallback Functions (for when DB is unavailable)
# =============================================================================

# In-memory fallback storage
_memory_users: Dict[int, User] = {}
_memory_messages: Dict[int, List[Message]] = {}

async def get_or_create_user_fallback(telegram_id: int, name: str = None) -> User:
    """Fallback user management using in-memory storage"""
    if telegram_id not in _memory_users:
        _memory_users[telegram_id] = User(telegram_id=telegram_id, name=name)
    return _memory_users[telegram_id]

async def get_recent_messages_fallback(user_id: int, limit: int = 10) -> List[Message]:
    """Fallback message retrieval using in-memory storage"""
    messages = _memory_messages.get(user_id, [])
    return messages[-limit:] if len(messages) > limit else messages

async def add_message_fallback(user_id: int, conversation_id: int, role: str, content: str) -> Message:
    """Fallback message storage using in-memory storage"""
    if user_id not in _memory_messages:
        _memory_messages[user_id] = []
    
    message = Message(user_id=user_id, role=role, content=content)
    _memory_messages[user_id].append(message)
    return message

# =============================================================================
# Public API Functions (with fallback)
# =============================================================================

async def init_database():
    """Initialize database connection"""
    success = await db.connect()
    if success:
        logger.info("🗄️ PostgreSQL initialized successfully")
    else:
        logger.warning("🧠 Using in-memory fallback storage")

async def get_or_create_user(telegram_id: int, name: str = None) -> User:
    """Get or create user with fallback"""
    if db.connected:
        return await db.get_or_create_user(telegram_id, name)
    else:
        return await get_or_create_user_fallback(telegram_id, name)

async def get_recent_messages(user_id: int, limit: int = 10) -> List[Message]:
    """Get recent messages with fallback"""
    if db.connected:
        return await db.get_recent_messages(user_id, limit)
    else:
        return await get_recent_messages_fallback(user_id, limit)

async def add_message_to_conversation(user_id: int, role: str, content: str) -> Message:
    """Add message with fallback"""
    if db.connected:
        # Get or create conversation first
        conversations = await db.pool.fetch("""
            SELECT * FROM conversations 
            WHERE user_id = $1 
            ORDER BY last_message_at DESC LIMIT 1
        """, user_id)
        
        if conversations:
            conv_id = conversations[0]['id']
        else:
            # Create new conversation
            conv_id = await db.pool.fetchval("""
                INSERT INTO conversations (user_id, started_at, last_message_at, message_count)
                VALUES ($1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
                RETURNING id
            """, user_id)
        
        # Add message
        message_id = await db.pool.fetchval("""
            INSERT INTO messages (user_id, conversation_id, role, content)
            VALUES ($1, $2, $3, $4) RETURNING id
        """, user_id, conv_id, role, content)
        
        # Update conversation count
        await db.pool.execute("""
            UPDATE conversations 
            SET message_count = message_count + 1, 
                last_message_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """, conv_id)
        
        return Message(
            id=message_id,
            user_id=user_id,
            role=role,
            content=content
        )
    else:
        return await add_message_fallback(user_id, None, role, content)
