"""
ConversationHandler for Mutabaah workflow supporting:
1. Interactive Today Dashboard
2. Sequential Guided Flow (only through active amalan)
3. Single Amalan Entry (fill or edit one habit at a time)
"""
import logging
from typing import Dict, Any, List, Optional
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from app.services.sheets import SheetsService
from app.services.members import MembersService
from app.services.settings import UserSettingsService
from app.services.statistics import StatisticsService
from app.services.amalan import (
    AMALAN_DEFINITIONS,
    ALL_AMALAN_KEYS,
    get_amalan_info,
    format_amalan_value,
)
from app.utils.datetime import (
    get_now,
    get_today_str,
    get_timestamp_str,
    format_date_id,
    parse_date_input,
    format_missing_dates_id,
)

from app.config import Config
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_user_main_menu_keyboard,
    get_today_dashboard_keyboard,
    get_amalan_input_keyboard,
    get_single_saved_keyboard,
    get_confirmation_keyboard,
    get_date_picker_keyboard,
)

logger = logging.getLogger(__name__)

# Conversation States
(
    STATE_DASHBOARD,
    STATE_SINGLE_INPUT,
    STATE_SEQUENTIAL_STEP,
    STATE_CONFIRMATION,
    STATE_DATE_SELECTION,
) = range(5)


async def send_or_edit(update: Update, text: str, reply_markup=None):
    """Utility to edit message if callback_query, or send new message if text."""
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
            return
        except Exception:
            pass
    if update.effective_message:
        await update.effective_message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def init_user_mutabaah_data(
    user_id: int, user, context: ContextTypes.DEFAULT_TYPE, target_date: Optional[str] = None
) -> Dict[str, Any]:
    """Initialize or load user mutabaah session data for a specific date (defaults to today)."""
    date_str = target_date or get_today_str(Config.TIMEZONE)
    settings_service = UserSettingsService.get_instance()
    active_keys = await settings_service.get_active_amalan(user_id)
    targets = await settings_service.get_user_targets(user_id)

    members_service = MembersService()
    member = await members_service.get_member(user_id)
    full_name = member.get("Full Name", user.first_name) if member else user.first_name
    username = f"@{user.username.lstrip('@')}" if user.username else ""

    # Check for existing submission for this date in Google Sheets
    sheets_service = SheetsService.get_instance()
    existing = None
    try:
        existing = await sheets_service.get_user_mutabaah_record(user_id, date_str)
    except Exception as e:
        logger.error("Error fetching mutabaah for %s on %s: %s", user_id, date_str, e)

    data: Dict[str, Any] = {
        "date": date_str,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "active_keys": active_keys,
        "targets": targets,
        "seq_index": 0,
        "single_key": None,
    }

    if existing:
        for key, defn in AMALAN_DEFINITIONS.items():
            col = defn["column"]
            if col in existing and existing[col] != "":
                raw_val = existing[col]
                if str(raw_val).strip().lower() in ["berhalangan", "haid", "halangan"]:
                    data[key] = "Berhalangan"
                elif defn["type"] == "bool":
                    data[key] = str(raw_val).strip().upper() in ["TRUE", "1", "YES", "YA"]
                else:
                    try:
                        data[key] = int(float(str(raw_val).strip()))
                    except (ValueError, TypeError):
                        pass

    context.user_data["mutabaah"] = data
    return data


