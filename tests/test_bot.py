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
    format_missing_dates_id,
    get_recent_dates_list,
    INDONESIAN_MONTHS,
)
from app.config import Config
from app.services.amalan import (
    AMALAN_DEFINITIONS,
    ALL_AMALAN_KEYS,
    get_default_targets,
    get_amalan_info,
    format_amalan_value,
)
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_tilawah_keyboard,
    get_sholat_wajib_keyboard,
    get_rawatib_keyboard,
    get_almatsurat_keyboard,
    get_yes_no_keyboard,
    get_confirmation_keyboard,
    get_admin_keyboard,
    get_today_dashboard_keyboard,
    get_amalan_selection_keyboard,
    get_amalan_target_list_keyboard,
    get_target_options_keyboard,
    get_amalan_input_keyboard,
    get_date_picker_keyboard,
    get_edit_name_keyboard,
    get_progress_keyboard,
)

from telegram.ext import ConversationHandler
from app.services.members import MembersService
from app.services.statistics import StatisticsService
from app.services.settings import UserSettingsService
from app.handlers.profile import (
    edit_name_command,
    handle_new_name_input,
    cancel_edit_name,
    WAITING_NEW_NAME,
)



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
        self.assertEqual(len(menu.inline_keyboard), 4)

        tilawah = get_tilawah_keyboard()
        self.assertGreaterEqual(len(tilawah.inline_keyboard), 2)

        wajib = get_sholat_wajib_keyboard()
        self.assertGreaterEqual(len(wajib.inline_keyboard), 2)

        rawatib = get_rawatib_keyboard()
        self.assertGreaterEqual(len(rawatib.inline_keyboard), 2)

        almatsurat = get_almatsurat_keyboard()
        self.assertGreaterEqual(len(almatsurat.inline_keyboard), 2)

        yes_no = get_yes_no_keyboard()
        self.assertEqual(len(yes_no.inline_keyboard), 2)

        confirm = get_confirmation_keyboard()
        self.assertEqual(len(confirm.inline_keyboard), 2)

        admin_kb = get_admin_keyboard("test_sheet_id")
        self.assertEqual(len(admin_kb.inline_keyboard), 3)
        self.assertEqual(admin_kb.inline_keyboard[2][0].callback_data, "btn_main_menu")

        # New keyboards
        dashboard_kb = get_today_dashboard_keyboard(["tilawah", "shalawat", "istighfar"])
        self.assertGreater(len(dashboard_kb.inline_keyboard), 2)

        selection_kb = get_amalan_selection_keyboard(["tilawah", "shalawat"])
        self.assertGreater(len(selection_kb.inline_keyboard), 4)

        target_kb = get_amalan_target_list_keyboard({"shalawat": 100}, ["shalawat"])
        self.assertGreater(len(target_kb.inline_keyboard), 1)

        options_kb = get_target_options_keyboard("shalawat", 100)
        self.assertGreater(len(options_kb.inline_keyboard), 1)

        date_picker_kb = get_date_picker_keyboard()
        self.assertGreaterEqual(len(date_picker_kb.inline_keyboard), 4)

    def test_admin_config(self):
        Config.ADMIN_TELEGRAM_IDS = {12345, 67890}
        self.assertTrue(Config.is_admin(12345))
        self.assertTrue(Config.is_admin(67890))
        self.assertFalse(Config.is_admin(99999))


