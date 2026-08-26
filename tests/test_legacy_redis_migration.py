import json
import unittest
from datetime import datetime

from src.legacy_redis_migration import MIGRATION_NAME, migrate_legacy_redis


class FakeRedis:
    def __init__(self, lists=None, hashes=None):
        self.lists = lists or {}
        self.hashes = hashes or {}
        self.pinged = False

    async def ping(self):
        self.pinged = True

    async def scan_iter(self, match):
        prefix = match[:-1]
        source = self.hashes if match == "user:*" else self.lists
        for key in source:
            if key.startswith(prefix):
                yield key

    async def lrange(self, key, start, end):
        return list(self.lists[key])

    async def hgetall(self, key):
        return dict(self.hashes[key])


class FakeDatabase:
    def __init__(self, complete=False):
        self.complete = complete
        self.messages = {}
        self.preferences = {}
        self.marker = None

    async def is_legacy_migration_complete(self, name):
        return self.complete

    async def store_message_if_absent(self, message):
        key = (message.user_id, message.message_id)
        if key in self.messages:
            return False
        self.messages[key] = message
        return True

    async def store_user_preference(self, user_id, key, value):
        self.preferences[(user_id, key)] = value

    async def mark_legacy_migration_complete(self, name, metadata):
        self.complete = True
        self.marker = (name, metadata)


class LegacyRedisMigrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_migrates_conversations_archives_and_preferences_idempotently(self):
        duplicate = json.dumps({
            "role": "user",
            "content": "I need help",
            "timestamp": "2026-01-02T03:04:05",
            "message_id": "msg-1",
        })
        no_id = json.dumps({
            "role": "assistant",
            "content": "I am here",
            "timestamp": "2026-01-02T03:05:05",
        })
        redis = FakeRedis(
            lists={
                "conversation:42": [no_id, duplicate],
                "archive:42": [duplicate],
            },
            hashes={"user:42": {"mode": '"personal"', "enabled": "true"}},
        )
        db = FakeDatabase()

        result = await migrate_legacy_redis(db, "redis://unused", redis)

        self.assertTrue(redis.pinged)
        self.assertEqual(2, result["messages"])
        self.assertEqual(2, result["preferences"])
        self.assertEqual("personal", db.preferences[(42, "mode")])
        self.assertIs(True, db.preferences[(42, "enabled")])
        generated = [m for m in db.messages.values() if m.message_id.startswith("legacy-")]
        self.assertEqual(1, len(generated))
        self.assertIsInstance(generated[0].timestamp, datetime)
        self.assertEqual(MIGRATION_NAME, db.marker[0])

        second = await migrate_legacy_redis(db, "redis://unused", redis)
        self.assertTrue(second["already_complete"])
        self.assertEqual(2, len(db.messages))

    async def test_empty_redis_remains_retryable(self):
        redis = FakeRedis()
        db = FakeDatabase()

        result = await migrate_legacy_redis(db, "redis://unused", redis)

        self.assertFalse(result["already_complete"])
        self.assertIsNone(db.marker)
        self.assertFalse(db.complete)

    async def test_malformed_records_are_skipped_without_blocking_valid_data(self):
        valid = json.dumps({
            "role": "user",
            "content": "valid",
            "timestamp": "2026-01-02T03:04:05",
            "message_id": "valid-1",
        })
        redis = FakeRedis(lists={"conversation:7": ["not-json", valid]})
        db = FakeDatabase()

        result = await migrate_legacy_redis(db, "redis://unused", redis)

        self.assertEqual(1, result["messages"])
        self.assertEqual(1, result["skipped"])
        self.assertTrue(db.complete)


if __name__ == "__main__":
    unittest.main()
