"""
Inline keyboards for Telegram Mutabaah Bot.
"""
from datetime import datetime
from typing import List, Dict, Optional, Set, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.config import Config
from app.services.amalan import (
    AMALAN_DEFINITIONS,
    ALL_AMALAN_KEYS,
    get_amalan_info,
)
from app.utils.datetime import get_recent_dates_list, INDONESIAN_MONTHS_SHORT


def get_main_menu_keyboard(
    is_murobbi: bool = False, is_admin: bool = False
) -> InlineKeyboardMarkup:
    """Main menu keyboard shown after /start or completion."""
    keyboard = [
        [InlineKeyboardButton("📝 Isi Mutabaah Hari Ini", callback_data="btn_isi")],
        [InlineKeyboardButton("📊 Lihat Progress Saya", callback_data="btn_progress")],
        [InlineKeyboardButton("✏️ Edit / Isi Hari Lain", callback_data="btn_edit")],
        [InlineKeyboardButton("⚙️ Pengaturan Amalan & Target", callback_data="btn_settings")],
    ]
    if is_murobbi:
        keyboard.append([
            InlineKeyboardButton("👥 Cek Mutabaah Binaan", callback_data="btn_cek_binaan")
        ])
    if is_admin:
        keyboard.append([
            InlineKeyboardButton("👑 Panel Admin", callback_data="admin_stats")
        ])
    return InlineKeyboardMarkup(keyboard)