class TestAmalanDefinitions(unittest.TestCase):
    def test_required_amalan_present(self):
        # Requirement 1: Shalawat 100x, Istighfar 100x, Tadabbur 1 ayat, Shaum Sunnah 4/bln
        self.assertIn("shalawat", AMALAN_DEFINITIONS)
        self.assertIn("istighfar", AMALAN_DEFINITIONS)
        self.assertIn("tadabbur", AMALAN_DEFINITIONS)
        self.assertIn("shaum_sunnah", AMALAN_DEFINITIONS)
        self.assertIn("olahraga", AMALAN_DEFINITIONS)
        self.assertIn("silaturahim", AMALAN_DEFINITIONS)
        self.assertIn("doa_ummat_islam", AMALAN_DEFINITIONS)

        defaults = get_default_targets()
        self.assertEqual(defaults["shalawat"], 100)
        self.assertEqual(defaults["istighfar"], 100)
        self.assertEqual(defaults["tadabbur"], 1)
        self.assertEqual(defaults["shaum_sunnah"], 4)
        self.assertEqual(defaults["tilawah"], 20)
        self.assertEqual(defaults["sholat_wajib"], 5)
        # Olahraga default target 30 menit per minggu
        self.assertEqual(defaults["olahraga"], 30)
        self.assertEqual(defaults["silaturahim"], 4)
        self.assertEqual(defaults["doa_ummat_islam"], 1)

    def test_olahraga_definition(self):
        defn = get_amalan_info("olahraga")
        self.assertEqual(defn["type"], "int")
        self.assertEqual(defn["unit"], "menit")
        self.assertEqual(defn["default_target"], 30)
        self.assertEqual(defn["target_period"], "weekly")

    def test_new_amalan_definitions(self):
        silaturahim = get_amalan_info("silaturahim")
        self.assertEqual(silaturahim["type"], "bool")
        self.assertEqual(silaturahim["unit"], "hari")
        self.assertEqual(silaturahim["default_target"], 4)
        self.assertEqual(silaturahim["target_period"], "monthly")

        doa = get_amalan_info("doa_ummat_islam")
        self.assertEqual(doa["type"], "int")
        self.assertEqual(doa["unit"], "kali")
        self.assertEqual(doa["default_target"], 1)
        self.assertEqual(doa["target_period"], "daily")

    def test_format_amalan_value(self):
        self.assertEqual(format_amalan_value("shalawat", 100), "100 kali")
        self.assertEqual(format_amalan_value("shaum_sunnah", True), "✅ Ya")
        self.assertEqual(format_amalan_value("shaum_sunnah", False), "❌ Tidak")
        self.assertEqual(format_amalan_value("shaum_sunnah", None), "Belum diisi")
        self.assertEqual(format_amalan_value("olahraga", 30), "30 menit")
        self.assertEqual(format_amalan_value("olahraga", "TRUE"), "30 menit")
        self.assertEqual(format_amalan_value("silaturahim", True), "✅ Ya")
        self.assertEqual(format_amalan_value("silaturahim", False), "❌ Tidak")
        self.assertEqual(format_amalan_value("doa_ummat_islam", 3), "3 kali")


class TestUserSettingsService(unittest.IsolatedAsyncioTestCase):
    async def test_user_settings_service_toggle_and_target(self):
        mock_sheets = MagicMock()
        mock_sheets.get_all_user_settings = AsyncMock(return_value=[])
        mock_sheets.get_user_settings = AsyncMock(return_value=None)
        mock_sheets.save_user_settings = AsyncMock(return_value=True)

        service = UserSettingsService(sheets_service=mock_sheets)

        # Default settings
        settings = await service.get_user_settings(123)
        self.assertEqual(len(settings["active_amalan"]), len(ALL_AMALAN_KEYS))
        self.assertEqual(settings["targets"]["shalawat"], 100)

        # Requirement 3: Toggle amalan off (e.g. user excludes Qiyamulail)
        active = await service.toggle_amalan(123, "qiyamulail")
        self.assertNotIn("qiyamulail", active)
        self.assertIn("tilawah", active)

        # Requirement 2: Custom target adjustment
        targets = await service.set_target(123, "tilawah", 30)
        self.assertEqual(targets["tilawah"], 30)
        mock_sheets.save_user_settings.assert_called()


