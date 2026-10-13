import logging
from typing import Dict, Any, List, Optional
from app.services.sheets import SheetsService
from app.services.members import MembersService
from app.utils.datetime import (
    get_now,
    get_today_str,
    get_current_month_prefix,
    format_month_year_id,
)
from app.config import Config

logger = logging.getLogger(__name__)


def _parse_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().upper() in ["TRUE", "1", "YES", "YA"]


def _parse_int(val: Any, default: int = 0) -> int:
    try:
        if val is None or str(val).strip() == "":
            return default
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


class StatisticsService:
    def __init__(
        self,
        sheets_service: Optional[SheetsService] = None,
        members_service: Optional[MembersService] = None,
    ):
        self.sheets = sheets_service or SheetsService.get_instance()
        self.members = members_service or MembersService(self.sheets)

    async def calculate_user_month_progress(
        self, user_id: int, tz_name: str = Config.TIMEZONE
    ) -> Dict[str, Any]:
        """
        Calculate personal progress for the current month in specified timezone.
        """
        now = get_now(tz_name)
        month_prefix = get_current_month_prefix(tz_name)
        month_label = format_month_year_id(now, tz_name)
        days_passed = now.day

        all_rows = await self.sheets.get_all_mutabaah_rows()
        str_user_id = str(user_id).strip()

        # Filter rows for this user in current month
        user_rows: List[Dict[str, Any]] = []
        for r in all_rows:
            r_uid = str(r.get("Telegram User ID", "")).strip()
            r_date = str(r.get("Date", "")).strip()
            if r_uid == str_user_id and r_date.startswith(month_prefix):
                user_rows.append(r)

        days_submitted = len(user_rows)

        total_tilawah = sum(_parse_int(r.get("Tilawah Pages", 0)) for r in user_rows)
        total_wajib = sum(_parse_int(r.get("Sholat Wajib", 0)) for r in user_rows)
        total_rawatib = sum(_parse_int(r.get("Rawatib Rakaat", 0)) for r in user_rows)
        total_almatsurat = sum(_parse_int(r.get("Almatsurat", 0)) for r in user_rows)

        count_qiyamulail = sum(1 for r in user_rows if _parse_bool(r.get("Qiyamulail")))
        count_dhuha = sum(1 for r in user_rows if _parse_bool(r.get("Dhuha")))
        count_olahraga = sum(1 for r in user_rows if _parse_bool(r.get("Olahraga")))

        # Targets based on days passed so far in current month
        target_tilawah = 20 * days_passed
        target_wajib = 5 * days_passed
        target_rawatib = 12 * days_passed
        target_almatsurat = 2 * days_passed

        # Calculate completion rate (average of core habits, capped at 100% per habit for fairness)
        tilawah_ratio = min(total_tilawah / target_tilawah, 1.0) if target_tilawah > 0 else 0.0
        wajib_ratio = min(total_wajib / target_wajib, 1.0) if target_wajib > 0 else 0.0
        rawatib_ratio = min(total_rawatib / target_rawatib, 1.0) if target_rawatib > 0 else 0.0
        almatsurat_ratio = (
            min(total_almatsurat / target_almatsurat, 1.0) if target_almatsurat > 0 else 0.0
        )

        avg_ratio = (tilawah_ratio + wajib_ratio + rawatib_ratio + almatsurat_ratio) / 4.0
        completion_pct = round(avg_ratio * 100, 1)

        return {
            "month_label": month_label,
            "days_submitted": days_submitted,
            "days_passed": days_passed,
            "total_tilawah": total_tilawah,
            "target_tilawah": target_tilawah,
            "total_wajib": total_wajib,
            "target_wajib": target_wajib,
            "total_rawatib": total_rawatib,
            "target_rawatib": target_rawatib,
            "total_almatsurat": total_almatsurat,
            "target_almatsurat": target_almatsurat,
            "count_qiyamulail": count_qiyamulail,
            "count_dhuha": count_dhuha,
            "count_olahraga": count_olahraga,
            "completion_percentage": completion_pct,
        }

    async def calculate_monthly_admin_stats(
        self, tz_name: str = Config.TIMEZONE
    ) -> Dict[str, Any]:
        """
        Calculate aggregate stats for admin:
        - registered members
        - active submitters this month
        - submissions today
        - submission rate today
        - average completion rate
        """
        now = get_now(tz_name)
        today_str = get_today_str(tz_name)
        month_prefix = get_current_month_prefix(tz_name)
        month_label = format_month_year_id(now, tz_name)
        days_passed = now.day

        active_members = await self.members.get_all_active_members()
        registered_count = len(active_members)

        all_rows = await self.sheets.get_all_mutabaah_rows()

        # Submissions today
        today_submitters = set()
        month_submitters = set()
        month_rows = []

        for r in all_rows:
            r_uid = str(r.get("Telegram User ID", "")).strip()
            r_date = str(r.get("Date", "")).strip()

            if r_date == today_str and r_uid:
                today_submitters.add(r_uid)

            if r_date.startswith(month_prefix) and r_uid:
                month_submitters.add(r_uid)
                month_rows.append(r)

        today_submissions_count = len(today_submitters)
        submission_rate_today = (
            round((today_submissions_count / registered_count) * 100, 1)
            if registered_count > 0
            else 0.0
        )
        active_submitters_month = len(month_submitters)

        # Average completion rate of monthly submissions
        if month_rows:
            total_score = 0.0
            for r in month_rows:
                t = min(_parse_int(r.get("Tilawah Pages", 0)) / 20.0, 1.0)
                w = min(_parse_int(r.get("Sholat Wajib", 0)) / 5.0, 1.0)
                rw = min(_parse_int(r.get("Rawatib Rakaat", 0)) / 12.0, 1.0)
                al = min(_parse_int(r.get("Almatsurat", 0)) / 2.0, 1.0)
                total_score += (t + w + rw + al) / 4.0
            avg_completion = round((total_score / len(month_rows)) * 100, 1)
        else:
            avg_completion = 0.0

        return {
            "month_label": month_label,
            "registered_members": registered_count,
            "submissions_today": today_submissions_count,
            "submission_rate_today": submission_rate_today,
            "active_submitters_month": active_submitters_month,
            "average_completion_rate": avg_completion,
            "total_monthly_records": len(month_rows),
        }
