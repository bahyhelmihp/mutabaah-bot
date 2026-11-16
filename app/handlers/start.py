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
from app.keyboards.common import get_main_menu_keyboard, get_user_main_menu_keyboard

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
        "Silakan isi amalan hari ini. Data akan otomatis direkap.\n\n"
        "💡 _Salah ketik nama? Ketik /editnama untuk mengubah nama Anda kapan saja._"
    )
    markup = await get_user_main_menu_keyboard(user.id)
    await update.message.reply_text(
        text,
        reply_markup=markup,
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
        "Secara default, semua amalan yaumiyah aktif dengan target standar.\n"
        "Anda dapat langsung mengisi mutabaah, atau menyesuaikan pilihan amalan & target Anda kapan saja melalui tombol *⚙️ Pengaturan* atau perintah /amalan.\n\n"
        f"{WELCOME_TEXT}"
    )
    markup = await get_user_main_menu_keyboard(user.id)
    await update.message.reply_text(
        reply,
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel to cancel ongoing conversation."""
    user = update.effective_user
    context.user_data.clear()
    msg = "❌ Proses dibatalkan. Anda dapat mengakses menu utama kapan saja dengan /start."
    markup = await get_user_main_menu_keyboard(user.id) if user else get_main_menu_keyboard()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=markup,
        )
    elif update.message:
        await update.message.reply_text(
            msg,
            reply_markup=markup,
        )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user = update.effective_user
    help_text = (
        "📖 *Panduan Penggunaan Bot Mutabaah IMA Korea*\n\n"
        "Bot ini mencatat amalan yaumiyah harian Anda secara otomatis ke Google Sheet terpusat.\n\n"
        "📌 *Perintah Utama:*\n"
        "• /start - Menampilkan menu utama & sapaan\n"
        "• /isi - Mengisi mutabaah hari ini (per amalan atau berurutan)\n"
        "• /edit - Mengubah mutabaah hari ini\n"
        "• /progress - Melihat progres & capaian bulan ini\n"
        "• /amalan - Memilih amalan apa saja yang ingin dimutabaah\n"
        "• /target - Mengatur target angka harian & bulanan pribadi\n"
        "• /settings - Menu pengaturan amalan & target\n"
        "• /cekbinaan - _(Khusus Murobbi)_ Memantau mutabaah harian & progres bulanan binaan\n"
        "• /editnama atau /nama - Mengubah nama lengkap terdaftar Anda\n"
        "• /help - Menampilkan panduan ini\n"
        "• /cancel - Membatalkan proses yang sedang aktif\n\n"

        "🎯 *Daftar Amalan Yaumiyah:*\n"
        "1. 📖 *Tilawah Al-Qur'an*: Target default 20 halaman / hari\n"
        "2. 🕌 *Sholat Wajib*: Target default 5 waktu tepat waktu / berjamaah\n"
        "3. 🌙 *Rawatib*: Target default 12 rakaat / hari\n"
        "4. 📿 *Al-Ma’tsurat*: Target default 2 kali (pagi & petang)\n"
        "5. 🌸 *Shalawat*: Target default 100 kali / hari\n"
        "6. 🤲 *Istighfar*: Target default 100 kali / hari\n"
        "7. 📜 *Tadabbur*: Target default 1 ayat / hari\n"
        "8. 🍽️ *Shaum Sunnah*: Target default min. 4 kali / bulan\n"
        "9. 🌃 *Qiyamulail*: Min. 3x / pekan (12x / bulan)\n"
        "10. ☀️ *Sholat Dhuha*: Min. 3x / pekan (12x / bulan)\n"
        "11. 🏃 *Olahraga*: Min. 5 menit / hari\n\n"
        "💡 *Tips:* Anda bebas memilih amalan apa saja yang ingin dimutabaah serta mengubah angka targetnya lewat perintah /amalan atau /target!"
    )
    markup = await get_user_main_menu_keyboard(user.id) if user else get_main_menu_keyboard()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            help_text, reply_markup=markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            help_text, reply_markup=markup, parse_mode="Markdown"
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