class TestStatisticsService(unittest.IsolatedAsyncioTestCase):
    async def test_calculate_user_month_progress_with_custom_amalan(self):
        mock_sheets = MagicMock()
        today_prefix = get_current_month_prefix("Asia/Seoul")
        mock_rows = [
            {
                "Date": f"{today_prefix}-01",
                "Telegram User ID": "111",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
                "Rawatib Rakaat": "12",
                "Almatsurat": "2",
                "Shalawat": "100",
                "Istighfar": "100",
                "Tadabbur Ayat": "1",
                "Shaum Sunnah": "TRUE",
                "Qiyamulail": "FALSE",
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
                "Shalawat": "50",
                "Istighfar": "100",
                "Tadabbur Ayat": "2",
                "Shaum Sunnah": "FALSE",
                "Qiyamulail": "FALSE",
                "Dhuha": "TRUE",
                "Olahraga": "FALSE",
            },
        ]
        mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=mock_rows)

        mock_members = MagicMock()

        # Mock settings service where QL is inactive
        mock_settings = MagicMock()
        # Active: tilawah, sholat_wajib, shalawat, shaum_sunnah (4 items)
        active_list = ["tilawah", "sholat_wajib", "shalawat", "shaum_sunnah"]
        custom_targets = {
            "tilawah": 20,
            "sholat_wajib": 5,
            "shalawat": 100,
            "shaum_sunnah": 4,
        }
        mock_settings.get_active_amalan = AsyncMock(return_value=active_list)
        mock_settings.get_user_targets = AsyncMock(return_value=custom_targets)

        stats_service = StatisticsService(
            sheets_service=mock_sheets,
            members_service=mock_members,
            settings_service=mock_settings,
        )

        res = await stats_service.calculate_user_month_progress(111)
        self.assertEqual(res["days_submitted"], 2)
        self.assertIn("submitted_dates", res)
        self.assertIn("missing_dates", res)
        self.assertEqual(len(res["submitted_dates"]), 2)
        self.assertIn("shalawat", res["items"])

        self.assertEqual(res["items"]["shalawat"]["actual"], 150)
        self.assertIn("shaum_sunnah", res["items"])
        self.assertEqual(res["items"]["shaum_sunnah"]["actual"], 1)
        self.assertNotIn("qiyamulail", res["items"])  # excluded by user preference!
        self.assertGreater(res["completion_percentage"], 0)

    async def test_calculate_period_admin_stats(self):
        mock_sheets = MagicMock()
        mock_rows = [
            {
                "Date": "2026-10-01",
                "Telegram User ID": "111",
                "Full Name": "User Satu",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
                "Rawatib Rakaat": "12",
                "Almatsurat": "2",
                "Shalawat": "100",
                "Istighfar": "100",
                "Tadabbur Ayat": "1",
                "Shaum Sunnah": "TRUE",
                "Qiyamulail": "TRUE",
                "Dhuha": "TRUE",
                "Olahraga": "TRUE",
                "Silaturahim": "TRUE",
                "Doa Ummat Islam": "2",
            },
            {
                "Date": "2026-10-05",
                "Telegram User ID": "222",
                "Full Name": "User Dua",
                "Tilawah Pages": "10",
                "Sholat Wajib": "4",
                "Rawatib Rakaat": "6",
                "Almatsurat": "1",
                "Shalawat": "50",
                "Istighfar": "50",
                "Tadabbur Ayat": "0",
                "Shaum Sunnah": "FALSE",
                "Qiyamulail": "FALSE",
                "Dhuha": "TRUE",
                "Olahraga": "FALSE",
                "Silaturahim": "FALSE",
                "Doa Ummat Islam": "1",
            },
            {
                # Out-of-period row (September)
                "Date": "2026-09-20",
                "Telegram User ID": "111",
                "Tilawah Pages": "20",
            },
        ]
        mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=mock_rows)

        mock_members = MagicMock()
        mock_members.get_all_active_members = AsyncMock(return_value=[
            {"Telegram User ID": "111", "Full Name": "User Satu", "Active": "TRUE"},
            {"Telegram User ID": "222", "Full Name": "User Dua", "Active": "TRUE"},
            {"Telegram User ID": "333", "Full Name": "User Tiga", "Active": "TRUE"},
        ])

        stats_service = StatisticsService(sheets_service=mock_sheets, members_service=mock_members)

        # Test period 2026-10-01 to 2026-10-10
        stats = await stats_service.calculate_period_admin_stats(
            start_date="2026-10-01",
            end_date="2026-10-10",
            period_label="Pekan 1 Oktober",
        )

        self.assertEqual(stats["registered_members"], 3)
        self.assertEqual(stats["total_submissions"], 2)  # Sept row excluded
        self.assertEqual(stats["active_submitters"], 2)
        self.assertEqual(stats["total_tilawah"], 30)
        self.assertEqual(stats["avg_tilawah"], 15.0)
        self.assertEqual(stats["total_shalawat"], 150)
        self.assertEqual(stats["count_shaum"], 1)
        self.assertEqual(stats["count_silaturahim"], 1)
        self.assertEqual(stats["total_doa_ummat"], 3)
        self.assertEqual(stats["avg_doa_ummat"], 1.5)
        self.assertEqual(len(stats["member_breakdown"]), 3)
        # Top member should be User Satu (submitted 1 day with higher score)
        self.assertEqual(stats["member_breakdown"][0]["user_id"], "111")
        self.assertEqual(stats["member_breakdown"][0]["count_silaturahim"], 1)
        self.assertEqual(stats["member_breakdown"][0]["total_doa_ummat"], 2)
        self.assertEqual(stats["min_tilawah"], 10.0)
        self.assertEqual(stats["max_tilawah"], 20.0)
        self.assertEqual(stats["total_olahraga"], 30)
        self.assertTrue(len(stats["member_breakdown"][0]["highlights"]) > 0)
        self.assertEqual(stats["dhuha_members"], 2)
        self.assertEqual(stats["pct_dhuha_members"], 100.0)
        self.assertEqual(stats["avg_dhuha_per_member"], 1.0)

        # Test format_admin_stats_text output
        from app.handlers.admin import format_admin_stats_text
        formatted = format_admin_stats_text(stats)
        self.assertIn("Olahraga:", formatted)
        self.assertIn("mnt", formatted)
        self.assertNotIn("805 hari", formatted)
        self.assertIn("Rentang:", formatted)
        self.assertIn("Top 3 Anggota Terajin", formatted)
        self.assertIn("Unggul di:", formatted)
        self.assertIn("orang", formatted)
        self.assertIn("member", formatted)
        self.assertIn("15 hal/hari", formatted)
        self.assertIn("5 waktu/hari", formatted)

        # Test calculate_period_admin_stats with kelompok_filter
        from unittest.mock import patch
        with patch("app.services.mapping.MappingService.get_instance") as mock_map_inst:
            mock_map = MagicMock()
            mock_map.reload_cache = AsyncMock()
            mock_map.get_member_kelompok = MagicMock(side_effect=lambda uid, fname: "Muayyid" if uid == "111" else "Muntasib")
            mock_map_inst.return_value = mock_map

            stats_muayyid = await stats_service.calculate_period_admin_stats(
                start_date="2026-10-01",
                end_date="2026-10-10",
                period_label="Pekan 1 Oktober",
                kelompok_filter="Muayyid",
            )
            self.assertEqual(stats_muayyid["registered_members"], 1)
            self.assertEqual(stats_muayyid["active_submitters"], 1)
            self.assertEqual(stats_muayyid["total_tilawah"], 20)
            self.assertEqual(stats_muayyid["kelompok_filter"], "Muayyid")

            formatted_k = format_admin_stats_text(stats_muayyid)
            self.assertIn("Kelompok:", formatted_k)
            self.assertIn("Muayyid", formatted_k)

        # Test get_admin_period_keyboard with kelompok
        from app.keyboards.common import get_admin_period_keyboard
        markup = get_admin_period_keyboard("sheet123", "monthly", "Muayyid", ["Muntasib", "Muayyid"])
        btn_texts = [b.text for row in markup.inline_keyboard for b in row]
        self.assertIn("✅ Muayyid", btn_texts)
        self.assertIn("Muntasib", btn_texts)
        self.assertIn("Semua", btn_texts)


