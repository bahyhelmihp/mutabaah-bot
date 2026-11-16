import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
import gspread
from gspread.utils import rowcol_to_a1
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
    "Shalawat",
    "Istighfar",
    "Tadabbur Ayat",
    "Shaum Sunnah",
    "Qiyamulail",
    "Dhuha",
    "Olahraga",
    "Silaturahim",
    "Doa Ummat Islam",
    "Submission Time",
    "Last Updated",
]

SETTINGS_COLUMNS = [
    "Telegram User ID",
    "Active Amalan",
    "Target Tilawah",
    "Target Sholat Wajib",
    "Target Rawatib",
    "Target Almatsurat",
    "Target Shalawat",
    "Target Istighfar",
    "Target Tadabbur",
    "Target Shaum Sunnah",
    "Target Qiyamulail",
    "Target Dhuha",
    "Target Olahraga",
    "Target Silaturahim",
    "Target Doa Ummat",
    "Last Updated",
]

SUMMARY_STATS_COLUMNS = [
    "Period",
    "Start Date",
    "End Date",
    "Registered Members",
    "Active Submitters",
    "Total Submissions",
    "Submission Rate (%)",
    "Avg Completion (%)",
    "Avg Tilawah (pages)",
    "Avg Sholat Wajib",
    "Avg Rawatib (rakaat)",
    "Avg Almatsurat",
    "Avg Shalawat",
    "Avg Istighfar",
    "Avg Tadabbur",
    "Total Shaum Sunnah",
    "Total Qiyamulail",
    "Total Dhuha",
    "Total Olahraga (menit)",
    "Total Silaturahim",
    "Avg Doa Ummat",
    "Generated At",
]

MAPPING_COLUMNS = [
    "Murobbi ID",
    "Murobbi",
    "Mutarabbi ID",
    "Mutarabbi",
    "Kelompok",
]


