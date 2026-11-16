"""
Service for managing Murobbi - Mutarabbi mapping and monitoring.
Source of truth: 'Mapping' worksheet in Google Sheets.
"""
import logging
import asyncio
import time
from typing import Dict, List, Optional, Set, Any
from app.services.sheets import SheetsService
from app.services.statistics import StatisticsService
from app.services.members import MembersService
from app.utils.datetime import get_today_str, format_date_id, get_now
from app.config import Config

logger = logging.getLogger(__name__)


class MappingService:
    _instance: Optional["MappingService"] = None

    def __init__(self, sheets_service: Optional[SheetsService] = None):
        self.sheets = sheets_service or SheetsService.get_instance()
        self._murobbi_ids: Set[str] = set()
        self._murobbi_names: Dict[str, str] = {}
        self._murobbi_binaan: Dict[str, List[Dict[str, str]]] = {}
        self._mutarabbi_meta: Dict[str, Dict[str, str]] = {}
        self._cache_loaded = False
        self._cache_time: float = 0.0
        self.MAPPING_CACHE_TTL: float = 300.0  # 5 minutes auto-refresh TTL
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "MappingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def reload_cache(self, force: bool = False) -> None:
        """Fetch all mapping rows from Google Sheets and build cache."""
        now = time.time()
        if not force and self._cache_loaded and (now - self._cache_time < self.MAPPING_CACHE_TTL):
            return

        async with self._lock:
            # Double check inside lock
            if not force and self._cache_loaded and (time.time() - self._cache_time < self.MAPPING_CACHE_TTL):
                return
            try:
                rows = await self.sheets.get_all_mapping_rows(force_refresh=force)
                new_murobbi_ids: Set[str] = set()
                new_murobbi_names: Dict[str, str] = {}
                new_murobbi_binaan: Dict[str, List[Dict[str, str]]] = {}
                new_mutarabbi_meta: Dict[str, Dict[str, str]] = {}

                for r in rows:
                    m_id = str(r.get("murobbi_id", "")).strip()
                    m_name = str(r.get("murobbi_name", "")).strip()
                    mut_id = str(r.get("mutarabbi_id", "")).strip()
                    mut_name = str(r.get("mutarabbi_name", "")).strip()
                    kelompok = str(r.get("kelompok", "")).strip()

                    if m_id:
                        new_murobbi_ids.add(m_id)
                        if m_name and m_id not in new_murobbi_names:
                            new_murobbi_names[m_id] = m_name

                    if m_id and mut_id:
                        if m_id not in new_murobbi_binaan:
                            new_murobbi_binaan[m_id] = []
                        # Avoid duplicates
                        existing_ids = {b["id"] for b in new_murobbi_binaan[m_id]}
                        if mut_id not in existing_ids:
                            new_murobbi_binaan[m_id].append({
                                "id": mut_id,
                                "name": mut_name,
                                "kelompok": kelompok,
                            })

                        if mut_id not in new_mutarabbi_meta:
                            new_mutarabbi_meta[mut_id] = {
                                "id": mut_id,
                                "name": mut_name,
                                "kelompok": kelompok,
                            }

                self._murobbi_ids = new_murobbi_ids
                self._murobbi_names = new_murobbi_names
                self._murobbi_binaan = new_murobbi_binaan
                self._mutarabbi_meta = new_mutarabbi_meta
                self._cache_loaded = True
                self._cache_time = time.time()
                logger.info(
                    "Loaded mapping cache: %d murobbi, %d total binaan entries",
                    len(self._murobbi_ids),
                    sum(len(b) for b in self._murobbi_binaan.values()),
                )
            except Exception as e:
                logger.error("Failed to load mapping cache from Google Sheets: %s", e)

    async def is_murobbi_async(self, user_id: int) -> bool:
        """Check if user_id is listed as a Murobbi (auto-loads or refreshes cache if TTL expired)."""
        now = time.time()
        if not self._cache_loaded or (now - self._cache_time > self.MAPPING_CACHE_TTL):
            await self.reload_cache()
        return str(user_id).strip() in self._murobbi_ids

    def is_murobbi(self, user_id: int) -> bool:
        """Synchronous check if user_id is a Murobbi based on current cache."""
        return str(user_id).strip() in self._murobbi_ids

    def get_murobbi_name(self, user_id: int) -> str:
        """Get Murobbi display name."""
        return self._murobbi_names.get(str(user_id).strip(), "")

    def get_binaan(self, user_id: int) -> List[Dict[str, str]]:
        """Get list of binaan for this Murobbi."""
        return self._murobbi_binaan.get(str(user_id).strip(), [])

    def get_mutarabbi_meta(self, mutarabbi_id: str) -> Optional[Dict[str, str]]:
        """Get metadata (name, kelompok) for a mutarabbi."""
        return self._mutarabbi_meta.get(str(mutarabbi_id).strip())

    async def get_binaan_overview(
        self, user_id: int, tz_name: str = Config.TIMEZONE
    ) -> Dict[str, Any]:
        """
        Generate overview of all binaan for a Murobbi:
        - Submission status today
        - Monthly progress completion %
        """
        now = time.time()
        if not self._cache_loaded or (now - self._cache_time > self.MAPPING_CACHE_TTL):
            await self.reload_cache()

        uid_str = str(user_id).strip()
        murobbi_name = self.get_murobbi_name(user_id) or "Murobbi"
        binaan_list = self.get_binaan(user_id)

        today_str = get_today_str(tz_name)
        now_dt = get_now(tz_name)
        today_formatted = format_date_id(date_str=today_str, tz_name=tz_name)

        stats_service = StatisticsService(self.sheets)

        # Pre-check today submissions from all mutabaah rows
        all_rows = await self.sheets.get_all_mutabaah_rows()
        submitted_today_uids = {
            str(r.get("Telegram User ID", "")).strip()
            for r in all_rows
            if str(r.get("Date", "")).strip() == today_str
        }

        # Calculate progress for each binaan concurrently
        async def fetch_binaan_stat(b: Dict[str, str]) -> Dict[str, Any]:
            b_id_str = b["id"]
            is_submitted_today = b_id_str in submitted_today_uids
            month_days_submitted = 0
            month_days_passed = max(1, now_dt.day)
            completion_pct = 0.0

            try:
                b_uid_int = int(b_id_str)
                p_data = await stats_service.calculate_user_month_progress(b_uid_int, tz_name)
                month_days_submitted = p_data.get("days_submitted", 0)
                month_days_passed = p_data.get("days_passed", max(1, now_dt.day))
                completion_pct = p_data.get("completion_percentage", 0.0)
            except Exception as e:
                logger.warning("Could not calculate month progress for mutarabbi %s: %s", b_id_str, e)

            return {
                "id": b_id_str,
                "name": b["name"],
                "kelompok": b["kelompok"],
                "is_submitted_today": is_submitted_today,
                "month_days_submitted": month_days_submitted,
                "month_days_passed": month_days_passed,
                "completion_pct": completion_pct,
            }

        tasks = [fetch_binaan_stat(b) for b in binaan_list]
        enriched_binaan = await asyncio.gather(*tasks) if tasks else []

        submitted_count = sum(1 for b in enriched_binaan if b["is_submitted_today"])
        unsubmitted_count = len(enriched_binaan) - submitted_count

        return {
            "murobbi_id": uid_str,
            "murobbi_name": murobbi_name,
            "today_str": today_str,
            "today_formatted": today_formatted,
            "total_binaan": len(enriched_binaan),
            "submitted_today_count": submitted_count,
            "unsubmitted_today_count": unsubmitted_count,
            "binaan_list": enriched_binaan,
        }

    async def get_binaan_detail(
        self, mutarabbi_id: str, tz_name: str = Config.TIMEZONE
    ) -> Dict[str, Any]:
        """
        Get detailed mutabaah report for a specific mutarabbi:
        - Today's filled habits
        - Monthly achievement & missing dates
        """
        mid_str = str(mutarabbi_id).strip()
        meta = self.get_mutarabbi_meta(mid_str) or {
            "id": mid_str,
            "name": f"User {mid_str}",
            "kelompok": "-",
        }

        today_str = get_today_str(tz_name)
        today_formatted = format_date_id(date_str=today_str, tz_name=tz_name)

        # Today's submission
        today_record = None
        try:
            today_record = await self.sheets.get_user_mutabaah_record(int(mid_str), today_str)
        except Exception as e:
            logger.error("Error fetching today mutabaah for %s: %s", mid_str, e)

        # Monthly progress
        stats_service = StatisticsService(self.sheets)
        month_progress = {}
        try:
            month_progress = await stats_service.calculate_user_month_progress(int(mid_str), tz_name)
        except Exception as e:
            logger.error("Error calculating month progress for %s: %s", mid_str, e)

        # Member details (e.g. username)
        members_service = MembersService(self.sheets)
        member = await members_service.get_member(int(mid_str)) if mid_str.isdigit() else None
        username = member.get("Telegram Username", "") if member else ""

        return {
            "meta": meta,
            "username": username,
            "today_str": today_str,
            "today_formatted": today_formatted,
            "is_submitted_today": bool(today_record),
            "today_record": today_record,
            "month_progress": month_progress,
        }
