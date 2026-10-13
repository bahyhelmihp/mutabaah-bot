from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard shown after /start or completion."""
    keyboard = [
        [InlineKeyboardButton("📝 Isi Mutabaah Hari Ini", callback_data="btn_isi")],
        [InlineKeyboardButton("📊 Lihat Progress Saya", callback_data="btn_progress")],
        [InlineKeyboardButton("✏️ Edit Hari Ini", callback_data="btn_edit")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_tilawah_keyboard() -> InlineKeyboardMarkup:
    """Quick selection for tilawah pages (0-100 allowed via text or buttons)."""
    keyboard = [
        [
            InlineKeyboardButton("0", callback_data="tilawah_0"),
            InlineKeyboardButton("5", callback_data="tilawah_5"),
            InlineKeyboardButton("10", callback_data="tilawah_10"),
            InlineKeyboardButton("15", callback_data="tilawah_15"),
        ],
        [
            InlineKeyboardButton("20 (Target)", callback_data="tilawah_20"),
            InlineKeyboardButton("25", callback_data="tilawah_25"),
            InlineKeyboardButton("30", callback_data="tilawah_30"),
            InlineKeyboardButton("40", callback_data="tilawah_40"),
        ],
        [
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_sholat_wajib_keyboard() -> InlineKeyboardMarkup:
    """Buttons 0 to 5 for Sholat Wajib."""
    keyboard = [
        [
            InlineKeyboardButton("0", callback_data="wajib_0"),
            InlineKeyboardButton("1", callback_data="wajib_1"),
            InlineKeyboardButton("2", callback_data="wajib_2"),
        ],
        [
            InlineKeyboardButton("3", callback_data="wajib_3"),
            InlineKeyboardButton("4", callback_data="wajib_4"),
            InlineKeyboardButton("5", callback_data="wajib_5"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_rawatib_keyboard() -> InlineKeyboardMarkup:
    """Buttons for Rawatib rakaat (0-12)."""
    keyboard = [
        [
            InlineKeyboardButton("0", callback_data="rawatib_0"),
            InlineKeyboardButton("2", callback_data="rawatib_2"),
            InlineKeyboardButton("4", callback_data="rawatib_4"),
            InlineKeyboardButton("6", callback_data="rawatib_6"),
        ],
        [
            InlineKeyboardButton("8", callback_data="rawatib_8"),
            InlineKeyboardButton("10", callback_data="rawatib_10"),
            InlineKeyboardButton("12 (Target)", callback_data="rawatib_12"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_almatsurat_keyboard() -> InlineKeyboardMarkup:
    """Buttons for Al-Ma'tsurat (0, 1, 2)."""
    keyboard = [
        [
            InlineKeyboardButton("0 (Tidak)", callback_data="almatsurat_0"),
            InlineKeyboardButton("1 (Pagi/Petang)", callback_data="almatsurat_1"),
            InlineKeyboardButton("2 (Pagi & Petang)", callback_data="almatsurat_2"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Generic Yes/No keyboard for Qiyamulail, Dhuha, Olahraga."""
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
    """Summary confirmation buttons."""
    keyboard = [
        [InlineKeyboardButton("✅ Simpan", callback_data="save")],
        [
            InlineKeyboardButton("✏️ Edit", callback_data="edit_summary"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_reminder_keyboard() -> InlineKeyboardMarkup:
    """Keyboard sent in daily reminder message."""
    keyboard = [
        [InlineKeyboardButton("📝 Isi Sekarang", callback_data="btn_isi")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard(sheet_id: str) -> InlineKeyboardMarkup:
    """Admin menu keyboard."""
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    keyboard = [
        [InlineKeyboardButton("📊 Statistik Bulan Ini", callback_data="admin_stats")],
        [InlineKeyboardButton("🔗 Buka Google Sheet", url=sheet_url)],
    ]
    return InlineKeyboardMarkup(keyboard)