class TestDatePresetsAndCustomParser(unittest.TestCase):
    def test_date_range_presets(self):
        from app.utils.datetime import get_date_range_presets
        presets = get_date_range_presets("Asia/Seoul")
        self.assertIn("today", presets)
        self.assertIn("weekly", presets)
        self.assertIn("monthly", presets)
        self.assertIn("last_month", presets)
        self.assertEqual(presets["today"]["start_date"], presets["today"]["end_date"])
        self.assertLessEqual(presets["weekly"]["start_date"], presets["weekly"]["end_date"])

    def test_parse_custom_date_range(self):
        from app.utils.datetime import parse_custom_date_range
        # Range with s/d
        res1 = parse_custom_date_range("2026-10-01 s/d 2026-10-14")
        self.assertIsNotNone(res1)
        self.assertEqual(res1["start_date"], "2026-10-01")
        self.assertEqual(res1["end_date"], "2026-10-14")

        # Range with hyphen
        res2 = parse_custom_date_range("2026-10-05 - 2026-10-20")
        self.assertIsNotNone(res2)
        self.assertEqual(res2["start_date"], "2026-10-05")
        self.assertEqual(res2["end_date"], "2026-10-20")

        # Single date
        res3 = parse_custom_date_range("2026-10-14")
        self.assertIsNotNone(res3)
        self.assertEqual(res3["start_date"], "2026-10-14")
        self.assertEqual(res3["end_date"], "2026-10-14")

    def test_parse_date_input(self):
        from app.utils.datetime import parse_date_input, get_today_str
        today_str = get_today_str("Asia/Seoul")

        self.assertEqual(parse_date_input("hari ini", "Asia/Seoul"), today_str)
        self.assertEqual(parse_date_input("today", "Asia/Seoul"), today_str)
        self.assertIsNotNone(parse_date_input("kemarin", "Asia/Seoul"))
        self.assertEqual(parse_date_input("2026-10-14"), "2026-10-14")
        self.assertEqual(parse_date_input("14-10-2026"), "2026-10-14")
        self.assertEqual(parse_date_input("14/10/2026"), "2026-10-14")
        self.assertIsNone(parse_date_input("invalid date"))

    def test_get_recent_dates_list(self):
        from app.utils.datetime import get_recent_dates_list
        dates = get_recent_dates_list(num_days=6, tz_name="Asia/Seoul")
        self.assertEqual(len(dates), 7)
        self.assertTrue(dates[0]["is_today"])
        self.assertTrue(dates[1]["is_yesterday"])
        self.assertIn("Kemarin", dates[1]["label"])

    def test_edit_name_keyboard(self):
        kb = get_edit_name_keyboard()
        self.assertEqual(len(kb.inline_keyboard), 1)
        self.assertEqual(kb.inline_keyboard[0][0].callback_data, "cancel_edit_name")

    def test_format_missing_dates_id(self):
        # Empty
        self.assertEqual(format_missing_dates_id([]), "")
        # Single
        self.assertEqual(format_missing_dates_id(["2026-10-05"]), "5 Oktober")
        # Multiple
        self.assertEqual(format_missing_dates_id(["2026-10-02", "2026-10-05", "2026-10-18"]), "2, 5, 18 Oktober")
        # Long sequence (> 10 days)
        long_list = [f"2026-10-{d:02d}" for d in range(1, 11)] + ["2026-10-15", "2026-10-18"]
        res = format_missing_dates_id(long_list)
        self.assertIn("1-10", res)
        self.assertIn("15", res)

    def test_date_picker_keyboard_with_indicators(self):
        # Passed submitted_dates from recent list so test is time-agnostic
        recent = get_recent_dates_list(num_days=6, tz_name="Asia/Seoul")
        submitted = {recent[0]["date"]}
        missing = ["2026-05-02", "2026-05-05"]
        kb = get_date_picker_keyboard(
            tz_name="Asia/Seoul",
            submitted_dates=submitted,
            missing_dates=missing,
        )
        all_btn_texts = [btn.text for row in kb.inline_keyboard for btn in row]
        # Should contain ✅ and 🔴 icons
        has_green = any("✅" in t for t in all_btn_texts)
        has_red = any("🔴" in t for t in all_btn_texts)
        self.assertTrue(has_green)
        self.assertTrue(has_red)
        # Should contain older missing date button (e.g. 2 Mei / 5 Mei)
        has_older = any("2 Mei" in t or "5 Mei" in t for t in all_btn_texts)
        self.assertTrue(has_older)

    def test_progress_keyboard(self):
        kb_missing = get_progress_keyboard(has_missing=True)
        btn_data = [btn.callback_data for row in kb_missing.inline_keyboard for btn in row]
        self.assertIn("btn_edit", btn_data)
        self.assertIn("btn_isi", btn_data)
        self.assertIn("btn_main_menu", btn_data)

        kb_no_missing = get_progress_keyboard(has_missing=False)
        btn_data_no = [btn.callback_data for row in kb_no_missing.inline_keyboard for btn in row]
        self.assertNotIn("btn_edit", btn_data_no)
        self.assertIn("btn_isi", btn_data_no)



