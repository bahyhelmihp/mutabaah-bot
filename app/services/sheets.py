import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
import gspread
from google.oauth2.service_account import Credentials
from app.config import Config
from app.utils.datetime import get_timestamp_str

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

MEMBERS_COLUMNS = [
    "Telegram User ID",
    "Telegram Username",
    "Full Name",
    "Registration Date",
    "Active",
]

MUTABAAH_COLUMNS = [
    "Date",
    "Telegram User ID",
    "Telegram Username",
    "Full Name",
    "Tilawah Pages",
    "Sholat Wajib",
    "Rawatib Rakaat",
    "Almatsurat",
    "Qiyamulail",
    "Dhuha",
    "Olahraga",
    "Submission Time",
    "Last Updated",
]


class SheetsService:
    _instance: Optional["SheetsService"] = None

    def __init__(self):
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
        self._members_worksheet: Optional[gspread.Worksheet] = None
        self._mutabaah_worksheet: Optional[gspread.Worksheet] = None
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "SheetsService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_credentials(self) -> Credentials:
        raw_cred = Config.GOOGLE_SERVICE_ACCOUNT_JSON
        if not raw_cred:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not configured in environment variables."
            )

        # Check if raw_cred is a file path that exists
        if os.path.exists(raw_cred):
            logger.info("Loading Google credentials from file: %s", raw_cred)
            return Credentials.from_service_account_file(raw_cred, scopes=SCOPES)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        abs_cred = os.path.join(project_root, raw_cred)
        if os.path.exists(abs_cred):
            logger.info("Loading Google credentials from file: %s", abs_cred)
            return Credentials.from_service_account_file(abs_cred, scopes=SCOPES)

        # Check if raw_cred is a JSON string
        try:
            cred_info = json.loads(raw_cred)
            logger.info("Loading Google credentials from JSON string environment variable.")
            return Credentials.from_service_account_info(cred_info, scopes=SCOPES)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"GOOGLE_SERVICE_ACCOUNT_JSON is neither a valid file path nor valid JSON: {exc}"
            )

    def _connect_sync(self):
        """Synchronous connection initialization and worksheet verification."""
        if self._spreadsheet is not None:
            return

        if not Config.GOOGLE_SHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID is not configured in environment variables.")

        credentials = self._get_credentials()
        self._client = gspread.authorize(credentials)
        self._spreadsheet = self._client.open_by_key(Config.GOOGLE_SHEET_ID)

        # Initialize Members worksheet
        self._members_worksheet = self._ensure_worksheet_sync(
            Config.SHEET_MEMBERS, MEMBERS_COLUMNS
        )

        # Initialize Daily Mutabaah worksheet
        self._mutabaah_worksheet = self._ensure_worksheet_sync(
            Config.SHEET_DAILY_MUTABAAH, MUTABAAH_COLUMNS
        )

    def _ensure_worksheet_sync(self, title: str, expected_headers: List[str]) -> gspread.Worksheet:
        """Finds worksheet by title or creates it with header row."""
        try:
            ws = self._spreadsheet.worksheet(title)
            # Verify or append header if empty
            existing_values = ws.get_all_values()
            if not existing_values:
                ws.append_row(expected_headers, value_input_option="USER_ENTERED")
            return ws
        except gspread.WorksheetNotFound:
            logger.info("Worksheet '%s' not found. Creating new worksheet.", title)
            ws = self._spreadsheet.add_worksheet(title=title, rows=1000, cols=len(expected_headers))
            ws.append_row(expected_headers, value_input_option="USER_ENTERED")
            return ws

    async def connect(self):
        """Ensure connected asynchronously."""
        async with self._lock:
            if self._spreadsheet is None:
                await asyncio.to_thread(self._connect_sync)

    # -------------------------------------------------------------
    # MEMBERS METHODS
    # -------------------------------------------------------------

    def _get_all_members_sync(self) -> List[Dict[str, Any]]:
        self._connect_sync()
        rows = self._members_worksheet.get_all_values()
        if len(rows) <= 1:
            return []
        headers = rows[0]
        result = []
        for row in rows[1:]:
            record = {}
            for col_idx, header in enumerate(headers):
                record[header] = row[col_idx] if col_idx < len(row) else ""
            result.append(record)
        return result

    async def get_all_members(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_members_sync)

    def _find_member_sync(self, user_id: int) -> Optional[Dict[str, Any]]:
        members = self._get_all_members_sync()
        str_user_id = str(user_id)
        for member in members:
            if str(member.get("Telegram User ID", "")).strip() == str_user_id:
                return member
        return None

    async def find_member(self, user_id: int) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._find_member_sync, user_id)

    def _register_member_sync(
        self, user_id: int, username: str, full_name: str, registration_date: str
    ) -> bool:
        self._connect_sync()
        rows = self._members_worksheet.get_all_values()
        str_user_id = str(user_id)

        # Check if already exists (update name / activate if exists)
        for idx, row in enumerate(rows[1:], start=2):
            if row and str(row[0]).strip() == str_user_id:
                # Update row
                updated_row = [
                    str_user_id,
                    username or (row[1] if len(row) > 1 else ""),
                    full_name or (row[2] if len(row) > 2 else ""),
                    row[3] if len(row) > 3 and row[3] else registration_date,
                    "TRUE",
                ]
                self._members_worksheet.update(f"A{idx}:E{idx}", [updated_row])
                return True

        # Append new member
        new_row = [str_user_id, username, full_name, registration_date, "TRUE"]
        self._members_worksheet.append_row(new_row, value_input_option="USER_ENTERED")
        return True

    async def register_member(
        self, user_id: int, username: str, full_name: str, registration_date: str
    ) -> bool:
        return await asyncio.to_thread(
            self._register_member_sync, user_id, username, full_name, registration_date
        )

    # -------------------------------------------------------------
    # DAILY MUTABAAH METHODS
    # -------------------------------------------------------------

    def _upsert_mutabaah_sync(self, data: Dict[str, Any]) -> bool:
        """
        Upsert a mutabaah submission for a given date and user_id.
        Data format expected:
        {
            "date": "YYYY-MM-DD",
            "user_id": int/str,
            "username": str,
            "full_name": str,
            "tilawah": int,
            "sholat_wajib": int,
            "rawatib": int,
            "almatsurat": int,
            "qiyamulail": bool,
            "dhuha": bool,
            "olahraga": bool,
            "timestamp": str,
        }
        """
        self._connect_sync()
        rows = self._mutabaah_worksheet.get_all_values()
        str_user_id = str(data["user_id"]).strip()
        target_date = str(data["date"]).strip()

        row_index_to_update = None
        existing_submission_time = data["timestamp"]

        for idx, row in enumerate(rows[1:], start=2):
            if len(row) >= 2:
                row_date = str(row[0]).strip()
                row_uid = str(row[1]).strip()
                if row_date == target_date and row_uid == str_user_id:
                    row_index_to_update = idx
                    if len(row) >= 12 and row[11]:
                        existing_submission_time = row[11]
                    break

        new_row = [
            target_date,
            str_user_id,
            data.get("username", ""),
            data.get("full_name", ""),
            int(data.get("tilawah", 0)),
            int(data.get("sholat_wajib", 0)),
            int(data.get("rawatib", 0)),
            int(data.get("almatsurat", 0)),
            "TRUE" if data.get("qiyamulail") else "FALSE",
            "TRUE" if data.get("dhuha") else "FALSE",
            "TRUE" if data.get("olahraga") else "FALSE",
            existing_submission_time,
            data["timestamp"],  # Last Updated
        ]

        if row_index_to_update:
            # Update existing row
            col_end = chr(ord('A') + len(new_row) - 1)
            cell_range = f"A{row_index_to_update}:{col_end}{row_index_to_update}"
            self._mutabaah_worksheet.update(cell_range, [new_row])
            logger.info("Updated mutabaah row %d for user %s on %s", row_index_to_update, str_user_id, target_date)
        else:
            # Append new row
            self._mutabaah_worksheet.append_row(new_row, value_input_option="USER_ENTERED")
            logger.info("Appended new mutabaah row for user %s on %s", str_user_id, target_date)

        return True

    async def upsert_mutabaah(self, data: Dict[str, Any]) -> bool:
        return await asyncio.to_thread(self._upsert_mutabaah_sync, data)

    def _get_user_mutabaah_record_sync(
        self, user_id: int, date_str: str
    ) -> Optional[Dict[str, Any]]:
        self._connect_sync()
        rows = self._mutabaah_worksheet.get_all_values()
        str_user_id = str(user_id).strip()
        target_date = str(date_str).strip()

        if len(rows) <= 1:
            return None

        headers = rows[0]
        for row in rows[1:]:
            if len(row) >= 2:
                if str(row[0]).strip() == target_date and str(row[1]).strip() == str_user_id:
                    record = {}
                    for c_idx, h in enumerate(headers):
                        record[h] = row[c_idx] if c_idx < len(row) else ""
                    return record
        return None

    async def get_user_mutabaah_record(
        self, user_id: int, date_str: str
    ) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_user_mutabaah_record_sync, user_id, date_str)

    def _get_all_mutabaah_rows_sync(self) -> List[Dict[str, Any]]:
        self._connect_sync()
        rows = self._mutabaah_worksheet.get_all_values()
        if len(rows) <= 1:
            return []
        headers = rows[0]
        result = []
        for row in rows[1:]:
            record = {}
            for c_idx, h in enumerate(headers):
                record[h] = row[c_idx] if c_idx < len(row) else ""
            result.append(record)
        return result

    async def get_all_mutabaah_rows(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_mutabaah_rows_sync)
