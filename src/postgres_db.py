"""
PostgreSQL Database Module for MindMate Bot
Handles the active persistent storage path for the current runtime.
"""
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import logging
import psycopg2
from psycopg2.extras import Json, RealDictCursor
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
    """PostgreSQL database manager for the active production storage path."""

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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_feedback (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    feedback_text TEXT NOT NULL,
                    source VARCHAR(50) DEFAULT 'command',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_user_journey (
                    user_id BIGINT PRIMARY KEY,
                    journey_data JSONB NOT NULL DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_journal_entries (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    local_date DATE NOT NULL,
                    entry_type VARCHAR(50) NOT NULL,
                    entry_text TEXT NOT NULL,
                    mood TEXT,
                    plan_tomorrow TEXT,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mindmate_daily_checkins (
                    user_id BIGINT NOT NULL,
                    local_date DATE NOT NULL,
                    waiting_for_summary BOOLEAN NOT NULL DEFAULT FALSE,
                    sent_at TIMESTAMP,
                    responded_at TIMESTAMP,
                    prompt_message_id VARCHAR(100),
                    response_message_id VARCHAR(100),
                    prompt_kind VARCHAR(50) NOT NULL DEFAULT 'daily_heartbeat',
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, local_date)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON mindmate_messages(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON mindmate_messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prefs_user ON mindmate_user_preferences(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON mindmate_feedback(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON mindmate_feedback(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_user_date ON mindmate_journal_entries(user_id, local_date, created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_source_message ON mindmate_journal_entries(user_id, entry_type, ((metadata->>'source_message_id'))) WHERE metadata ? 'source_message_id'")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkins_user_updated ON mindmate_daily_checkins(user_id, updated_at DESC)")

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
            return [{"role": row["role"], "content": row["content"]} for row in reversed(results)]
        finally:
            pool.putconn(conn)

    async def semantic_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Keyword-only message lookup."""
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

    async def get_user_ids_with_preference(self, key: str, expected_value: Any = True) -> List[int]:
        """Return users whose stored preference matches the expected value."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT DISTINCT user_id, pref_value
                FROM mindmate_user_preferences
                WHERE pref_key = %s
            """, (key,))

            matching_user_ids: List[int] = []
            for user_id, raw_value in cursor.fetchall():
                try:
                    parsed_value = json.loads(raw_value)
                except Exception:
                    parsed_value = raw_value
                if parsed_value == expected_value:
                    matching_user_ids.append(int(user_id))
            return matching_user_ids
        finally:
            pool.putconn(conn)

    async def get_known_user_ids(self) -> List[int]:
        """Return users MindMate has seen via messages or stored preferences."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT DISTINCT user_id
                FROM (
                    SELECT user_id FROM mindmate_messages
                    UNION
                    SELECT user_id FROM mindmate_user_preferences
                    UNION
                    SELECT user_id FROM mindmate_user_journey
                    UNION
                    SELECT user_id FROM mindmate_journal_entries
                    UNION
                    SELECT user_id FROM mindmate_daily_checkins
                ) AS known_users
                ORDER BY user_id
                """
            )
            return [int(user_id) for (user_id,) in cursor.fetchall()]
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

    async def get_user_journey(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return the latest durable journey snapshot for a user."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT journey_data, updated_at
                FROM mindmate_user_journey
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            journey = dict(row.get("journey_data") or {})
            updated_at = row.get("updated_at")
            if updated_at and "last_updated" not in journey:
                journey["last_updated"] = updated_at.isoformat()
            return journey
        finally:
            pool.putconn(conn)

    async def save_user_journey(self, user_id: int, journey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persist the current durable journey snapshot for a user."""
        payload = dict(journey_data or {})
        payload.setdefault("last_updated", datetime.now().isoformat())

        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO mindmate_user_journey (user_id, journey_data, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    journey_data = EXCLUDED.journey_data,
                    updated_at = EXCLUDED.updated_at
                """,
                (user_id, Json(payload), datetime.now()),
            )
            conn.commit()
            return payload
        finally:
            pool.putconn(conn)

    async def delete_user_journey_keys(self, user_id: int, keys: List[str]) -> Dict[str, Any]:
        """Remove specific keys from the durable journey snapshot."""
        journey = await self.get_user_journey(user_id) or {}
        for key in keys:
            journey.pop(key, None)
        journey["last_updated"] = datetime.now().isoformat()
        return await self.save_user_journey(user_id, journey)

    async def append_journal_entry(
        self,
        user_id: int,
        local_date: str,
        entry_text: str,
        entry_type: str = "journal",
        mood: Optional[str] = None,
        plan_tomorrow: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Append a durable journal/check-in entry."""
        created_at = created_at or datetime.now()
        entry: Dict[str, Any] = {
            "timestamp": created_at.isoformat(),
            "entry": entry_text,
            "type": entry_type,
            "mood": mood,
            "plan_tomorrow": plan_tomorrow,
        }
        if metadata:
            entry["metadata"] = metadata

        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO mindmate_journal_entries (
                    user_id, local_date, entry_type, entry_text, mood, plan_tomorrow, metadata, created_at
                )
                VALUES (%s, %s::date, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, local_date, entry_type, entry_text, mood, plan_tomorrow, Json(metadata or {}), created_at),
            )
            conn.commit()
            return entry
        finally:
            pool.putconn(conn)

    async def get_journal_entry_by_source_message(
        self,
        user_id: int,
        source_message_id: str,
        local_date: Optional[str] = None,
        entry_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return a durable journal entry previously tied to a source message id."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            params: List[Any] = [user_id, source_message_id]
            where = ["user_id = %s", "metadata->>'source_message_id' = %s"]
            if local_date:
                where.append("local_date = %s::date")
                params.append(local_date)
            if entry_type:
                where.append("entry_type = %s")
                params.append(entry_type)

            cursor.execute(
                f"""
                SELECT local_date, entry_type, entry_text, mood, plan_tomorrow, metadata, created_at
                FROM mindmate_journal_entries
                WHERE {' AND '.join(where)}
                ORDER BY created_at ASC
                LIMIT 1
                """,
                tuple(params),
            )
            row = cursor.fetchone()
            if not row:
                return None

            item: Dict[str, Any] = {
                "timestamp": row["created_at"].isoformat(),
                "entry": row["entry_text"],
                "type": row["entry_type"],
                "mood": row["mood"],
                "plan_tomorrow": row["plan_tomorrow"],
            }
            metadata = row.get("metadata") or {}
            if metadata:
                item["metadata"] = dict(metadata)
            return item
        finally:
            pool.putconn(conn)

    async def get_journal_entries(
        self,
        user_id: int,
        local_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return durable journal entries, optionally filtered by local date."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            params: List[Any] = [user_id]
            where = ["user_id = %s"]
            if local_date:
                where.append("local_date = %s::date")
                params.append(local_date)

            query = f"""
                SELECT local_date, entry_type, entry_text, mood, plan_tomorrow, metadata, created_at
                FROM mindmate_journal_entries
                WHERE {' AND '.join(where)}
                ORDER BY created_at ASC
            """
            if limit:
                query += " LIMIT %s"
                params.append(limit)

            cursor.execute(query, tuple(params))
            entries: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                item: Dict[str, Any] = {
                    "timestamp": row["created_at"].isoformat(),
                    "entry": row["entry_text"],
                    "type": row["entry_type"],
                    "mood": row["mood"],
                    "plan_tomorrow": row["plan_tomorrow"],
                }
                metadata = row.get("metadata") or {}
                if metadata:
                    item["metadata"] = dict(metadata)
                entries.append(item)
            return entries
        finally:
            pool.putconn(conn)

    async def upsert_daily_checkin(
        self,
        user_id: int,
        local_date: str,
        waiting_for_summary: bool,
        sent_at: Optional[datetime] = None,
        responded_at: Optional[datetime] = None,
        prompt_message_id: Optional[Any] = None,
        response_message_id: Optional[Any] = None,
        prompt_kind: str = "daily_heartbeat",
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist or update durable daily check-in state for a local day."""
        now = datetime.now()
        if status is None:
            if responded_at:
                status = "completed"
            elif waiting_for_summary:
                status = "sent"
            else:
                status = "dismissed"

        payload = {
            "waiting_for_summary": bool(waiting_for_summary),
            "sent_time": sent_at.isoformat() if sent_at else None,
            "responded_at": responded_at.isoformat() if responded_at else None,
            "message_id": str(prompt_message_id) if prompt_message_id is not None else None,
            "response_message_id": str(response_message_id) if response_message_id is not None else None,
            "kind": prompt_kind,
            "status": status,
        }
        if metadata:
            payload["metadata"] = metadata

        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO mindmate_daily_checkins (
                    user_id, local_date, waiting_for_summary, sent_at, responded_at,
                    prompt_message_id, response_message_id, prompt_kind, status, metadata, updated_at
                )
                VALUES (%s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, local_date) DO UPDATE SET
                    waiting_for_summary = EXCLUDED.waiting_for_summary,
                    sent_at = COALESCE(EXCLUDED.sent_at, mindmate_daily_checkins.sent_at),
                    responded_at = COALESCE(EXCLUDED.responded_at, mindmate_daily_checkins.responded_at),
                    prompt_message_id = COALESCE(EXCLUDED.prompt_message_id, mindmate_daily_checkins.prompt_message_id),
                    response_message_id = COALESCE(EXCLUDED.response_message_id, mindmate_daily_checkins.response_message_id),
                    prompt_kind = EXCLUDED.prompt_kind,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    user_id,
                    local_date,
                    bool(waiting_for_summary),
                    sent_at,
                    responded_at,
                    str(prompt_message_id) if prompt_message_id is not None else None,
                    str(response_message_id) if response_message_id is not None else None,
                    prompt_kind,
                    status,
                    Json(metadata or {}),
                    now,
                ),
            )
            conn.commit()
            return payload
        finally:
            pool.putconn(conn)

    async def get_daily_checkin(self, user_id: int, local_date: str) -> Optional[Dict[str, Any]]:
        """Return durable daily check-in state for a given local day."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT waiting_for_summary, sent_at, responded_at, prompt_message_id,
                       response_message_id, prompt_kind, status, metadata, updated_at
                FROM mindmate_daily_checkins
                WHERE user_id = %s AND local_date = %s::date
                """,
                (user_id, local_date),
            )
            row = cursor.fetchone()
            if not row:
                return None
            result = {
                "waiting_for_summary": bool(row["waiting_for_summary"]),
                "sent_time": row["sent_at"].isoformat() if row["sent_at"] else None,
                "responded_at": row["responded_at"].isoformat() if row["responded_at"] else None,
                "message_id": row["prompt_message_id"],
                "response_message_id": row["response_message_id"],
                "kind": row["prompt_kind"],
                "status": row["status"],
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
            metadata = row.get("metadata") or {}
            if metadata:
                result["metadata"] = dict(metadata)
            return result
        finally:
            pool.putconn(conn)

    async def get_latest_pending_daily_checkin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return the most recent pending daily check-in for a user, if any."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT local_date, waiting_for_summary, sent_at, responded_at, prompt_message_id,
                       response_message_id, prompt_kind, status, metadata, updated_at
                FROM mindmate_daily_checkins
                WHERE user_id = %s AND waiting_for_summary = TRUE
                ORDER BY local_date DESC, updated_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            result = {
                "local_date": str(row["local_date"]),
                "waiting_for_summary": bool(row["waiting_for_summary"]),
                "sent_time": row["sent_at"].isoformat() if row["sent_at"] else None,
                "responded_at": row["responded_at"].isoformat() if row["responded_at"] else None,
                "message_id": row["prompt_message_id"],
                "response_message_id": row["response_message_id"],
                "kind": row["prompt_kind"],
                "status": row["status"],
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
            metadata = row.get("metadata") or {}
            if metadata:
                result["metadata"] = dict(metadata)
            return result
        finally:
            pool.putconn(conn)

    async def store_feedback(self, user_id: int, feedback_text: str, metadata: Optional[Dict[str, Any]] = None, source: str = "command") -> Dict[str, Any]:
        """Store user feedback for later review."""
        pool = self._get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO mindmate_feedback (user_id, feedback_text, source, metadata)
                VALUES (%s, %s, %s, %s)
            """, (user_id, feedback_text, source, json.dumps(metadata or {})))
            conn.commit()
            return {"saved": True, "storage": "postgresql", "session_only": False}
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

            cursor.execute("SELECT COUNT(*) FROM mindmate_journal_entries")
            total_journal_entries = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM mindmate_daily_checkins")
            total_daily_checkins = cursor.fetchone()[0]

            return {
                "total_messages": total_messages,
                "total_users": total_users,
                "total_journal_entries": total_journal_entries,
                "total_daily_checkins": total_daily_checkins,
                "storage": "postgresql"
            }
        finally:
            pool.putconn(conn)

    async def close(self):
        """Close database pool"""
        if self.pool:
            self.pool.closeall()


class InMemoryDatabase:
    """Simple in-memory fallback"""

    def __init__(self, db_url=None, openai_client=None):
        self.messages = {}
        self.preferences = {}
        self.feedback = []
        self.journeys: Dict[int, Dict[str, Any]] = {}
        self.journal_entries: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
        self.daily_checkins: Dict[int, Dict[str, Dict[str, Any]]] = {}

    async def connect(self):
        logger.info("✅ Using in-memory storage (fallback)")

    async def store_message(self, message: Message):
        key = f"{message.user_id}"
        if key not in self.messages:
            self.messages[key] = []
        self.messages[key].append({
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id,
        })

    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        history = self.messages.get(str(user_id), [])[-limit:]
        return [{"role": msg["role"], "content": msg["content"]} for msg in history]

    async def store_user_preference(self, user_id: int, key: str, value: Any):
        k = f"{user_id}:{key}"
        self.preferences[k] = value

    async def get_user_preference(self, user_id: int, key: str) -> Optional[Any]:
        return self.preferences.get(f"{user_id}:{key}")

    async def get_user_ids_with_preference(self, key: str, expected_value: Any = True) -> List[int]:
        matching_user_ids: List[int] = []
        for stored_key, stored_value in self.preferences.items():
            user_id_str, pref_key = stored_key.split(":", 1)
            if pref_key == key and stored_value == expected_value:
                matching_user_ids.append(int(user_id_str))
        return matching_user_ids

    async def get_known_user_ids(self) -> List[int]:
        known_user_ids = {int(user_id_str) for user_id_str in self.messages.keys()}
        for stored_key in self.preferences.keys():
            user_id_str, _ = stored_key.split(":", 1)
            known_user_ids.add(int(user_id_str))
        known_user_ids.update(self.journeys.keys())
        known_user_ids.update(self.journal_entries.keys())
        known_user_ids.update(self.daily_checkins.keys())
        return sorted(known_user_ids)

    async def clear_conversation(self, user_id: int):
        self.messages.pop(str(user_id), None)

    async def get_user_journey(self, user_id: int) -> Optional[Dict[str, Any]]:
        journey = self.journeys.get(user_id)
        return dict(journey) if journey else None

    async def save_user_journey(self, user_id: int, journey_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(journey_data or {})
        payload.setdefault("last_updated", datetime.now().isoformat())
        self.journeys[user_id] = payload
        return dict(payload)

    async def delete_user_journey_keys(self, user_id: int, keys: List[str]) -> Dict[str, Any]:
        journey = dict(self.journeys.get(user_id, {}))
        for key in keys:
            journey.pop(key, None)
        journey["last_updated"] = datetime.now().isoformat()
        self.journeys[user_id] = journey
        return dict(journey)

    async def append_journal_entry(
        self,
        user_id: int,
        local_date: str,
        entry_text: str,
        entry_type: str = "journal",
        mood: Optional[str] = None,
        plan_tomorrow: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        created_at = created_at or datetime.now()
        entry: Dict[str, Any] = {
            "timestamp": created_at.isoformat(),
            "entry": entry_text,
            "type": entry_type,
            "mood": mood,
            "plan_tomorrow": plan_tomorrow,
        }
        if metadata:
            entry["metadata"] = dict(metadata)
        self.journal_entries.setdefault(user_id, {}).setdefault(local_date, []).append(entry)
        return dict(entry)

    async def get_journal_entry_by_source_message(
        self,
        user_id: int,
        source_message_id: str,
        local_date: Optional[str] = None,
        entry_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        candidate_dates = [local_date] if local_date else sorted(self.journal_entries.get(user_id, {}).keys())
        for day in candidate_dates:
            for entry in self.journal_entries.get(user_id, {}).get(day, []):
                metadata = entry.get("metadata") or {}
                if str(metadata.get("source_message_id")) != str(source_message_id):
                    continue
                if entry_type and entry.get("type") != entry_type:
                    continue
                return dict(entry)
        return None

    async def get_journal_entries(
        self,
        user_id: int,
        local_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if local_date:
            entries = list(self.journal_entries.get(user_id, {}).get(local_date, []))
        else:
            entries = []
            for day in sorted(self.journal_entries.get(user_id, {}).keys()):
                entries.extend(self.journal_entries[user_id][day])
        if limit:
            entries = entries[-limit:]
        return [dict(entry) for entry in entries]

    async def upsert_daily_checkin(
        self,
        user_id: int,
        local_date: str,
        waiting_for_summary: bool,
        sent_at: Optional[datetime] = None,
        responded_at: Optional[datetime] = None,
        prompt_message_id: Optional[Any] = None,
        response_message_id: Optional[Any] = None,
        prompt_kind: str = "daily_heartbeat",
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if status is None:
            if responded_at:
                status = "completed"
            elif waiting_for_summary:
                status = "sent"
            else:
                status = "dismissed"
        payload = {
            "waiting_for_summary": bool(waiting_for_summary),
            "sent_time": sent_at.isoformat() if sent_at else None,
            "responded_at": responded_at.isoformat() if responded_at else None,
            "message_id": str(prompt_message_id) if prompt_message_id is not None else None,
            "response_message_id": str(response_message_id) if response_message_id is not None else None,
            "kind": prompt_kind,
            "status": status,
        }
        if metadata:
            payload["metadata"] = dict(metadata)
        self.daily_checkins.setdefault(user_id, {})[local_date] = payload
        return dict(payload)

    async def get_daily_checkin(self, user_id: int, local_date: str) -> Optional[Dict[str, Any]]:
        record = self.daily_checkins.get(user_id, {}).get(local_date)
        return dict(record) if record else None

    async def get_latest_pending_daily_checkin(self, user_id: int) -> Optional[Dict[str, Any]]:
        pending = []
        for local_date, record in self.daily_checkins.get(user_id, {}).items():
            if record.get("waiting_for_summary"):
                item = dict(record)
                item["local_date"] = local_date
                pending.append(item)
        if not pending:
            return None
        pending.sort(key=lambda item: item["local_date"], reverse=True)
        return pending[0]

    async def store_feedback(self, user_id: int, feedback_text: str, metadata: Optional[Dict[str, Any]] = None, source: str = "command") -> Dict[str, Any]:
        self.feedback.append({
            "user_id": user_id,
            "feedback_text": feedback_text,
            "source": source,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        })
        return {"saved": True, "storage": "memory", "session_only": True}

    async def get_stats(self):
        return {
            "storage": "memory",
            "messages": len(self.messages),
            "journeys": len(self.journeys),
            "journal_days": sum(len(days) for days in self.journal_entries.values()),
            "daily_checkins": sum(len(days) for days in self.daily_checkins.values()),
        }

    async def close(self):
        pass
