"""
Handler for /progress command displaying personal monthly achievement based on active amalan.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.services.statistics import StatisticsService
from app.services.members import MembersService
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_user_main_menu_keyboard,
    get_progress_keyboard,
)
from app.utils.datetime import format_missing_dates_id

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
        markup = await get_user_main_menu_keyboard(user.id)
        if update.callback_query:
            await update.callback_query.message.reply_text(
                err_msg, reply_markup=markup
            )
        else:
            await update.message.reply_text(
                err_msg, reply_markup=markup
            )
        return

    lines = [
        f"📊 *Progress Bulan {data['month_label']}*\n",
        f"📅 Hari terisi: *{data['days_submitted']} dari {data['days_passed']} hari*",
    ]

    missing_dates = data.get("missing_dates", [])
    if missing_dates:
        formatted_missing = format_missing_dates_id(missing_dates)
        lines.append(f"🔴 *Tanggal belum diisi ({len(missing_dates)} hari):*")
        lines.append(f"   👉 *{formatted_missing}*\n")
    else:
        lines.append("✅ *Alhamdulillah, semua hari bulan ini telah terisi!*\n")

    items = data.get("items", {})
    for key, item in items.items():
        icon = item.get("icon", "✨")
        name = item.get("name", key)
        actual = item.get("actual", 0)
        target = item.get("target", 0)
        unit = item.get("unit", "")
        pct = round(item.get("ratio", 0.0) * 100)

        lines.append(f"{icon} *{name}:*")
        berhalangan_days = item.get("berhalangan_days", 0)
        if berhalangan_days > 0:
            lines.append(f"   {actual} / {target} {unit} ({pct}%) • _🌸 {berhalangan_days} hari berhalangan_")
        else:
            lines.append(f"   {actual} / {target} {unit} ({pct}%)")

    lines.append(
        f"\n🎯 *Tingkat Ketercapaian Target Keseluruhan:* *{data['completion_percentage']}%*"
    )

    full_text = "\n".join(lines)
    reply_markup = get_progress_keyboard(has_missing=bool(missing_dates))

    if update.callback_query:
        await update.callback_query.message.reply_text(
            full_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            full_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

