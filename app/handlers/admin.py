"""
Admin handlers for Mutabaah IMA Korea Bot.
Supports:
1. Period filtering: Today, Weekly (7 days), Monthly, Last Month, and Custom Date Range.
2. Writing/syncing complete executive summary and member leaderboard to Google Sheets 'Summary Stats'.
"""
import logging
import math
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from app.config import Config
from app.services.statistics import StatisticsService
from app.services.sheets import SheetsService
from app.services.mapping import MappingService
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


def _ceil_int(val: Any) -> int:
    """Helper to round float values UP to integer (math.ceil)."""
    try:
        return math.ceil(float(val))
    except (ValueError, TypeError):
        return 0


def format_admin_stats_text(stats: Dict[str, Any]) -> str:
    """Format comprehensive stats text for admin with counts rounded UP (math.ceil)."""
    period_label = stats.get("period_label", "Periode")
    start_date = stats.get("start_date", "")
    end_date = stats.get("end_date", "")
    kelompok_filter = stats.get("kelompok_filter", "all")

    date_range_str = f"_{start_date} s/d {end_date}_" if start_date != end_date else f"_{start_date}_"
    n_entries = stats.get("total_submissions", 0)

    kelompok_badge = ""
    group_header = "👥 *Keaktifan Anggota:*"
    if kelompok_filter and kelompok_filter.lower() not in ["all", "semua"]:
        kelompok_badge = f"🏷️ *Kelompok:* `{kelompok_filter}`\n"
        group_header = f"👥 *Keaktifan Anggota ({kelompok_filter}):*"

    lines = [
        f"📊 *Statistik Mutabaah: {period_label}*",
        f"{kelompok_badge}{date_range_str}\n" if kelompok_badge else f"{date_range_str}\n",
        group_header,
        f"• Terdaftar: {stats.get('registered_members', 0)} orang | Aktif Mengisi: {stats.get('active_submitters', 0)} orang ({stats.get('submission_rate', 0.0)}%)",
        f"• Total Entri: {n_entries} laporan harian",
        f"• Hari Mengisi: Rata-rata *{_ceil_int(stats.get('avg_days_submitted', 0))} hari* (Min: {_ceil_int(stats.get('min_days_submitted', 0))} • Max: {_ceil_int(stats.get('max_days_submitted', 0))} hari)\n",
        "⭐ *Performa Capaian Target:*",
        f"• Rata-rata Capaian: *{stats.get('average_completion_rate', 0.0)}%* (Min: {stats.get('min_completion_rate', 0.0)}% • Max: {stats.get('max_completion_rate', 0.0)}%)\n",
        "📌 *Rata-rata & Akumulasi Amalan (Harian):*",
        f"• 📖 Tilawah: *{_ceil_int(stats.get('avg_tilawah', 0))} hal/hari* (Total: {stats.get('total_tilawah', 0)} hal | Rentang: {_ceil_int(stats.get('min_tilawah', 0))} – {_ceil_int(stats.get('max_tilawah', 0))})",
        f"• 🕌 Sholat Wajib: *{_ceil_int(stats.get('avg_wajib', 0))} waktu/hari* (Total: {stats.get('total_wajib', 0)} | Rentang: {_ceil_int(stats.get('min_wajib', 0))} – {_ceil_int(stats.get('max_wajib', 0))})",
        f"• 🌙 Rawatib: *{_ceil_int(stats.get('avg_rawatib', 0))} rakaat/hari* (Total: {stats.get('total_rawatib', 0)} rkt | Rentang: {_ceil_int(stats.get('min_rawatib', 0))} – {_ceil_int(stats.get('max_rawatib', 0))})",
        f"• 📿 Al-Ma’tsurat: *{_ceil_int(stats.get('avg_almatsurat', 0))}x/hari* (Total: {stats.get('total_almatsurat', 0)}x | Rentang: {_ceil_int(stats.get('min_almatsurat', 0))} – {_ceil_int(stats.get('max_almatsurat', 0))})",
        f"• 🌸 Shalawat: *{_ceil_int(stats.get('avg_shalawat', 0))}x/hari* (Total: {stats.get('total_shalawat', 0):,} | Rentang: {_ceil_int(stats.get('min_shalawat', 0))} – {_ceil_int(stats.get('max_shalawat', 0))})".replace(",", "."),
        f"• 🤲 Istighfar: *{_ceil_int(stats.get('avg_istighfar', 0))}x/hari* (Total: {stats.get('total_istighfar', 0):,} | Rentang: {_ceil_int(stats.get('min_istighfar', 0))} – {_ceil_int(stats.get('max_istighfar', 0))})".replace(",", "."),
        f"• 📜 Tadabbur: *{_ceil_int(stats.get('avg_tadabbur', 0))} ayat/hari* (Total: {stats.get('total_tadabbur', 0)} ayat | Rentang: {_ceil_int(stats.get('min_tadabbur', 0))} – {_ceil_int(stats.get('max_tadabbur', 0))})",
        f"• 🏃 Olahraga: *{_ceil_int(stats.get('avg_olahraga', 0))} menit/hari* (Total: {stats.get('total_olahraga', 0)} mnt | Rentang: {_ceil_int(stats.get('min_olahraga', 0))} – {_ceil_int(stats.get('max_olahraga', 0))})",
        f"• 🤲 Doa Ummat: *{_ceil_int(stats.get('avg_doa_ummat', 0))}x/hari* (Total: {stats.get('total_doa_ummat', 0)}x | Rentang: {_ceil_int(stats.get('min_doa_ummat', 0))} – {_ceil_int(stats.get('max_doa_ummat', 0))})\n",
        "📌 *Amalan Berkala (Checklist):*",
        f"• ☀️ Dhuha: *{stats.get('dhuha_members', 0)} orang* ({stats.get('pct_dhuha_members', 0.0)}%) • Rata-rata *{_ceil_int(stats.get('avg_dhuha_per_member', 0))}x / member* (Total: {stats.get('count_dhuha', 0)}x | Rentang: {_ceil_int(stats.get('min_dhuha', 0))} – {_ceil_int(stats.get('max_dhuha', 0))}x)",
        f"• 🌃 Qiyamulail: *{stats.get('qiyam_members', 0)} orang* ({stats.get('pct_qiyam_members', 0.0)}%) • Rata-rata *{_ceil_int(stats.get('avg_qiyam_per_member', 0))}x / member* (Total: {stats.get('count_qiyam', 0)}x | Rentang: {_ceil_int(stats.get('min_qiyam', 0))} – {_ceil_int(stats.get('max_qiyam', 0))}x)",
        f"• 🤝 Silaturahim: *{stats.get('silaturahim_members', 0)} orang* ({stats.get('pct_silaturahim_members', 0.0)}%) • Rata-rata *{_ceil_int(stats.get('avg_silaturahim_per_member', 0))}x / member* (Total: {stats.get('count_silaturahim', 0)}x | Rentang: {_ceil_int(stats.get('min_silaturahim', 0))} – {_ceil_int(stats.get('max_silaturahim', 0))}x)",
        f"• 🍽️ Shaum Sunnah: *{stats.get('shaum_members', 0)} orang* ({stats.get('pct_shaum_members', 0.0)}%) • Rata-rata *{_ceil_int(stats.get('avg_shaum_per_member', 0))} hari / member* (Total: {stats.get('count_shaum', 0)} hari | Rentang: {_ceil_int(stats.get('min_shaum', 0))} – {_ceil_int(stats.get('max_shaum', 0))} hari)",
    ]

    # Show top active members preview if available
    members = stats.get("member_breakdown", [])
    if members:
        lines.append("\n🏆 *Top 3 Anggota Terajin:*")
        for idx, m in enumerate(members[:3], start=1):
            name = m.get("full_name") or m.get("username") or f"User {m.get('user_id')}"
            lines.append(f"{idx}. {name} — *{m.get('days_submitted', 0)} hari* ({m.get('avg_completion', 0.0)}%)")
            highlights = m.get("highlights", [])
            if highlights:
                lines.append(f"   └ 🌟 _Unggul di:_ {', '.join(highlights)}")
            elif m.get("days_submitted", 0) > 0:
                lines.append(f"   └ 🌟 _Konsisten mengisi {m.get('days_submitted', 0)} hari_")

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
        "• /stats - Rekap statistik (Pilih Kelompok, Periode, atau Rentang Bebas)\n"
        "• /export - Tautan spreadsheet Google Sheets\n\n"
        "Silakan pilih kelompok atau periode statistik di bawah untuk langsung melihat laporan:"
    )
    mapping_service = MappingService.get_instance()
    await mapping_service.reload_cache()
    avail_k = mapping_service.get_all_kelompoks()
    sel_k = context.user_data.get("admin_selected_kelompok", "all")

    await update.effective_message.reply_text(
        text,
        reply_markup=get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, "monthly", sel_k, avail_k),
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
    mapping_service = MappingService.get_instance()
    await mapping_service.reload_cache()
    avail_k = mapping_service.get_all_kelompoks()
    sel_k = context.user_data.get("admin_selected_kelompok", "all")

    try:
        stats = await stats_service.calculate_period_admin_stats(
            start_date=start_date,
            end_date=end_date,
            period_label=period_label,
            tz_name=Config.TIMEZONE,
            kelompok_filter=sel_k,
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
    markup = get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, period_key, sel_k, avail_k)

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
    """Handle period filter buttons, kelompok filter buttons, and sync to sheet."""
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

    mapping_service = MappingService.get_instance()
    await mapping_service.reload_cache()
    avail_k = mapping_service.get_all_kelompoks()

    if data.startswith("admin_kelompok_"):
        await query.answer()
        sel_k = data.replace("admin_kelompok_", "").strip()
        context.user_data["admin_selected_kelompok"] = sel_k

        p_key = context.user_data.get("last_admin_period_key", "monthly")
        if p_key == "custom" and "last_admin_custom_range" in context.user_data:
            c_start, c_end, c_label = context.user_data["last_admin_custom_range"]
            start_date, end_date, period_label = c_start, c_end, c_label
        else:
            preset = presets.get(p_key, presets["monthly"])
            start_date, end_date, period_label = preset["start_date"], preset["end_date"], preset["label"]

        stats_service = StatisticsService()
        try:
            stats = await stats_service.calculate_period_admin_stats(
                start_date=start_date,
                end_date=end_date,
                period_label=period_label,
                tz_name=Config.TIMEZONE,
                kelompok_filter=sel_k,
            )
            context.user_data["last_admin_stats"] = stats
            text = format_admin_stats_text(stats)
            markup = get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, p_key, sel_k, avail_k)
            await query.edit_message_text(text=text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            logger.error("Error calculating stats for kelompok %s: %s", sel_k, e)
            await query.message.reply_text("⚠️ Gagal mengambil statistik untuk kelompok tersebut.")
        return

    if data in ["admin_period_today", "admin_period_weekly", "admin_period_monthly", "admin_period_last_month"]:
        await query.answer()
        p_key = data.replace("admin_period_", "")
        preset = presets.get(p_key, presets["monthly"])
        sel_k = context.user_data.get("admin_selected_kelompok", "all")

        stats_service = StatisticsService()
        try:
            stats = await stats_service.calculate_period_admin_stats(
                start_date=preset["start_date"],
                end_date=preset["end_date"],
                period_label=preset["label"],
                tz_name=Config.TIMEZONE,
                kelompok_filter=sel_k,
            )
            context.user_data["last_admin_stats"] = stats
            context.user_data["last_admin_period_key"] = p_key
            text = format_admin_stats_text(stats)
            markup = get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, p_key, sel_k, avail_k)
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
    context.user_data["last_admin_custom_range"] = (parsed["start_date"], parsed["end_date"], parsed["label"])

    stats_service = StatisticsService()
    mapping_service = MappingService.get_instance()
    await mapping_service.reload_cache()
    avail_k = mapping_service.get_all_kelompoks()
    sel_k = context.user_data.get("admin_selected_kelompok", "all")

    try:
        stats = await stats_service.calculate_period_admin_stats(
            start_date=parsed["start_date"],
            end_date=parsed["end_date"],
            period_label=parsed["label"],
            tz_name=Config.TIMEZONE,
            kelompok_filter=sel_k,
        )
        context.user_data["last_admin_stats"] = stats
        context.user_data["last_admin_period_key"] = "custom"

        formatted_text = format_admin_stats_text(stats)
        markup = get_admin_period_keyboard(Config.GOOGLE_SHEET_ID, "custom", sel_k, avail_k)
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
