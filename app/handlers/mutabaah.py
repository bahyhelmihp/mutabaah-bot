import logging
from typing import Dict, Any
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
from app.utils.datetime import (
    get_now,
    get_today_str,
    get_timestamp_str,
    format_date_id,
)
from app.config import Config
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_tilawah_keyboard,
    get_sholat_wajib_keyboard,
    get_rawatib_keyboard,
    get_almatsurat_keyboard,
    get_yes_no_keyboard,
    get_confirmation_keyboard,
)

logger = logging.getLogger(__name__)

# Conversation States
(
    STATE_TILAWAH,
    STATE_SHOLAT_WAJIB,
    STATE_RAWATIB,
    STATE_ALMATSURAT,
    STATE_QIYAMULAIL,
    STATE_DHUHA,
    STATE_OLAHRAGA,
    STATE_CONFIRMATION,
) = range(8)


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
            # If editing fails (e.g. content didn't change), send a reply
            pass
    if update.effective_message:
        await update.effective_message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def show_tilawah_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "📖 *1. Tilawah Al-Qur'an*\n"
        "Berapa halaman Tilawah hari ini?\n"
        "_Target: 20 halaman/hari_\n\n"
        "Pilih tombol cepat di bawah atau ketik langsung angka (0 - 100):"
    )
    await send_or_edit(update, text, get_tilawah_keyboard())
    return STATE_TILAWAH


async def show_sholat_wajib_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "🕌 *2. Sholat Wajib*\n"
        "Berapa sholat wajib yang dilakukan berjamaah atau tepat waktu?\n"
        "_Maksimal: 5 waktu_\n\n"
        "Silakan pilih:"
    )
    await send_or_edit(update, text, get_sholat_wajib_keyboard())
    return STATE_SHOLAT_WAJIB


async def show_rawatib_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "🌙 *3. Sholat Sunnah Rawatib*\n"
        "Berapa rakaat sholat sunnah rawatib hari ini?\n"
        "_Maksimal: 12 rakaat_\n\n"
        "Pilih tombol atau ketik angka (0 - 12):"
    )
    await send_or_edit(update, text, get_rawatib_keyboard())
    return STATE_RAWATIB


async def show_almatsurat_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "📿 *4. Al-Ma’tsurat*\n"
        "Berapa kali membaca Al-Ma’tsurat hari ini?\n\n"
        "• *0* = Tidak\n"
        "• *1* = Pagi atau petang\n"
        "• *2* = Pagi dan petang"
    )
    await send_or_edit(update, text, get_almatsurat_keyboard())
    return STATE_ALMATSURAT


async def show_qiyamulail_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "🌃 *5. Qiyamulail*\n"
        "Apakah Anda melaksanakan Qiyamulail hari ini?"
    )
    await send_or_edit(update, text, get_yes_no_keyboard())
    return STATE_QIYAMULAIL


async def show_dhuha_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "☀️ *6. Sholat Dhuha*\n"
        "Apakah Anda melaksanakan Sholat Dhuha hari ini?"
    )
    await send_or_edit(update, text, get_yes_no_keyboard())
    return STATE_DHUHA


async def show_olahraga_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "🏃 *7. Olahraga*\n"
        "Apakah Anda berolahraga minimal 5 menit hari ini?"
    )
    await send_or_edit(update, text, get_yes_no_keyboard())
    return STATE_OLAHRAGA


