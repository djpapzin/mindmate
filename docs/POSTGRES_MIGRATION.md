# MindMate PostgreSQL Migration Guide

## Overview

MindMate has migrated from **Redis** to **PostgreSQL** for persistent storage. This guide covers the migration and usage.

## Why PostgreSQL?

- **Free**: Uses Neon free tier (no billing required)
- **Reliable**: Persistent storage, no data loss on restart
- **Accessible**: Works from anywhere (not internal-only like Render Redis)
- **Same infrastructure**: Reuses existing PapzinAI Task Tracker Neon DB

## Architecture

```
┌─────────────────────────────────────┐
│         MindMate Bot               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      postgres_db.py                 │
│  (PostgreSQL Storage)               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Neon PostgreSQL                 │
│   (Free tier, 256MB)                │
└─────────────────────────────────────┘
```

## Database Schema

### Tables

1. **mindmate_messages** - Stores conversation messages
   - `id` - Primary key
   - `user_id` - Telegram user ID
   - `conversation_id` - Conversation identifier
   - `role` - 'user' or 'assistant'
   - `content` - Message text
   - `message_id` - Telegram message ID
   - `timestamp` - Message timestamp

2. **mindmate_user_preferences** - Stores user settings
   - `user_id` - Telegram user ID
   - `pref_key` - Preference key
   - `pref_value` - Preference value (JSON)

## Setup

### 1. Environment Variables

```bash
# Option 1: Use existing Neon DB (shared with Task Tracker)
NEON_MINDMATE_DB_URL=postgresql://neondb_owner:password@ep-xxx.us-west-2.aws.neon.tech:5432/neondb?sslmode=require

# Option 2: Create separate database in Neon
# Go to https://neon.tech → Create new project → MindMate
```

### 2. Update bot.py

Replace Redis import:

```python
# Before (Redis)
from redis_db import RedisDatabase

# After (PostgreSQL)
from postgres_db import PostgresDatabase
```

Initialize:

```python
# Before
db = RedisDatabase(redis_url)

# After
db = PostgresDatabase(db_url)
```

## API Reference

### Methods

| Method | Description |
|--------|-------------|
| `await db.connect()` | Initialize DB and create tables |
| `await db.store_message(message)` | Store a message |
| `await db.get_conversation_history(user_id, limit)` | Get chat history |
| `await db.semantic_search(user_id, query)` | Search messages |
| `await db.store_user_preference(user_id, key, value)` | Save preference |
| `await db.get_user_preference(user_id, key)` | Get preference |
| `await db.clear_conversation(user_id)` | Clear history |
| `await db.get_stats()` | Get DB statistics |

### Message Structure

```python
from datetime import datetime

message = Message(
    user_id=123456789,
    content="Hello",
    role="user",
    timestamp=datetime.now(),
    message_id="msg_123"
)
```

## Migration from Redis

If you have existing Redis data:

1. Run the backup script (see `scripts/backup_redis.py`)
2. Export to JSON
3. Import to PostgreSQL using the new storage

Note: Old conversation history in Redis may be inaccessible due to Render suspension. Fresh start is recommended.

## Fallback

If PostgreSQL is unavailable, the bot falls back to in-memory storage:

```python
from postgres_db import InMemoryDatabase

db = InMemoryDatabase()  # Works without DB connection
```

## Troubleshooting

### Connection Error
```
could not translate host name
```
- Check DATABASE_URL is correct
- Verify Neon project is active

### SSL Error
```
sslmode not supported
```
- Ensure `?sslmode=require` is in connection string

## Files

- `src/postgres_db.py` - Main PostgreSQL storage module
- `src/redis_db.py` - Old Redis module (deprecated)
- `scripts/backup_redis.py` - Redis backup script
- `scripts/migrate_to_neon.py` - Migration script

## Status

✅ **Migrated** - PostgreSQL storage is ready for use

---

Last updated: 2026-03-20