async def get_user_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Helper to return main menu keyboard customized with user permissions (Murobbi / Admin)."""
    from app.services.mapping import MappingService
    is_murobbi = await MappingService.get_instance().is_murobbi_async(user_id)
    is_admin = Config.is_admin(user_id)
    return get_main_menu_keyboard(is_murobbi=is_murobbi, is_admin=is_admin)


def get_progress_keyboard(has_missing: bool = False) -> InlineKeyboardMarkup:
    """Keyboard shown below personal monthly progress report."""
    keyboard = []
    if has_missing:
        keyboard.append([
            InlineKeyboardButton("🗓️ Isi Hari yang Kosong / Terlewat", callback_data="btn_edit")
        ])
    keyboard.append([
        InlineKeyboardButton("📝 Isi Mutabaah Hari Ini", callback_data="btn_isi"),
        InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu"),
    ])
    return InlineKeyboardMarkup(keyboard)


def get_date_picker_keyboard(
    tz_name: str = Config.TIMEZONE,
    submitted_dates: Optional[Set[str]] = None,
    missing_dates: Optional[List[str]] = None,
) -> InlineKeyboardMarkup:
    """
    Interactive keyboard to pick today, yesterday, past days, or type custom date.
    Highlights filled (✅) and missing/unfilled (🔴) dates when submitted_dates is provided.
    """
    recent_dates = get_recent_dates_list(num_days=6, tz_name=tz_name)
    keyboard = []

    def get_btn_label(item: dict) -> str:
        base_label = item["label"]
        if submitted_dates is None:
            return base_label
        is_submitted = item["date"] in submitted_dates
        icon = "✅" if is_submitted else "🔴"
        if item["is_today"]:
            clean_part = base_label.split("Hari Ini")[-1].strip()
            return f"{icon} Hari Ini {clean_part}"
        elif item["is_yesterday"]:
            clean_part = base_label.split("Kemarin")[-1].strip()
            return f"{icon} Kemarin {clean_part}"
        else:
            return f"{icon} {base_label}"

    # Row 1: Today & Yesterday
    top_row = []
    for item in recent_dates[:2]:
        top_row.append(InlineKeyboardButton(get_btn_label(item), callback_data=f"pick_date_{item['date']}"))
    if top_row:
        keyboard.append(top_row)

    # Subsequent rows: 2 per row for past days (H-2 to H-6)
    row = []
    for item in recent_dates[2:]:
        row.append(InlineKeyboardButton(get_btn_label(item), callback_data=f"pick_date_{item['date']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Older missing dates (dates not covered in recent_dates)
    recent_date_strs = {item["date"] for item in recent_dates}
    older_missing = [d for d in (missing_dates or []) if d not in recent_date_strs]
    if older_missing:
        missing_row = []
        for d_str in sorted(older_missing)[:6]:
            try:
                dt = datetime.strptime(d_str.strip(), "%Y-%m-%d")
                month_short = INDONESIAN_MONTHS_SHORT.get(dt.month, str(dt.month))
                btn_text = f"🔴 {dt.day} {month_short}"
            except Exception:
                btn_text = f"🔴 {d_str}"
            missing_row.append(InlineKeyboardButton(btn_text, callback_data=f"pick_date_{d_str}"))
            if len(missing_row) == 3:
                keyboard.append(missing_row)
                missing_row = []
        if missing_row:
            keyboard.append(missing_row)

    # Custom date button
    keyboard.append([
        InlineKeyboardButton("🗓️ Ketik Tanggal Lain", callback_data="pick_date_custom")
    ])

    # Navigation
    keyboard.append([
        InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu"),
    ])
    return InlineKeyboardMarkup(keyboard)



def get_today_dashboard_keyboard(active_keys: List[str]) -> InlineKeyboardMarkup:
    """
    Dashboard shown in /isi or /edit allowing user to:
    1. Fill all active amalan sequentially
    2. Tap a single amalan to fill just that one
    """
    keyboard = []

    # Sequential filling option
    keyboard.append([
        InlineKeyboardButton("📝 Isi Semua Berurutan", callback_data="btn_fill_all")
    ])

    # 2 buttons per row for each active amalan
    row = []
    for key in active_keys:
        defn = get_amalan_info(key)
        if not defn:
            continue
        icon = defn.get("icon", "✨")
        short_name = defn.get("short_name", key)
        btn_text = f"{icon} {short_name}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"fill_one_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Change date option
    keyboard.append([
        InlineKeyboardButton("🗓️ Ganti Tanggal", callback_data="btn_change_date"),
    ])

    # Footer navigation
    keyboard.append([
        InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu"),
        InlineKeyboardButton("❌ Selesai", callback_data="cancel"),
    ])
    return InlineKeyboardMarkup(keyboard)


def get_amalan_input_keyboard(
    amalan_key: str,
    user_target: int = 0,
    is_sequential: bool = False,
) -> InlineKeyboardMarkup:
    """
    Dynamic input keyboard for any amalan (both integer and boolean).
    """
    defn = get_amalan_info(amalan_key)
    back_cb = "back" if is_sequential else "back_dashboard"
    keyboard = []

    if not defn:
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)])
        return InlineKeyboardMarkup(keyboard)

    amalan_type = defn.get("type", "int")

    if amalan_type == "bool":
        keyboard.append([
            InlineKeyboardButton("✅ Ya", callback_data="val_yes"),
            InlineKeyboardButton("❌ Tidak", callback_data="val_no"),
        ])
    elif amalan_key == "almatsurat":
        keyboard.append([
            InlineKeyboardButton("0 (Tidak)", callback_data="val_0"),
            InlineKeyboardButton("1 (Pagi/Petang)", callback_data="val_1"),
            InlineKeyboardButton("2 (Pagi & Petang)", callback_data="val_2"),
        ])
    else:
        # Integer buttons with quick options
        options = defn.get("quick_options", [0, 5, 10, 20])
        # Include user's custom target if not present
        if user_target > 0 and user_target not in options and user_target <= defn.get("max_value", 1000):
            options = sorted(list(set(options + [user_target])))

        row = []
        for opt in options:
            label = str(opt)
            if opt == user_target and user_target > 0:
                label = f"{opt} (Target)"
            row.append(InlineKeyboardButton(label, callback_data=f"val_{opt}"))
            # 4 buttons per row for compact numbers, 2-3 for longer text
            max_per_row = 3 if len(label) > 5 else 4
            if len(row) == max_per_row:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        if defn.get("allow_berhalangan"):
            keyboard.append([
                InlineKeyboardButton("🌸 Berhalangan", callback_data="val_berhalangan")
            ])

    # Navigation row
    nav_row = [InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)]
    if is_sequential:
        nav_row.append(InlineKeyboardButton("❌ Batal", callback_data="cancel"))
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)


def get_single_saved_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown immediately after saving a single amalan."""
    keyboard = [
        [InlineKeyboardButton("📝 Lanjut Isi Amalan Lain", callback_data="btn_back_to_dashboard")],
        [InlineKeyboardButton("📊 Lihat Progress Saya", callback_data="btn_progress")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_amalan_selection_keyboard(active_keys: List[str]) -> InlineKeyboardMarkup:
    """Checklist keyboard allowing user to toggle amalan on/off."""
    keyboard = []
    row = []
    for key, defn in AMALAN_DEFINITIONS.items():
        is_active = key in active_keys
        mark = "✅" if is_active else "❌"
        icon = defn.get("icon", "")
        name = defn.get("short_name", key)
        text = f"{mark} {icon} {name}"
        row.append(InlineKeyboardButton(text, callback_data=f"toggle_amalan_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Quick toggle all / reset
    keyboard.append([
        InlineKeyboardButton("✅ Pilih Semua", callback_data="amalan_select_all"),
        InlineKeyboardButton("🔄 Reset Default", callback_data="amalan_reset_default"),
    ])
    # Action buttons
    keyboard.append([
        InlineKeyboardButton("🎯 Atur Target Angka", callback_data="btn_settings_target"),
        InlineKeyboardButton("👤 Ubah Nama", callback_data="btn_edit_name"),
    ])
    keyboard.append([
        InlineKeyboardButton("💾 Selesai", callback_data="btn_settings_save"),
        InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu"),
    ])
    return InlineKeyboardMarkup(keyboard)


def get_amalan_target_list_keyboard(
    user_targets: Dict[str, int], active_keys: List[str]
) -> InlineKeyboardMarkup:
    """Menu showing list of active amalan to adjust their targets."""
    keyboard = []
    for key in active_keys:
        defn = get_amalan_info(key)
        if not defn:
            continue
        icon = defn.get("icon", "")
        name = defn.get("short_name", key)
        target = user_targets.get(key, defn.get("default_target", 0))
        unit = defn.get("unit", "")
        period = "/bln" if defn.get("target_period") == "monthly" else "/hari"

        text = f"{icon} {name}: {target} {unit}{period}"
        keyboard.append([
            InlineKeyboardButton(text, callback_data=f"edit_target_{key}")
        ])

    keyboard.append([
        InlineKeyboardButton("📋 Pilih Amalan (Checklist)", callback_data="btn_settings_amalan"),
        InlineKeyboardButton("👤 Ubah Nama", callback_data="btn_edit_name"),
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu"),
    ])
    return InlineKeyboardMarkup(keyboard)


def get_edit_name_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown when prompting user to input a new full name."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Batal / Kembali", callback_data="cancel_edit_name")]
    ])



