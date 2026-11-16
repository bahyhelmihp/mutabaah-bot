"""
Service for calculating user month progress and aggregate admin statistics.
"""
import logging
from typing import Dict, Any, List, Optional
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
                entry_scores = []
                til_str = str(r.get("Tilawah Pages", "")).strip().lower()
                if til_str not in ["berhalangan", "haid", "halangan"]:
                    entry_scores.append(min(_parse_int(r.get("Tilawah Pages", 0)) / 20.0, 1.0))

                waj_str = str(r.get("Sholat Wajib", "")).strip().lower()
                if waj_str not in ["berhalangan", "haid", "halangan"]:
                    entry_scores.append(min(_parse_int(r.get("Sholat Wajib", 0)) / 5.0, 1.0))

                entry_scores.append(min(_parse_int(r.get("Rawatib Rakaat", 0)) / 12.0, 1.0))
                entry_scores.append(min(_parse_int(r.get("Almatsurat", 0)) / 2.0, 1.0))
                entry_scores.append(min(_parse_int(r.get("Shalawat", 0)) / 100.0, 1.0))
                entry_scores.append(min(_parse_int(r.get("Istighfar", 0)) / 100.0, 1.0))
                entry_scores.append(min(_parse_int(r.get("Tadabbur Ayat", 0)) / 1.0, 1.0))

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
                "count_olahraga": 0,
                "count_silaturahim": 0,
                "total_doa_ummat": 0,
                "total_score": 0.0,
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
                    "count_olahraga": 0,
                    "count_silaturahim": 0,
                    "total_doa_ummat": 0,
                    "total_score": 0.0,
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
            if _parse_bool(r.get("Olahraga")):
                m_stat["count_olahraga"] += 1
            if _parse_bool(r.get("Silaturahim")):
                m_stat["count_silaturahim"] += 1
            m_stat["total_doa_ummat"] += _parse_int(r.get("Doa Ummat Islam", 0))

            # Score per row excluding berhalangan
            m_scores = []
            til_str = str(r.get("Tilawah Pages", "")).strip().lower()
            if til_str not in ["berhalangan", "haid", "halangan"]:
                m_scores.append(min(_parse_int(r.get("Tilawah Pages", 0)) / 20.0, 1.0))

            waj_str = str(r.get("Sholat Wajib", "")).strip().lower()
            if waj_str not in ["berhalangan", "haid", "halangan"]:
                m_scores.append(min(_parse_int(r.get("Sholat Wajib", 0)) / 5.0, 1.0))

            m_scores.append(min(_parse_int(r.get("Rawatib Rakaat", 0)) / 12.0, 1.0))
            m_scores.append(min(_parse_int(r.get("Almatsurat", 0)) / 2.0, 1.0))
            if m_scores:
                m_stat["total_score"] += sum(m_scores) / len(m_scores)

        member_breakdown = list(member_map.values())
        for m_stat in member_breakdown:
            days = m_stat["days_submitted"]
            m_stat["avg_completion"] = (
                round((m_stat["total_score"] / days) * 100, 1) if days > 0 else 0.0
            )

        # Sort members by days submitted descending, then avg_completion descending
        member_breakdown.sort(
            key=lambda x: (x["days_submitted"], x["avg_completion"]), reverse=True
        )

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
            "total_tilawah": total_tilawah,
            "avg_tilawah": avg_tilawah,
            "total_wajib": total_wajib,
            "avg_wajib": avg_wajib,
            "total_rawatib": total_rawatib,
            "avg_rawatib": avg_rawatib,
            "total_almatsurat": total_almatsurat,
            "avg_almatsurat": avg_almatsurat,
            "total_shalawat": total_shalawat,
            "avg_shalawat": avg_shalawat,
            "total_istighfar": total_istighfar,
            "avg_istighfar": avg_istighfar,
            "total_tadabbur": total_tadabbur,
            "avg_tadabbur": avg_tadabbur,
            "count_shaum": count_shaum,
            "count_qiyam": count_qiyam,
            "count_dhuha": count_dhuha,
            "count_olahraga": count_olahraga,
            "total_olahraga": total_olahraga,
            "avg_olahraga": avg_olahraga,
            "count_silaturahim": count_silaturahim,
            "total_doa_ummat": total_doa_ummat,
            "avg_doa_ummat": avg_doa_ummat,
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
