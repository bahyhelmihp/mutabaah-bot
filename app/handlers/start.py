import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from app.services.members import MembersService
from app.keyboards.common import get_main_menu_keyboard

logger = logging.getLogger(__name__)

WAITING_NAME = 1

WELCOME_TEXT = (
    "Assalamu’alaikum 👋\n"
    "Selamat datang di Bot Mutabaah Amalan Harian.\n\n"
    "Silakan isi amalan hari ini. Data akan otomatis direkap."
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command. Check registration, prompt for name if new user."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    members_service = MembersService()
    try:
        is_registered = await members_service.is_registered(user.id)
    except Exception as e:
        logger.error("Error checking registration for user %s: %s", user.id, e)
        is_registered = False

    if not is_registered:
        # Prompt for registration
        await update.message.reply_text(
            "Assalamu’alaikum! Sebelum memulai, mari berkenalan terlebih dahulu.\n\n"
            "Siapa nama Anda?",
        )
        return WAITING_NAME

    # User is registered, greet with full name if available
    member = await members_service.get_member(user.id)
    full_name = member.get("Full Name", user.first_name) if member else user.first_name

    text = (
        f"Assalamu’alaikum *{full_name}* 👋\n"
        "Selamat datang di Bot Mutabaah Amalan Harian.\n\n"
        "Silakan isi amalan hari ini. Data akan otomatis direkap."
    )
    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def handle_registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process user full name input and complete registration."""
    user = update.effective_user
    name_text = update.message.text.strip() if update.message.text else ""

    if not name_text:
        await update.message.reply_text(
            "Mohon masukkan nama lengkap yang valid ya. Siapa nama Anda?"
        )
        return WAITING_NAME

    members_service = MembersService()
    try:
        await members_service.register_member(
            user_id=user.id,
            username=user.username or "",
            full_name=name_text,
        )
    except Exception as e:
        logger.error("Failed to register member %s: %s", user.id, e)
        await update.message.reply_text(
            "⚠️ Maaf, terjadi kendala saat menyimpan pendaftaran ke Google Sheets. "
            "Silakan coba ketik /start kembali sebentar lagi."
        )
        return ConversationHandler.END

    reply = (
        f"Alhamdulillah, salam kenal *{name_text}*! Pendaftaran berhasil. 🎉\n\n"
        f"{WELCOME_TEXT}"
    )
    await update.message.reply_text(
        reply,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel to cancel ongoing conversation."""
    context.user_data.clear()
    msg = "❌ Proses dibatalkan. Anda dapat mengakses menu utama kapan saja dengan /start."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=get_main_menu_keyboard(),
        )
    elif update.message:
        await update.message.reply_text(
            msg,
            reply_markup=get_main_menu_keyboard(),
        )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "📖 *Panduan Penggunaan Bot Mutabaah IMA Korea*\n\n"
        "Bot ini mencatat amalan yaumiyah harian Anda secara otomatis ke Google Sheet terpusat.\n\n"
        "📌 *Perintah Utama:*\n"
        "• /start - Menampilkan menu utama & sapaan\n"
        "• /isi - Mengisi mutabaah hari ini\n"
        "• /edit - Mengubah mutabaah hari ini\n"
        "• /progress - Melihat progres & capaian bulan ini\n"
        "• /help - Menampilkan panduan ini\n"
        "• /cancel - Membatalkan proses pengisian yang sedang aktif\n\n"
        "🎯 *Target Amalan Harian:*\n"
        "1. 📖 *Tilawah*: 20 halaman / hari\n"
        "2. 🕌 *Sholat Wajib*: 5 waktu tepat waktu / berjamaah\n"
        "3. 🌙 *Rawatib*: 12 rakaat / hari\n"
        "4. 📿 *Al-Ma’tsurat*: 2 kali (pagi & petang)\n"
        "5. 🌃 *Qiyamulail*: Minimal 3x / pekan\n"
        "6. ☀️ *Sholat Dhuha*: Minimal 3x / pekan\n"
        "7. 🏃 *Olahraga*: Minimal 5 menit / hari\n\n"
        "Jika ada pertanyaan atau kendala, silakan hubungi pengurus IMA Korea."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            help_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            help_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown"
        )


def get_registration_handler() -> ConversationHandler:
    """ConversationHandler for member registration flow."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        name="registration_conversation",
        persistent=False,
        per_message=False,
        per_chat=True,
        per_user=True,
        allow_reentry=True,
    )
