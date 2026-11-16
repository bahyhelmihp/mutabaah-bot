"""
Handler for Murobbi features:
- /cekbinaan command
- Inline buttons: btn_cek_binaan, binaan_list, binaan_refresh, binaan_detail_<id>
Allows registered Murobbis to inspect today's mutabaah submissions and monthly achievements of their binaan.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.services.mapping import MappingService
from app.services.amalan import AMALAN_DEFINITIONS, format_amalan_value
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_binaan_list_keyboard,
    get_binaan_detail_keyboard,
)
from app.utils.datetime import format_missing_dates_id
from app.config import Config

logger = logging.getLogger(__name__)


async def cekbinaan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /cekbinaan command."""
    user = update.effective_user
    if not user:
        return

    mapping_service = MappingService.get_instance()
    is_murobbi = await mapping_service.is_murobbi_async(user.id)

    if not is_murobbi:
        is_admin = Config.is_admin(user.id)
        msg = (
            "⚠️ *Akses Ditolak*\n\n"
            "Fitur ini khusus untuk *Murobbi* yang terdaftar pada lembar *Mapping* di Google Sheets.\n"
            f"ID Telegram Anda (`{user.id}`) tidak terdaftar sebagai Murobbi ID."
        )
        if update.callback_query:
            await update.callback_query.answer("Akses ditolak: Anda bukan Murobbi.", show_alert=True)
            await update.callback_query.edit_message_text(
                msg,
                reply_markup=get_main_menu_keyboard(is_murobbi=False, is_admin=is_admin),
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                msg,
                reply_markup=get_main_menu_keyboard(is_murobbi=False, is_admin=is_admin),
                parse_mode="Markdown",
            )
        return

    await show_binaan_list(update, context, user.id, is_refresh=False)


async def show_binaan_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    murobbi_id: int,
    is_refresh: bool = False,
):
    """Show list of all binaan for the Murobbi."""
    mapping_service = MappingService.get_instance()
    if is_refresh:
        from app.services.sheets import SheetsService
        SheetsService.get_instance().invalidate_mutabaah_cache()
        await mapping_service.reload_cache(force=True)

    try:
        overview = await mapping_service.get_binaan_overview(murobbi_id)
    except Exception as e:
        logger.error("Error generating binaan overview for murobbi %s: %s", murobbi_id, e)
        err_msg = "⚠️ Maaf, terjadi kendala saat mengambil data binaan dari Google Sheets. Silakan coba kembali."
        is_admin = Config.is_admin(murobbi_id)
        if update.callback_query:
            await update.callback_query.answer("Gagal memuat data binaan.")
            await update.callback_query.edit_message_text(
                err_msg,
                reply_markup=get_main_menu_keyboard(is_murobbi=True, is_admin=is_admin),
            )
        else:
            await update.message.reply_text(
                err_msg,
                reply_markup=get_main_menu_keyboard(is_murobbi=True, is_admin=is_admin),
            )
        return

    murobbi_name = overview.get("murobbi_name") or "Murobbi"
    today_formatted = overview.get("today_formatted", "")
    total_binaan = overview.get("total_binaan", 0)
    submitted_count = overview.get("submitted_today_count", 0)
    unsubmitted_count = overview.get("unsubmitted_today_count", 0)
    binaan_list = overview.get("binaan_list", [])

    lines = [
        "👥 *Monitoring Mutabaah Binaan*",
        f"👤 Murobbi: *{murobbi_name}*",
        f"📅 Tanggal: *{today_formatted}*\n",
        "📊 *Ringkasan Hari Ini:*",
        f"• Total Binaan: *{total_binaan} orang*",
        f"• Sudah Mengisi: *{submitted_count} orang*",
        f"• Belum Mengisi: *{unsubmitted_count} orang*\n",
        "📋 *Status Binaan Hari Ini:*",
    ]

    if not binaan_list:
        lines.append("_(Belum ada mutarabbi yang dipetakan untuk Anda di sheet Mapping)_")
    else:
        for idx, b in enumerate(binaan_list, start=1):
            status_icon = "✅ Sudah Isi" if b["is_submitted_today"] else "🔴 Belum Isi"
            lines.append(
                f"{idx}. *{b['name']}* ({b['kelompok']})\n"
                f"   • Hari Ini: {status_icon}\n"
                f"   • Bulan Ini: {b['month_days_submitted']}/{b['month_days_passed']} hari ({round(b['completion_pct'])}%)"
            )

    lines.append("\n👇 _Pilih tombol binaan di bawah untuk melihat rincian mutabaah:_")
    full_text = "\n".join(lines)
    markup = get_binaan_list_keyboard(binaan_list)

    if update.callback_query:
        await update.callback_query.answer("Data binaan diperbarui" if is_refresh else None)
        try:
            await update.callback_query.edit_message_text(
                full_text, reply_markup=markup, parse_mode="Markdown"
            )
        except Exception:
            # In case content didn't change
            pass
    elif update.message:
        await update.message.reply_text(
            full_text, reply_markup=markup, parse_mode="Markdown"
        )


