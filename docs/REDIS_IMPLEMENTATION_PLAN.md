# 🔄 Redis Vector Storage Implementation Plan

**Migration from In-Memory Storage to Redis with Vector Capabilities**

---

## 📋 Overview

This document outlines the complete migration from the current in-memory storage system to Redis with vector search capabilities for the MindMate Telegram bot.

**Current State:** In-memory dictionaries (`conversation_history`, `user_model_selection`)
**Target State:** Redis cloud storage with semantic search via embeddings

---

## 🎯 Implementation Goals

1. **Persistent Storage:** Replace in-memory data with Redis
2. **Vector Search:** Add semantic memory retrieval
3. **Performance:** Maintain sub-millisecond response times
4. **Scalability:** Support unlimited concurrent users
5. **Simplicity:** Keep code clean and maintainable

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEW ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Server                         │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │  /webhook   │  │  /health    │  │  /docs (Swagger)│   │  │
│  │  └──────┬──────┘  └─────────────┘  └─────────────────┘   │  │
│  │         │                                                 │  │
│  │         ▼                                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │           python-telegram-bot Library               │  │  │
│  │  │                                                     │  │  │
│  │  │   • Command Handlers (/start, /help, /clear, etc)   │  │  │
│  │  │   • Message Handler (regular messages)              │  │  │
│  │  │   • Personal Mode Logic                             │  │  │
│  │  └──────────────────────┬──────────────────────────────┘  │  │
│  │                         │                                 │  │
│  │                         ▼                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              Redis Storage (NEW)                    │  │  │
│  │  │                                                     │  │  │
│  │  │   • conversation_history: Redis Lists              │  │  │
│  │  │   • user_model_selection: Redis Hash                 │  │  │
│  │  │   • processed_messages: Redis Set                   │  │  │
│  │  │   • embeddings: Redis Vector Search                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REDIS CLOUD (Render)                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Redis Stack                            │  │
│  │                                                           │  │
│  │  • Redis Core (key-value storage)                         │  │
│  │  • RediSearch (vector search)                             │  │
│  │  • RedisJSON (document storage)                           │  │
│  │  • Auto-expiration (TTL)                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Dependencies

### New Requirements
```txt
redis==5.0.1
redisearch==2.0.0
sentence-transformers==2.2.2
numpy==1.24.3
```

### Updated requirements.txt
```txt
python-telegram-bot==21.0
openai
python-dotenv
fastapi
uvicorn[standard]
aiofiles>=23.0.0,<24.0.0
redis==5.0.1
sentence-transformers==2.2.2
numpy==1.24.3
```

---

## 🔧 Implementation Steps

### Phase 1: Redis Infrastructure Setup

#### 1.1 Create Redis Service on Render
```yaml
# render.yaml addition
services:
  - type: web
    name: mindmate
    # ... existing config ...
    
  - type: redis
    name: mindmate-redis
    plan: free
    ipAllowList: []  # Allow all connections from web service
```

#### 1.2 Environment Configuration
```bash
# .env additions
REDIS_URL=redis://mindmate-redis:6379
REDIS_PASSWORD=your_redis_password
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Phase 2: Database Module Creation

#### 2.1 Create `src/redis_db.py`
```python
"""
Redis Database Module
Redis connection and vector search for persistent conversation storage.
"""

