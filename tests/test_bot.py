import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import pytz

from app.utils.datetime import (
    get_now,
    get_today_str,
    get_timestamp_str,
    format_date_id,
    format_month_year_id,
    get_current_month_prefix,
    INDONESIAN_MONTHS,
)
from app.config import Config
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_tilawah_keyboard,
    get_sholat_wajib_keyboard,
    get_rawatib_keyboard,
    get_almatsurat_keyboard,
    get_yes_no_keyboard,
    get_confirmation_keyboard,
    get_admin_keyboard,
)
from app.services.statistics import StatisticsService


class TestUtilsAndKeyboards(unittest.TestCase):
    def test_datetime_utils(self):
        tz_name = "Asia/Seoul"
        now = get_now(tz_name)
        self.assertIsNotNone(now)
        self.assertIsNotNone(now.tzinfo)

        today_str = get_today_str(tz_name)
        self.assertEqual(len(today_str), 10)
        self.assertEqual(today_str.count("-"), 2)

        ts_str = get_timestamp_str(tz_name)
        self.assertEqual(len(ts_str), 19)

        # Indonesian date formatting
        dt_sample = datetime(2026, 10, 13, 12, 0, tzinfo=pytz.timezone("Asia/Seoul"))
        formatted = format_date_id(dt_sample)
        self.assertEqual(formatted, "13 Oktober 2026")

        month_label = format_month_year_id(dt_sample)
        self.assertEqual(month_label, "Oktober 2026")

        # Test formatting with string
        formatted_from_str = format_date_id(date_str="2026-05-20")
        self.assertEqual(formatted_from_str, "20 Mei 2026")

    def test_keyboards_structure(self):
        menu = get_main_menu_keyboard()
        self.assertEqual(len(menu.inline_keyboard), 3)

        tilawah = get_tilawah_keyboard()
        self.assertGreaterEqual(len(tilawah.inline_keyboard), 3)

        wajib = get_sholat_wajib_keyboard()
        self.assertEqual(len(wajib.inline_keyboard), 3)

        rawatib = get_rawatib_keyboard()
        self.assertEqual(len(rawatib.inline_keyboard), 3)

        almatsurat = get_almatsurat_keyboard()
        self.assertEqual(len(almatsurat.inline_keyboard), 2)

        yes_no = get_yes_no_keyboard()
        self.assertEqual(len(yes_no.inline_keyboard), 2)

        confirm = get_confirmation_keyboard()
        self.assertEqual(len(confirm.inline_keyboard), 2)

        admin_kb = get_admin_keyboard("test_sheet_id")
        self.assertEqual(len(admin_kb.inline_keyboard), 2)

    def test_admin_config(self):
        Config.ADMIN_TELEGRAM_IDS = {12345, 67890}
        self.assertTrue(Config.is_admin(12345))
        self.assertTrue(Config.is_admin(67890))
        self.assertFalse(Config.is_admin(99999))


class TestStatisticsService(unittest.IsolatedAsyncioTestCase):
    async def test_calculate_user_month_progress(self):
        mock_sheets = MagicMock()
        # Mock 2 rows for user 111 in current month
        today_prefix = get_current_month_prefix("Asia/Seoul")
        mock_rows = [
            {
                "Date": f"{today_prefix}-01",
                "Telegram User ID": "111",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
                "Rawatib Rakaat": "12",
                "Almatsurat": "2",
                "Qiyamulail": "TRUE",
                "Dhuha": "TRUE",
                "Olahraga": "TRUE",
            },
            {
                "Date": f"{today_prefix}-02",
                "Telegram User ID": "111",
                "Tilawah Pages": "10",
                "Sholat Wajib": "5",
                "Rawatib Rakaat": "8",
                "Almatsurat": "1",
                "Qiyamulail": "FALSE",
                "Dhuha": "TRUE",
                "Olahraga": "FALSE",
            },
            {
                # Other user
                "Date": f"{today_prefix}-02",
                "Telegram User ID": "222",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
                "Rawatib Rakaat": "12",
                "Almatsurat": "2",
                "Qiyamulail": "TRUE",
                "Dhuha": "TRUE",
                "Olahraga": "TRUE",
            },
        ]
        mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=mock_rows)

        mock_members = MagicMock()
        stats_service = StatisticsService(sheets_service=mock_sheets, members_service=mock_members)

        res = await stats_service.calculate_user_month_progress(111)
        self.assertEqual(res["days_submitted"], 2)
        self.assertEqual(res["total_tilawah"], 30)
        self.assertEqual(res["total_wajib"], 10)
        self.assertEqual(res["total_rawatib"], 20)
        self.assertEqual(res["total_almatsurat"], 3)
        self.assertEqual(res["count_qiyamulail"], 1)
        self.assertEqual(res["count_dhuha"], 2)
        self.assertEqual(res["count_olahraga"], 1)
        self.assertGreater(res["completion_percentage"], 0)

    async def test_calculate_admin_stats(self):
        mock_sheets = MagicMock()
        today_str = get_today_str("Asia/Seoul")
        mock_rows = [
            {
                "Date": today_str,
                "Telegram User ID": "111",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
                "Rawatib Rakaat": "12",
                "Almatsurat": "2",
            },
            {
                "Date": today_str,
                "Telegram User ID": "222",
                "Tilawah Pages": "10",
                "Sholat Wajib": "4",
                "Rawatib Rakaat": "6",
                "Almatsurat": "1",
            },
        ]
        mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=mock_rows)

        mock_members = MagicMock()
        mock_members.get_all_active_members = AsyncMock(return_value=[
            {"Telegram User ID": "111", "Active": "TRUE"},
            {"Telegram User ID": "222", "Active": "TRUE"},
            {"Telegram User ID": "333", "Active": "TRUE"},
            {"Telegram User ID": "444", "Active": "TRUE"},
        ])

        stats_service = StatisticsService(sheets_service=mock_sheets, members_service=mock_members)
        admin_stats = await stats_service.calculate_monthly_admin_stats()

        self.assertEqual(admin_stats["registered_members"], 4)
        self.assertEqual(admin_stats["submissions_today"], 2)
        self.assertEqual(admin_stats["submission_rate_today"], 50.0)
        self.assertEqual(admin_stats["active_submitters_month"], 2)
        self.assertGreater(admin_stats["average_completion_rate"], 0)


if __name__ == "__main__":
    unittest.main()
