"""One-time, idempotent recovery of legacy MindMate Redis data."""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

try:
    from postgres_db import Message
except ImportError:  # package import path used by tests
    from src.postgres_db import Message

logger = logging.getLogger(__name__)
MIGRATION_NAME = "legacy-redis-v1"


def _message_from_legacy(user_id: int, raw: str) -> Message | None:
    try:
        item = json.loads(raw)
        role = str(item["role"])
        content = str(item["content"])
        timestamp_raw = str(item["timestamp"])
        timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

    message_id = str(item.get("message_id") or "").strip()
    if not message_id:
        digest_source = f"{user_id}\0{role}\0{content}\0{timestamp_raw}".encode("utf-8")
        message_id = f"legacy-{hashlib.sha256(digest_source).hexdigest()}"
    return Message(
        user_id=user_id,
        content=content,
        role=role,
        timestamp=timestamp,
        message_id=message_id,
    )


def _parse_legacy_preference(raw_value: Any) -> Any:
    """Preserve values written by RedisDatabase's json-or-str encoding."""
    if raw_value == "True":
        return True
    if raw_value == "False":
        return False
    if raw_value == "None":
        return None
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return raw_value


async def migrate_legacy_redis(db: Any, redis_url: str, redis_client: Any = None) -> dict[str, int | bool]:
    """Copy recoverable Redis conversations/preferences into PostgreSQL once.

    The target writes are idempotent, so a process interruption can safely retry.
    No legacy Redis keys are changed or deleted.
    """
    if await db.is_legacy_migration_complete(MIGRATION_NAME):
        return {"already_complete": True, "messages": 0, "preferences": 0, "skipped": 0}

    owns_client = redis_client is None
    if redis_client is None:
        import redis.asyncio as redis
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=5,
            health_check_interval=30,
        )

    messages = preferences = skipped = recoverable = 0
    try:
        await redis_client.ping()
        for pattern in ("conversation:*", "archive:*"):
            async for key in redis_client.scan_iter(match=pattern):
                try:
                    user_id = int(str(key).rsplit(":", 1)[1])
                except (IndexError, ValueError):
                    skipped += 1
                    continue
                raw_items = await redis_client.lrange(key, 0, -1)
                for raw in reversed(raw_items):
                    message = _message_from_legacy(user_id, raw)
                    if message is None:
                        skipped += 1
                        continue
                    recoverable += 1
                    if await db.store_message_if_absent(message):
                        messages += 1

        async for key in redis_client.scan_iter(match="user:*"):
            try:
                user_id = int(str(key).rsplit(":", 1)[1])
            except (IndexError, ValueError):
                skipped += 1
                continue
            for pref_key, raw_value in (await redis_client.hgetall(key)).items():
                recoverable += 1
                value = _parse_legacy_preference(raw_value)
                if await db.store_user_preference_if_absent(user_id, pref_key, value):
                    preferences += 1

        if recoverable == 0:
            logger.warning("Legacy Redis recovery found no recoverable records; leaving migration retryable")
            return {"already_complete": False, "messages": 0, "preferences": 0, "skipped": skipped}

        await db.mark_legacy_migration_complete(
            MIGRATION_NAME,
            {"messages": messages, "preferences": preferences, "skipped": skipped},
        )
        logger.info(
            "Legacy Redis recovery completed: messages=%s preferences=%s skipped=%s",
            messages,
            preferences,
            skipped,
        )
        return {
            "already_complete": False,
            "messages": messages,
            "preferences": preferences,
            "skipped": skipped,
        }
    finally:
        if owns_client:
            await redis_client.aclose()
