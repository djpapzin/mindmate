# 🗺️ MindMate Roadmap

This roadmap is aligned to the current implementation state as of 2026-03-22.

## Current state

### ✅ Already active
- FastAPI + python-telegram-bot runtime
- PostgreSQL-backed persistent storage via `src/postgres_db.py`
- In-memory fallback when PostgreSQL is unavailable
- Personal Mode
- Voice handling
- Daily heartbeat scheduler
- Explicit/limited live web lookup support

### ⚠️ Important implementation truth
- MindMate is currently standardized on **PostgreSQL** as the official active storage path.
- Redis is **legacy** and not the primary runtime datastore.
- The current Postgres `semantic_search(...)` implementation is actually **keyword-based text matching**, not true vector semantic retrieval.

## Near-term priorities

### 1. Stabilize current PostgreSQL path
- improve migrations/schema discipline
- add focused tests around startup fallback behavior
- keep docs aligned with runtime truth

### 2. Better memory retrieval
- if needed, add real embedding/vector retrieval on PostgreSQL intentionally
- do not describe this as complete until a true vector path exists in production

### 3. Product iteration
- improve daily check-ins and feedback review workflows
- continue refining Personal Mode support
- expand operational monitoring and deployment hygiene

## Deferred / historical items

### Redis vector memory
This was part of an earlier implementation direction and historical planning, but it is **not** the current official path.
Any future Redis work should be treated as a new deliberate decision, not assumed ongoing architecture.

### WhatsApp / broader platform expansion
Still possible, but secondary to keeping the existing Telegram + PostgreSQL runtime stable.

## Notes

If true semantic retrieval becomes a priority again, the roadmap should distinguish clearly between:
- keyword search now
- vector search later

**Last Updated:** 2026-03-22