def build_dashboard_text(data: Dict[str, Any], date_label: str) -> str:
    """Render the Mutabaah summary dashboard for the selected date."""
    active_keys = data.get("active_keys", ALL_AMALAN_KEYS)
    targets = data.get("targets", {})

    target_date = data.get("date", get_today_str(Config.TIMEZONE))
    today_str = get_today_str(Config.TIMEZONE)
    title_context = "Hari Ini" if target_date == today_str else "Hari Terlewat / Lain"

    lines = [
        f"📋 *Mutabaah Yaumiyah ({title_context})*",
        f"_{date_label}_\n",
    ]

    for key in active_keys:
        defn = get_amalan_info(key)
        if not defn:
            continue
        icon = defn.get("icon", "✨")
        name = defn.get("short_name", key)
        val = data.get(key)
        target = targets.get(key, defn.get("default_target", 0))
        unit = defn.get("unit", "")

        if val is None:
            status_str = "_Belum diisi_"
        else:
            if str(val).strip().lower() in ["berhalangan", "haid", "halangan"]:
                status_str = "🌸 Berhalangan"
            elif defn["type"] == "bool":
                status_str = "✅ Ya" if val else "❌ Tidak"
            else:
                status_str = f"*{val} {unit}* (Target: {target})"

        lines.append(f"{icon} {name}: {status_str}")

    lines.append("\n_Pilih amalan untuk diisi/diubah, atau pilih Isi Semua Berurutan:_")
    return "\n".join(lines)


