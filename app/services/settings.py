"""
Service for managing user-specific amalan choices and custom targets.
"""
import logging
import time
from typing import Dict, List, Any, Optional
from app.services.sheets import SheetsService
from app.services.amalan import (
    ALL_AMALAN_KEYS,
    get_default_targets,
    AMALAN_DEFINITIONS,
)
from app.config import Config
from app.utils.datetime import get_timestamp_str

logger = logging.getLogger(__name__)


class UserSettingsService:
    _instance: Optional["UserSettingsService"] = None

    def __new__(cls, sheets_service: Optional[SheetsService] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, sheets_service: Optional[SheetsService] = None):
        if getattr(self, "_initialized", False):
            if sheets_service and sheets_service is not self.sheets:
                self.sheets = sheets_service
            return
        self.sheets = sheets_service or SheetsService.get_instance()
        # Cache format: {str(user_id): {"active_amalan": [...], "targets": {...}}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_loaded = False
        self._cache_time: float = 0.0
        self._initialized = True

    @classmethod
    def get_instance(cls, sheets_service: Optional[SheetsService] = None) -> "UserSettingsService":
        if cls._instance is None:
            cls._instance = cls(sheets_service)
        return cls._instance

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "active_amalan": list(ALL_AMALAN_KEYS),
            "targets": get_default_targets(),
        }

    async def reload_cache(self, force: bool = False) -> None:
        """Fetch all user settings from sheets into cache."""
        now = time.time()
        if not force and self._cache_loaded and (now - self._cache_time < 120):
            return
        try:
            records = await self.sheets.get_all_user_settings(force_refresh=force)
            self._cache.clear()
            for r in records:
                uid = str(r.get("Telegram User ID", "")).strip()
                if not uid:
                    continue

                active_raw = str(r.get("Active Amalan", "")).strip()
                if active_raw:
                    active_list = [k.strip() for k in active_raw.split(",") if k.strip() in AMALAN_DEFINITIONS]
                    if not active_list:
                        active_list = list(ALL_AMALAN_KEYS)
                else:
                    active_list = list(ALL_AMALAN_KEYS)

                targets = get_default_targets()
                for key, defn in AMALAN_DEFINITIONS.items():
                    candidate_cols = [
                        f"Target {defn['short_name']}",
                        f"Target {defn['column']}",
                        f"Target {defn['name']}",
                    ]
                    for col_name in candidate_cols:
                        if col_name in r and str(r[col_name]).strip().isdigit():
                            targets[key] = int(str(r[col_name]).strip())
                            break

                self._cache[uid] = {
                    "active_amalan": active_list,
                    "targets": targets,
                }
            self._cache_loaded = True
            self._cache_time = now
            logger.info("Loaded settings for %d users into cache.", len(self._cache))
        except Exception as e:
            logger.error("Failed to load user settings from sheets: %s", e)

    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get settings for a user, returning default if not configured yet."""
        uid_str = str(user_id).strip()
        if not self._cache_loaded or (time.time() - self._cache_time > 180):
            await self.reload_cache()

        if uid_str in self._cache:
            return self._cache[uid_str]

        # Check directly from sheets in case cache missed
        try:
            sheet_record = await self.sheets.get_user_settings(user_id)
            if sheet_record:
                active_raw = str(sheet_record.get("Active Amalan", "")).strip()
                if active_raw:
                    active_list = [
                        k.strip()
                        for k in active_raw.split(",")
                        if k.strip() in AMALAN_DEFINITIONS
                    ]
                    if not active_list:
                        active_list = list(ALL_AMALAN_KEYS)
                else:
                    active_list = list(ALL_AMALAN_KEYS)

                targets = get_default_targets()
                for key, defn in AMALAN_DEFINITIONS.items():
                    candidate_cols = [
                        f"Target {defn['short_name']}",
                        f"Target {defn['column']}",
                        f"Target {defn['name']}",
                    ]
                    for col_name in candidate_cols:
                        if col_name in sheet_record and str(sheet_record[col_name]).strip().isdigit():
                            targets[key] = int(str(sheet_record[col_name]).strip())
                            break

                settings = {
                    "active_amalan": active_list,
                    "targets": targets,
                }
                self._cache[uid_str] = settings
                return settings
        except Exception as e:
            logger.error("Error looking up settings for user %s: %s", user_id, e)

        # Default configuration
        default_cfg = self._get_default_config()
        self._cache[uid_str] = default_cfg
        return default_cfg

    async def get_active_amalan(self, user_id: int) -> List[str]:
        settings = await self.get_user_settings(user_id)
        return settings.get("active_amalan", list(ALL_AMALAN_KEYS))

    async def get_user_targets(self, user_id: int) -> Dict[str, int]:
        settings = await self.get_user_settings(user_id)
        return settings.get("targets", get_default_targets())

    async def save_user_settings(
        self, user_id: int, active_amalan: List[str], targets: Dict[str, int]
    ) -> bool:
        """Persist settings to Google Sheets and in-memory cache."""
        uid_str = str(user_id).strip()
        # Clean active amalan
        valid_active = [k for k in active_amalan if k in AMALAN_DEFINITIONS]
        if not valid_active:
            # Prevent empty list, fallback to all
            valid_active = list(ALL_AMALAN_KEYS)

        # Merge with default targets for completeness
        merged_targets = get_default_targets()
        merged_targets.update(targets)

        self._cache[uid_str] = {
            "active_amalan": valid_active,
            "targets": merged_targets,
        }

        # Save to Google Sheets
        try:
            payload = {
                "user_id": uid_str,
                "active_amalan": ",".join(valid_active),
                "targets": merged_targets,
                "timestamp": get_timestamp_str(Config.TIMEZONE),
            }
            return await self.sheets.save_user_settings(payload)
        except Exception as e:
            logger.error("Failed to save user settings for %s to sheet: %s", user_id, e)
            return False

    async def toggle_amalan(self, user_id: int, amalan_key: str) -> List[str]:
        """Toggle an amalan on/off for a user."""
        settings = await self.get_user_settings(user_id)
        active = list(settings.get("active_amalan", list(ALL_AMALAN_KEYS)))
        targets = dict(settings.get("targets", get_default_targets()))

        if amalan_key in active:
            if len(active) > 1:  # Keep at least 1 amalan active
                active.remove(amalan_key)
        else:
            active.append(amalan_key)

        await self.save_user_settings(user_id, active, targets)
        return active

    async def set_target(self, user_id: int, amalan_key: str, new_target: int) -> Dict[str, int]:
        """Update a specific target for a user."""
        settings = await self.get_user_settings(user_id)
        active = list(settings.get("active_amalan", list(ALL_AMALAN_KEYS)))
        targets = dict(settings.get("targets", get_default_targets()))

        targets[amalan_key] = max(1, int(new_target))
        await self.save_user_settings(user_id, active, targets)
        return targets

    async def reset_to_default(self, user_id: int) -> Dict[str, Any]:
        """Reset user to all default amalan and targets."""
        default_cfg = self._get_default_config()
        await self.save_user_settings(
            user_id, default_cfg["active_amalan"], default_cfg["targets"]
        )
        return default_cfg
