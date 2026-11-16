import os
import sys
import logging
import warnings
from datetime import time
from telegram import Update
from telegram.error import Forbidden, BadRequest, TelegramError
from telegram.warnings import PTBUserWarning
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Silence PTB warning for CallbackQueryHandler in chat-level conversations
warnings.filterwarnings("ignore", category=PTBUserWarning)
from app.config import Config
from app.utils.datetime import get_tz, get_today_str
from app.keyboards.common import get_reminder_keyboard
from app.services.sheets import SheetsService
from app.services.members import MembersService
from app.handlers import (
    start_command,
    help_command,
    cancel_command,
    get_registration_handler,
    get_mutabaah_conversation_handler,
    progress_command,
    admin_command,
    stats_command,
    export_command,
    handle_admin_callbacks,
    handle_admin_custom_date_text,
    settings_command,
    target_command,
    handle_settings_callbacks,
    handle_custom_target_text,
    edit_name_command,
    get_edit_name_conversation_handler,
    cekbinaan_command,
    handle_murobbi_callbacks,
    handle_murobbi_custom_date_text,
)


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# Reduce noisy logs from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("mutabaah_bot")


async def daily_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Scheduled job sending a friendly reminder at REMINDER_HOUR
    to active members who haven't submitted today's mutabaah.
    """
    logger.info("Executing daily reminder job...")
    try:
        sheets_service = SheetsService.get_instance()
        members_service = MembersService(sheets_service)

        today_str = get_today_str(Config.TIMEZONE)
        active_members = await members_service.get_all_active_members()

        all_mutabaah = await sheets_service.get_all_mutabaah_rows()
        submitted_user_ids = {
            str(r.get("Telegram User ID", "")).strip()
            for r in all_mutabaah
            if str(r.get("Date", "")).strip() == today_str
        }

        reminder_text = (
            "🌙 *Jangan lupa isi Mutabaah Yaumiyah hari ini.*\n\n"
            "Kurang dari 1 menit kok 😊"
        )
        reminder_markup = get_reminder_keyboard()

        sent_count = 0
        for member in active_members:
            uid_str = str(member.get("Telegram User ID", "")).strip()
            if not uid_str or uid_str in submitted_user_ids:
                continue

            try:
                user_id = int(uid_str)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=reminder_text,
                    reply_markup=reminder_markup,
                    parse_mode="Markdown",
                )
                sent_count += 1
            except Forbidden:
                logger.warning("User %s has blocked the bot or chat not found.", uid_str)
            except (BadRequest, TelegramError) as te:
                logger.warning("Failed to send reminder to user %s: %s", uid_str, te)

        logger.info("Daily reminder sent to %d members.", sent_count)
    except Exception as e:
        logger.error("Error running daily reminder job: %s", e, exc_info=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and inform user gracefully."""
    logger.error("Exception while handling an update: %s", context.error, exc_info=True)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Maaf, terjadi kesalahan teknis pada sistem.\n"
                "Silakan coba sesaat lagi atau gunakan /start."
            )
        except Exception:
            pass


def create_application() -> Application:
    """Build and configure the telegram application."""
    validation_errors = Config.validate()
    if validation_errors:
        for err in validation_errors:
            logger.warning("CONFIG WARNING: %s", err)

    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("CRITICAL: TELEGRAM_BOT_TOKEN is not configured! Exiting.")
        sys.exit(1)

    async def post_init(application: Application):
        try:
            from app.services.sheets import SheetsService
            from app.services.mapping import MappingService
            from app.services.members import MembersService
            from app.services.settings import UserSettingsService
            logger.info("Connecting and pre-warming in-memory caches...")
            sheets_svc = SheetsService.get_instance()
            await sheets_svc.connect()

            # Preload caches sequentially to avoid Google Sheets API rate limit burst
            await MappingService.get_instance().reload_cache()
            await MembersService.get_instance().reload_cache()
            await UserSettingsService.get_instance().reload_cache()
            await sheets_svc.get_all_mutabaah_rows()
            logger.info("All caches (Mapping, Members, Settings, Mutabaah) successfully preloaded.")
        except Exception as e:
            logger.warning("Failed to initialize caches on startup: %s", e)

    app = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Register handlers
    # Registration conversation handler (handles /start for unregistered users)
    app.add_handler(get_registration_handler())

    # Edit name conversation handler (handles /editnama, /nama, /gantinama, and btn_edit_name)
    app.add_handler(get_edit_name_conversation_handler())

    # Mutabaah conversation handler (handles /isi, /edit, and flow buttons)
    app.add_handler(get_mutabaah_conversation_handler())


    # Standard commands & callback handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CallbackQueryHandler(progress_command, pattern="^btn_progress$"))

    # Amalan selection & target settings
    app.add_handler(CommandHandler(["amalan", "settings"], settings_command))
    app.add_handler(CommandHandler("target", target_command))
    app.add_handler(
        CallbackQueryHandler(
            handle_settings_callbacks,
            pattern="^(btn_settings|btn_settings_amalan|btn_settings_target|toggle_amalan_|amalan_select_all|amalan_reset_default|btn_settings_save|btn_main_menu|edit_target_|set_target_)",
        )
    )

    # Admin commands & callbacks
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(
        CallbackQueryHandler(
            handle_admin_callbacks,
            pattern="^(admin_stats|admin_period_|admin_sync_)",
        )
    )

    # Murobbi commands & callbacks
    app.add_handler(CommandHandler(["cekbinaan", "binaan"], cekbinaan_command))
    app.add_handler(
        CallbackQueryHandler(
            handle_murobbi_callbacks,
            pattern="^(btn_cek_binaan|binaan_list|binaan_refresh|binaan_detail_|binaan_period_)",
        )
    )

    # General text message handler (custom target & admin custom date range & murobbi custom date)
    async def general_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get("waiting_admin_custom_date"):
            await handle_admin_custom_date_text(update, context)
            return
        if context.user_data.get("editing_target_amalan"):
            await handle_custom_target_text(update, context)
            return
        if context.user_data.get("waiting_murobbi_custom_date"):
            await handle_murobbi_custom_date_text(update, context)
            return

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, general_text_router))

    # Error handling
    app.add_error_handler(error_handler)

    # Schedule Daily Reminder Job via JobQueue
    if app.job_queue:
        tz = get_tz(Config.TIMEZONE)
        reminder_target_time = time(
            hour=Config.REMINDER_HOUR,
            minute=Config.REMINDER_MINUTE,
            tzinfo=tz,
        )
        app.job_queue.run_daily(
            daily_reminder_job,
            time=reminder_target_time,
            name="daily_mutabaah_reminder",
        )
        logger.info(
            "Scheduled daily reminder job at %02d:%02d (%s)",
            Config.REMINDER_HOUR,
            Config.REMINDER_MINUTE,
            Config.TIMEZONE,
        )
    else:
        logger.warning("JobQueue not initialized. Scheduled reminders are disabled.")

    return app


def main():
    """Run bot using Polling or Webhook depending on environment."""
    app = create_application()

    webhook_url = os.getenv("WEBHOOK_URL", "").strip()
    port = int(os.getenv("PORT", "8080"))

    if webhook_url:
        logger.info("Starting bot with Webhook mode on port %d...", port)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="telegram",
            webhook_url=f"{webhook_url.rstrip('/')}/telegram",
        )
    else:
        logger.info("Starting bot with Long Polling mode...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