def build_summary_text(data: Dict[str, Any], date_label: str) -> str:
    tilawah = data.get("tilawah", 0)
    sholat_wajib = data.get("sholat_wajib", 0)
    rawatib = data.get("rawatib", 0)
    almatsurat = data.get("almatsurat", 0)
    qiyam = "✅" if data.get("qiyamulail") else "❌"
    dhuha = "✅" if data.get("dhuha") else "❌"
    olahraga = "✅" if data.get("olahraga") else "❌"

    return (
        f"📋 *Mutabaah Hari Ini*\n"
        f"_{date_label}_\n\n"
        f"📖 Tilawah: *{tilawah} halaman*\n"
        f"🕌 Sholat wajib: *{sholat_wajib}/5*\n"
        f"🌙 Rawatib: *{rawatib}/12 rakaat*\n"
        f"📿 Al-Ma’tsurat: *{almatsurat}/2*\n"
        f"🌃 Qiyamulail: {qiyam}\n"
        f"☀️ Dhuha: {dhuha}\n"
        f"🏃 Olahraga: {olahraga}\n\n"
        "Apakah data di atas sudah benar?"
    )


async def show_confirmation_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("mutabaah", {})
    today_label = format_date_id(date_str=data.get("date"), tz_name=Config.TIMEZONE)
    summary_text = build_summary_text(data, today_label)
    await send_or_edit(update, summary_text, get_confirmation_keyboard())
    return STATE_CONFIRMATION


# --- Entry Points ---

async def start_mutabaah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start filling mutabaah."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    members_service = MembersService()
    is_reg = await members_service.is_registered(user.id)
    if not is_reg:
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        await send_or_edit(update, msg)
        return ConversationHandler.END

    member = await members_service.get_member(user.id)
    full_name = member.get("Full Name", user.first_name) if member else user.first_name

    today_str = get_today_str(Config.TIMEZONE)
    context.user_data["mutabaah"] = {
        "date": today_str,
        "user_id": user.id,
        "username": f"@{user.username.lstrip('@')}" if user.username else "",
        "full_name": full_name,
    }

    return await show_tilawah_prompt(update, context)


async def edit_mutabaah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /edit or [✏️ Edit Hari Ini]."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    members_service = MembersService()
    is_reg = await members_service.is_registered(user.id)
    if not is_reg:
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        await send_or_edit(update, msg)
        return ConversationHandler.END

    # Check if there is an existing submission for today
    today_str = get_today_str(Config.TIMEZONE)
    sheets_service = SheetsService.get_instance()
    try:
        existing = await sheets_service.get_user_mutabaah_record(user.id, today_str)
    except Exception as e:
        logger.error("Error fetching existing mutabaah for %s: %s", user.id, e)
        existing = None

    member = await members_service.get_member(user.id)
    full_name = member.get("Full Name", user.first_name) if member else user.first_name

    context.user_data["mutabaah"] = {
        "date": today_str,
        "user_id": user.id,
        "username": f"@{user.username.lstrip('@')}" if user.username else "",
        "full_name": full_name,
    }

    if existing:
        prefix_msg = "✏️ *Mode Edit Mutabaah*\nMemperbarui data mutabaah Anda hari ini.\n\n"
        # Prepopulate existing values
        try:
            context.user_data["mutabaah"]["tilawah"] = int(existing.get("Tilawah Pages", 0) or 0)
            context.user_data["mutabaah"]["sholat_wajib"] = int(existing.get("Sholat Wajib", 0) or 0)
            context.user_data["mutabaah"]["rawatib"] = int(existing.get("Rawatib Rakaat", 0) or 0)
            context.user_data["mutabaah"]["almatsurat"] = int(existing.get("Almatsurat", 0) or 0)
            context.user_data["mutabaah"]["qiyamulail"] = str(existing.get("Qiyamulail", "")).strip().upper() in ["TRUE", "1", "YES"]
            context.user_data["mutabaah"]["dhuha"] = str(existing.get("Dhuha", "")).strip().upper() in ["TRUE", "1", "YES"]
            context.user_data["mutabaah"]["olahraga"] = str(existing.get("Olahraga", "")).strip().upper() in ["TRUE", "1", "YES"]
        except Exception:
            pass
    else:
        prefix_msg = "ℹ️ Anda belum mengisi mutabaah hari ini. Mari kita mulai:\n\n"

    text = (
        f"{prefix_msg}"
        "📖 *1. Tilawah Al-Qur'an*\n"
        "Berapa halaman Tilawah hari ini?\n"
        "_Target: 20 halaman/hari_\n\n"
        "Pilih tombol cepat di bawah atau ketik langsung angka (0 - 100):"
    )
    await send_or_edit(update, text, get_tilawah_keyboard())
    return STATE_TILAWAH