async def show_binaan_detail(
    update: Update, context: ContextTypes.DEFAULT_TYPE, mutarabbi_id: str
):
    """Show detailed today & monthly mutabaah for a single binaan."""
    query = update.callback_query
    if query:
        await query.answer()

    mapping_service = MappingService.get_instance()
    try:
        detail = await mapping_service.get_binaan_detail(mutarabbi_id)
    except Exception as e:
        logger.error("Error fetching binaan detail for %s: %s", mutarabbi_id, e)
        if query:
            await query.answer("Gagal memuat rincian binaan.", show_alert=True)
        return

    meta = detail.get("meta", {})
    name = meta.get("name", "Binaan")
    kelompok = meta.get("kelompok", "-")
    username = detail.get("username", "")
    username_str = f" ({username})" if username else ""
    today_formatted = detail.get("today_formatted", "")
    is_submitted = detail.get("is_submitted_today", False)
    record = detail.get("today_record") or {}
    m_progress = detail.get("month_progress") or {}

    lines = [
        "👤 *Detail Mutabaah Binaan*",
        f"• Nama: *{name}*",
        f"• Kelompok: *{kelompok}*",
        f"• ID Telegram: `{mutarabbi_id}`{username_str}",
        f"• Tanggal: *{today_formatted}*\n",
    ]

    # Section 1: Today
    if is_submitted:
        lines.append("📅 *Status Hari Ini:* ✅ *Sudah Mengisi*")
        for key, defn in AMALAN_DEFINITIONS.items():
            col = defn["column"]
            raw_val = record.get(col, "")
            formatted = format_amalan_value(key, raw_val)
            lines.append(f"• {defn['icon']} {defn['name']}: *{formatted}*")
        lines.append("")
    else:
        lines.append("📅 *Status Hari Ini:* 🔴 *Belum Mengisi*\n")

    # Section 2: Month Progress
    if m_progress:
        month_label = m_progress.get("month_label", "")
        days_sub = m_progress.get("days_submitted", 0)
        days_passed = m_progress.get("days_passed", 0)
        comp_pct = m_progress.get("completion_percentage", 0.0)
        missing = m_progress.get("missing_dates", [])

        lines.append(f"📊 *Progress Bulan {month_label}:*")
        lines.append(f"• Hari Terisi: *{days_sub} dari {days_passed} hari*")
        lines.append(f"• Capaian Target: *{comp_pct}%*")
        if missing:
            lines.append(f"• Belum Diisi ({len(missing)} hari): 👉 *{format_missing_dates_id(missing)}*")
        else:
            lines.append("• Belum Diisi: ✅ *Alhamdulillah, semua hari terisi!*")

        items = m_progress.get("items", {})
        if items:
            lines.append("\n📌 *Rincian Amalan Bulan Ini:*")
            for key, item in items.items():
                icon = item.get("icon", "✨")
                s_name = item.get("name", key)
                actual = item.get("actual", 0)
                target = item.get("target", 0)
                unit = item.get("unit", "")
                pct = round(item.get("ratio", 0.0) * 100)
                berhalangan = item.get("berhalangan_days", 0)
                if berhalangan > 0:
                    lines.append(f"• {icon} {s_name}: {actual} / {target} {unit} ({pct}%) • _🌸 {berhalangan} hari berhalangan_")
                else:
                    lines.append(f"• {icon} {s_name}: {actual} / {target} {unit} ({pct}%)")

    full_text = "\n".join(lines)
    markup = get_binaan_detail_keyboard(mutarabbi_id)

    if query:
        try:
            await query.edit_message_text(full_text, reply_markup=markup, parse_mode="Markdown")
        except Exception:
            pass


async def handle_murobbi_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for Murobbi menus."""
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    user = update.effective_user

    mapping_service = MappingService.get_instance()
    is_murobbi = await mapping_service.is_murobbi_async(user.id)

    if not is_murobbi:
        await query.answer("Akses ditolak: Anda bukan Murobbi.", show_alert=True)
        return

    if data == "btn_cek_binaan" or data == "binaan_list":
        await show_binaan_list(update, context, user.id, is_refresh=False)
    elif data == "binaan_refresh":
        await show_binaan_list(update, context, user.id, is_refresh=True)
    elif data.startswith("binaan_detail_"):
        mutarabbi_id = data.replace("binaan_detail_", "").strip()
        await show_binaan_detail(update, context, mutarabbi_id)

