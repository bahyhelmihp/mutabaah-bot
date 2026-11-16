from datetime import datetime
from typing import Optional, List, Dict, Set
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

INDONESIAN_MONTHS_SHORT = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "Mei",
    6: "Jun",
    7: "Jul",
    8: "Agt",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Des",
}

INDONESIAN_DAYS = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
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


def _format_day_ranges(days: List[int]) -> str:
    """Format a list of day numbers: e.g. [2, 5, 8] -> '2, 5, 8' or long ranges -> '1-10, 15, 18-20'."""
    if not days:
        return ""
    sorted_days = sorted(set(days))
    if len(sorted_days) <= 10:
        return ", ".join(str(d) for d in sorted_days)

    ranges = []
    start = sorted_days[0]
    prev = sorted_days[0]
    for d in sorted_days[1:]:
        if d == prev + 1:
            prev = d
        else:
            if start == prev:
                ranges.append(str(start))
            elif prev == start + 1:
                ranges.append(f"{start}, {prev}")
            else:
                ranges.append(f"{start}-{prev}")
            start = d
            prev = d
    if start == prev:
        ranges.append(str(start))
    elif prev == start + 1:
        ranges.append(f"{start}, {prev}")
    else:
        ranges.append(f"{start}-{prev}")
    return ", ".join(ranges)


def format_missing_dates_id(missing_dates: List[str], tz_name: str = "Asia/Seoul") -> str:
    """
    Format a list of YYYY-MM-DD date strings into a readable Indonesian list.
    e.g. ['2026-10-02', '2026-10-05', '2026-10-18'] -> '2, 5, 18 Oktober'
    Handles single month or multi-month lists gracefully.
    """
    if not missing_dates:
        return ""

    from collections import defaultdict
    by_month = defaultdict(list)
    for d_str in missing_dates:
        try:
            dt = datetime.strptime(d_str.strip(), "%Y-%m-%d")
            by_month[(dt.year, dt.month)].append(dt.day)
        except ValueError:
            pass

    if not by_month:
        return ", ".join(missing_dates)

    parts = []
    for (year, month), days in sorted(by_month.items()):
        month_name = INDONESIAN_MONTHS.get(month, str(month))
        days_str = _format_day_ranges(days)
        parts.append(f"{days_str} {month_name}")

    return "; ".join(parts)



def get_date_range_presets(tz_name: str = "Asia/Seoul"):
    """
    Returns preset date ranges for admin reporting:
    - today
    - weekly (last 7 days)
    - monthly (current month)
    - last_month (previous calendar month)
    """
    from datetime import timedelta
    now = get_now(tz_name)
    today_str = now.strftime("%Y-%m-%d")

    # Today
    today_preset = {
        "key": "today",
        "label": f"Hari Ini ({format_date_id(now)})",
        "start_date": today_str,
        "end_date": today_str,
    }

    # Weekly: last 7 days including today
    week_start = now - timedelta(days=6)
    week_start_str = week_start.strftime("%Y-%m-%d")
    weekly_preset = {
        "key": "weekly",
        "label": f"7 Hari Terakhir ({week_start.day} {INDONESIAN_MONTHS.get(week_start.month)} - {format_date_id(now)})",
        "start_date": week_start_str,
        "end_date": today_str,
    }

    # Monthly: current month from 1st to today
    month_start_str = now.strftime("%Y-%m-01")
    monthly_preset = {
        "key": "monthly",
        "label": f"Bulan Ini ({format_month_year_id(now, tz_name)})",
        "start_date": month_start_str,
        "end_date": today_str,
    }

    # Last Month: 1st to last day of previous month
    first_of_curr_month = datetime(now.year, now.month, 1)
    last_day_prev_month = first_of_curr_month - timedelta(days=1)
    first_day_prev_month = datetime(last_day_prev_month.year, last_day_prev_month.month, 1)
    last_month_preset = {
        "key": "last_month",
        "label": f"Bulan Lalu ({format_month_year_id(last_day_prev_month, tz_name)})",
        "start_date": first_day_prev_month.strftime("%Y-%m-%d"),
        "end_date": last_day_prev_month.strftime("%Y-%m-%d"),
    }

    return {
        "today": today_preset,
        "weekly": weekly_preset,
        "monthly": monthly_preset,
        "last_month": last_month_preset,
    }