# --- Step Handlers ---

async def handle_tilawah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle tilawah answer via callback or text."""
    val = None
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb.startswith("tilawah_"):
            val = int(cb.split("_")[1])
    elif update.message and update.message.text:
        text = update.message.text.strip()
        if text.isdigit():
            v = int(text)
            if 0 <= v <= 100:
                val = v

    if val is None:
        await update.effective_message.reply_text(
            "⚠️ Masukkan angka yang valid antara 0 sampai 100, atau gunakan tombol cepat di bawah:",
            reply_markup=get_tilawah_keyboard(),
        )
        return STATE_TILAWAH

    context.user_data["mutabaah"]["tilawah"] = val
    return await show_sholat_wajib_prompt(update, context)


async def handle_sholat_wajib(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle sholat wajib answer."""
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back":
            return await show_tilawah_prompt(update, context)
        if cb.startswith("wajib_"):
            val = int(cb.split("_")[1])
            context.user_data["mutabaah"]["sholat_wajib"] = val
            return await show_rawatib_prompt(update, context)

    if update.message and update.message.text:
        text = update.message.text.strip()
        if text.isdigit() and 0 <= int(text) <= 5:
            context.user_data["mutabaah"]["sholat_wajib"] = int(text)
            return await show_rawatib_prompt(update, context)

    await update.effective_message.reply_text(
        "⚠️ Silakan pilih antara 0 sampai 5:",
        reply_markup=get_sholat_wajib_keyboard(),
    )
    return STATE_SHOLAT_WAJIB


