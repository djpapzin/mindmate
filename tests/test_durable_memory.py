import os
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

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


class PersonaPromptTests(unittest.TestCase):
    def test_standard_system_prompt_includes_safety_and_anti_template_rules(self):
        prompt = bot.build_generation_system_prompt(
            user_id=999,
            personal_mode=False,
            response_mode="chat",
            current_time="09:00 AM on March 24, 2026",
        )

        self.assertIn("not a licensed therapist", prompt)
        self.assertIn("Do not follow a rigid 'summary + validate + question' template", prompt)
        self.assertIn("Current time: 09:00 AM on March 24, 2026", prompt)

    def test_personal_mode_prompt_keeps_boundaries_and_user_context(self):
        prompt = bot.get_personal_mode_prompt(339651126)

        self.assertIn("DJ/Papzin", prompt)
        self.assertIn("do not create dependency", prompt.lower())
        self.assertIn("same safety boundaries", prompt)
        self.assertNotIn("You ARE qualified to help", prompt)

    def test_voice_prompt_uses_voice_response_rules(self):
        prompt = bot.build_generation_system_prompt(
            user_id=339651126,
            personal_mode=True,
            response_mode="voice",
        )

        self.assertIn("Voice Response Mode", prompt)
        self.assertIn("End cleanly; don't tack on an unnecessary question every time", prompt)


class DailyHeartbeatCopyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot.db_manager = InMemoryDatabase()
        await bot.db_manager.connect()
        bot.user_journey.clear()
        bot.daily_journals.clear()
        bot.daily_summary_tracking.clear()

    async def test_daily_heartbeat_uses_lighter_distinct_checkin_voice(self):
        user_id = 339651126
        await bot.append_journal_entry_for_user(
            user_id=user_id,
            local_date="2026-03-23",
            entry_text="I felt tired and stressed after work.",
            entry_type="daily_heartbeat",
        )

        message = await bot.build_daily_heartbeat_message(
            user_id,
            now=datetime(2026, 3, 24, 7, 0, 0, tzinfo=bot.get_daily_heartbeat_timezone()),
        )

        self.assertIn("Tiny check-in", message)
        self.assertIn("Gentle nudge:", message)
        self.assertIn("If you want, send a quick mood check", message)
        self.assertNotIn("How are you feeling today?", message)
        self.assertNotIn("Here's a gentle check-in for today", message)


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


class TelegramCommandRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_safe_set_bot_commands_logs_and_continues_on_telegram_error(self):
        fake_app = types.SimpleNamespace(
            bot=types.SimpleNamespace(
                set_my_commands=AsyncMock(side_effect=bot.TelegramError("Unauthorized"))
            )
        )
        warning_logger = Mock()
        original_logger = bot.logger
        bot.logger = types.SimpleNamespace(warning=warning_logger)

        try:
            result = await bot.safe_set_bot_commands(fake_app, [])
        finally:
            bot.logger = original_logger

        self.assertFalse(result)
        warning_logger.assert_called_once()
        self.assertIn("Unable to set Telegram bot commands", warning_logger.call_args.args[0])

    async def test_safe_start_telegram_app_keeps_initialize_failures_nonfatal(self):
        fake_app = types.SimpleNamespace(
            bot=types.SimpleNamespace(
                set_my_commands=AsyncMock(return_value=None),
                delete_webhook=AsyncMock(return_value=None),
                set_webhook=AsyncMock(return_value=None),
            ),
            updater=types.SimpleNamespace(start_polling=AsyncMock(return_value=None)),
            initialize=AsyncMock(side_effect=bot.TelegramError("InvalidToken")),
            start=AsyncMock(return_value=None),
        )
        warning_logger = Mock()
        original_logger = bot.logger
        bot.logger = types.SimpleNamespace(warning=warning_logger, info=Mock())

        try:
            result = await bot.safe_start_telegram_app(fake_app, [])
        finally:
            bot.logger = original_logger

        self.assertFalse(result)
        fake_app.bot.set_my_commands.assert_awaited_once()
        fake_app.initialize.assert_awaited_once()
        fake_app.start.assert_not_awaited()
        fake_app.updater.start_polling.assert_not_awaited()
        warning_logger.assert_called_once()
        self.assertIn("Telegram startup failed; continuing without Telegram integration", warning_logger.call_args.args[0])


class TelegramStartupResilienceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original_token = bot.TELEGRAM_BOT_TOKEN
        self.original_telegram_app = bot.telegram_app
        self.original_status = bot.telegram_startup_status.copy()
        self.original_db_manager = bot.db_manager
        self.original_daily_heartbeat_task = bot.daily_heartbeat_task

    async def asyncTearDown(self):
        bot.TELEGRAM_BOT_TOKEN = self.original_token
        bot.telegram_app = self.original_telegram_app
        bot.telegram_startup_status.clear()
        bot.telegram_startup_status.update(self.original_status)
        bot.db_manager = self.original_db_manager
        bot.daily_heartbeat_task = self.original_daily_heartbeat_task

    async def test_lifespan_degrades_cleanly_when_telegram_initialize_fails(self):
        class FakeDB:
            async def connect(self):
                return None

            async def close(self):
                return None

        class FakeBotAPI:
            async def set_my_commands(self, *args, **kwargs):
                return None

            async def delete_webhook(self, *args, **kwargs):
                return None

            async def set_webhook(self, *args, **kwargs):
                return None

        class FakeUpdater:
            running = False

            async def start_polling(self, *args, **kwargs):
                return None

            async def stop(self):
                return None

        class FakeTelegramApp:
            def __init__(self):
                self.bot = FakeBotAPI()
                self.updater = FakeUpdater()

            def add_handler(self, *args, **kwargs):
                return None

            def add_error_handler(self, *args, **kwargs):
                return None

            async def initialize(self):
                raise RuntimeError("Unauthorized")

            async def start(self):
                return None

            async def stop(self):
                return None

            async def shutdown(self):
                return None

        class FakeBuilder:
            def token(self, token):
                self.token = token
                return self

            def build(self):
                return FakeTelegramApp()

        bot.TELEGRAM_BOT_TOKEN = "expired-token"
        with patch.object(bot, "PostgresDatabase", lambda *args, **kwargs: FakeDB()), patch.object(
            bot, "PostgresInMemoryDatabase", lambda *args, **kwargs: FakeDB()
        ), patch.object(bot.Application, "builder", return_value=FakeBuilder()):
            async with bot.lifespan(types.SimpleNamespace()):
                self.assertIsNone(bot.telegram_app)
                self.assertEqual(bot.telegram_startup_status["state"], "degraded")
                self.assertIn("Unauthorized", str(bot.telegram_startup_status["detail"]))
                health = bot._build_health_payload()
                self.assertEqual(health["status"], "degraded")
                self.assertEqual(health["telegram"]["state"], "degraded")
                self.assertIn("Telegram integration is disabled or degraded", health["details"])

    async def test_health_payload_reports_degraded_when_telegram_disabled(self):
        bot.TELEGRAM_BOT_TOKEN = None
        bot._set_telegram_startup_status("not_configured", "TELEGRAM_BOT_TOKEN not configured")
        payload = bot._build_health_payload()

        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["telegram"]["state"], "not_configured")
        self.assertIn("Telegram integration is disabled or degraded", payload["details"])


if __name__ == "__main__":
    unittest.main()