import redis
import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class RedisDatabase:
    """Redis database manager for MindMate with vector search capabilities"""
    
    def __init__(self):
        self.redis_client = None
        self.embedding_model = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Initialize Redis connection and embedding model"""
        try:
            # Connect to Redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            
            # Load embedding model
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)
            
            # Create vector search index
            await self.create_vector_index()
            
            self.connected = True
            logger.info("✅ Redis connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    async def create_vector_index(self):
        """Create RediSearch vector index for semantic search"""
        try:
            # Drop existing index if any
            try:
                self.redis_client.ft("idx:conversations").dropindex()
            except:
                pass
            
            # Create new index
            self.redis_client.ft("idx:conversations").create_index(
                fields=[
                    redis.fields.TextField("user_id"),
                    redis.fields.TextField("content"),
                    redis.fields.VectorField(
                        "embedding",
                        "FLAT",
                        {
                            "TYPE": "FLOAT32",
                            "DIM": 384,  # Model dimension
                            "DISTANCE_METRIC": "COSINE"
                        }
                    )
                ]
            )
            logger.info("✅ Vector index created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create vector index: {e}")
```

#### 2.2 Core Storage Operations
```python
    async def store_message(self, user_id: int, role: str, content: str) -> str:
        """Store message in Redis with optional embedding"""
        message_id = f"msg:{user_id}:{int(datetime.now().timestamp())}"
        
        # Store message
        message_data = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in user's conversation list
        self.redis_client.lpush(f"conversation:{user_id}", json.dumps(message_data))
        
        # Keep only last 100 messages
        self.redis_client.ltrim(f"conversation:{user_id}", 0, 99)
        
        # Set expiration (30 days)
        self.redis_client.expire(f"conversation:{user_id}", 2592000)
        
        # Store embedding for semantic search
        if role == "assistant" or role == "user":
            embedding = self.embedding_model.encode(content).astype(np.float32).tobytes()
            self.redis_client.hset(message_id, mapping={
                "user_id": str(user_id),
                "content": content,
                "role": role,
                "embedding": embedding
            })
            self.redis_client.expire(message_id, 2592000)
        
        return message_id
    
    async def get_conversation_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get conversation history for a user"""
        messages = self.redis_client.lrange(f"conversation:{user_id}", 0, limit - 1)
        return [json.loads(msg) for msg in messages]
    
    async def semantic_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Search conversation history using semantic similarity"""
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query).astype(np.float32).tobytes()
            
            # Search using RediSearch
            result = self.redis_client.ft("idx:conversations").search(
                f"@user_id:{user_id}=>[KNN {limit} @embedding $query_vec]",
                query_params={"query_vec": query_embedding}
            )
            
            # Format results
            return [
                {
                    "content": doc.content,
                    "score": doc.score,
                    "role": json.loads(self.redis_client.hget(doc.id, "role") or "{}")
                }
                for doc in result.docs
            ]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
```

### Phase 3: Bot Integration

#### 3.1 Update `src/bot.py`
```python
# Add imports
from src.redis_db import RedisDatabase

# Replace global variables
# OLD:
# conversation_history: dict[int, list[dict[str, str]]] = {}
# user_model_selection: dict[int, str] = {}

# NEW:
redis_db = RedisDatabase()

# Update lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app, redis_db
    
    # Initialize Redis
    await redis_db.connect()
    
    # ... existing telegram setup ...
    
    yield
    
    # Cleanup
    if redis_db.connected:
        redis_db.redis_client.close()
```

#### 3.2 Update Message Handler
```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    message = update.message.text
    
    # Store user message
    await redis_db.store_message(user_id, "user", message)
    
    # Get conversation history
    history = await redis_db.get_conversation_history(user_id)
    
    # Optional: Semantic search for relevant context
    relevant_context = await redis_db.semantic_search(user_id, message, limit=3)
    
    # Build prompt with semantic context
    if relevant_context:
        context_str = "\n".join([f"Previous relevant: {ctx['content']}" for ctx in relevant_context])
        # Add to system prompt
    
    # ... rest of OpenAI call ...
    
    # Store assistant response
    await redis_db.store_message(user_id, "assistant", reply)
```

### Phase 4: Configuration Updates

#### 4.1 Update `render.yaml`
```yaml
services:
  - type: web
    name: mindmate
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    plan: free
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: REDIS_URL
        value: redis://mindmate-redis:6379
        sync: false
      - key: EMBEDDING_MODEL
        value: all-MiniLM-L6-v2
        sync: false

  - type: redis
    name: mindmate-redis
    plan: free
    ipAllowList: []
```

---

## 🧪 Testing Strategy

### Phase 1: Unit Tests
```python
# tests/test_redis_db.py
import pytest
from src.redis_db import RedisDatabase

@pytest.mark.asyncio
async def test_redis_connection():
    db = RedisDatabase()
    assert await db.connect() == True

@pytest.mark.asyncio
async def test_message_storage():
    db = RedisDatabase()
    await db.connect()
    
    message_id = await db.store_message(123, "user", "Hello")
    assert message_id is not None
    
    history = await db.get_conversation_history(123)
    assert len(history) == 1
    assert history[0]["content"] == "Hello"
```

### Phase 2: Integration Tests
```python
# tests/test_bot_integration.py
async def test_conversation_flow():
    # Test full conversation flow with Redis
    # Verify semantic search works
    # Check message persistence
```

### Phase 3: Load Testing
```python
# Test with 100+ concurrent users
# Verify response times < 100ms
# Check memory usage stays stable
```

---

## 📊 Performance Expectations

### Metrics
- **Message Storage:** < 1ms
- **History Retrieval:** < 5ms
- **Semantic Search:** < 50ms
- **Memory Usage:** ~1KB per message
- **Concurrent Users:** 1000+

### Scaling
- **Redis Free Tier:** 25MB memory, 10k connections
- **Redis Pro Tier:** 100MB+ memory, unlimited connections
- **Auto-expiration:** Prevents memory bloat

---

## 🔄 Migration Timeline

### Week 1: Infrastructure
- [ ] Set up Redis on Render
- [ ] Update environment configuration
- [ ] Create `src/redis_db.py`

### Week 2: Integration
- [ ] Update `src/bot.py` with Redis integration
- [ ] Implement semantic search
- [ ] Add error handling and fallbacks

### Week 3: Testing
- [ ] Unit tests for Redis operations
- [ ] Integration tests for bot flow
- [ ] Performance testing

### Week 4: Deployment
- [ ] Deploy to staging environment
- [ ] Monitor performance
- [ ] Deploy to production

---

## 🚨 Risk Mitigation

### Technical Risks
1. **Redis Connection Failure**
   - **Mitigation:** Graceful fallback to in-memory storage
   - **Implementation:** Connection health checks

2. **Memory Overflow**
   - **Mitigation:** TTL auto-expiration, message limits
   - **Implementation:** Redis memory monitoring

3. **Semantic Search Performance**
   - **Mitigation:** Fallback to text search if slow
   - **Implementation:** Timeout handling

### Operational Risks
1. **Data Loss**
   - **Mitigation:** Redis persistence configuration
   - **Implementation:** Regular backups

2. **Downtime**
   - **Mitigation:** Gradual rollout, rollback plan
   - **Implementation:** Feature flags

---

## 📚 Documentation Updates

### Files to Update
1. **ARCHITECTURE.md** - Update diagrams
2. **PROJECT_STRUCTURE.md** - Add Redis module
3. **ROADMAP.md** - Mark PostgreSQL as deprecated
4. **README.md** - Add Redis setup instructions

### New Documentation
1. **REDIS_IMPLEMENTATION_PLAN.md** (this file)
2. **REDIS_TROUBLESHOOTING.md**
3. **SEMANTIC_SEARCH_GUIDE.md**

---

## 🎯 Success Criteria

### Functional
- [ ] All conversations persist across restarts
- [ ] Semantic search finds relevant past messages
- [ ] Performance < 100ms for all operations
- [ ] Zero data loss during migration

### Technical
- [ ] 99.9% uptime maintained
- [ ] Memory usage stable under load
- [ ] Error rates < 0.1%
- [ ] Backup/restore procedures tested

### User Experience
- [ ] Faster response times
- [ ] Better contextual responses
- [ ] Seamless migration (no user impact)

---

## 📈 Future Enhancements

### Phase 2 Features
- **Conversation Summarization:** AI-generated session summaries
- **User Profiles:** Persistent preferences and context
- **Analytics:** Conversation insights and patterns

### Phase 3 Features
- **Multi-modal Search:** Image/document semantic search
- **Cross-session Memory:** Long-term relationship building
- **Personalization:** Adaptive response styles

---

**Last Updated:** February 2026
**Author:** DJ Papzin
**Status:** Planning Phase
