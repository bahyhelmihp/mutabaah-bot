import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, CallbackQuery
from telegram.ext import ContextTypes

from app.services.mapping import MappingService
from app.services.sheets import SheetsService
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_binaan_list_keyboard,
    get_binaan_detail_keyboard,
)
from app.handlers.murobbi import (
    cekbinaan_command,
    handle_murobbi_callbacks,
    show_binaan_list,
    show_binaan_detail,
)


class TestMurobbiFeature(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_sheets = MagicMock(spec=SheetsService)
        # Mock Mapping data matching spreadsheet screenshot
        self.mock_mapping_rows = [
            {
                "murobbi_id": "218042450",
                "murobbi_name": "Nurhadi Sukma Waluyo",
                "mutarabbi_id": "819899948",
                "mutarabbi_name": "Doni Nurdiansah",
                "kelompok": "Muntasib",
            },
            {
                "murobbi_id": "218042450",
                "murobbi_name": "Nurhadi Sukma Waluyo",
                "mutarabbi_id": "1809144522",
                "mutarabbi_name": "Han Hisyam Pratama",
                "kelompok": "Muntasib",
            },
            {
                "murobbi_id": "858816179",
                "murobbi_name": "Bahy Helmi Hartoyo Putra",
                "mutarabbi_id": "819899948",
                "mutarabbi_name": "Doni Nurdiansah",
                "kelompok": "Muntasib",
            },
        ]
        self.mock_sheets.get_all_mapping_rows = AsyncMock(return_value=self.mock_mapping_rows)
        self.mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=[])
        self.mock_sheets.get_user_mutabaah_record = AsyncMock(return_value=None)
        self.mock_sheets.get_all_members = AsyncMock(return_value=[])
        self.mock_sheets.find_member = AsyncMock(return_value=None)
        self.mock_sheets.get_user_settings = AsyncMock(return_value=None)

        self.mapping_service = MappingService(self.mock_sheets)

    async def test_mapping_cache_and_is_murobbi(self):
        await self.mapping_service.reload_cache()

        # Check Murobbi detection
        self.assertTrue(self.mapping_service.is_murobbi(218042450))
        self.assertTrue(self.mapping_service.is_murobbi(858816179))
        self.assertFalse(self.mapping_service.is_murobbi(999999999))
        self.assertFalse(self.mapping_service.is_murobbi(819899948))  # Mutarabbi only

        # Check binaan list
        binaan_nurhadi = self.mapping_service.get_binaan(218042450)
        self.assertEqual(len(binaan_nurhadi), 2)
        self.assertEqual(binaan_nurhadi[0]["name"], "Doni Nurdiansah")
        self.assertEqual(binaan_nurhadi[1]["name"], "Han Hisyam Pratama")

        binaan_bahy = self.mapping_service.get_binaan(858816179)
        self.assertEqual(len(binaan_bahy), 1)
        self.assertEqual(binaan_bahy[0]["name"], "Doni Nurdiansah")

    async def test_binaan_overview_today_status(self):
        # Mutabaah rows: Doni submitted today
        today_date = "2026-11-03"
        self.mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=[
            {
                "Date": today_date,
                "Telegram User ID": "819899948",
                "Full Name": "Doni",
                "Tilawah Pages": "20",
            }
        ])

        with patch("app.services.mapping.get_today_str", return_value=today_date):
            overview = await self.mapping_service.get_binaan_overview(218042450)
            self.assertEqual(overview["total_binaan"], 2)
            self.assertEqual(overview["submitted_today_count"], 1)
            self.assertEqual(overview["unsubmitted_today_count"], 1)

            b_doni = next(b for b in overview["binaan_list"] if b["id"] == "819899948")
            b_han = next(b for b in overview["binaan_list"] if b["id"] == "1809144522")
            self.assertTrue(b_doni["is_submitted_today"])
            self.assertFalse(b_han["is_submitted_today"])

    def test_main_menu_keyboard_visibility(self):
        # Murobbi gets Cek Mutabaah Binaan button
        kb_murobbi = get_main_menu_keyboard(is_murobbi=True, is_admin=False)
        all_texts_murobbi = [b.text for row in kb_murobbi.inline_keyboard for b in row]
        self.assertTrue(any("Cek Mutabaah Binaan" in t for t in all_texts_murobbi))

        # Non-murobbi does NOT get button
        kb_regular = get_main_menu_keyboard(is_murobbi=False, is_admin=False)
        all_texts_regular = [b.text for row in kb_regular.inline_keyboard for b in row]
        self.assertFalse(any("Cek Mutabaah Binaan" in t for t in all_texts_regular))

    def test_binaan_keyboards(self):
        binaan_list = [
            {"id": "819899948", "name": "Doni", "is_submitted_today": True},
            {"id": "1809144522", "name": "Han", "is_submitted_today": False},
        ]
        kb_list = get_binaan_list_keyboard(binaan_list)
        btn_data = [b.callback_data for row in kb_list.inline_keyboard for b in row]
        btn_texts = [b.text for row in kb_list.inline_keyboard for b in row]

        self.assertIn("binaan_detail_819899948", btn_data)
        self.assertIn("binaan_detail_1809144522", btn_data)
        self.assertIn("binaan_refresh", btn_data)
        self.assertIn("btn_main_menu", btn_data)

        self.assertTrue(any("✅ Doni" in t for t in btn_texts))
        self.assertTrue(any("🔴 Han" in t for t in btn_texts))

        kb_detail = get_binaan_detail_keyboard("819899948")
        detail_data = [b.callback_data for row in kb_detail.inline_keyboard for b in row]
        self.assertIn("binaan_list", detail_data)
        self.assertIn("binaan_period_weekly_819899948", detail_data)
        self.assertIn("binaan_period_monthly_819899948", detail_data)
        self.assertIn("binaan_period_custom_819899948", detail_data)
        self.assertIn("btn_main_menu", detail_data)

    async def test_cekbinaan_command_permission_denied(self):
        MappingService._instance = self.mapping_service

        update = MagicMock(spec=Update)
        user = MagicMock(spec=User)
        user.id = 999999999  # Not a murobbi
        user.first_name = "Regular User"
        update.effective_user = user
        update.callback_query = None
        message = MagicMock(spec=Message)
        message.reply_text = AsyncMock()
        update.message = message

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await cekbinaan_command(update, context)

        message.reply_text.assert_called_once()
        call_args = message.reply_text.call_args[0][0]
        self.assertIn("Akses Ditolak", call_args)

    async def test_cekbinaan_command_success_murobbi(self):
        MappingService._instance = self.mapping_service

        update = MagicMock(spec=Update)
        user = MagicMock(spec=User)
        user.id = 218042450  # Murobbi Nurhadi
        user.first_name = "Nurhadi"
        update.effective_user = user
        update.callback_query = None
        message = MagicMock(spec=Message)
        message.reply_text = AsyncMock()
        update.message = message

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await cekbinaan_command(update, context)

        message.reply_text.assert_called_once()
        call_args = message.reply_text.call_args[0][0]
        self.assertIn("Monitoring Mutabaah Binaan", call_args)
        self.assertIn("Nurhadi Sukma Waluyo", call_args)
        self.assertIn("Doni Nurdiansah", call_args)

    async def test_get_binaan_detail_period_weekly_and_custom(self):
        await self.mapping_service.reload_cache()
        detail_weekly = await self.mapping_service.get_binaan_detail(
            "819899948", period_key="weekly"
        )
        self.assertEqual(detail_weekly["meta"]["name"], "Doni Nurdiansah")
        self.assertEqual(detail_weekly["period_key"], "weekly")
        self.assertIn("period_progress", detail_weekly)

        detail_custom = await self.mapping_service.get_binaan_detail(
            "819899948",
            period_key="custom",
            start_date="2026-11-01",
            end_date="2026-11-07",
            period_label="Liqo Pekan 1",
        )
        self.assertEqual(detail_custom["period_key"], "custom")
        self.assertEqual(detail_custom["period_label"], "Liqo Pekan 1")
        self.assertIn("items", detail_custom["period_progress"])


if __name__ == "__main__":
    unittest.main()
