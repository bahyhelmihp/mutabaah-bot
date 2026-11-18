"""
Service for calculating user month progress and aggregate admin statistics.
"""
import logging
import math
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from app.services.sheets import SheetsService
from app.services.members import MembersService
from app.services.settings import UserSettingsService
from app.services.amalan import (
    AMALAN_DEFINITIONS,
    ALL_AMALAN_KEYS,
    get_amalan_info,
)
from app.utils.datetime import (
    get_now,
    get_today_str,
    get_current_month_prefix,
    format_month_year_id,
    get_date_range_presets,
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


def _calculate_row_scores(r: Dict[str, Any]) -> List[float]:
    """Calculate normalized scores for a single submission row."""
    scores = []
    til_str = str(r.get("Tilawah Pages", "")).strip().lower()
    if til_str not in ["berhalangan", "haid", "halangan"]:
        scores.append(min(_parse_int(r.get("Tilawah Pages", 0)) / 20.0, 1.0))

    waj_str = str(r.get("Sholat Wajib", "")).strip().lower()
    if waj_str not in ["berhalangan", "haid", "halangan"]:
        scores.append(min(_parse_int(r.get("Sholat Wajib", 0)) / 5.0, 1.0))

    scores.append(min(_parse_int(r.get("Rawatib Rakaat", 0)) / 12.0, 1.0))
    scores.append(min(_parse_int(r.get("Almatsurat", 0)) / 2.0, 1.0))
    scores.append(min(_parse_int(r.get("Shalawat", 0)) / 100.0, 1.0))
    scores.append(min(_parse_int(r.get("Istighfar", 0)) / 100.0, 1.0))
    scores.append(min(_parse_int(r.get("Tadabbur Ayat", 0)) / 1.0, 1.0))
    return scores


def _extract_member_highlights(m: Dict[str, Any]) -> List[str]:
    """Extract top 2-3 standout achievements for a member."""
    days = max(1, m.get("days_submitted", 1))
    achievements = []

    # Tilawah
    avg_til = m.get("total_tilawah", 0) / days
    if avg_til >= 5.0:
        achievements.append((avg_til / 20.0, f"📖 Tilawah {math.ceil(avg_til)} hal/hari"))
    elif m.get("total_tilawah", 0) > 0:
        achievements.append((avg_til / 20.0, f"📖 Tilawah {m.get('total_tilawah')} hal"))

    # Sholat Wajib
    avg_waj = m.get("total_wajib", 0) / days
    if avg_waj >= 4.0:
        achievements.append((avg_waj / 5.0, f"🕌 Wajib {math.ceil(avg_waj)}/5 waktu/hari"))

    # Rawatib
    avg_raw = m.get("total_rawatib", 0) / days
    if avg_raw >= 4.0:
        achievements.append((avg_raw / 12.0, f"🌙 Rawatib {math.ceil(avg_raw)} rkt/hari"))

    # Al-Ma'tsurat
    avg_mat = m.get("total_almatsurat", 0) / days
    if avg_mat >= 1.0:
        achievements.append((avg_mat / 2.0, f"📿 Ma’tsurat {math.ceil(avg_mat)}x/hari"))

    # Shalawat
    avg_shal = m.get("total_shalawat", 0) / days
    if avg_shal >= 50.0:
        achievements.append((avg_shal / 100.0, f"🌸 Shalawat {math.ceil(avg_shal)}x/hari"))

    # Istighfar
    avg_ist = m.get("total_istighfar", 0) / days
    if avg_ist >= 50.0:
        achievements.append((avg_ist / 100.0, f"🤲 Istighfar {math.ceil(avg_ist)}x/hari"))

    # Tadabbur
    avg_tad = m.get("total_tadabbur", 0) / days
    if avg_tad >= 1.0:
        achievements.append((avg_tad / 1.0, f"📜 Tadabbur {math.ceil(avg_tad)} ayat/hari"))

    # Qiyamulail
    q_count = m.get("count_qiyam", 0)
    if q_count >= 1:
        achievements.append((q_count / days, f"🌃 Qiyam {q_count} malam"))

    # Dhuha
    d_count = m.get("count_dhuha", 0)
    if d_count >= 1:
        achievements.append((d_count / days, f"☀️ Dhuha {d_count} hari"))

    # Shaum Sunnah
    s_count = m.get("count_shaum", 0)
    if s_count >= 1:
        achievements.append((s_count * 3.0 / days, f"🍽️ Shaum {s_count} hari"))

    # Olahraga (menit)
    tot_ol = m.get("total_olahraga", 0)
    if tot_ol >= 15:
        achievements.append((tot_ol / 30.0, f"🏃 Olahraga total {tot_ol} mnt"))

    # Silaturahim
    sil_count = m.get("count_silaturahim", 0)
    if sil_count >= 1:
        achievements.append((sil_count / days, f"🤝 Silaturahim {sil_count}x"))

    # Doa Ummat
    avg_doa = m.get("total_doa_ummat", 0) / days
    if avg_doa >= 1.0:
        achievements.append((avg_doa / 1.0, f"🤲 Doa Ummat {math.ceil(avg_doa)}x/hari"))
    elif m.get("total_doa_ummat", 0) >= 1:
        achievements.append((m.get("total_doa_ummat", 0) / days, f"🤲 Doa Ummat total {m.get('total_doa_ummat')}x"))

    achievements.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in achievements[:3]]