class TestEditNameFeature(unittest.IsolatedAsyncioTestCase):
    async def test_members_service_update_name(self):
        mock_sheets = MagicMock()
        mock_sheets.update_member_name = AsyncMock(return_value=True)

        members_service = MembersService(sheets_service=mock_sheets)
        members_service._cache["12345"] = {
            "Telegram User ID": "12345",
            "Telegram Username": "@olduser",
            "Full Name": "Old Name",
            "Registration Date": "2026-10-14",
            "Active": "TRUE",
        }

        res = await members_service.update_name(12345, "Nama Baru Lengkap", "newuser")
        self.assertTrue(res)
        self.assertEqual(members_service._cache["12345"]["Full Name"], "Nama Baru Lengkap")
        self.assertEqual(members_service._cache["12345"]["Telegram Username"], "@newuser")
        mock_sheets.update_member_name.assert_called_once_with(
            user_id=12345,
            new_full_name="Nama Baru Lengkap",
            username="@newuser",
        )

    async def test_edit_name_command_registered(self):
        update = MagicMock()
        user = MagicMock()
        user.id = 12345
        user.first_name = "User"
        update.effective_user = user
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        with patch("app.handlers.profile.MembersService") as MockMS:
            inst = MockMS.return_value
            inst.is_registered = AsyncMock(return_value=True)
            inst.get_member = AsyncMock(return_value={"Full Name": "Nama Lama"})

            state = await edit_name_command(update, MagicMock())
            self.assertEqual(state, WAITING_NEW_NAME)
            update.message.reply_text.assert_called_once()
            call_text = update.message.reply_text.call_args.kwargs.get("text") or update.message.reply_text.call_args[0][0]
            self.assertIn("Nama Lama", call_text)


    async def test_edit_name_command_unregistered(self):
        update = MagicMock()
        user = MagicMock()
        user.id = 99999
        update.effective_user = user
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        with patch("app.handlers.profile.MembersService") as MockMS:
            inst = MockMS.return_value
            inst.is_registered = AsyncMock(return_value=False)

            state = await edit_name_command(update, MagicMock())
            self.assertEqual(state, ConversationHandler.END)
            call_text = update.message.reply_text.call_args[0][0]
            self.assertIn("belum terdaftar", call_text)

    async def test_handle_new_name_validation(self):
        update = MagicMock()
        user = MagicMock()
        user.id = 12345
        user.username = "testuser"
        update.effective_user = user
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        # Case 1: Too short
        update.message.text = "A"
        state_short = await handle_new_name_input(update, MagicMock())
        self.assertEqual(state_short, WAITING_NEW_NAME)
        self.assertIn("terlalu pendek", update.message.reply_text.call_args[0][0])

        # Case 2: Too long
        update.message.text = "A" * 105
        state_long = await handle_new_name_input(update, MagicMock())
        self.assertEqual(state_long, WAITING_NEW_NAME)
        self.assertIn("terlalu panjang", update.message.reply_text.call_args[0][0])

        # Case 3: Valid name
        update.message.text = "Ahmad Dahlan"
        with patch("app.handlers.profile.MembersService") as MockMS:
            inst = MockMS.return_value
            inst.update_name = AsyncMock(return_value=True)

            state_valid = await handle_new_name_input(update, MagicMock())
            self.assertEqual(state_valid, ConversationHandler.END)
            self.assertIn("Ahmad Dahlan", update.message.reply_text.call_args[0][0])

    async def test_cancel_edit_name(self):
        update = MagicMock()
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        state = await cancel_edit_name(update, MagicMock())
        self.assertEqual(state, ConversationHandler.END)
        self.assertIn("dibatalkan", update.message.reply_text.call_args[0][0])


