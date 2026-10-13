import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.config import Config
from app.services.statistics import StatisticsService
from app.keyboards.common import get_admin_keyboard

logger = logging.getLogger(__name__)


def is_admin_user(user_id: int) -> bool:
    return Config.is_admin(user_id)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command."""
    user = update.effective_user
    if not user or not is_admin_user(user.id):
        await update.effective_message.reply_text(
            "⛔ Maaf, Anda tidak memiliki akses ke fitur admin."
        )
        return

    text = (
        "👑 *Panel Admin Mutabaah IMA Korea*\n\n"
        "Menu khusus pengurus untuk memantau rekap mutabaah anggota IMA Korea:\n\n"
        "• /stats - Ringkasan statistik bulanan\n"
        "• /export - Tautan spreadsheet Google Sheets"
    )
    await update.effective_message.reply_text(
        text,
        reply_markup=get_admin_keyboard(Config.GOOGLE_SHEET_ID),
        parse_mode="Markdown",
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command or admin_stats callback."""
    user = update.effective_user
    if not user or not is_admin_user(user.id):
        if update.callback_query:
            await update.callback_query.answer("⛔ Akses ditolak", show_alert=True)
        else:
            await update.effective_message.reply_text(
                "⛔ Maaf, Anda tidak memiliki akses ke fitur admin."
            )
        return

    if update.callback_query:
        await update.callback_query.answer()

    stats_service = StatisticsService()
    try:
        stats = await stats_service.calculate_monthly_admin_stats()
    except Exception as e:
        logger.error("Error fetching admin stats: %s", e)
        await update.effective_message.reply_text(
            "⚠️ Terjadi kesalahan saat menghitung statistik dari Google Sheets."
        )
        return

    text = (
        f"📊 *Statistik Agregat Mutabaah ({stats['month_label']})*\n\n"
        f"👥 *Total Anggota Terdaftar:* {stats['registered_members']} orang\n"
        f"📝 *Pengisian Hari Ini:* {stats['submissions_today']} anggota\n"
        f"📈 *Persentase Pengisian Hari Ini:* {stats['submission_rate_today']}%\n"
        f"🔥 *Anggota Aktif Mengisi Bulan Ini:* {stats['active_submitters_month']} orang\n"
        f"📋 *Total Data Bulan Ini:* {stats['total_monthly_records']} entri\n"
        f"⭐ *Rata-rata Tingkat Ketercapaian:* {stats['average_completion_rate']}%\n\n"
        "_Catatan: Data diperbarui secara realtime sesuai isian Google Sheets._"
    )
    await update.effective_message.reply_text(
        text,
        reply_markup=get_admin_keyboard(Config.GOOGLE_SHEET_ID),
        parse_mode="Markdown",
    )


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command."""
    user = update.effective_user
    if not user or not is_admin_user(user.id):
        await update.effective_message.reply_text(
            "⛔ Maaf, Anda tidak memiliki akses ke fitur admin."
        )
        return

    sheet_url = f"https://docs.google.com/spreadsheets/d/{Config.GOOGLE_SHEET_ID}"
    text = (
        "📊 *Sinkronisasi Data Google Sheets*\n\n"
        "Semua entri mutabaah tersinkronisasi langsung secara realtime ke spreadsheet utama:\n\n"
        f"🔗 [Buka Google Sheets Mutabaah]({sheet_url})\n\n"
        f"• *ID Spreadsheet:* `{Config.GOOGLE_SHEET_ID}`\n"
        "• *Lembar Kerja:* `Daily Mutabaah` & `Members`"
    )
    await update.effective_message.reply_text(
        text,
        disable_web_page_preview=False,
        parse_mode="Markdown",
    )
