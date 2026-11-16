"""
Admin handlers for Mutabaah IMA Korea Bot.
Supports:
1. Period filtering: Today, Weekly (7 days), Monthly, Last Month, and Custom Date Range.
2. Writing/syncing complete executive summary and member leaderboard to Google Sheets 'Summary Stats'.
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from app.config import Config
from app.services.statistics import StatisticsService
from app.services.sheets import SheetsService
from app.keyboards.common import (
    get_admin_keyboard,
    get_admin_period_keyboard,
)
from app.utils.datetime import (
    get_date_range_presets,
    parse_custom_date_range,
    format_date_id,
)

logger = logging.getLogger(__name__)


def is_admin_user(user_id: int) -> bool:
    return Config.is_admin(user_id)


def format_admin_stats_text(stats: Dict[str, Any]) -> str:
    """Format comprehensive stats text for admin."""
    period_label = stats.get("period_label", "Periode")
    start_date = stats.get("start_date", "")
    end_date = stats.get("end_date", "")

    date_range_str = f"_{start_date} s/d {end_date}_" if start_date != end_date else f"_{start_date}_"

    lines = [
        f"📊 *Statistik Mutabaah: {period_label}*",
        f"{date_range_str}\n",
        f"👥 *Total Anggota Terdaftar:* {stats.get('registered_members', 0)} orang",
        f"📝 *Anggota Mengisi Periode Ini:* {stats.get('active_submitters', 0)} orang",
        f"📈 *Tingkat Keaktifan:* {stats.get('submission_rate', 0.0)}%",
        f"📋 *Total Entri Pengisian:* {stats.get('total_submissions', 0)} data",
        f"⭐ *Rata-rata Capaian Target:* {stats.get('average_completion_rate', 0.0)}%\n",
        "📌 *Rata-rata Amalan per Pengisian:*",
        f"• 📖 Tilawah: *{stats.get('avg_tilawah', 0.0)} hal* (Total: {stats.get('total_tilawah', 0)})",
        f"• 🕌 Sholat Wajib: *{stats.get('avg_wajib', 0.0)} waktu* (Total: {stats.get('total_wajib', 0)})",
        f"• 🌙 Rawatib: *{stats.get('avg_rawatib', 0.0)} rakaat* (Total: {stats.get('total_rawatib', 0)})",
        f"• 📿 Al-Ma’tsurat: *{stats.get('avg_almatsurat', 0.0)}x* (Total: {stats.get('total_almatsurat', 0)})",
        f"• 🌸 Shalawat: *{stats.get('avg_shalawat', 0.0)}x* (Total: {stats.get('total_shalawat', 0)})",
        f"• 🤲 Istighfar: *{stats.get('avg_istighfar', 0.0)}x* (Total: {stats.get('total_istighfar', 0)})",
        f"• 📜 Tadabbur: *{stats.get('avg_tadabbur', 0.0)} ayat* (Total: {stats.get('total_tadabbur', 0)})",
        f"• 🍽️ Shaum Sunnah: *{stats.get('count_shaum', 0)} hari*",
        f"• 🌃 Qiyamulail: *{stats.get('count_qiyam', 0)} hari*",
        f"• ☀️ Dhuha: *{stats.get('count_dhuha', 0)} hari*",
        f"• 🏃 Olahraga: *{stats.get('count_olahraga', 0)} hari*",
        f"• 🤝 Silaturahim: *{stats.get('count_silaturahim', 0)} hari*",
        f"• 🤲 Doa Ummat Islam: *{stats.get('avg_doa_ummat', 0.0)}x* (Total: {stats.get('total_doa_ummat', 0)})",
    ]

    # Show top active members preview if available
    members = stats.get("member_breakdown", [])
    if members:
        lines.append("\n🏆 *Top 3 Anggota Terajin:*")
        for idx, m in enumerate(members[:3], start=1):
            name = m.get("full_name") or m.get("username") or f"User {m.get('user_id')}"
            lines.append(f"{idx}. {name} — *{m.get('days_submitted', 0)} hari* ({m.get('avg_completion', 0.0)}%)")

    lines.append("\n_Pilih periode lain di bawah atau klik Simpan ke Google Sheets:_")
    return "\n".join(lines)


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
        "Menu khusus pengurus untuk memantau rekap mutabaah anggota:\n\n"
        "• /stats - Rekap statistik (Pilih Periode, Mingguan, Bulanan, atau Rentang Bebas)\n"
        "• /export - Tautan spreadsheet Google Sheets\n\n"
        "Silakan pilih periode statistik di bawah untuk langsung melihat laporan:"
    )
    await update.effective_message.reply_text(
        text,
        reply_markup=get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, "monthly"),
        parse_mode="Markdown",
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stats command with optional period arguments:
    - /stats (defaults to current month)
    - /stats weekly / pekan
    - /stats today / hari_ini
    - /stats last_month / bulan_lalu
    - /stats 2026-10-01 - 2026-10-10 (custom range)
    """
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

    # Determine period from args or default to monthly
    presets = get_date_range_presets(Config.TIMEZONE)
    period_key = "monthly"
    start_date = presets["monthly"]["start_date"]
    end_date = presets["monthly"]["end_date"]
    period_label = presets["monthly"]["label"]

    if context.args:
        arg_str = " ".join(context.args).strip().lower()
        if arg_str in ["today", "hari", "hari_ini"]:
            period_key = "today"
            p = presets["today"]
            start_date, end_date, period_label = p["start_date"], p["end_date"], p["label"]
        elif arg_str in ["weekly", "pekan", "minggu", "pekan_ini"]:
            period_key = "weekly"
            p = presets["weekly"]
            start_date, end_date, period_label = p["start_date"], p["end_date"], p["label"]
        elif arg_str in ["last_month", "bulan_lalu"]:
            period_key = "last_month"
            p = presets["last_month"]
            start_date, end_date, period_label = p["start_date"], p["end_date"], p["label"]
        else:
            custom_range = parse_custom_date_range(" ".join(context.args))
            if custom_range:
                period_key = "custom"
                start_date = custom_range["start_date"]
                end_date = custom_range["end_date"]
                period_label = custom_range["label"]

    stats_service = StatisticsService()
    try:
        stats = await stats_service.calculate_period_admin_stats(
            start_date=start_date,
            end_date=end_date,
            period_label=period_label,
            tz_name=Config.TIMEZONE,
        )
        context.user_data["last_admin_stats"] = stats
        context.user_data["last_admin_period_key"] = period_key
    except Exception as e:
        logger.error("Error calculating admin stats: %s", e)
        await update.effective_message.reply_text(
            "⚠️ Terjadi kesalahan saat menghitung statistik dari Google Sheets."
        )
        return

    text = format_admin_stats_text(stats)
    markup = get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, period_key)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=markup, parse_mode="Markdown"
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text=text, reply_markup=markup, parse_mode="Markdown"
            )
    else:
        await update.effective_message.reply_text(
            text, reply_markup=markup, parse_mode="Markdown"
        )