async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the main mutabaah dashboard."""
    data = context.user_data.get("mutabaah", {})
    date_label = format_date_id(date_str=data.get("date"), tz_name=Config.TIMEZONE)
    text = build_dashboard_text(data, date_label)
    markup = get_today_dashboard_keyboard(data.get("active_keys", ALL_AMALAN_KEYS))
    await send_or_edit(update, text, markup)
    return STATE_DASHBOARD


# -------------------------------------------------------------
# ENTRY POINTS
# -------------------------------------------------------------

async def start_mutabaah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /isi or [📝 Isi Mutabaah Hari Ini]."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    members_service = MembersService()
    if not await members_service.is_registered(user.id):
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        await send_or_edit(update, msg)
        return ConversationHandler.END

    target_date = None
    if context.args:
        arg_text = " ".join(context.args).strip()
        parsed = parse_date_input(arg_text, tz_name=Config.TIMEZONE)
        if parsed:
            target_date = parsed

    await init_user_mutabaah_data(user.id, user, context, target_date=target_date)
    return await show_dashboard(update, context)


async def show_date_picker(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int
) -> int:
    """Show interactive date selection with missing dates list and filled indicators."""
    stats_service = StatisticsService()
    try:
        user_month_data = await stats_service.calculate_user_month_progress(user_id)
        submitted_dates = set(user_month_data.get("all_submitted_dates", user_month_data.get("submitted_dates", [])))
        missing_dates = user_month_data.get("missing_dates", [])
    except Exception as e:
        logger.error("Error fetching user month data for date picker: %s", e)
        user_month_data = {}
        submitted_dates = set()
        missing_dates = []

    if missing_dates:
        formatted_missing = format_missing_dates_id(missing_dates)
        text = (
            "🗓️ *Pilih Tanggal Mutabaah*\n\n"
            f"📅 *Status Bulan {user_month_data.get('month_label', '')}:*\n"
            f"Terisi: *{user_month_data.get('days_submitted', 0)} dari {user_month_data.get('days_passed', 0)} hari*\n\n"
            f"🔴 *Tanggal belum diisi ({len(missing_dates)} hari):*\n"
            f"👉 *{formatted_missing}*\n\n"
            "Pilih tombol tanggal di bawah (🔴 = belum diisi, ✅ = sudah diisi), atau ketik tanggal lain:"
        )
    elif user_month_data:
        text = (
            "🗓️ *Pilih Tanggal Mutabaah*\n\n"
            f"📅 *Status Bulan {user_month_data.get('month_label', '')}:*\n"
            f"✅ *Alhamdulillah, semua hari ({user_month_data.get('days_passed', 0)} hari) telah terisi!*\n\n"
            "Pilih tombol tanggal di bawah jika ingin mengedit atau memeriksa isian amalan:"
        )
    else:
        text = (
            "🗓️ *Pilih Tanggal Mutabaah*\n\n"
            "Silakan pilih hari yang ingin Anda isi atau perbaiki datanya, "
            "atau ketik tanggal lainnya:"
        )

    markup = get_date_picker_keyboard(
        Config.TIMEZONE,
        submitted_dates=submitted_dates if submitted_dates else None,
        missing_dates=missing_dates,
    )
    await send_or_edit(update, text, markup)
    return STATE_DATE_SELECTION


async def edit_mutabaah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /edit or [✏️ Edit / Isi Hari Lain]."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    members_service = MembersService()
    if not await members_service.is_registered(user.id):
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        await send_or_edit(update, msg)
        return ConversationHandler.END

    # If user provided a date argument: /edit 2026-10-14 or /edit kemarin
    if context.args:
        arg_text = " ".join(context.args).strip()
        parsed = parse_date_input(arg_text, tz_name=Config.TIMEZONE)
        if parsed:
            await init_user_mutabaah_data(user.id, user, context, target_date=parsed)
            return await show_dashboard(update, context)

    # Show date picker keyboard with missing dates info
    return await show_date_picker(update, context, user.id)



async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle date chosen via button or typed by user."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data

        if cb in ["btn_main_menu", "cancel"]:
            context.user_data.pop("mutabaah", None)
            markup = await get_user_main_menu_keyboard(update.effective_user.id) if update.effective_user else get_main_menu_keyboard()
            await update.callback_query.edit_message_text(
                "Alhamdulillah. Anda dapat kembali mengisi atau melihat progres kapan saja melalui menu utama:",
                reply_markup=markup,
            )
            return ConversationHandler.END

        if cb == "pick_date_custom":
            await update.callback_query.edit_message_text(
                "🗓️ *Ketik Tanggal Mutabaah*\n\n"
                "Silakan ketik tanggal yang ingin diisi/diperbaiki.\n\n"
                "Contoh format yang didukung:\n"
                "• `2026-10-14` atau `14-10-2026`\n"
                "• `kemarin` atau `kemarin lusa`\n"
                "• `14/10`\n\n"
                "Ketik tanggal Anda:",
                parse_mode="Markdown",
            )
            return STATE_DATE_SELECTION

        if cb.startswith("pick_date_"):
            date_str = cb.replace("pick_date_", "")
            await init_user_mutabaah_data(user.id, user, context, target_date=date_str)
            return await show_dashboard(update, context)

    if update.message and update.message.text:
        text = update.message.text.strip()
        parsed_date = parse_date_input(text, tz_name=Config.TIMEZONE)
        if parsed_date:
            await init_user_mutabaah_data(user.id, user, context, target_date=parsed_date)
            return await show_dashboard(update, context)
        else:
            await update.message.reply_text(
                "⚠️ Format tanggal tidak dikenali.\n"
                "Silakan pilih tanggal di bawah atau ketik format `YYYY-MM-DD` (contoh: `2026-10-14`) atau `kemarin`:",
            )
            return await show_date_picker(update, context, user.id)

    return STATE_DATE_SELECTION


# -------------------------------------------------------------
# DASHBOARD INTERACTIONS
# -------------------------------------------------------------

async def handle_dashboard_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return STATE_DASHBOARD

    await query.answer()
    cb = query.data
    data = context.user_data.get("mutabaah", {})
    user = update.effective_user

    if cb == "btn_fill_all":
        # Start sequential flow through active amalan
        data["seq_index"] = 0
        return await show_sequential_prompt(update, context)

    if cb.startswith("fill_one_"):
        key = cb.replace("fill_one_", "")
        data["single_key"] = key
        return await show_single_prompt(update, context, key)

    if cb == "btn_change_date":
        return await show_date_picker(update, context, user.id if user else 0)


    if cb == "btn_back_to_dashboard":
        return await show_dashboard(update, context)

    if cb == "btn_main_menu" or cb == "cancel":
        context.user_data.pop("mutabaah", None)
        markup = await get_user_main_menu_keyboard(update.effective_user.id) if update.effective_user else get_main_menu_keyboard()
        await query.edit_message_text(
            "Alhamdulillah. Anda dapat kembali mengisi atau melihat progres kapan saja melalui menu utama:",
            reply_markup=markup,
        )
        return ConversationHandler.END

    return STATE_DASHBOARD


# -------------------------------------------------------------
# SINGLE AMALAN ENTRY FLOW
# -------------------------------------------------------------

async def show_single_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str) -> int:
    """Show prompt for filling a single selected amalan."""
    data = context.user_data.get("mutabaah", {})
    defn = get_amalan_info(key)
    if not defn:
        return await show_dashboard(update, context)

    targets = data.get("targets", {})
    target = targets.get(key, defn.get("default_target", 0))
    unit = defn.get("unit", "")
    current_val = data.get(key)
    current_str = format_amalan_value(key, current_val)

    prompt = defn.get("prompt", "")
    icon = defn.get("icon", "")
    name = defn.get("name", key)

    text = (
        f"{icon} *{name}*\n"
        f"{prompt}\n\n"
        f"🎯 *Target Anda:* {target} {unit}\n"
        f"📌 *Saat ini:* {current_str}\n\n"
        "Pilih tombol cepat di bawah atau ketik angka secara manual:"
    )
    markup = get_amalan_input_keyboard(key, user_target=target, is_sequential=False)
    await send_or_edit(update, text, markup)
    return STATE_SINGLE_INPUT


async def handle_single_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle answer for single amalan mode (via callback or text)."""
    data = context.user_data.get("mutabaah", {})
    key = data.get("single_key")
    if not key:
        return await show_dashboard(update, context)

    defn = get_amalan_info(key)
    if not defn:
        return await show_dashboard(update, context)

    # Check back button
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back_dashboard":
            return await show_dashboard(update, context)

    val = parse_input_value(update, defn)
    if val is None:
        targets = data.get("targets", {})
        target = targets.get(key, defn.get("default_target", 0))
        await update.effective_message.reply_text(
            f"⚠️ Input tidak valid. Silakan gunakan tombol di bawah atau ketik angka:",
            reply_markup=get_amalan_input_keyboard(key, user_target=target, is_sequential=False),
        )
        return STATE_SINGLE_INPUT

    # Update in data
    data[key] = val
    data["timestamp"] = get_timestamp_str(Config.TIMEZONE)

    # Immediately save to Google Sheets!
    sheets_service = SheetsService.get_instance()
    try:
        await sheets_service.upsert_mutabaah(data)
    except Exception as e:
        logger.error("Failed to save single amalan %s to sheets: %s", key, e)

    formatted_val = format_amalan_value(key, val)
    icon = defn.get("icon", "")
    name = defn.get("name", key)
    date_label = format_date_id(date_str=data.get("date"), tz_name=Config.TIMEZONE)

    success_text = (
        f"✅ *{icon} {name}* berhasil dicatat: *{formatted_val}*! 🎉\n"
        f"📅 *Tanggal:* {date_label}\n\n"
        "Data sudah otomatis tersimpan ke Google Sheets."
    )
    await send_or_edit(update, success_text, get_single_saved_keyboard())
    return STATE_DASHBOARD