def parse_custom_date_range(text: str) -> Optional[dict]:
    """
    Parse user input into start_date and end_date (YYYY-MM-DD).
    Extracts dates regardless of separators (s/d, -, to, sampai, etc.).
    Supported:
    - 2026-10-01 s/d 2026-10-10
    - 2026-10-01 - 2026-10-10
    - 2026-10-01 to 2026-10-10
    - 2026-10-05 (single date)
    - 01/10/2026 - 10/10/2026 or 01-10-2026 - 10-10-2026
    """
    import re
    cleaned = text.strip()
    if not cleaned:
        return None

    def parse_single_date(d_str: str) -> Optional[datetime]:
        d_str = d_str.strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(d_str, fmt)
            except ValueError:
                continue
        return None

    # Find all date patterns in the text
    matches = re.findall(
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b", cleaned
    )

    if len(matches) == 1:
        dt = parse_single_date(matches[0])
        if dt:
            dt_str = dt.strftime("%Y-%m-%d")
            return {
                "key": "custom",
                "label": f"Tanggal {format_date_id(dt)}",
                "start_date": dt_str,
                "end_date": dt_str,
            }
        return None

    if len(matches) >= 2:
        dt1 = parse_single_date(matches[0])
        dt2 = parse_single_date(matches[1])
        if dt1 and dt2:
            if dt1 > dt2:
                dt1, dt2 = dt2, dt1
            s_str = dt1.strftime("%Y-%m-%d")
            e_str = dt2.strftime("%Y-%m-%d")
            return {
                "key": "custom",
                "label": f"Rentang {format_date_id(dt1)} s/d {format_date_id(dt2)}",
                "start_date": s_str,
                "end_date": e_str,
            }

    return None


def parse_date_input(text: str, tz_name: str = "Asia/Seoul") -> Optional[str]:
    """
    Parse a single date from user input.
    Supported:
    - Keywords: 'hari ini', 'today', 'kemarin', 'yesterday', 'kemarin lusa', 'h-2', 'h-3'
    - Formats: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, YYYY/MM/DD, DD-MM, DD/MM
    Returns formatted date 'YYYY-MM-DD' or None.
    """
    from datetime import timedelta
    cleaned = text.strip().lower()
    if not cleaned:
        return None

    now = get_now(tz_name)

    if cleaned in ["hari ini", "today", "hariini"]:
        return now.strftime("%Y-%m-%d")
    if cleaned in ["kemarin", "yesterday", "kmrn", "h-1"]:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    if cleaned in ["kemarin lusa", "lusa kemarin", "h-2"]:
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")
    if cleaned in ["h-3"]:
        return (now - timedelta(days=3)).strftime("%Y-%m-%d")

    # Try standard formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Try DD-MM or DD/MM with current year
    for fmt in ("%d-%m", "%d/%m"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            dt = dt.replace(year=now.year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def get_recent_dates_list(num_days: int = 6, tz_name: str = "Asia/Seoul"):
    """
    Returns recent dates from today going backwards.
    Used for date picker keyboards.
    """
    from datetime import timedelta
    now = get_now(tz_name)
    items = []

    for i in range(num_days + 1):
        dt = now - timedelta(days=i)
        d_str = dt.strftime("%Y-%m-%d")
        day_name = INDONESIAN_DAYS.get(dt.weekday(), "")
        month_short = INDONESIAN_MONTHS_SHORT.get(dt.month, str(dt.month))

        if i == 0:
            label = f"📅 Hari Ini ({dt.day} {month_short})"
        elif i == 1:
            label = f"⏪ Kemarin ({dt.day} {month_short})"
        else:
            label = f"{day_name}, {dt.day} {month_short}"

        items.append({
            "date": d_str,
            "label": label,
            "is_today": (i == 0),
            "is_yesterday": (i == 1),
            "day_name": day_name,
        })

    return items