class StatisticsService:
    def __init__(
        self,
        sheets_service: Optional[SheetsService] = None,
        members_service: Optional[MembersService] = None,
        settings_service: Optional[UserSettingsService] = None,
    ):
        self.sheets = sheets_service or SheetsService.get_instance()
        self.members = members_service or MembersService(self.sheets)
        self.settings = settings_service or UserSettingsService(self.sheets)

    async def calculate_user_month_progress(
        self, user_id: int, tz_name: str = Config.TIMEZONE
    ) -> Dict[str, Any]:
        """
        Calculate personal progress for the current month based on the user's
        active amalan and custom targets.
        """
        now = get_now(tz_name)
        month_prefix = get_current_month_prefix(tz_name)
        month_label = format_month_year_id(now, tz_name)
        days_passed = max(1, now.day)

        # Retrieve user settings
        active_keys = await self.settings.get_active_amalan(user_id)
        targets = await self.settings.get_user_targets(user_id)

        all_rows = await self.sheets.get_all_mutabaah_rows()
        str_user_id = str(user_id).strip()

        # Filter rows for this user in current month
        user_rows: List[Dict[str, Any]] = []
        all_user_submitted_dates: Set[str] = set()
        for r in all_rows:
            r_uid = str(r.get("Telegram User ID", "")).strip()
            if r_uid == str_user_id:
                r_date = str(r.get("Date", "")).strip()
                if r_date:
                    all_user_submitted_dates.add(r_date)
                if r_date.startswith(month_prefix):
                    user_rows.append(r)

        # Unique dates submitted by user in current month
        submitted_dates = sorted(list({str(r.get("Date", "")).strip() for r in user_rows if r.get("Date")}))
        # Missing dates in the current month up to today (day 1 to now.day)
        missing_dates = [
            f"{month_prefix}-{d:02d}"
            for d in range(1, now.day + 1)
            if f"{month_prefix}-{d:02d}" not in submitted_dates
        ]
        days_submitted = len(submitted_dates)

        items: Dict[str, Any] = {}
        ratios: List[float] = []


        for key in active_keys:
            defn = get_amalan_info(key)
            if not defn:
                continue

            col = defn["column"]
            custom_target = targets.get(key, defn.get("default_target", 1))

            if defn["type"] == "bool":
                actual_count = sum(1 for r in user_rows if _parse_bool(r.get(col)))
                if defn.get("target_period") == "monthly":
                    # Target is monthly count (e.g. shaum sunnah 4x/month, qiyamulail 12x/month)
                    target_val = custom_target
                else:
                    # Daily boolean (e.g. olahraga 1x/day)
                    target_val = days_passed

                ratio = min(actual_count / target_val, 1.0) if target_val > 0 else 0.0
                ratios.append(ratio)

                items[key] = {
                    "name": defn["name"],
                    "short_name": defn["short_name"],
                    "icon": defn["icon"],
                    "type": "bool",
                    "actual": actual_count,
                    "target": target_val,
                    "unit": "hari",
                    "ratio": ratio,
                }
            else:
                # Integer type (tilawah, sholat wajib, rawatib, almatsurat, shalawat, istighfar, tadabbur, olahraga)
                if key == "olahraga":
                    actual_sum = sum(_parse_int(r.get(col, 0)) if not _parse_bool(r.get(col)) else 30 for r in user_rows)
                    # Weekly target (default 30 min/week): scale target based on days passed
                    target_val = max(1, round((days_passed / 7.0) * custom_target))
                    ratio = min(actual_sum / target_val, 1.0) if target_val > 0 else 0.0
                    ratios.append(ratio)
                    berhalangan_days = 0
                else:
                    berhalangan_days = sum(
                        1 for r in user_rows 
                        if str(r.get(col, "")).strip().lower() in ["berhalangan", "haid", "halangan"]
                    )
                    actual_sum = sum(
                        _parse_int(r.get(col, 0)) for r in user_rows 
                        if str(r.get(col, "")).strip().lower() not in ["berhalangan", "haid", "halangan"]
                    )
                    effective_days = max(0, days_passed - berhalangan_days)
                    target_val = custom_target * effective_days

                    if target_val > 0:
                        ratio = min(actual_sum / target_val, 1.0)
                        ratios.append(ratio)
                    elif berhalangan_days > 0 and effective_days == 0:
                        ratio = 1.0
                    else:
                        ratio = 0.0
                        ratios.append(ratio)

                items[key] = {
                    "name": defn["name"],
                    "short_name": defn["short_name"],
                    "icon": defn["icon"],
                    "type": "int",
                    "actual": actual_sum,
                    "target": target_val,
                    "daily_target": custom_target,
                    "unit": defn.get("unit", ""),
                    "ratio": ratio,
                    "berhalangan_days": berhalangan_days,
                }

        avg_ratio = (sum(ratios) / len(ratios)) if ratios else 0.0
        completion_pct = round(avg_ratio * 100, 1)

        # Retain backward-compatible top-level keys for existing tests & code
        total_tilawah = items.get("tilawah", {}).get("actual", sum(_parse_int(r.get("Tilawah Pages", 0)) for r in user_rows))
        target_tilawah = items.get("tilawah", {}).get("target", 20 * days_passed)
        total_wajib = items.get("sholat_wajib", {}).get("actual", sum(_parse_int(r.get("Sholat Wajib", 0)) for r in user_rows))
        target_wajib = items.get("sholat_wajib", {}).get("target", 5 * days_passed)
        total_rawatib = items.get("rawatib", {}).get("actual", sum(_parse_int(r.get("Rawatib Rakaat", 0)) for r in user_rows))
        target_rawatib = items.get("rawatib", {}).get("target", 12 * days_passed)
        total_almatsurat = items.get("almatsurat", {}).get("actual", sum(_parse_int(r.get("Almatsurat", 0)) for r in user_rows))
        target_almatsurat = items.get("almatsurat", {}).get("target", 2 * days_passed)

        return {
            "month_label": month_label,
            "days_submitted": days_submitted,
            "days_passed": days_passed,
            "active_keys": active_keys,
            "items": items,
            "total_tilawah": total_tilawah,
            "target_tilawah": target_tilawah,
            "total_wajib": total_wajib,
            "target_wajib": target_wajib,
            "total_rawatib": total_rawatib,
            "target_rawatib": target_rawatib,
            "total_almatsurat": total_almatsurat,
            "target_almatsurat": target_almatsurat,
            "count_qiyamulail": items.get("qiyamulail", {}).get("actual", sum(1 for r in user_rows if _parse_bool(r.get("Qiyamulail")))),
            "count_dhuha": items.get("dhuha", {}).get("actual", sum(1 for r in user_rows if _parse_bool(r.get("Dhuha")))),
            "count_olahraga": items.get("olahraga", {}).get("actual", sum(1 for r in user_rows if _parse_bool(r.get("Olahraga")))),
            "completion_percentage": completion_pct,
            "submitted_dates": submitted_dates,
            "all_submitted_dates": sorted(list(all_user_submitted_dates)),
            "missing_dates": missing_dates,
        }

    async def calculate_user_period_progress(
        self,
        user_id: int,
        start_date: str,
        end_date: str,
        period_label: str,
        period_key: str = "weekly",
        tz_name: str = Config.TIMEZONE,
    ) -> Dict[str, Any]:
        """
        Calculate user progress over an arbitrary date range (e.g. weekly for liqo, monthly, or custom).
        """
        now = get_now(tz_name)
        today_str = get_today_str(tz_name)

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        today_dt = datetime(now.year, now.month, now.day)

        total_days_in_period = max(1, (end_dt - start_dt).days + 1)
        effective_end_dt = min(end_dt, today_dt)
        days_passed = max(1, (effective_end_dt - start_dt).days + 1) if effective_end_dt >= start_dt else 1

        # Retrieve user settings
        active_keys = await self.settings.get_active_amalan(user_id)
        targets = await self.settings.get_user_targets(user_id)

        all_rows = await self.sheets.get_all_mutabaah_rows()
        str_user_id = str(user_id).strip()

        # Filter rows for this user in period
        user_rows: List[Dict[str, Any]] = []
        all_user_submitted_dates: Set[str] = set()
        for r in all_rows:
            r_uid = str(r.get("Telegram User ID", "")).strip()
            if r_uid == str_user_id:
                r_date = str(r.get("Date", "")).strip()
                if r_date:
                    all_user_submitted_dates.add(r_date)
                if start_date <= r_date <= end_date:
                    user_rows.append(r)

        submitted_dates = sorted(list({str(r.get("Date", "")).strip() for r in user_rows if r.get("Date")}))
        days_submitted = len(submitted_dates)

        # Missing dates in the period up to effective_end_dt
        missing_dates = []
        if effective_end_dt >= start_dt:
            curr = start_dt
            while curr <= effective_end_dt:
                d_str = curr.strftime("%Y-%m-%d")
                if d_str not in submitted_dates:
                    missing_dates.append(d_str)
                curr += timedelta(days=1)

        items: Dict[str, Any] = {}
        ratios: List[float] = []

        for key in active_keys:
            defn = get_amalan_info(key)
            if not defn:
                continue

            col = defn["column"]
            custom_target = targets.get(key, defn.get("default_target", 1))

            if defn["type"] == "bool":
                actual_count = sum(1 for r in user_rows if _parse_bool(r.get(col)))
                if period_key == "monthly" or total_days_in_period >= 28:
                    if defn.get("target_period") == "monthly":
                        target_val = custom_target
                    else:
                        target_val = days_passed
                elif period_key == "weekly" or (6 <= total_days_in_period <= 8):
                    if defn.get("target_period") == "monthly":
                        target_val = max(1, round(custom_target / 4.0))
                    elif defn.get("target_period") == "weekly":
                        target_val = custom_target
                    else:
                        target_val = days_passed
                else:
                    # Custom range: scale target proportionally
                    if defn.get("target_period") == "monthly":
                        target_val = max(1, round((total_days_in_period / 30.0) * custom_target))
                    elif defn.get("target_period") == "weekly":
                        target_val = max(1, round((total_days_in_period / 7.0) * custom_target))
                    else:
                        target_val = days_passed

                ratio = min(actual_count / target_val, 1.0) if target_val > 0 else 0.0
                ratios.append(ratio)

                items[key] = {
                    "name": defn["name"],
                    "short_name": defn["short_name"],
                    "icon": defn["icon"],
                    "type": "bool",
                    "actual": actual_count,
                    "target": target_val,
                    "unit": "hari",
                    "ratio": ratio,
                }
            else:
                # Integer type (tilawah, sholat wajib, rawatib, almatsurat, shalawat, istighfar, tadabbur, olahraga)
                if key == "olahraga":
                    actual_sum = sum(_parse_int(r.get(col, 0)) if not _parse_bool(r.get(col)) else 30 for r in user_rows)
                    if period_key == "weekly" or (6 <= total_days_in_period <= 8):
                        target_val = custom_target
                    else:
                        target_val = max(1, round((total_days_in_period / 7.0) * custom_target))
                    ratio = min(actual_sum / target_val, 1.0) if target_val > 0 else 0.0
                    ratios.append(ratio)
                    berhalangan_days = 0
                else:
                    berhalangan_days = sum(
                        1 for r in user_rows 
                        if str(r.get(col, "")).strip().lower() in ["berhalangan", "haid", "halangan"]
                    )
                    actual_sum = sum(
                        _parse_int(r.get(col, 0)) for r in user_rows 
                        if str(r.get(col, "")).strip().lower() not in ["berhalangan", "haid", "halangan"]
                    )
                    effective_days = max(0, days_passed - berhalangan_days)
                    target_val = custom_target * effective_days

                    if target_val > 0:
                        ratio = min(actual_sum / target_val, 1.0)
                        ratios.append(ratio)
                    elif berhalangan_days > 0 and effective_days == 0:
                        ratio = 1.0
                    else:
                        ratio = 0.0
                        ratios.append(ratio)

                items[key] = {
                    "name": defn["name"],
                    "short_name": defn["short_name"],
                    "icon": defn["icon"],
                    "type": "int",
                    "actual": actual_sum,
                    "target": target_val,
                    "daily_target": custom_target,
                    "unit": defn.get("unit", ""),
                    "ratio": ratio,
                    "berhalangan_days": berhalangan_days,
                }

        avg_ratio = (sum(ratios) / len(ratios)) if ratios else 0.0
        completion_pct = round(avg_ratio * 100, 1)

        return {
            "period_key": period_key,
            "period_label": period_label,
            "start_date": start_date,
            "end_date": end_date,
            "days_submitted": days_submitted,
            "days_passed": days_passed,
            "total_days_in_period": total_days_in_period,
            "active_keys": active_keys,
            "items": items,
            "completion_percentage": completion_pct,
            "submitted_dates": submitted_dates,
            "missing_dates": missing_dates,
        }


    async def calculate_period_admin_stats(
        self,
        start_date: str,
        end_date: str,
        period_label: str,
        tz_name: str = Config.TIMEZONE,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive aggregate stats for admin over any given period
        (today, weekly, monthly, last month, or custom range).
        """
        today_str = get_today_str(tz_name)
        active_members = await self.members.get_all_active_members()
        registered_count = len(active_members)

        all_rows = await self.sheets.get_all_mutabaah_rows()

        # Filter rows by date range
        period_rows: List[Dict[str, Any]] = []
        today_submitters = set()
        period_submitters = set()

        for r in all_rows:
            r_uid = str(r.get("Telegram User ID", "")).strip()
            r_date = str(r.get("Date", "")).strip()

            if r_date == today_str and r_uid:
                today_submitters.add(r_uid)

            if start_date <= r_date <= end_date and r_uid:
                period_rows.append(r)
                period_submitters.add(r_uid)

        active_submitters_count = len(period_submitters)
        submission_rate = (
            round((active_submitters_count / registered_count) * 100, 1)
            if registered_count > 0
            else 0.0
        )
        today_submissions_count = len(today_submitters)
        submission_rate_today = (
            round((today_submissions_count / registered_count) * 100, 1)
            if registered_count > 0
            else 0.0
        )

        # Aggregate amalan values
        total_tilawah = sum(_parse_int(r.get("Tilawah Pages", 0)) for r in period_rows)
        total_wajib = sum(_parse_int(r.get("Sholat Wajib", 0)) for r in period_rows)
        total_rawatib = sum(_parse_int(r.get("Rawatib Rakaat", 0)) for r in period_rows)
        total_almatsurat = sum(_parse_int(r.get("Almatsurat", 0)) for r in period_rows)
        total_shalawat = sum(_parse_int(r.get("Shalawat", 0)) for r in period_rows)
        total_istighfar = sum(_parse_int(r.get("Istighfar", 0)) for r in period_rows)
        total_tadabbur = sum(_parse_int(r.get("Tadabbur Ayat", 0)) for r in period_rows)
        count_shaum = sum(1 for r in period_rows if _parse_bool(r.get("Shaum Sunnah")))
        count_qiyam = sum(1 for r in period_rows if _parse_bool(r.get("Qiyamulail")))
        count_dhuha = sum(1 for r in period_rows if _parse_bool(r.get("Dhuha")))
        total_olahraga = sum(_parse_int(r.get("Olahraga", 0)) if not _parse_bool(r.get("Olahraga")) else 30 for r in period_rows)
        count_olahraga = total_olahraga
        count_silaturahim = sum(1 for r in period_rows if _parse_bool(r.get("Silaturahim")))
        total_doa_ummat = sum(_parse_int(r.get("Doa Ummat Islam", 0)) for r in period_rows)

        valid_tilawah_rows = [
            r for r in period_rows 
            if str(r.get("Tilawah Pages", "")).strip().lower() not in ["berhalangan", "haid", "halangan"]
        ]
        valid_wajib_rows = [
            r for r in period_rows 
            if str(r.get("Sholat Wajib", "")).strip().lower() not in ["berhalangan", "haid", "halangan"]
        ]

        n_entries = len(period_rows)
        avg_tilawah = round(total_tilawah / len(valid_tilawah_rows), 1) if valid_tilawah_rows else 0.0
        avg_wajib = round(total_wajib / len(valid_wajib_rows), 1) if valid_wajib_rows else 0.0
        avg_rawatib = round(total_rawatib / n_entries, 1) if n_entries > 0 else 0.0
        avg_almatsurat = round(total_almatsurat / n_entries, 1) if n_entries > 0 else 0.0
        avg_shalawat = round(total_shalawat / n_entries, 1) if n_entries > 0 else 0.0
        avg_istighfar = round(total_istighfar / n_entries, 1) if n_entries > 0 else 0.0
        avg_tadabbur = round(total_tadabbur / n_entries, 1) if n_entries > 0 else 0.0
        avg_olahraga = round(total_olahraga / n_entries, 1) if n_entries > 0 else 0.0
        avg_doa_ummat = round(total_doa_ummat / n_entries, 1) if n_entries > 0 else 0.0

        # Calculate average completion score across submissions
        if period_rows:
            total_score = 0.0
            valid_submission_count = 0
            for r in period_rows:
                entry_scores = _calculate_row_scores(r)
                if entry_scores:
                    total_score += sum(entry_scores) / len(entry_scores)
                    valid_submission_count += 1
            avg_completion = round((total_score / valid_submission_count) * 100, 1) if valid_submission_count > 0 else 0.0
        else:
            avg_completion = 0.0

        # Per-member breakdown in this period
        member_map: Dict[str, Dict[str, Any]] = {}
        for m in active_members:
            uid = str(m.get("Telegram User ID", "")).strip()
            if not uid:
                continue
            member_map[uid] = {
                "user_id": uid,
                "full_name": m.get("Full Name", ""),
                "username": m.get("Telegram Username", ""),
                "days_submitted": 0,
                "total_tilawah": 0,
                "total_wajib": 0,
                "total_rawatib": 0,
                "total_almatsurat": 0,
                "total_shalawat": 0,
                "total_istighfar": 0,
                "total_tadabbur": 0,
                "count_shaum": 0,
                "count_qiyam": 0,
                "count_dhuha": 0,
                "total_olahraga": 0,
                "count_olahraga": 0,
                "count_silaturahim": 0,
                "total_doa_ummat": 0,
                "total_score": 0.0,
                "highlights": [],
            }

        for r in period_rows:
            uid = str(r.get("Telegram User ID", "")).strip()
            if uid not in member_map:
                member_map[uid] = {
                    "user_id": uid,
                    "full_name": r.get("Full Name", ""),
                    "username": r.get("Telegram Username", ""),
                    "days_submitted": 0,
                    "total_tilawah": 0,
                    "total_wajib": 0,
                    "total_rawatib": 0,
                    "total_almatsurat": 0,
                    "total_shalawat": 0,
                    "total_istighfar": 0,
                    "total_tadabbur": 0,
                    "count_shaum": 0,
                    "count_qiyam": 0,
                    "count_dhuha": 0,
                    "total_olahraga": 0,
                    "count_olahraga": 0,
                    "count_silaturahim": 0,
                    "total_doa_ummat": 0,
                    "total_score": 0.0,
                    "highlights": [],
                }
            m_stat = member_map[uid]
            m_stat["days_submitted"] += 1
            m_stat["total_tilawah"] += _parse_int(r.get("Tilawah Pages", 0))
            m_stat["total_wajib"] += _parse_int(r.get("Sholat Wajib", 0))
            m_stat["total_rawatib"] += _parse_int(r.get("Rawatib Rakaat", 0))
            m_stat["total_almatsurat"] += _parse_int(r.get("Almatsurat", 0))
            m_stat["total_shalawat"] += _parse_int(r.get("Shalawat", 0))
            m_stat["total_istighfar"] += _parse_int(r.get("Istighfar", 0))
            m_stat["total_tadabbur"] += _parse_int(r.get("Tadabbur Ayat", 0))
            if _parse_bool(r.get("Shaum Sunnah")):
                m_stat["count_shaum"] += 1
            if _parse_bool(r.get("Qiyamulail")):
                m_stat["count_qiyam"] += 1
            if _parse_bool(r.get("Dhuha")):
                m_stat["count_dhuha"] += 1
            
            ol_val = _parse_int(r.get("Olahraga", 0)) if not _parse_bool(r.get("Olahraga")) else 30
            m_stat["total_olahraga"] += ol_val
            if ol_val > 0 or _parse_bool(r.get("Olahraga")):
                m_stat["count_olahraga"] += 1

            if _parse_bool(r.get("Silaturahim")):
                m_stat["count_silaturahim"] += 1
            m_stat["total_doa_ummat"] += _parse_int(r.get("Doa Ummat Islam", 0))

            # Unified scoring per row
            row_scores = _calculate_row_scores(r)
            if row_scores:
                m_stat["total_score"] += sum(row_scores) / len(row_scores)

        member_breakdown = list(member_map.values())
        for m_stat in member_breakdown:
            days = m_stat["days_submitted"]
            m_stat["avg_completion"] = (
                round((m_stat["total_score"] / days) * 100, 1) if days > 0 else 0.0
            )
            m_stat["highlights"] = _extract_member_highlights(m_stat)

        # Sort members by days submitted descending, then avg_completion descending
        member_breakdown.sort(
            key=lambda x: (x["days_submitted"], x["avg_completion"]), reverse=True
        )

        active_submitted = [m for m in member_breakdown if m["days_submitted"] > 0]
        if active_submitted:
            comp_list = [m["avg_completion"] for m in active_submitted]
            min_completion_rate = min(comp_list)
            max_completion_rate = max(comp_list)

            days_list = [m["days_submitted"] for m in active_submitted]
            avg_days_submitted = round(sum(days_list) / len(days_list), 1)
            min_days_submitted = min(days_list)
            max_days_submitted = max(days_list)

            til_list = [round(m["total_tilawah"] / m["days_submitted"], 1) for m in active_submitted]
            min_tilawah = min(til_list)
            max_tilawah = max(til_list)

            waj_list = [round(m["total_wajib"] / m["days_submitted"], 1) for m in active_submitted]
            min_wajib = min(waj_list)
            max_wajib = max(waj_list)

            raw_list = [round(m["total_rawatib"] / m["days_submitted"], 1) for m in active_submitted]
            min_rawatib = min(raw_list)
            max_rawatib = max(raw_list)

            mat_list = [round(m["total_almatsurat"] / m["days_submitted"], 1) for m in active_submitted]
            min_almatsurat = min(mat_list)
            max_almatsurat = max(mat_list)

            shal_list = [round(m["total_shalawat"] / m["days_submitted"], 1) for m in active_submitted]
            min_shalawat = min(shal_list)
            max_shalawat = max(shal_list)

            ist_list = [round(m["total_istighfar"] / m["days_submitted"], 1) for m in active_submitted]
            min_istighfar = min(ist_list)
            max_istighfar = max(ist_list)

            tad_list = [round(m["total_tadabbur"] / m["days_submitted"], 1) for m in active_submitted]
            min_tadabbur = min(tad_list)
            max_tadabbur = max(tad_list)

            ol_list = [round(m["total_olahraga"] / m["days_submitted"], 1) for m in active_submitted]
            min_olahraga = min(ol_list)
            max_olahraga = max(ol_list)

            doa_list = [round(m["total_doa_ummat"] / m["days_submitted"], 1) for m in active_submitted]
            min_doa_ummat = min(doa_list)
            max_doa_ummat = max(doa_list)

            # Checklist amalan per-member stats
            dhuha_counts = [m["count_dhuha"] for m in active_submitted]
            dhuha_members = sum(1 for c in dhuha_counts if c > 0)
            pct_dhuha_members = round((dhuha_members / len(active_submitted)) * 100, 1)
            avg_dhuha_per_member = round(sum(dhuha_counts) / len(active_submitted), 1)
            min_dhuha = min(dhuha_counts)
            max_dhuha = max(dhuha_counts)

            qiyam_counts = [m["count_qiyam"] for m in active_submitted]
            qiyam_members = sum(1 for c in qiyam_counts if c > 0)
            pct_qiyam_members = round((qiyam_members / len(active_submitted)) * 100, 1)
            avg_qiyam_per_member = round(sum(qiyam_counts) / len(active_submitted), 1)
            min_qiyam = min(qiyam_counts)
            max_qiyam = max(qiyam_counts)

            shaum_counts = [m["count_shaum"] for m in active_submitted]
            shaum_members = sum(1 for c in shaum_counts if c > 0)
            pct_shaum_members = round((shaum_members / len(active_submitted)) * 100, 1)
            avg_shaum_per_member = round(sum(shaum_counts) / len(active_submitted), 1)
            min_shaum = min(shaum_counts)
            max_shaum = max(shaum_counts)

            silaturahim_counts = [m["count_silaturahim"] for m in active_submitted]
            silaturahim_members = sum(1 for c in silaturahim_counts if c > 0)
            pct_silaturahim_members = round((silaturahim_members / len(active_submitted)) * 100, 1)
            avg_silaturahim_per_member = round(sum(silaturahim_counts) / len(active_submitted), 1)
            min_silaturahim = min(silaturahim_counts)
            max_silaturahim = max(silaturahim_counts)
        else:
            min_completion_rate = 0.0
            max_completion_rate = 0.0
            avg_days_submitted = 0.0
            min_days_submitted = 0
            max_days_submitted = 0
            min_tilawah = max_tilawah = 0.0
            min_wajib = max_wajib = 0.0
            min_rawatib = max_rawatib = 0.0
            min_almatsurat = max_almatsurat = 0.0
            min_shalawat = max_shalawat = 0.0
            min_istighfar = max_istighfar = 0.0
            min_tadabbur = max_tadabbur = 0.0
            min_olahraga = max_olahraga = 0.0
            min_doa_ummat = max_doa_ummat = 0.0
            dhuha_members = qiyam_members = shaum_members = silaturahim_members = 0
            pct_dhuha_members = pct_qiyam_members = pct_shaum_members = pct_silaturahim_members = 0.0
            avg_dhuha_per_member = avg_qiyam_per_member = avg_shaum_per_member = avg_silaturahim_per_member = 0.0
            min_dhuha = max_dhuha = 0
            min_qiyam = max_qiyam = 0
            min_shaum = max_shaum = 0
            min_silaturahim = max_silaturahim = 0

        pct_shaum = round((count_shaum / n_entries) * 100, 1) if n_entries > 0 else 0.0
        pct_qiyam = round((count_qiyam / n_entries) * 100, 1) if n_entries > 0 else 0.0
        pct_dhuha = round((count_dhuha / n_entries) * 100, 1) if n_entries > 0 else 0.0
        pct_silaturahim = round((count_silaturahim / n_entries) * 100, 1) if n_entries > 0 else 0.0

        return {
            "period_label": period_label,
            "start_date": start_date,
            "end_date": end_date,
            "registered_members": registered_count,
            "active_submitters": active_submitters_count,
            "active_submitters_month": active_submitters_count,  # backward compatibility
            "submissions_today": today_submissions_count,
            "submission_rate_today": submission_rate_today,
            "submission_rate": submission_rate,
            "total_submissions": n_entries,
            "total_monthly_records": n_entries,  # backward compatibility
            "month_label": period_label,  # backward compatibility
            "average_completion_rate": avg_completion,
            "min_completion_rate": min_completion_rate,
            "max_completion_rate": max_completion_rate,
            "avg_days_submitted": avg_days_submitted,
            "min_days_submitted": min_days_submitted,
            "max_days_submitted": max_days_submitted,
            "total_tilawah": total_tilawah,
            "avg_tilawah": avg_tilawah,
            "min_tilawah": min_tilawah,
            "max_tilawah": max_tilawah,
            "total_wajib": total_wajib,
            "avg_wajib": avg_wajib,
            "min_wajib": min_wajib,
            "max_wajib": max_wajib,
            "total_rawatib": total_rawatib,
            "avg_rawatib": avg_rawatib,
            "min_rawatib": min_rawatib,
            "max_rawatib": max_rawatib,
            "total_almatsurat": total_almatsurat,
            "avg_almatsurat": avg_almatsurat,
            "min_almatsurat": min_almatsurat,
            "max_almatsurat": max_almatsurat,
            "total_shalawat": total_shalawat,
            "avg_shalawat": avg_shalawat,
            "min_shalawat": min_shalawat,
            "max_shalawat": max_shalawat,
            "total_istighfar": total_istighfar,
            "avg_istighfar": avg_istighfar,
            "min_istighfar": min_istighfar,
            "max_istighfar": max_istighfar,
            "total_tadabbur": total_tadabbur,
            "avg_tadabbur": avg_tadabbur,
            "min_tadabbur": min_tadabbur,
            "max_tadabbur": max_tadabbur,
            "count_shaum": count_shaum,
            "pct_shaum": pct_shaum,
            "shaum_members": shaum_members,
            "pct_shaum_members": pct_shaum_members,
            "avg_shaum_per_member": avg_shaum_per_member,
            "min_shaum": min_shaum,
            "max_shaum": max_shaum,
            "count_qiyam": count_qiyam,
            "pct_qiyam": pct_qiyam,
            "qiyam_members": qiyam_members,
            "pct_qiyam_members": pct_qiyam_members,
            "avg_qiyam_per_member": avg_qiyam_per_member,
            "min_qiyam": min_qiyam,
            "max_qiyam": max_qiyam,
            "count_dhuha": count_dhuha,
            "pct_dhuha": pct_dhuha,
            "dhuha_members": dhuha_members,
            "pct_dhuha_members": pct_dhuha_members,
            "avg_dhuha_per_member": avg_dhuha_per_member,
            "min_dhuha": min_dhuha,
            "max_dhuha": max_dhuha,
            "count_olahraga": count_olahraga,
            "total_olahraga": total_olahraga,
            "avg_olahraga": avg_olahraga,
            "min_olahraga": min_olahraga,
            "max_olahraga": max_olahraga,
            "count_silaturahim": count_silaturahim,
            "pct_silaturahim": pct_silaturahim,
            "silaturahim_members": silaturahim_members,
            "pct_silaturahim_members": pct_silaturahim_members,
            "avg_silaturahim_per_member": avg_silaturahim_per_member,
            "min_silaturahim": min_silaturahim,
            "max_silaturahim": max_silaturahim,
            "total_doa_ummat": total_doa_ummat,
            "avg_doa_ummat": avg_doa_ummat,
            "min_doa_ummat": min_doa_ummat,
            "max_doa_ummat": max_doa_ummat,
            "member_breakdown": member_breakdown,
        }

    async def calculate_monthly_admin_stats(
        self, tz_name: str = Config.TIMEZONE
    ) -> Dict[str, Any]:
        """Calculate aggregate stats for current month (admin default)."""
        presets = get_date_range_presets(tz_name)
        monthly = presets["monthly"]
        return await self.calculate_period_admin_stats(
            monthly["start_date"],
            monthly["end_date"],
            monthly["label"],
            tz_name,
        )