# -------------------------------------------------------------
# SEQUENTIAL FILLING FLOW ("Isi Semua Berurutan")
# -------------------------------------------------------------

async def show_sequential_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("mutabaah", {})
    active_keys = data.get("active_keys", ALL_AMALAN_KEYS)
    idx = data.get("seq_index", 0)

    if idx >= len(active_keys):
        # All active amalan filled, show confirmation
        return await show_confirmation_prompt(update, context)

    key = active_keys[idx]
    defn = get_amalan_info(key)
    targets = data.get("targets", {})
    target = targets.get(key, defn.get("default_target", 0))
    unit = defn.get("unit", "")

    step_num = idx + 1
    total_steps = len(active_keys)

    text = (
        f"*{step_num}/{total_steps}. {defn.get('icon', '')} {defn.get('name', key)}*\n"
        f"{defn.get('prompt', '')}\n"
        f"_Target Anda: {target} {unit}_\n\n"
        "Pilih tombol cepat di bawah atau ketik angka secara manual:"
    )
    markup = get_amalan_input_keyboard(key, user_target=target, is_sequential=True)
    await send_or_edit(update, text, markup)
    return STATE_SEQUENTIAL_STEP


async def handle_sequential_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("mutabaah", {})
    active_keys = data.get("active_keys", ALL_AMALAN_KEYS)
    idx = data.get("seq_index", 0)

    if idx >= len(active_keys):
        return await show_confirmation_prompt(update, context)

    key = active_keys[idx]
    defn = get_amalan_info(key)

    # Handle navigation callbacks
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back":
            if idx > 0:
                data["seq_index"] = idx - 1
                return await show_sequential_prompt(update, context)
            else:
                return await show_dashboard(update, context)

    val = parse_input_value(update, defn)
    if val is None:
        targets = data.get("targets", {})
        target = targets.get(key, defn.get("default_target", 0))
        await update.effective_message.reply_text(
            "⚠️ Masukkan nilai yang valid atau gunakan tombol di bawah:",
            reply_markup=get_amalan_input_keyboard(key, user_target=target, is_sequential=True),
        )
        return STATE_SEQUENTIAL_STEP

    data[key] = val
    data["seq_index"] = idx + 1
    return await show_sequential_prompt(update, context)


