import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.services.statistics import StatisticsService
from app.services.members import MembersService
from app.keyboards.common import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display user's personal progress for the current month."""
    user = update.effective_user
    if not user:
        return

    if update.callback_query:
        await update.callback_query.answer()

    members_service = MembersService()
    try:
        is_reg = await members_service.is_registered(user.id)
    except Exception as e:
        logger.error("Error checking registration for %s: %s", user.id, e)
        is_reg = False

    if not is_reg:
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        if update.callback_query:
            await update.callback_query.message.reply_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    stats_service = StatisticsService()
    try:
        data = await stats_service.calculate_user_month_progress(user.id)
    except Exception as e:
        logger.error("Error calculating progress for %s: %s", user.id, e)
        err_msg = "⚠️ Maaf, terjadi kendala saat mengambil data progress dari Google Sheets."
        if update.callback_query:
            await update.callback_query.message.reply_text(err_msg, reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text(err_msg, reply_markup=get_main_menu_keyboard())
        return

    text = (
        f"📊 *Progress {data['month_label']}*\n\n"
        f"Hari terisi: *{data['days_submitted']}/{data['days_passed']}*\n\n"
        f"📖 *Tilawah:*\n"
        f"{data['total_tilawah']} / {data['target_tilawah']} halaman\n\n"
        f"🕌 *Sholat wajib:*\n"
        f"{data['total_wajib']} / {data['target_wajib']}\n\n"
        f"🌙 *Rawatib:*\n"
        f"{data['total_rawatib']} rakaat\n\n"
        f"📿 *Al-Ma’tsurat:*\n"
        f"{data['total_almatsurat']}x\n\n"
        f"🌃 *Qiyamulail:*\n"
        f"{data['count_qiyamulail']} hari\n\n"
        f"☀️ *Dhuha:*\n"
        f"{data['count_dhuha']} hari\n\n"
        f"🏃 *Olahraga:*\n"
        f"{data['count_olahraga']} hari\n\n"
        f"🎯 *Tingkat Ketercapaian Target:* *{data['completion_percentage']}%*"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
