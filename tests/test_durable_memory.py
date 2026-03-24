import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import bot  # noqa: E402
from postgres_db import InMemoryDatabase  # noqa: E402


class DurableMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot.db_manager = InMemoryDatabase()
        await bot.db_manager.connect()
        bot.user_journey.clear()
        bot.daily_journals.clear()
        bot.daily_summary_tracking.clear()
        bot.degraded_mode_notice_sent.clear()
        self.original_daily_heartbeat_enabled = bot.DAILY_HEARTBEAT_ENABLED
        self.original_telegram_app = bot.telegram_app

    async def asyncTearDown(self):
        bot.DAILY_HEARTBEAT_ENABLED = self.original_daily_heartbeat_enabled
        bot.telegram_app = self.original_telegram_app

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


if __name__ == "__main__":
    unittest.main()