def parse_input_value(update: Update, defn: Dict[str, Any]) -> Optional[Any]:
    """Helper to parse input from callback or text message."""
    amalan_type = defn.get("type", "int")
    max_val = defn.get("max_value", 10000)

    if update.callback_query:
        cb = update.callback_query.data
        if cb == "val_berhalangan":
            return "Berhalangan"
        if amalan_type == "bool":
            if cb in ["val_yes", "yes"]:
                return True
            if cb in ["val_no", "no"]:
                return False
        elif cb.startswith("val_"):
            num_str = cb.replace("val_", "")
            if num_str.isdigit():
                return int(num_str)
        # Backward-compatibility callback prefixes
        for prefix in ["tilawah_", "wajib_", "rawatib_", "almatsurat_"]:
            if cb.startswith(prefix):
                n_str = cb.replace(prefix, "")
                if n_str.isdigit():
                    return int(n_str)
        if cb in ["yes", "no"]:
            return (cb == "yes")

    if update.message and update.message.text:
        text = update.message.text.strip()
        if defn.get("allow_berhalangan") and text.lower() in ["berhalangan", "haid", "halangan"]:
            return "Berhalangan"
        if amalan_type == "bool":
            lower = text.lower()
            if lower in ["ya", "y", "yes", "true", "1", "sudah", "ada"]:
                return True
            if lower in ["tidak", "t", "no", "false", "0", "belum"]:
                return False
        else:
            if text.isdigit():
                val = int(text)
                if 0 <= val <= max_val:
                    return val

    return None


# -------------------------------------------------------------
# CONFIRMATION & SAVE
# -------------------------------------------------------------

def build_summary_text(data: Dict[str, Any], date_label: str) -> str:
    active_keys = data.get("active_keys", ALL_AMALAN_KEYS)
    targets = data.get("targets", {})

    target_date = data.get("date", get_today_str(Config.TIMEZONE))
    today_str = get_today_str(Config.TIMEZONE)
    date_title = "Hari Ini" if target_date == today_str else "Hari Terlewat / Lain"

    lines = [
        f"📋 *Ringkasan Mutabaah ({date_title})*",
        f"_{date_label}_\n",
    ]
    for key in active_keys:
        defn = get_amalan_info(key)
        if not defn:
            continue
        icon = defn.get("icon", "")
        name = defn.get("short_name", key)
        val = data.get(key)
        val_str = format_amalan_value(key, val)
        lines.append(f"{icon} {name}: *{val_str}*")

    lines.append("\nApakah data di atas sudah benar dan siap disimpan?")
    return "\n".join(lines)