async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle period filter buttons and sync to sheet."""
    query = update.callback_query
    if not query:
        return

    data = query.data
    user = update.effective_user
    if not user or not is_admin_user(user.id):
        await query.answer("⛔ Akses ditolak", show_alert=True)
        return

    presets = get_date_range_presets(Config.TIMEZONE)

    if data == "admin_stats":
        await query.answer()
        return await stats_command(update, context)

    if data in ["admin_period_today", "admin_period_weekly", "admin_period_monthly", "admin_period_last_month"]:
        await query.answer()
        p_key = data.replace("admin_period_", "")
        preset = presets.get(p_key, presets["monthly"])

        stats_service = StatisticsService()
        try:
            stats = await stats_service.calculate_period_admin_stats(
                start_date=preset["start_date"],
                end_date=preset["end_date"],
                period_label=preset["label"],
                tz_name=Config.TIMEZONE,
            )
            context.user_data["last_admin_stats"] = stats
            context.user_data["last_admin_period_key"] = p_key
            text = format_admin_stats_text(stats)
            markup = get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, p_key)
            await query.edit_message_text(text=text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            logger.error("Error calculating stats for %s: %s", p_key, e)
            await query.message.reply_text("⚠️ Gagal mengambil statistik dari Google Sheets.")
        return

    if data == "admin_period_custom":
        await query.answer()
        context.user_data["waiting_admin_custom_date"] = True
        prompt = (
            "🔍 *Filter Tanggal / Rentang Bebas*\n\n"
            "Ketik tanggal atau rentang tanggal yang ingin dianalisis.\n\n"
            "Contoh format:\n"
            "• `2026-10-01 s/d 2026-10-14`\n"
            "• `2026-10-01 - 2026-10-14`\n"
            "• `2026-10-14` (satu tanggal saja)"
        )
        await query.message.reply_text(prompt, parse_mode="Markdown")
        return

    if data.startswith("admin_sync_"):
        await query.answer("Menyimpan ke Google Sheets...")
        stats = context.user_data.get("last_admin_stats")
        if not stats:
            stats_service = StatisticsService()
            stats = await stats_service.calculate_monthly_admin_stats()
            context.user_data["last_admin_stats"] = stats

        member_breakdown = stats.get("member_breakdown", [])
        sheets_service = SheetsService.get_instance()

        try:
            # Write both the executive report and log entry
            await sheets_service.write_summary_stats_report(stats, member_breakdown)
            await sheets_service.append_or_update_summary_log(stats)

            sheet_url = f"https://docs.google.com/spreadsheets/d/{Config.GOOGLE_SHEET_ID}"
            success_text = (
                f"✅ *Rekap Statistik Berhasil Disimpan!*\n\n"
                f"Laporan periode *{stats.get('period_label')}* telah berhasil ditulis ke lembar kerja *Summary Stats* di Google Sheets.\n\n"
                f"🔗 [Buka Google Sheets Summary]({sheet_url})"
            )
            await query.message.reply_text(
                success_text,
                disable_web_page_preview=False,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("Failed to write summary report to sheets: %s", e)
            await query.message.reply_text(
                "⚠️ Gagal menyimpan rekap statistik ke Google Sheets. Silakan periksa koneksi atau kredensial."
            )
        return


async def handle_admin_custom_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process custom date range text input from admin."""
    if not context.user_data.get("waiting_admin_custom_date"):
        return

    user = update.effective_user
    if not user or not is_admin_user(user.id):
        context.user_data.pop("waiting_admin_custom_date", None)
        return

    text = update.message.text.strip() if update.message and update.message.text else ""
    parsed = parse_custom_date_range(text)

    if not parsed:
        await update.message.reply_text(
            "⚠️ Format tanggal tidak dikenali.\n"
            "Gunakan format: `YYYY-MM-DD s/d YYYY-MM-DD` atau `YYYY-MM-DD` (contoh: `2026-10-01 - 2026-10-10`)."
        )
        return

    context.user_data.pop("waiting_admin_custom_date", None)
    stats_service = StatisticsService()

    try:
        stats = await stats_service.calculate_period_admin_stats(
            start_date=parsed["start_date"],
            end_date=parsed["end_date"],
            period_label=parsed["label"],
            tz_name=Config.TIMEZONE,
        )
        context.user_data["last_admin_stats"] = stats
        context.user_data["last_admin_period_key"] = "custom"

        formatted_text = format_admin_stats_text(stats)
        markup = get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, "custom")
        await update.message.reply_text(
            formatted_text, reply_markup=markup, parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Error calculating custom period stats: %s", e)
        await update.message.reply_text("⚠️ Terjadi kesalahan saat menghitung data statistik.")


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
        "Semua entri mutabaah dan rekap statistik tersinkronisasi langsung ke spreadsheet utama:\n\n"
        f"🔗 [Buka Google Sheets Mutabaah]({sheet_url})\n\n"
        f"• *ID Spreadsheet:* `{Config.GOOGLE_SHEET_ID}`\n"
        "• *Lembar Kerja Utama:*\n"
        "  1. `Daily Mutabaah` (Seluruh entri harian)\n"
        "  2. `Members` (Daftar anggota aktif)\n"
        "  3. `User Settings` (Target & pilihan amalan user)\n"
        "  4. `Summary Stats` (Rekap statistik agregat & leaderboard)"
    )
    await update.effective_message.reply_text(
        text,
        disable_web_page_preview=False,
        parse_mode="Markdown",
    )