class SheetsService:
    _instance: Optional["SheetsService"] = None

    def __init__(self):
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
        self._members_worksheet: Optional[gspread.Worksheet] = None
        self._mutabaah_worksheet: Optional[gspread.Worksheet] = None
        self._settings_worksheet: Optional[gspread.Worksheet] = None
        self._summary_stats_worksheet: Optional[gspread.Worksheet] = None
        self._mapping_worksheet: Optional[gspread.Worksheet] = None
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

        # Initialize User Settings worksheet
        self._settings_worksheet = self._ensure_worksheet_sync(
            Config.SHEET_USER_SETTINGS, SETTINGS_COLUMNS
        )

        # Initialize Summary Stats worksheet
        self._summary_stats_worksheet = self._ensure_worksheet_sync(
            Config.SHEET_SUMMARY_STATS, SUMMARY_STATS_COLUMNS
        )

        # Initialize Mapping worksheet
        self._mapping_worksheet = self._ensure_worksheet_sync(
            Config.SHEET_MAPPING, MAPPING_COLUMNS
        )

    def _ensure_worksheet_sync(self, title: str, expected_headers: List[str]) -> gspread.Worksheet:
        """Finds worksheet by title or creates it with header row. Adds any missing columns."""
        try:
            ws = self._spreadsheet.worksheet(title)
            existing_values = ws.get_all_values()
            if not existing_values:
                ws.append_row(expected_headers, value_input_option="USER_ENTERED")
            else:
                current_headers = existing_values[0]
                missing = [h for h in expected_headers if h not in current_headers]
                if missing:
                    logger.info("Updating worksheet '%s' with missing headers: %s", title, missing)
                    updated_headers = current_headers + missing
                    ws.update("A1", [updated_headers])
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

    def _update_member_name_sync(
        self, user_id: int, new_full_name: str, username: Optional[str] = None
    ) -> bool:
        self._connect_sync()
        rows = self._members_worksheet.get_all_values()
        str_user_id = str(user_id)
        found = False

        for idx, row in enumerate(rows[1:], start=2):
            if row and str(row[0]).strip() == str_user_id:
                updated_row = [
                    str_user_id,
                    username if username is not None else (row[1] if len(row) > 1 else ""),
                    new_full_name,
                    row[3] if len(row) > 3 else "",
                    row[4] if len(row) > 4 else "TRUE",
                ]
                self._members_worksheet.update(f"A{idx}:E{idx}", [updated_row])
                found = True
                break

        if not found:
            # Fallback to registering member if not yet in members worksheet
            new_row = [
                str_user_id,
                username or "",
                new_full_name,
                get_today_str(Config.TIMEZONE),
                "TRUE",
            ]
            self._members_worksheet.append_row(new_row, value_input_option="USER_ENTERED")

        # Also update Full Name in _mutabaah_worksheet if previous entries exist
        try:
            m_rows = self._mutabaah_worksheet.get_all_values()
            updates = []
            for m_idx, m_row in enumerate(m_rows[1:], start=2):
                if len(m_row) > 1 and str(m_row[1]).strip() == str_user_id:
                    updates.append({
                        "range": f"D{m_idx}",
                        "values": [[new_full_name]],
                    })
            if updates and hasattr(self._mutabaah_worksheet, "batch_update"):
                self._mutabaah_worksheet.batch_update(updates)
        except Exception as e:
            logger.warning("Could not batch update mutabaah rows with new full name: %s", e)

        return True

    async def update_member_name(
        self, user_id: int, new_full_name: str, username: Optional[str] = None
    ) -> bool:
        return await asyncio.to_thread(
            self._update_member_name_sync, user_id, new_full_name, username
        )


    # -------------------------------------------------------------
    # DAILY MUTABAAH METHODS
    # -------------------------------------------------------------

    def _upsert_mutabaah_sync(self, data: Dict[str, Any]) -> bool:
        """
        Upsert a mutabaah submission for a given date and user_id.
        Supports both full submissions and single-amalan updates while preserving
        existing values.
        """
        self._connect_sync()
        rows = self._mutabaah_worksheet.get_all_values()
        headers = rows[0] if rows else MUTABAAH_COLUMNS
        str_user_id = str(data["user_id"]).strip()
        target_date = str(data["date"]).strip()

        row_index_to_update = None
        existing_row_data: Dict[str, Any] = {}
        existing_submission_time = data.get("timestamp", get_timestamp_str(Config.TIMEZONE))

        for idx, row in enumerate(rows[1:], start=2):
            if len(row) >= 2:
                row_date = str(row[0]).strip()
                row_uid = str(row[1]).strip()
                if row_date == target_date and row_uid == str_user_id:
                    row_index_to_update = idx
                    for col_idx, h in enumerate(headers):
                        existing_row_data[h] = row[col_idx] if col_idx < len(row) else ""
                    if "Submission Time" in existing_row_data and existing_row_data["Submission Time"]:
                        existing_submission_time = existing_row_data["Submission Time"]
                    break

        # Helper to get field value, defaulting to existing row value if not provided in data
        def get_int_val(key: str, col_name: str) -> Any:
            if key in data:
                val = data[key]
                if str(val).strip().lower() in ["berhalangan", "haid", "halangan"]:
                    return "Berhalangan"
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            if col_name in existing_row_data:
                raw = str(existing_row_data[col_name]).strip()
                if raw.lower() in ["berhalangan", "haid", "halangan"]:
                    return "Berhalangan"
                if raw.upper() in ["TRUE", "1", "YES", "YA"]:
                    return 30
                try:
                    return int(float(raw))
                except (ValueError, TypeError):
                    return 0
            return 0

        def get_bool_val(key: str, col_name: str) -> str:
            if key in data:
                val = data[key]
                if isinstance(val, bool):
                    return "TRUE" if val else "FALSE"
                return "TRUE" if str(val).strip().upper() in ["TRUE", "1", "YES", "YA"] else "FALSE"
            if col_name in existing_row_data:
                existing_val = str(existing_row_data[col_name]).strip().upper()
                return "TRUE" if existing_val in ["TRUE", "1", "YES", "YA"] else "FALSE"
            return "FALSE"

        new_row = []
        for h in headers:
            if h == "Date":
                new_row.append(target_date)
            elif h == "Telegram User ID":
                new_row.append(str_user_id)
            elif h == "Telegram Username":
                new_row.append(data.get("username", existing_row_data.get("Telegram Username", "")))
            elif h == "Full Name":
                new_row.append(data.get("full_name", existing_row_data.get("Full Name", "")))
            elif h == "Tilawah Pages":
                new_row.append(get_int_val("tilawah", "Tilawah Pages"))
            elif h == "Sholat Wajib":
                new_row.append(get_int_val("sholat_wajib", "Sholat Wajib"))
            elif h == "Rawatib Rakaat":
                new_row.append(get_int_val("rawatib", "Rawatib Rakaat"))
            elif h == "Almatsurat":
                new_row.append(get_int_val("almatsurat", "Almatsurat"))
            elif h == "Shalawat":
                new_row.append(get_int_val("shalawat", "Shalawat"))
            elif h == "Istighfar":
                new_row.append(get_int_val("istighfar", "Istighfar"))
            elif h == "Tadabbur Ayat":
                new_row.append(get_int_val("tadabbur", "Tadabbur Ayat"))
            elif h == "Shaum Sunnah":
                new_row.append(get_bool_val("shaum_sunnah", "Shaum Sunnah"))
            elif h == "Qiyamulail":
                new_row.append(get_bool_val("qiyamulail", "Qiyamulail"))
            elif h == "Dhuha":
                new_row.append(get_bool_val("dhuha", "Dhuha"))
            elif h == "Olahraga":
                new_row.append(get_int_val("olahraga", "Olahraga"))
            elif h == "Silaturahim":
                new_row.append(get_bool_val("silaturahim", "Silaturahim"))
            elif h == "Doa Ummat Islam":
                new_row.append(get_int_val("doa_ummat_islam", "Doa Ummat Islam"))
            elif h == "Submission Time":
                new_row.append(existing_submission_time)
            elif h == "Last Updated":
                new_row.append(data.get("timestamp", get_timestamp_str(Config.TIMEZONE)))
            else:
                # Any unknown custom column
                new_row.append(data.get(h, existing_row_data.get(h, "")))

        if row_index_to_update:
            end_cell = rowcol_to_a1(row_index_to_update, len(new_row))
            cell_range = f"A{row_index_to_update}:{end_cell}"
            self._mutabaah_worksheet.update(cell_range, [new_row])
            logger.info("Updated mutabaah row %d for user %s on %s", row_index_to_update, str_user_id, target_date)
        else:
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

    # -------------------------------------------------------------
    # USER SETTINGS METHODS
    # -------------------------------------------------------------

    def _get_all_user_settings_sync(self) -> List[Dict[str, Any]]:
        self._connect_sync()
        if self._settings_worksheet is None:
            return []
        rows = self._settings_worksheet.get_all_values()
        if len(rows) <= 1:
            return []
        headers = rows[0]
        result = []
        for row in rows[1:]:
            record = {}
            for col_idx, h in enumerate(headers):
                record[h] = row[col_idx] if col_idx < len(row) else ""
            result.append(record)
        return result

    async def get_all_user_settings(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_user_settings_sync)

    def _get_user_settings_sync(self, user_id: int) -> Optional[Dict[str, Any]]:
        records = self._get_all_user_settings_sync()
        str_user_id = str(user_id).strip()
        for r in records:
            if str(r.get("Telegram User ID", "")).strip() == str_user_id:
                return r
        return None

    async def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_user_settings_sync, user_id)

    def _save_user_settings_sync(self, payload: Dict[str, Any]) -> bool:
        """
        Save or update user settings in User Settings worksheet.
        payload: {
            "user_id": str/int,
            "active_amalan": str (comma-separated),
            "targets": dict { amalan_key: int },
            "timestamp": str,
        }
        """
        self._connect_sync()
        rows = self._settings_worksheet.get_all_values()
        headers = rows[0] if rows else SETTINGS_COLUMNS
        str_user_id = str(payload["user_id"]).strip()
        targets = payload.get("targets", {})

        row_index_to_update = None
        for idx, row in enumerate(rows[1:], start=2):
            if row and str(row[0]).strip() == str_user_id:
                row_index_to_update = idx
                break

        # Map targets to headers
        target_map = {
            "Target Tilawah": targets.get("tilawah", 20),
            "Target Sholat Wajib": targets.get("sholat_wajib", 5),
            "Target Rawatib": targets.get("rawatib", 12),
            "Target Almatsurat": targets.get("almatsurat", 2),
            "Target Shalawat": targets.get("shalawat", 100),
            "Target Istighfar": targets.get("istighfar", 100),
            "Target Tadabbur": targets.get("tadabbur", 1),
            "Target Shaum Sunnah": targets.get("shaum_sunnah", 4),
            "Target Qiyamulail": targets.get("qiyamulail", 12),
            "Target Dhuha": targets.get("dhuha", 12),
            "Target Olahraga": targets.get("olahraga", 1),
            "Target Silaturahim": targets.get("silaturahim", 4),
            "Target Doa Ummat": targets.get("doa_ummat_islam", 1),
        }

        new_row = []
        for h in headers:
            if h == "Telegram User ID":
                new_row.append(str_user_id)
            elif h == "Active Amalan":
                new_row.append(payload.get("active_amalan", ""))
            elif h in target_map:
                new_row.append(target_map[h])
            elif h == "Last Updated":
                new_row.append(payload.get("timestamp", get_timestamp_str(Config.TIMEZONE)))
            else:
                new_row.append("")

        if row_index_to_update:
            end_cell = rowcol_to_a1(row_index_to_update, len(new_row))
            cell_range = f"A{row_index_to_update}:{end_cell}"
            self._settings_worksheet.update(cell_range, [new_row])
            logger.info("Updated user settings for user %s", str_user_id)
        else:
            self._settings_worksheet.append_row(new_row, value_input_option="USER_ENTERED")
            logger.info("Appended new user settings for user %s", str_user_id)

        return True

    async def save_user_settings(self, payload: Dict[str, Any]) -> bool:
        return await asyncio.to_thread(self._save_user_settings_sync, payload)

    # -------------------------------------------------------------
    # SUMMARY STATS METHODS
    # -------------------------------------------------------------

    def _append_or_update_summary_log_sync(self, stats: Dict[str, Any]) -> bool:
        """
        Record a summary entry in the Summary Stats worksheet.
        If a row with the same period exists, it updates it; otherwise appends.
        """
        self._connect_sync()
        rows = self._summary_stats_worksheet.get_all_values()
        headers = rows[0] if rows else SUMMARY_STATS_COLUMNS
        period_label = stats.get("period_label", "")
        start_date = stats.get("start_date", "")
        end_date = stats.get("end_date", "")

        row_index_to_update = None
        for idx, row in enumerate(rows[1:], start=2):
            if len(row) >= 3 and row[0] == period_label and row[1] == start_date and row[2] == end_date:
                row_index_to_update = idx
                break

        now_str = get_timestamp_str(Config.TIMEZONE)
        new_row = [
            period_label,
            start_date,
            end_date,
            stats.get("registered_members", 0),
            stats.get("active_submitters", 0),
            stats.get("total_submissions", 0),
            f"{stats.get('submission_rate', 0.0)}%",
            f"{stats.get('average_completion_rate', 0.0)}%",
            stats.get("avg_tilawah", 0.0),
            stats.get("avg_wajib", 0.0),
            stats.get("avg_rawatib", 0.0),
            stats.get("avg_almatsurat", 0.0),
            stats.get("avg_shalawat", 0.0),
            stats.get("avg_istighfar", 0.0),
            stats.get("avg_tadabbur", 0.0),
            stats.get("count_shaum", 0),
            stats.get("count_qiyam", 0),
            stats.get("count_dhuha", 0),
            stats.get("total_olahraga", stats.get("count_olahraga", 0)),
            stats.get("count_silaturahim", 0),
            stats.get("avg_doa_ummat", 0.0),
            now_str,
        ]

        if row_index_to_update:
            end_cell = rowcol_to_a1(row_index_to_update, len(new_row))
            self._summary_stats_worksheet.update(f"A{row_index_to_update}:{end_cell}", [new_row])
            logger.info("Updated summary stats row %d for %s", row_index_to_update, period_label)
        else:
            self._summary_stats_worksheet.append_row(new_row, value_input_option="USER_ENTERED")
            logger.info("Appended new summary stats row for %s", period_label)
        return True

    def _write_summary_stats_report_sync(
        self, stats: Dict[str, Any], member_breakdown: List[Dict[str, Any]]
    ) -> bool:
        """
        Write a complete, structured dashboard in the Summary Stats worksheet:
        - Executive summary of the chosen period
        - Detailed per-member summary leaderboard
        """
        self._connect_sync()
        now_str = get_timestamp_str(Config.TIMEZONE)
        period_label = stats.get("period_label", "")

        rows_to_write = [
            ["📊 RINGKASAN STATISTIK MUTABAAH YAUMIYAH (IMA KOREA)"],
            [f"Periode: {period_label}", f"Rentang: {stats.get('start_date')} s/d {stats.get('end_date')}", f"Dibuat pada: {now_str}"],
            [],
            ["1. RINGKASAN AGREGAT"],
            [
                "Total Anggota Terdaftar",
                "Anggota Aktif Mengisi",
                "Tingkat Keaktifan (%)",
                "Total Entri Terisi",
                "Rata-rata Capaian Target (%)",
            ],
            [
                stats.get("registered_members", 0),
                stats.get("active_submitters", 0),
                f"{stats.get('submission_rate', 0.0)}%",
                stats.get("total_submissions", 0),
                f"{stats.get('average_completion_rate', 0.0)}%",
            ],
            [],
            ["2. RATA-RATA AMALAN PER ENTRI"],
            [
                "Tilawah (Hal)",
                "Sholat Wajib",
                "Rawatib (Rakaat)",
                "Al-Ma'tsurat",
                "Shalawat",
                "Istighfar",
                "Tadabbur (Ayat)",
                "Total Shaum Sunnah",
                "Total Qiyamulail",
                "Total Dhuha",
                "Total Olahraga (Menit)",
                "Total Silaturahim",
                "Doa Ummat (Rata-rata)",
            ],
            [
                stats.get("avg_tilawah", 0.0),
                stats.get("avg_wajib", 0.0),
                stats.get("avg_rawatib", 0.0),
                stats.get("avg_almatsurat", 0.0),
                stats.get("avg_shalawat", 0.0),
                stats.get("avg_istighfar", 0.0),
                stats.get("avg_tadabbur", 0.0),
                stats.get("count_shaum", 0),
                stats.get("count_qiyam", 0),
                stats.get("count_dhuha", 0),
                stats.get("total_olahraga", stats.get("count_olahraga", 0)),
                stats.get("count_silaturahim", 0),
                stats.get("avg_doa_ummat", 0.0),
            ],
            [],
            ["3. REKAP KEAKTIFAN PER ANGGOTA (LEADERBOARD)"],
            [
                "No",
                "Telegram User ID",
                "Nama Lengkap",
                "Username",
                "Hari Terisi",
                "Tilawah (Hal)",
                "Sholat Wajib",
                "Rawatib (Rakaat)",
                "Al-Ma'tsurat",
                "Shalawat",
                "Istighfar",
                "Tadabbur (Ayat)",
                "Shaum Sunnah",
                "Qiyamulail",
                "Dhuha",
                "Olahraga",
                "Silaturahim",
                "Doa Ummat",
                "Rata-rata Capaian (%)",
            ],
        ]

        for idx, m in enumerate(member_breakdown, start=1):
            rows_to_write.append([
                idx,
                m.get("user_id", ""),
                m.get("full_name", ""),
                m.get("username", ""),
                m.get("days_submitted", 0),
                m.get("total_tilawah", 0),
                m.get("total_wajib", 0),
                m.get("total_rawatib", 0),
                m.get("total_almatsurat", 0),
                m.get("total_shalawat", 0),
                m.get("total_istighfar", 0),
                m.get("total_tadabbur", 0),
                m.get("count_shaum", 0),
                m.get("count_qiyam", 0),
                m.get("count_dhuha", 0),
                m.get("count_olahraga", 0),
                m.get("count_silaturahim", 0),
                m.get("total_doa_ummat", 0),
                f"{m.get('avg_completion', 0.0)}%",
            ])

        self._summary_stats_worksheet.clear()
        self._summary_stats_worksheet.update("A1", rows_to_write, value_input_option="USER_ENTERED")
        logger.info("Updated Summary Stats report worksheet for period %s", period_label)
        return True

    async def append_or_update_summary_log(self, stats: Dict[str, Any]) -> bool:
        return await asyncio.to_thread(self._append_or_update_summary_log_sync, stats)

    async def write_summary_stats_report(
        self, stats: Dict[str, Any], member_breakdown: List[Dict[str, Any]]
    ) -> bool:
        return await asyncio.to_thread(
            self._write_summary_stats_report_sync, stats, member_breakdown
        )

    # -------------------------------------------------------------
    # MAPPING WORKSHEET METHODS
    # -------------------------------------------------------------

    def _get_all_mapping_rows_sync(self) -> List[Dict[str, Any]]:
        self._connect_sync()
        if self._mapping_worksheet is None:
            return []
        rows = self._mapping_worksheet.get_all_values()
        if len(rows) <= 1:
            return []

        curr_murobbi_id = ""
        curr_murobbi_name = ""
        result = []
        for row in rows[1:]:
            m_id = str(row[0]).strip() if len(row) > 0 else ""
            m_name = str(row[1]).strip() if len(row) > 1 else ""
            mut_id = str(row[2]).strip() if len(row) > 2 else ""
            mut_name = str(row[3]).strip() if len(row) > 3 else ""
            kelompok = str(row[4]).strip() if len(row) > 4 else ""

            if m_id:
                curr_murobbi_id = m_id
            if m_name:
                curr_murobbi_name = m_name

            if curr_murobbi_id and mut_id:
                result.append({
                    "murobbi_id": curr_murobbi_id,
                    "murobbi_name": curr_murobbi_name,
                    "mutarabbi_id": mut_id,
                    "mutarabbi_name": mut_name,
                    "kelompok": kelompok,
                })
        return result

    async def get_all_mapping_rows(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_mapping_rows_sync)