async def handle_rawatib(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle rawatib answer."""
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back":
            return await show_sholat_wajib_prompt(update, context)
        if cb.startswith("rawatib_"):
            val = int(cb.split("_")[1])
            context.user_data["mutabaah"]["rawatib"] = val
            return await show_almatsurat_prompt(update, context)

    if update.message and update.message.text:
        text = update.message.text.strip()
        if text.isdigit() and 0 <= int(text) <= 12:
            context.user_data["mutabaah"]["rawatib"] = int(text)
            return await show_almatsurat_prompt(update, context)

    await update.effective_message.reply_text(
        "⚠️ Masukkan angka 0 sampai 12 rakaat:",
        reply_markup=get_rawatib_keyboard(),
    )
    return STATE_RAWATIB


async def handle_almatsurat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Al-Ma'tsurat answer."""
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back":
            return await show_rawatib_prompt(update, context)
        if cb.startswith("almatsurat_"):
            val = int(cb.split("_")[1])
            context.user_data["mutabaah"]["almatsurat"] = val
            return await show_qiyamulail_prompt(update, context)

    if update.message and update.message.text:
        text = update.message.text.strip()
        if text.isdigit() and int(text) in [0, 1, 2]:
            context.user_data["mutabaah"]["almatsurat"] = int(text)
            return await show_qiyamulail_prompt(update, context)

    await update.effective_message.reply_text(
        "⚠️ Silakan pilih 0, 1, atau 2:",
        reply_markup=get_almatsurat_keyboard(),
    )
    return STATE_ALMATSURAT


async def handle_qiyamulail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Qiyamulail answer."""
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back":
            return await show_almatsurat_prompt(update, context)
        if cb in ["yes", "no"]:
            context.user_data["mutabaah"]["qiyamulail"] = (cb == "yes")
            return await show_dhuha_prompt(update, context)

    await update.effective_message.reply_text(
        "⚠️ Silakan pilih Ya atau Tidak:",
        reply_markup=get_yes_no_keyboard(),
    )
    return STATE_QIYAMULAIL


async def handle_dhuha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Dhuha answer."""
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back":
            return await show_qiyamulail_prompt(update, context)
        if cb in ["yes", "no"]:
            context.user_data["mutabaah"]["dhuha"] = (cb == "yes")
            return await show_olahraga_prompt(update, context)

    await update.effective_message.reply_text(
        "⚠️ Silakan pilih Ya atau Tidak:",
        reply_markup=get_yes_no_keyboard(),
    )
    return STATE_DHUHA


async def handle_olahraga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Olahraga answer."""
    if update.callback_query:
        await update.callback_query.answer()
        cb = update.callback_query.data
        if cb == "back":
            return await show_dhuha_prompt(update, context)
        if cb in ["yes", "no"]:
            context.user_data["mutabaah"]["olahraga"] = (cb == "yes")
            return await show_confirmation_prompt(update, context)

    await update.effective_message.reply_text(
        "⚠️ Silakan pilih Ya atau Tidak:",
        reply_markup=get_yes_no_keyboard(),
    )
    return STATE_OLAHRAGA


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle final Save, Edit, or Cancel."""
    if not update.callback_query:
        return STATE_CONFIRMATION

    await update.callback_query.answer()
    cb = update.callback_query.data

    if cb == "edit_summary":
        # Restart question flow from question 1
        return await show_tilawah_prompt(update, context)

    if cb == "save":
        # Save to Google Sheets
        await update.callback_query.edit_message_text(
            "⏳ *Menyimpan ke Google Sheets...*",
            parse_mode="Markdown",
        )

        mutabaah_data = context.user_data.get("mutabaah", {})
        mutabaah_data["timestamp"] = get_timestamp_str(Config.TIMEZONE)

        sheets_service = SheetsService.get_instance()
        try:
            await sheets_service.upsert_mutabaah(mutabaah_data)
            success_text = (
                "✅ *Alhamdulillah!*\n"
                "Mutabaah amalan yaumiyah hari ini berhasil disimpan ke Google Sheets.\n\n"
                "Semoga Allah memberkahi ikhtiar dan istiqomah kita semua! 🤲"
            )
            await update.callback_query.message.reply_text(
                success_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("Failed to save mutabaah to Google Sheets: %s", e)
            await update.callback_query.message.reply_text(
                "⚠️ Maaf, terjadi kesalahan saat menyimpan ke Google Sheets.\n"
                "Silakan coba sesaat lagi dengan /isi atau hubungi admin.",
                reply_markup=get_main_menu_keyboard(),
            )

        context.user_data.pop("mutabaah", None)
        return ConversationHandler.END

    return STATE_CONFIRMATION


async def cancel_mutabaah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel mutabaah filling."""
    context.user_data.pop("mutabaah", None)
    msg = "❌ Pengisian mutabaah dibatalkan."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            msg, reply_markup=get_main_menu_keyboard()
        )
    elif update.message:
        await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
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
            STATE_TILAWAH: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_tilawah, pattern="^tilawah_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tilawah),
            ],
            STATE_SHOLAT_WAJIB: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_sholat_wajib, pattern="^(wajib_|back)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sholat_wajib),
            ],
            STATE_RAWATIB: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_rawatib, pattern="^(rawatib_|back)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rawatib),
            ],
            STATE_ALMATSURAT: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_almatsurat, pattern="^(almatsurat_|back)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_almatsurat),
            ],
            STATE_QIYAMULAIL: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_qiyamulail, pattern="^(yes|no|back)"),
            ],
            STATE_DHUHA: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_dhuha, pattern="^(yes|no|back)"),
            ],
            STATE_OLAHRAGA: [
                CallbackQueryHandler(cancel_mutabaah, pattern="^cancel$"),
                CallbackQueryHandler(handle_olahraga, pattern="^(yes|no|back)"),
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
