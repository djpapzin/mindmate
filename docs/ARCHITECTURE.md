# 🏗️ MindMate Architecture

Current architecture, aligned to the active runtime code.

---

## High-level runtime flow

```
Telegram user
   ↓
Telegram API
   ↓
FastAPI + python-telegram-bot handlers (`src/bot.py`)
   ↓
OpenAI responses / voice / optional explicit web lookup
   ↓
PostgreSQL persistence (`src/postgres_db.py`)
   ↓
In-memory fallback only if PostgreSQL is unavailable
```

---

## Active storage path

- **Primary persistent store:** PostgreSQL
- **Active implementation:** `src/postgres_db.py`
- **Configured from:** `NEON_MINDMATE_DB_URL` or `DATABASE_URL`
- **Fallback mode:** in-memory storage inside `src/postgres_db.py` when PostgreSQL cannot be reached
- **Not active runtime:** `src/redis_db.py`

### Important truth about retrieval

MindMate currently does **not** perform true vector semantic retrieval in production.
The `semantic_search(...)` method in `src/postgres_db.py` is currently a **basic keyword search** using `ILIKE` over stored message content.

That means:
- it can find direct text matches reasonably well
- it does **not** use embeddings or pgvector in the active path
- docs should describe it as keyword-based memory search, not semantic memory

---

## Startup behavior

At startup, `src/bot.py`:

1. loads project-local environment variables
2. reads `NEON_MINDMATE_DB_URL` or `DATABASE_URL`
3. tries to connect `PostgresDatabase(...)`
4. falls back to `InMemoryDatabase()` if the connection fails
5. starts the Telegram bot in webhook or polling mode

This keeps runtime behavior conservative and resilient without depending on Redis.

---

## Legacy modules retained on purpose

### `src/redis_db.py`
Retained as a **legacy/deprecated implementation reference** only.
It is not the current primary store and should not be described as production-active.

### `src/storage/postgres.py`
Retained as a **legacy/experimental duplicate helper**.
It is not wired into the current runtime path; `src/postgres_db.py` is the authoritative implementation.

---

## Deployment truth

- Render runs the Python worker process
- Persistent storage should come from PostgreSQL environment configuration
- Redis provisioning is no longer required for the active runtime path

---

**Last Updated:** 2026-03-22