class TestMissingDatesWorkflow(unittest.IsolatedAsyncioTestCase):
    async def test_progress_command_with_missing_dates(self):
        from app.handlers.progress import progress_command

        update = MagicMock()
        user = MagicMock()
        user.id = 12345
        update.effective_user = user
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        mock_data = {
            "month_label": "Oktober 2026",
            "days_submitted": 10,
            "days_passed": 12,
            "missing_dates": ["2026-10-02", "2026-10-05"],
            "submitted_dates": ["2026-10-01", "2026-10-03"],
            "items": {},
            "completion_percentage": 83.3,
        }

        with patch("app.handlers.progress.MembersService") as MockMS, \
             patch("app.handlers.progress.StatisticsService") as MockStats:
            MockMS.return_value.is_registered = AsyncMock(return_value=True)
            MockStats.return_value.calculate_user_month_progress = AsyncMock(return_value=mock_data)

            await progress_command(update, MagicMock())

            update.message.reply_text.assert_called_once()
            call_text = update.message.reply_text.call_args[0][0]
            call_markup = update.message.reply_text.call_args.kwargs.get("reply_markup") or update.message.reply_text.call_args[0][1]

            self.assertIn("Tanggal belum diisi", call_text)
            self.assertIn("2, 5 Oktober", call_text)
            btn_data = [btn.callback_data for row in call_markup.inline_keyboard for btn in row]
            self.assertIn("btn_edit", btn_data)

    async def test_progress_command_all_filled(self):
        from app.handlers.progress import progress_command

        update = MagicMock()
        user = MagicMock()
        user.id = 12345
        update.effective_user = user
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        mock_data = {
            "month_label": "Oktober 2026",
            "days_submitted": 12,
            "days_passed": 12,
            "missing_dates": [],
            "submitted_dates": [f"2026-10-{d:02d}" for d in range(1, 13)],
            "items": {},
            "completion_percentage": 100.0,
        }

        with patch("app.handlers.progress.MembersService") as MockMS, \
             patch("app.handlers.progress.StatisticsService") as MockStats:
            MockMS.return_value.is_registered = AsyncMock(return_value=True)
            MockStats.return_value.calculate_user_month_progress = AsyncMock(return_value=mock_data)

            await progress_command(update, MagicMock())

            call_text = update.message.reply_text.call_args[0][0]
            self.assertIn("semua hari bulan ini telah terisi", call_text)

    async def test_show_date_picker_with_missing_dates(self):
        from app.handlers.mutabaah import show_date_picker

        update = MagicMock()
        update.callback_query = None
        update.effective_message.reply_text = AsyncMock()
        update.message = update.effective_message


        mock_data = {
            "month_label": "Oktober 2026",
            "days_submitted": 8,
            "days_passed": 10,
            "missing_dates": ["2026-10-02", "2026-10-05"],
            "submitted_dates": ["2026-10-01", "2026-10-03"],
        }

        with patch("app.handlers.mutabaah.StatisticsService") as MockStats:
            MockStats.return_value.calculate_user_month_progress = AsyncMock(return_value=mock_data)

            state = await show_date_picker(update, MagicMock(), user_id=12345)
            self.assertIsNotNone(state)
            update.message.reply_text.assert_called_once()
            call_text = update.message.reply_text.call_args.kwargs.get("text") or update.message.reply_text.call_args[0][0]
            self.assertIn("Tanggal belum diisi", call_text)
            self.assertIn("2, 5 Oktober", call_text)



