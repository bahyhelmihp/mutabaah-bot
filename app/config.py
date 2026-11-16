import os
import logging
from typing import List, Set
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "").strip()
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

    # Comma-separated admin Telegram IDs e.g. "123456789,987654321"
    ADMIN_TELEGRAM_IDS_RAW: str = os.getenv("ADMIN_TELEGRAM_IDS", "").strip()
    ADMIN_TELEGRAM_IDS: Set[int] = set()

    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Seoul").strip()
    REMINDER_HOUR: int = int(os.getenv("REMINDER_HOUR", "21").strip())
    REMINDER_MINUTE: int = int(os.getenv("REMINDER_MINUTE", "0").strip())

    # Worksheet Names
    SHEET_MEMBERS: str = "Members"
    SHEET_DAILY_MUTABAAH: str = "Daily Mutabaah"
    SHEET_USER_SETTINGS: str = "User Settings"
    SHEET_SUMMARY_STATS: str = "Summary Stats"
    SHEET_MAPPING: str = "Mapping"

    @classmethod
    def load(cls):
        """Parse raw values and validate."""
        admin_ids: Set[int] = set()
        if cls.ADMIN_TELEGRAM_IDS_RAW:
            for item in cls.ADMIN_TELEGRAM_IDS_RAW.split(","):
                cleaned = item.strip()
                if cleaned.isdigit():
                    admin_ids.add(int(cleaned))
        cls.ADMIN_TELEGRAM_IDS = admin_ids

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        return user_id in cls.ADMIN_TELEGRAM_IDS

    @classmethod
    def validate(cls) -> List[str]:
        """Return list of configuration warnings/errors."""
        errors = []
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is missing or empty.")
        if not cls.GOOGLE_SHEET_ID:
            errors.append("GOOGLE_SHEET_ID is missing or empty.")
        if not cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            errors.append("GOOGLE_SERVICE_ACCOUNT_JSON is missing or empty.")
        return errors


Config.load()
