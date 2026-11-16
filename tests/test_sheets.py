import unittest
from unittest.mock import MagicMock
from app.services.sheets import (
    SheetsService,
    MUTABAAH_COLUMNS,
    SETTINGS_COLUMNS,
    SUMMARY_STATS_COLUMNS,
)


class TestSheetsUpsertLogic(unittest.TestCase):
    def test_columns_configuration(self):
        # Verify new amalan columns exist
        self.assertIn("Shalawat", MUTABAAH_COLUMNS)
        self.assertIn("Istighfar", MUTABAAH_COLUMNS)
        self.assertIn("Tadabbur Ayat", MUTABAAH_COLUMNS)
        self.assertIn("Shaum Sunnah", MUTABAAH_COLUMNS)
        self.assertIn("Silaturahim", MUTABAAH_COLUMNS)
        self.assertIn("Doa Ummat Islam", MUTABAAH_COLUMNS)
        self.assertEqual(len(MUTABAAH_COLUMNS), 19)
        self.assertIn("Target Silaturahim", SETTINGS_COLUMNS)
        self.assertIn("Target Doa Ummat", SETTINGS_COLUMNS)
        self.assertIn("Total Silaturahim", SUMMARY_STATS_COLUMNS)
        self.assertIn("Avg Doa Ummat", SUMMARY_STATS_COLUMNS)
        self.assertIn("Period", SUMMARY_STATS_COLUMNS)
        self.assertIn("Avg Completion (%)", SUMMARY_STATS_COLUMNS)

    def test_upsert_append_when_not_found(self):
        service = SheetsService()
        mock_ws = MagicMock()
        mock_ws.get_all_values.return_value = [MUTABAAH_COLUMNS]
        service._mutabaah_worksheet = mock_ws
        service._spreadsheet = MagicMock()

        data = {
            "date": "2026-10-14",
            "user_id": 12345,
            "username": "@testuser",
            "full_name": "Test User",
            "tilawah": 20,
            "sholat_wajib": 5,
            "rawatib": 12,
            "almatsurat": 2,
            "shalawat": 100,
            "istighfar": 100,
            "tadabbur": 1,
            "shaum_sunnah": True,
            "qiyamulail": True,
            "dhuha": True,
            "olahraga": True,
            "silaturahim": True,
            "doa_ummat_islam": 3,
            "timestamp": "2026-10-14 21:30:00",
        }

        service._upsert_mutabaah_sync(data)
        mock_ws.append_row.assert_called_once()
        args = mock_ws.append_row.call_args[0][0]
        self.assertEqual(args[0], "2026-10-14")
        self.assertEqual(args[1], "12345")
        # Check Shalawat, Istighfar, Tadabbur, Shaum Sunnah, Silaturahim, Doa Ummat Islam
        shalawat_idx = MUTABAAH_COLUMNS.index("Shalawat")
        istighfar_idx = MUTABAAH_COLUMNS.index("Istighfar")
        tadabbur_idx = MUTABAAH_COLUMNS.index("Tadabbur Ayat")
        shaum_idx = MUTABAAH_COLUMNS.index("Shaum Sunnah")
        silaturahim_idx = MUTABAAH_COLUMNS.index("Silaturahim")
        doa_idx = MUTABAAH_COLUMNS.index("Doa Ummat Islam")

        self.assertEqual(args[shalawat_idx], 100)
        self.assertEqual(args[istighfar_idx], 100)
        self.assertEqual(args[tadabbur_idx], 1)
        self.assertEqual(args[shaum_idx], "TRUE")
        self.assertEqual(args[silaturahim_idx], "TRUE")
        self.assertEqual(args[doa_idx], 3)

    def test_upsert_single_amalan_preserves_existing_data(self):
        """Test Requirement 4: single amalan entry preserves existing habits."""
        service = SheetsService()
        mock_ws = MagicMock()

        # Existing row with Tilawah=20, Sholat Wajib=5, Shalawat=0
        existing_row = [""] * len(MUTABAAH_COLUMNS)
        existing_row[MUTABAAH_COLUMNS.index("Date")] = "2026-10-14"
        existing_row[MUTABAAH_COLUMNS.index("Telegram User ID")] = "12345"
        existing_row[MUTABAAH_COLUMNS.index("Full Name")] = "Test User"
        existing_row[MUTABAAH_COLUMNS.index("Tilawah Pages")] = "20"
        existing_row[MUTABAAH_COLUMNS.index("Sholat Wajib")] = "5"
        existing_row[MUTABAAH_COLUMNS.index("Shalawat")] = "0"
        existing_row[MUTABAAH_COLUMNS.index("Submission Time")] = "2026-10-14 10:00:00"
        existing_row[MUTABAAH_COLUMNS.index("Last Updated")] = "2026-10-14 10:00:00"

        mock_ws.get_all_values.return_value = [MUTABAAH_COLUMNS, existing_row]
        service._mutabaah_worksheet = mock_ws
        service._spreadsheet = MagicMock()

        # User only updates Shalawat = 100
        single_update_data = {
            "date": "2026-10-14",
            "user_id": 12345,
            "shalawat": 100,
            "timestamp": "2026-10-14 15:00:00",
        }

        service._upsert_mutabaah_sync(single_update_data)
        mock_ws.update.assert_called_once()
        updated_values = mock_ws.update.call_args[0][1][0]

        # Verify Shalawat was updated
        shalawat_idx = MUTABAAH_COLUMNS.index("Shalawat")
        self.assertEqual(updated_values[shalawat_idx], 100)

        # Verify Tilawah and Sholat Wajib are preserved!
        tilawah_idx = MUTABAAH_COLUMNS.index("Tilawah Pages")
        wajib_idx = MUTABAAH_COLUMNS.index("Sholat Wajib")
        self.assertEqual(updated_values[tilawah_idx], 20)
        self.assertEqual(updated_values[wajib_idx], 5)

        # Submission time preserved
        sub_time_idx = MUTABAAH_COLUMNS.index("Submission Time")
        self.assertEqual(updated_values[sub_time_idx], "2026-10-14 10:00:00")
        # Last updated refreshed
        last_updated_idx = MUTABAAH_COLUMNS.index("Last Updated")
        self.assertEqual(updated_values[last_updated_idx], "2026-10-14 15:00:00")

    def test_upsert_berhalangan_value(self):
        """Verify that Berhalangan value is stored as text in Google Sheets."""
        service = SheetsService()
        mock_ws = MagicMock()
        mock_ws.get_all_values.return_value = [MUTABAAH_COLUMNS]
        service._mutabaah_worksheet = mock_ws
        service._spreadsheet = MagicMock()

        data = {
            "date": "2026-10-15",
            "user_id": 99999,
            "username": "@akhwat",
            "full_name": "Akhwat Test",
            "tilawah": "Berhalangan",
            "sholat_wajib": "Berhalangan",
            "rawatib": 0,
        }

        service._upsert_mutabaah_sync(data)
        mock_ws.append_row.assert_called_once()
        args = mock_ws.append_row.call_args[0][0]

        tilawah_idx = MUTABAAH_COLUMNS.index("Tilawah Pages")
        wajib_idx = MUTABAAH_COLUMNS.index("Sholat Wajib")
        self.assertEqual(args[tilawah_idx], "Berhalangan")
        self.assertEqual(args[wajib_idx], "Berhalangan")

    def test_save_and_get_user_settings(self):
        service = SheetsService()
        mock_settings_ws = MagicMock()
        mock_settings_ws.get_all_values.return_value = [
            SETTINGS_COLUMNS,
            ["12345", "tilawah,shalawat", "25", "5", "12", "2", "200", "100", "1", "4", "12", "12", "1", "2026-10-14 10:00:00"],
        ]
        service._settings_worksheet = mock_settings_ws
        service._spreadsheet = MagicMock()

        settings = service._get_user_settings_sync(12345)
        self.assertIsNotNone(settings)
        self.assertEqual(settings["Active Amalan"], "tilawah,shalawat")
        self.assertEqual(settings["Target Shalawat"], "200")

    def test_summary_stats_sheet_writer(self):
        service = SheetsService()
        mock_summary_ws = MagicMock()
        mock_summary_ws.get_all_values.return_value = [SUMMARY_STATS_COLUMNS]
        service._summary_stats_worksheet = mock_summary_ws
        service._spreadsheet = MagicMock()

        stats = {
            "period_label": "Pekan Ini",
            "start_date": "2026-10-08",
            "end_date": "2026-10-14",
            "registered_members": 10,
            "active_submitters": 8,
            "total_submissions": 35,
            "submission_rate": 80.0,
            "average_completion_rate": 85.5,
            "avg_tilawah": 18.2,
            "avg_wajib": 4.9,
            "avg_rawatib": 10.5,
            "avg_almatsurat": 1.8,
            "avg_shalawat": 120.0,
            "avg_istighfar": 95.0,
            "avg_tadabbur": 1.2,
            "count_shaum": 5,
            "count_qiyam": 12,
            "count_dhuha": 15,
            "count_olahraga": 20,
        }
        member_breakdown = [
            {
                "user_id": "111",
                "full_name": "Bahy Helmi",
                "username": "@bahyhelmihp",
                "days_submitted": 7,
                "total_tilawah": 140,
                "total_wajib": 35,
                "total_rawatib": 84,
                "total_almatsurat": 14,
                "total_shalawat": 700,
                "total_istighfar": 700,
                "total_tadabbur": 7,
                "count_shaum": 2,
                "count_qiyam": 3,
                "count_dhuha": 5,
                "count_olahraga": 5,
                "avg_completion": 98.0,
            }
        ]

        # Test log row append/update
        res_log = service._append_or_update_summary_log_sync(stats)
        self.assertTrue(res_log)
        mock_summary_ws.append_row.assert_called_once()

        # Test full report dashboard write
        res_report = service._write_summary_stats_report_sync(stats, member_breakdown)
        self.assertTrue(res_report)
        mock_summary_ws.clear.assert_called_once()
        mock_summary_ws.update.assert_called_once()

    def test_update_member_name_sync(self):
        service = SheetsService()
        mock_members_ws = MagicMock()
        mock_mutabaah_ws = MagicMock()

        # Existing member with old name
        mock_members_ws.get_all_values.return_value = [
            ["Telegram User ID", "Telegram Username", "Full Name", "Registration Date", "Active"],
            ["12345", "@olduser", "Old Name", "2026-10-14", "TRUE"],
        ]
        # Existing mutabaah row with old name
        mock_mutabaah_ws.get_all_values.return_value = [
            MUTABAAH_COLUMNS,
            ["2026-10-14", "12345", "@olduser", "Old Name", "20", "5", "12", "2", "100", "100", "1", "TRUE", "TRUE", "TRUE", "TRUE", "10:00", "10:00"],
        ]

        service._members_worksheet = mock_members_ws
        service._mutabaah_worksheet = mock_mutabaah_ws
        service._spreadsheet = MagicMock()

        res = service._update_member_name_sync(12345, "New Valid Name", "@newuser")
        self.assertTrue(res)

        # Verify members worksheet updated
        mock_members_ws.update.assert_called_once()
        updated_row = mock_members_ws.update.call_args[0][1][0]
        self.assertEqual(updated_row[0], "12345")
        self.assertEqual(updated_row[1], "@newuser")
        self.assertEqual(updated_row[2], "New Valid Name")

        # Verify mutabaah worksheet batch updated
        mock_mutabaah_ws.batch_update.assert_called_once()
        batch_args = mock_mutabaah_ws.batch_update.call_args[0][0]
        self.assertEqual(len(batch_args), 1)
        self.assertEqual(batch_args[0]["range"], "D2")
        self.assertEqual(batch_args[0]["values"], [["New Valid Name"]])


if __name__ == "__main__":
    unittest.main()

