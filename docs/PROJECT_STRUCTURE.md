# 📁 MindMate Project Structure

This file reflects the current, conservative runtime truth.

## Top-level overview

```
mindmate/
├── bot.py                       # Compatibility entrypoint that loads src/bot.py
├── src/
│   ├── bot.py                   # Main FastAPI + Telegram bot runtime
│   ├── postgres_db.py           # Active PostgreSQL storage implementation
│   ├── redis_db.py              # Legacy/deprecated Redis implementation retained for reference
│   ├── storage/
│   │   └── postgres.py          # Legacy/experimental duplicate Postgres helper (not runtime-active)
│   └── web_search.py            # Explicit Brave web lookup helper
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_STRUCTURE.md
│   ├── ROADMAP.md
│   └── REDIS_IMPLEMENTATION_PLAN.md
├── scripts/                     # Utility and migration scripts
├── research/                    # Research notes and model findings
├── render.yaml                  # Render deployment definition
├── .env.example                 # Example environment configuration
└── README.md                    # Main project overview
```

## Storage-related files

### `src/postgres_db.py`
- **Status:** active
- **Purpose:** primary persistent storage layer
- **Runtime role:** stores conversation history, preferences, and feedback in PostgreSQL
- **Fallback:** exposes the in-memory fallback used when PostgreSQL is unavailable

### `src/redis_db.py`
- **Status:** legacy / deprecated
- **Purpose:** historical Redis implementation kept for migration/reference use
- **Runtime role:** none in the current primary path

### `src/storage/postgres.py`
- **Status:** inactive / experimental
- **Purpose:** older duplicate Postgres helper kept conservatively to avoid destabilizing runtime during cleanup
- **Runtime role:** none in the current bot startup path

## Deployment notes

- The active deployment expects **PostgreSQL** via `DATABASE_URL` or `NEON_MINDMATE_DB_URL`.
- Current memory retrieval is **keyword-based**, not vector-semantic.
- In-memory storage exists only as a resilience fallback, not as the preferred mode.

**Last Updated:** 2026-03-22
