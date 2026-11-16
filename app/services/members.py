import logging
import time
from typing import Dict, List, Optional
from app.services.sheets import SheetsService
from app.utils.datetime import get_today_str
from app.config import Config

logger = logging.getLogger(__name__)


class MembersService:
    _instance: Optional["MembersService"] = None

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
        # In-memory cache of registered members: {user_id_str: member_dict}
        self._cache: Dict[str, Dict] = {}
        self._cache_loaded = False
        self._cache_time: float = 0.0
        self._initialized = True

    @classmethod
    def get_instance(cls, sheets_service: Optional[SheetsService] = None) -> "MembersService":
        if cls._instance is None:
            cls._instance = cls(sheets_service)
        return cls._instance

    async def reload_cache(self, force: bool = False) -> None:
        """Fetch all members from sheets and populate cache."""
        now = time.time()
        if not force and self._cache_loaded and (now - self._cache_time < 120):
            return
        try:
            members = await self.sheets.get_all_members(force_refresh=force)
            self._cache.clear()
            for m in members:
                uid = str(m.get("Telegram User ID", "")).strip()
                if uid:
                    self._cache[uid] = m
            self._cache_loaded = True
            self._cache_time = now
            logger.info("Loaded %d members into cache.", len(self._cache))
        except Exception as e:
            logger.error("Failed to load members from Google Sheets: %s", e)

    async def get_member(self, user_id: int) -> Optional[Dict]:
        """Get member info if registered."""
        uid_str = str(user_id)
        if not self._cache_loaded or (time.time() - self._cache_time > 180):
            await self.reload_cache()

        if uid_str in self._cache:
            return self._cache[uid_str]

        # Double check with direct sheet lookup in case cache is stale
        member = await self.sheets.find_member(user_id)
        if member:
            self._cache[uid_str] = member
            return member
        return None

    async def is_registered(self, user_id: int) -> bool:
        """Check if user is registered."""
        member = await self.get_member(user_id)
        if not member:
            return False
        active_val = str(member.get("Active", "")).strip().upper()
        return active_val in ["TRUE", "1", "YES"]

    async def register_member(self, user_id: int, username: str, full_name: str) -> bool:
        """Register a new member."""
        today = get_today_str(Config.TIMEZONE)
        success = await self.sheets.register_member(
            user_id=user_id,
            username=f"@{username.lstrip('@')}" if username else "",
            full_name=full_name,
            registration_date=today,
        )
        if success:
            # Update cache
            self._cache[str(user_id)] = {
                "Telegram User ID": str(user_id),
                "Telegram Username": f"@{username.lstrip('@')}" if username else "",
                "Full Name": full_name,
                "Registration Date": today,
                "Active": "TRUE",
            }
        return success

    async def update_name(
        self, user_id: int, new_full_name: str, username: Optional[str] = None
    ) -> bool:
        """Update full name for a member in Google Sheets and cache."""
        clean_name = new_full_name.strip()
        formatted_username = f"@{username.lstrip('@')}" if username else None
        success = await self.sheets.update_member_name(
            user_id=user_id,
            new_full_name=clean_name,
            username=formatted_username,
        )
        if success:
            uid_str = str(user_id)
            if uid_str in self._cache:
                self._cache[uid_str]["Full Name"] = clean_name
                if formatted_username:
                    self._cache[uid_str]["Telegram Username"] = formatted_username
            else:
                await self.reload_cache(force=True)
        return success


    async def get_all_active_members(self) -> List[Dict]:
        """Return list of all registered members where Active == TRUE."""
        await self.reload_cache()
        active_members = []
        for m in self._cache.values():
            active_val = str(m.get("Active", "")).strip().upper()
            if active_val in ["TRUE", "1", "YES"]:
                active_members.append(m)
        return active_members