async def show_confirmation_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("mutabaah", {})
    today_label = format_date_id(date_str=data.get("date"), tz_name=Config.TIMEZONE)
    summary_text = build_summary_text(data, today_label)
    await send_or_edit(update, summary_text, get_confirmation_keyboard())
    return STATE_CONFIRMATION


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.callback_query:
        return STATE_CONFIRMATION

    await update.callback_query.answer()
    cb = update.callback_query.data

    if cb == "edit_summary":
        # Return to dashboard to adjust any amalan
        return await show_dashboard(update, context)

    if cb == "save":
        await update.callback_query.edit_message_text(
            "⏳ *Menyimpan ke Google Sheets...*",
            parse_mode="Markdown",
        )

        data = context.user_data.get("mutabaah", {})
        data["timestamp"] = get_timestamp_str(Config.TIMEZONE)
        date_label = format_date_id(date_str=data.get("date"), tz_name=Config.TIMEZONE)

        sheets_service = SheetsService.get_instance()
        try:
            await sheets_service.upsert_mutabaah(data)
            success_text = (
                "✅ *Alhamdulillah!*\n"
                f"Mutabaah amalan yaumiyah tanggal *{date_label}* berhasil disimpan ke Google Sheets.\n\n"
                "Semoga Allah memberkahi ikhtiar dan istiqomah kita semua! 🤲"
            )
            markup = await get_user_main_menu_keyboard(update.effective_user.id) if update.effective_user else get_main_menu_keyboard()
            await update.callback_query.message.reply_text(
                success_text,
                reply_markup=markup,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("Failed to save mutabaah to Google Sheets: %s", e)
            markup = await get_user_main_menu_keyboard(update.effective_user.id) if update.effective_user else get_main_menu_keyboard()
            await update.callback_query.message.reply_text(
                "⚠️ Maaf, terjadi kesalahan saat menyimpan ke Google Sheets.\n"
                "Silakan coba sesaat lagi dengan /isi atau hubungi admin.",
                reply_markup=markup,
            )

        context.user_data.pop("mutabaah", None)
        return ConversationHandler.END

    return STATE_CONFIRMATION


async def cancel_mutabaah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("mutabaah", None)
    msg = "❌ Pengisian mutabaah ditutup."
    markup = await get_user_main_menu_keyboard(update.effective_user.id) if update.effective_user else get_main_menu_keyboard()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            msg, reply_markup=markup
        )
    elif update.message:
        await update.message.reply_text(msg, reply_markup=markup)
    return ConversationHandler.END


def get_mutabaah_conversation_handler() -> ConversationHandler:
    """Build ConversationHandler for Mutabaah workflow."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("isi", start_mutabaah),
            CommandHandler("edit", edit_mutabaah),
            CallbackQueryHandler(start_mutabaah, pattern="^btn_isi$"),
            CallbackQueryHandler(edit_mutabaah, pattern="^btn_edit$"),
        ],
        states={
            STATE_DASHBOARD: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_dashboard_actions),
            ],
            STATE_DATE_SELECTION: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_date_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_selection),
            ],
            STATE_SINGLE_INPUT: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_single_input),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_single_input),
            ],
            STATE_SEQUENTIAL_STEP: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_sequential_input),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sequential_input),
            ],
            STATE_CONFIRMATION: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_confirmation, pattern="^(save|edit_summary)$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_mutabaah),
            CommandHandler("start", cancel_mutabaah),
            CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
        ],
        name="mutabaah_conversation",
        persistent=False,
        per_message=False,
        per_chat=True,
        per_user=True,
        allow_reentry=True,
    )