class TestBerhalanganFeature(unittest.IsolatedAsyncioTestCase):
    def test_berhalangan_in_keyboards(self):
        tilawah_kb = get_amalan_input_keyboard("tilawah")
        tilawah_cbs = [btn.callback_data for row in tilawah_kb.inline_keyboard for btn in row]
        self.assertIn("val_berhalangan", tilawah_cbs)

        wajib_kb = get_amalan_input_keyboard("sholat_wajib")
        wajib_cbs = [btn.callback_data for row in wajib_kb.inline_keyboard for btn in row]
        self.assertIn("val_berhalangan", wajib_cbs)

        # Shalawat should not have berhalangan
        shalawat_kb = get_amalan_input_keyboard("shalawat")
        shalawat_cbs = [btn.callback_data for row in shalawat_kb.inline_keyboard for btn in row]
        self.assertNotIn("val_berhalangan", shalawat_cbs)

    def test_parse_input_value_berhalangan(self):
        from app.handlers.mutabaah import parse_input_value

        tilawah_defn = get_amalan_info("tilawah")

        # Test callback query
        update_cb = MagicMock()
        update_cb.callback_query.data = "val_berhalangan"
        update_cb.message = None
        self.assertEqual(parse_input_value(update_cb, tilawah_defn), "Berhalangan")

        # Test text message "berhalangan" and "haid"
        update_txt1 = MagicMock()
        update_txt1.callback_query = None
        update_txt1.message.text = "berhalangan"
        self.assertEqual(parse_input_value(update_txt1, tilawah_defn), "Berhalangan")

        update_txt2 = MagicMock()
        update_txt2.callback_query = None
        update_txt2.message.text = "Haid"
        self.assertEqual(parse_input_value(update_txt2, tilawah_defn), "Berhalangan")

    def test_format_amalan_value_berhalangan(self):
        self.assertEqual(format_amalan_value("tilawah", "Berhalangan"), "🌸 Berhalangan")
        self.assertEqual(format_amalan_value("sholat_wajib", "haid"), "🌸 Berhalangan")

    async def test_user_month_progress_excludes_berhalangan(self):
        mock_sheets = MagicMock()
        # Mock 3 days in current month: 2 days fulfilled (20 hal, 5 waktu), 1 day berhalangan
        mock_rows = [
            {
                "Date": "2026-10-01",
                "Telegram User ID": "999",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
            },
            {
                "Date": "2026-10-02",
                "Telegram User ID": "999",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
            },
            {
                "Date": "2026-10-03",
                "Telegram User ID": "999",
                "Tilawah Pages": "Berhalangan",
                "Sholat Wajib": "Berhalangan",
            },
        ]
        mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=mock_rows)

        mock_settings = MagicMock()
        mock_settings.get_active_amalan = AsyncMock(return_value=["tilawah", "sholat_wajib"])
        mock_settings.get_user_targets = AsyncMock(return_value={"tilawah": 20, "sholat_wajib": 5})

        stats_service = StatisticsService(sheets_service=mock_sheets, settings_service=mock_settings)

        # Mock current day as day 3
        with patch("app.services.statistics.get_now") as mock_now, \
             patch("app.services.statistics.get_current_month_prefix", return_value="2026-10"):
            mock_dt = datetime(2026, 10, 3, 12, 0, tzinfo=pytz.timezone("Asia/Seoul"))
            mock_now.return_value = mock_dt

            res = await stats_service.calculate_user_month_progress(999)

            # Days passed = 3, but 1 day berhalangan -> effective days = 2
            # Target tilawah = 20 * 2 = 40 (not 60)
            self.assertEqual(res["items"]["tilawah"]["target"], 40)
            self.assertEqual(res["items"]["tilawah"]["actual"], 40)
            self.assertEqual(res["items"]["tilawah"]["ratio"], 1.0)
            self.assertEqual(res["items"]["tilawah"]["berhalangan_days"], 1)

            # Target sholat wajib = 5 * 2 = 10 (not 15)
            self.assertEqual(res["items"]["sholat_wajib"]["target"], 10)
            self.assertEqual(res["items"]["sholat_wajib"]["actual"], 10)
            self.assertEqual(res["items"]["sholat_wajib"]["ratio"], 1.0)
            self.assertEqual(res["items"]["sholat_wajib"]["berhalangan_days"], 1)

            # 100% completion rate because non-berhalangan days were fully met!
            self.assertEqual(res["completion_percentage"], 100.0)

    async def test_admin_stats_excludes_berhalangan(self):
        mock_sheets = MagicMock()
        mock_rows = [
            {
                "Date": "2026-10-01",
                "Telegram User ID": "111",
                "Full Name": "User Satu",
                "Tilawah Pages": "20",
                "Sholat Wajib": "5",
                "Rawatib Rakaat": "12",
                "Almatsurat": "2",
                "Shalawat": "100",
                "Istighfar": "100",
                "Tadabbur Ayat": "1",
            },
            {
                "Date": "2026-10-02",
                "Telegram User ID": "222",
                "Full Name": "User Dua",
                "Tilawah Pages": "Berhalangan",
                "Sholat Wajib": "Berhalangan",
                "Rawatib Rakaat": "12",
                "Almatsurat": "2",
                "Shalawat": "100",
                "Istighfar": "100",
                "Tadabbur Ayat": "1",
            },
        ]
        mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=mock_rows)
        mock_members = MagicMock()
        mock_members.get_all_active_members = AsyncMock(return_value=[
            {"Telegram User ID": "111", "Full Name": "User Satu", "Active": "TRUE"},
            {"Telegram User ID": "222", "Full Name": "User Dua", "Active": "TRUE"},
        ])

        stats_service = StatisticsService(sheets_service=mock_sheets, members_service=mock_members)
        stats = await stats_service.calculate_period_admin_stats(
            start_date="2026-10-01",
            end_date="2026-10-02",
            period_label="Tes Berhalangan",
        )

        # Average Tilawah should be 20.0 (not 10.0), because Berhalangan is excluded from the average
        self.assertEqual(stats["avg_tilawah"], 20.0)
        # Average Sholat Wajib should be 5.0 (not 2.5)
        self.assertEqual(stats["avg_wajib"], 5.0)
        # Overall completion rate should not be dragged down by Berhalangan
        self.assertEqual(stats["average_completion_rate"], 100.0)

    async def test_user_month_progress_includes_previous_month_dates(self):
        mock_sheets = MagicMock()
        mock_rows = [
            {"Date": "2026-10-31", "Telegram User ID": "123", "Tilawah Pages": "20"},
            {"Date": "2026-11-01", "Telegram User ID": "123", "Tilawah Pages": "20"},
        ]
        mock_sheets.get_all_mutabaah_rows = AsyncMock(return_value=mock_rows)
        mock_settings = MagicMock()
        mock_settings.get_active_amalan = AsyncMock(return_value=["tilawah"])
        mock_settings.get_user_targets = AsyncMock(return_value={"tilawah": 20})

        stats_service = StatisticsService(sheets_service=mock_sheets, settings_service=mock_settings)
        with patch("app.services.statistics.get_current_month_prefix", return_value="2026-11"):
            res = await stats_service.calculate_user_month_progress(123)
            # submitted_dates is current month only
            self.assertEqual(res["submitted_dates"], ["2026-11-01"])
            # all_submitted_dates includes October
            self.assertIn("2026-10-31", res["all_submitted_dates"])
            self.assertIn("2026-11-01", res["all_submitted_dates"])


if __name__ == "__main__":
    unittest.main()


