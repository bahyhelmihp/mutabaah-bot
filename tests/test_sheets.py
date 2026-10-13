import unittest
from unittest.mock import MagicMock
from app.services.sheets import SheetsService


class TestSheetsUpsertLogic(unittest.TestCase):
    def test_upsert_append_when_not_found(self):
        service = SheetsService()
        mock_ws = MagicMock()
        # Initial rows with header only
        mock_ws.get_all_values.return_value = [
            ["Date", "Telegram User ID", "Telegram Username", "Full Name", "Tilawah Pages", "Sholat Wajib", "Rawatib Rakaat", "Almatsurat", "Qiyamulail", "Dhuha", "Olahraga", "Submission Time", "Last Updated"]
        ]
        service._mutabaah_worksheet = mock_ws
        service._spreadsheet = MagicMock()

        data = {
            "date": "2026-10-13",
            "user_id": 12345,
            "username": "@testuser",
            "full_name": "Test User",
            "tilawah": 20,
            "sholat_wajib": 5,
            "rawatib": 12,
            "almatsurat": 2,
            "qiyamulail": True,
            "dhuha": True,
            "olahraga": True,
            "timestamp": "2026-10-13 21:30:00",
        }

        service._upsert_mutabaah_sync(data)
        mock_ws.append_row.assert_called_once()
        args = mock_ws.append_row.call_args[0][0]
        self.assertEqual(args[0], "2026-10-13")
        self.assertEqual(args[1], "12345")
        self.assertEqual(args[4], 20)
        self.assertEqual(args[8], "TRUE")

    def test_upsert_update_when_exists(self):
        service = SheetsService()
        mock_ws = MagicMock()
        mock_ws.get_all_values.return_value = [
            ["Date", "Telegram User ID", "Telegram Username", "Full Name", "Tilawah Pages", "Sholat Wajib", "Rawatib Rakaat", "Almatsurat", "Qiyamulail", "Dhuha", "Olahraga", "Submission Time", "Last Updated"],
            ["2026-10-13", "12345", "@testuser", "Test User", "5", "3", "0", "1", "FALSE", "FALSE", "FALSE", "2026-10-13 10:00:00", "2026-10-13 10:00:00"],
        ]
        service._mutabaah_worksheet = mock_ws
        service._spreadsheet = MagicMock()

        data = {
            "date": "2026-10-13",
            "user_id": 12345,
            "username": "@testuser",
            "full_name": "Test User",
            "tilawah": 25,
            "sholat_wajib": 5,
            "rawatib": 12,
            "almatsurat": 2,
            "qiyamulail": True,
            "dhuha": True,
            "olahraga": True,
            "timestamp": "2026-10-13 21:30:00",
        }

        service._upsert_mutabaah_sync(data)
        # Should call update on row 2 (A2:M2) instead of append_row
        mock_ws.update.assert_called_once()
        cell_range = mock_ws.update.call_args[0][0]
        updated_values = mock_ws.update.call_args[0][1][0]
        self.assertEqual(cell_range, "A2:M2")
        self.assertEqual(updated_values[4], 25)
        # Submission time preserved
        self.assertEqual(updated_values[11], "2026-10-13 10:00:00")
        # Last updated refreshed
        self.assertEqual(updated_values[12], "2026-10-13 21:30:00")


if __name__ == "__main__":
    unittest.main()