def get_target_options_keyboard(amalan_key: str, current_target: int) -> InlineKeyboardMarkup:
    """Quick target selection buttons for editing an amalan's target."""
    defn = get_amalan_info(amalan_key)
    keyboard = []
    if not defn:
        return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="btn_settings_target")]])

    quick_options = defn.get("quick_options", [1, 5, 10, 20])
    # Filter positive non-zero options for targets
    target_options = [opt for opt in quick_options if opt > 0]
    if current_target not in target_options and current_target > 0:
        target_options = sorted(list(set(target_options + [current_target])))

    row = []
    for opt in target_options:
        label = f"{opt} (Saat ini)" if opt == current_target else str(opt)
        row.append(InlineKeyboardButton(label, callback_data=f"set_target_{amalan_key}_{opt}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali ke Target", callback_data="btn_settings_target"),
    ])
    return InlineKeyboardMarkup(keyboard)


# -------------------------------------------------------------
# BACKWARD COMPATIBLE KEYBOARDS (used in existing tests & code)
# -------------------------------------------------------------

def get_tilawah_keyboard() -> InlineKeyboardMarkup:
    return get_amalan_input_keyboard("tilawah", 20, is_sequential=True)


def get_sholat_wajib_keyboard() -> InlineKeyboardMarkup:
    return get_amalan_input_keyboard("sholat_wajib", 5, is_sequential=True)


def get_rawatib_keyboard() -> InlineKeyboardMarkup:
    return get_amalan_input_keyboard("rawatib", 12, is_sequential=True)


def get_almatsurat_keyboard() -> InlineKeyboardMarkup:
    return get_amalan_input_keyboard("almatsurat", 2, is_sequential=True)


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("✅ Ya", callback_data="yes"),
            InlineKeyboardButton("❌ Tidak", callback_data="no"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✅ Simpan", callback_data="save")],
        [
            InlineKeyboardButton("✏️ Edit", callback_data="edit_summary"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_reminder_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📝 Isi Sekarang", callback_data="btn_isi")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard(sheet_id: str) -> InlineKeyboardMarkup:
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    keyboard = [
        [InlineKeyboardButton("📊 Statistik Mutabaah", callback_data="admin_stats")],
        [InlineKeyboardButton("🔗 Buka Google Sheet", url=sheet_url)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_period_keyboard(
    sheet_id: str,
    current_period_key: str = "monthly",
) -> InlineKeyboardMarkup:
    """Admin keyboard with period filters and Google Sheets summary sync."""
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    keyboard = [
        [
            InlineKeyboardButton("📅 Hari Ini", callback_data="admin_period_today"),
            InlineKeyboardButton("📆 7 Hari Terakhir", callback_data="admin_period_weekly"),
        ],
        [
            InlineKeyboardButton("🗓️ Bulan Ini", callback_data="admin_period_monthly"),
            InlineKeyboardButton("⏪ Bulan Lalu", callback_data="admin_period_last_month"),
        ],
        [
            InlineKeyboardButton("🔍 Tanggal Bebas / Custom", callback_data="admin_period_custom"),
        ],
        [
            InlineKeyboardButton("📑 Tulis Rekap ke Google Sheets", callback_data=f"admin_sync_{current_period_key}"),
        ],
        [
            InlineKeyboardButton("🔗 Buka Google Sheet", url=sheet_url),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_binaan_list_keyboard(binaan_list: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Keyboard listing all binaan with quick indicators (✅/🔴)."""
    keyboard = []
    row = []
    for b in binaan_list:
        icon = "✅" if b.get("is_submitted_today") else "🔴"
        name = b.get("name", "Binaan")
        label = f"{icon} {name}"
        row.append(InlineKeyboardButton(label, callback_data=f"binaan_detail_{b['id']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🔄 Refresh Data", callback_data="binaan_refresh"),
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu"),
    ])
    return InlineKeyboardMarkup(keyboard)


def get_binaan_detail_keyboard(mutarabbi_id: str) -> InlineKeyboardMarkup:
    """Keyboard for inspecting single binaan mutabaah."""
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Kembali ke Daftar Binaan", callback_data="binaan_list"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"binaan_detail_{mutarabbi_id}"),
        ],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="btn_main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
