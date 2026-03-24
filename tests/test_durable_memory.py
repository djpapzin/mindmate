import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import bot  # noqa: E402
from postgres_db import InMemoryDatabase, PostgresDatabase  # noqa: E402


class DurableMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot.db_manager = InMemoryDatabase()
        await bot.db_manager.connect()
        bot.user_journey.clear()
        bot.daily_journals.clear()
        bot.daily_summary_tracking.clear()
        bot.degraded_mode_notice_sent.clear()
        bot.processed_messages.clear()
        self.original_daily_heartbeat_enabled = bot.DAILY_HEARTBEAT_ENABLED
        self.original_telegram_app = bot.telegram_app
        self.original_openai_client = bot.openai_client

    async def asyncTearDown(self):
        bot.DAILY_HEARTBEAT_ENABLED = self.original_daily_heartbeat_enabled
        bot.telegram_app = self.original_telegram_app
        bot.openai_client = self.original_openai_client

    async def test_journey_survives_restart_via_active_db_layer(self):
        user_id = 1234

        await bot.update_user_journey(user_id, "medication_status", "Currently taking medication")
        self.assertEqual(bot.user_journey[user_id]["medication_status"], "Currently taking medication")

        # Simulate process restart: in-memory bot caches cleared, active DB layer retained.
        bot.user_journey.clear()

        summary = await bot.get_user_journey_summary(user_id)
        self.assertIn("Medication: Currently taking medication", summary)

    async def test_journal_entries_reload_after_restart(self):
        user_id = 4321
        local_date = "2026-03-24"

        await bot.append_journal_entry_for_user(
            user_id=user_id,
            local_date=local_date,
            entry_text="Today felt heavy but manageable.",
            entry_type="daily_heartbeat",
            metadata={"source": "test"},
        )
        self.assertEqual(len(bot.daily_journals[user_id][local_date]), 1)

        bot.daily_journals.clear()
        restored = await bot.get_journal_entries_for_date(user_id, local_date)

        self.assertEqual(len(restored), 1)
        self.assertEqual(restored[0]["entry"], "Today felt heavy but manageable.")
        self.assertEqual(restored[0]["type"], "daily_heartbeat")

    async def test_pending_daily_checkin_survives_restart_and_blocks_duplicate_send(self):
        user_id = 777
        local_date = "2026-03-24"
        sent_at = datetime(2026, 3, 24, 7, 0, 0)

        await bot.set_daily_summary_tracking(
            user_id,
            local_date,
            True,
            sent_at=sent_at,
            prompt_message_id=999,
            status="sent",
        )

        bot.daily_summary_tracking.clear()
        restored = await bot.get_latest_pending_daily_summary_tracking(user_id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored["local_date"], local_date)
        self.assertTrue(restored["waiting_for_summary"])

        bot.DAILY_HEARTBEAT_ENABLED = True
        bot.telegram_app = types.SimpleNamespace(bot=object())
        bot.get_daily_heartbeat_candidate_user_ids = AsyncMock(return_value=[user_id])
        bot.get_daily_heartbeat_last_sent_date = AsyncMock(return_value=None)
        bot.send_scheduled_daily_summary = AsyncMock()

        count = await bot.run_daily_heartbeat_cycle(now=datetime(2026, 3, 24, 7, 5, 0))

        self.assertEqual(count, 0)
        bot.send_scheduled_daily_summary.assert_not_awaited()


    async def test_duplicate_daily_reply_is_not_appended_twice_across_retry_state(self):
        user_id = 888
        local_date = "2026-03-24"
        sent_at = datetime(2026, 3, 24, 7, 0, 0)
        update = types.SimpleNamespace(
            message=types.SimpleNamespace(message_id=12345, reply_text=AsyncMock())
        )

        await bot.set_daily_summary_tracking(
            user_id,
            local_date,
            True,
            sent_at=sent_at,
            prompt_message_id=999,
            status="sent",
        )

        await bot.handle_daily_summary_response(update, None, user_id, "Today was rough but manageable.")
        entries = await bot.get_journal_entries_for_date(user_id, local_date)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["metadata"]["source_message_id"], "12345")

        bot.daily_journals.clear()
        bot.daily_summary_tracking.clear()
        await bot.set_daily_summary_tracking(
            user_id,
            local_date,
            True,
            sent_at=sent_at,
            prompt_message_id=999,
            status="sent",
        )

        await bot.handle_daily_summary_response(update, None, user_id, "Today was rough but manageable.")
        entries = await bot.get_journal_entries_for_date(user_id, local_date)
        self.assertEqual(len(entries), 1)
        self.assertIn("didn't add it twice", update.message.reply_text.await_args_list[-1].args[0])

    async def test_daily_reply_in_degraded_mode_is_honest_about_temporary_storage(self):
        user_id = 889
        local_date = "2026-03-24"
        sent_at = datetime(2026, 3, 24, 7, 0, 0)
        update = types.SimpleNamespace(
            message=types.SimpleNamespace(message_id=67890, reply_text=AsyncMock())
        )

        await bot.set_daily_summary_tracking(
            user_id,
            local_date,
            True,
            sent_at=sent_at,
            prompt_message_id=1000,
            status="sent",
        )

        await bot.handle_daily_summary_response(update, None, user_id, "I got through today.")

        reply_text = update.message.reply_text.await_args_list[-1].args[0]
        self.assertIn("temporary lighter mode", reply_text)
        self.assertIn("may not survive a restart", reply_text)
        self.assertNotIn("better continuity", reply_text)

    async def test_personal_mode_chat_updates_durable_journey_from_normal_messages(self):
        user_id = 339651126
        update = types.SimpleNamespace(
            effective_user=types.SimpleNamespace(id=user_id),
            message=types.SimpleNamespace(
                message_id=54321,
                text="I had a therapy session today and my partner has been really supportive.",
                date=datetime(2026, 3, 24, 12, 0, 0),
                reply_text=AsyncMock(),
            ),
        )
        context = types.SimpleNamespace()
        bot.openai_client = types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(
                    create=Mock(
                        return_value=types.SimpleNamespace(
                            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Glad you shared that."))]
                        )
                    )
                )
            )
        )

        await bot.handle_message(update, context)

        summary = await bot.get_user_journey_summary(user_id)
        self.assertIn("Therapy: Currently in therapy", summary)
        journey = await bot.ensure_user_journey_loaded(user_id)
        self.assertEqual(journey.get("relationship_status"), "Supportive partner")


