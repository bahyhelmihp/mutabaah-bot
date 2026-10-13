from datetime import datetime
from typing import Optional
import pytz

INDONESIAN_MONTHS = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def get_tz(tz_name: str = "Asia/Seoul") -> pytz.BaseTzInfo:
    try:
        return pytz.timezone(tz_name)
    except Exception:
        return pytz.timezone("Asia/Seoul")


def get_now(tz_name: str = "Asia/Seoul") -> datetime:
    """Returns the current datetime in the specified timezone."""
    return datetime.now(get_tz(tz_name))


def get_today_str(tz_name: str = "Asia/Seoul") -> str:
    """Returns today's date formatted as YYYY-MM-DD in the specified timezone."""
    return get_now(tz_name).strftime("%Y-%m-%d")


def get_timestamp_str(tz_name: str = "Asia/Seoul") -> str:
    """Returns current timestamp formatted as YYYY-MM-DD HH:MM:SS."""
    return get_now(tz_name).strftime("%Y-%m-%d %H:%M:%S")


def get_current_month_prefix(tz_name: str = "Asia/Seoul") -> str:
    """Returns current year-month as YYYY-MM."""
    return get_now(tz_name).strftime("%Y-%m")


def format_date_id(dt: Optional[datetime] = None, date_str: Optional[str] = None, tz_name: str = "Asia/Seoul") -> str:
    """
    Format a datetime or YYYY-MM-DD string into Indonesian date:
    e.g. '13 Oktober 2026'
    """
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass

    if dt is None:
        dt = get_now(tz_name)

    month_name = INDONESIAN_MONTHS.get(dt.month, str(dt.month))
    return f"{dt.day} {month_name} {dt.year}"


def format_month_year_id(dt: Optional[datetime] = None, tz_name: str = "Asia/Seoul") -> str:
    """
    Format a datetime into Indonesian Month Year:
    e.g. 'Oktober 2026'
    """
    if dt is None:
        dt = get_now(tz_name)

    month_name = INDONESIAN_MONTHS.get(dt.month, str(dt.month))
    return f"{month_name} {dt.year}"