class _FakeCursor:
    def __init__(self, fetchone_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((" ".join(query.split()), params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commit_count = 0

    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.commit_count += 1


class _FakePool:
    def __init__(self, conn):
        self.conn = conn
        self.put_back_count = 0

    def getconn(self):
        return self.conn

    def putconn(self, conn):
        self.put_back_count += 1


class PostgresJournalDedupeTests(unittest.IsolatedAsyncioTestCase):
    async def test_append_journal_entry_uses_advisory_lock_and_reuses_existing_source_message(self):
        created_at = datetime(2026, 3, 24, 7, 10, 0)
        existing_row = (
            "2026-03-24",
            "daily_heartbeat",
            "Already stored",
            None,
            None,
            {"source_message_id": "12345", "source": "daily_checkin_reply"},
            created_at,
        )
        cursor = _FakeCursor(fetchone_results=[existing_row])
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        db = PostgresDatabase.__new__(PostgresDatabase)
        db.pool = pool
        db.prefix = ""
        db._get_pool = lambda: pool

        entry = await db.append_journal_entry(
            user_id=42,
            local_date="2026-03-24",
            entry_text="Already stored",
            entry_type="daily_heartbeat",
            metadata={"source_message_id": "12345", "source": "daily_checkin_reply"},
            created_at=created_at,
        )

        self.assertEqual(entry["entry"], "Already stored")
        self.assertEqual(entry["metadata"]["source_message_id"], "12345")
        self.assertEqual(conn.commit_count, 1)
        self.assertEqual(pool.put_back_count, 1)
        self.assertTrue(any("pg_advisory_xact_lock" in query for query, _ in cursor.executed))
        self.assertFalse(any("INSERT INTO mindmate_journal_entries" in query for query, _ in cursor.executed))


if __name__ == "__main__":
    unittest.main()
