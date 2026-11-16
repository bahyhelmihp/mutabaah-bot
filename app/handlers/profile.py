"""
Handler for editing user's registered name (/editnama, /nama, /gantinama).
"""
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from app.services.members import MembersService
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_user_main_menu_keyboard,
    get_edit_name_keyboard,
)

logger = logging.getLogger(__name__)

WAITING_NEW_NAME = 1


async def edit_name_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point to start the name editing conversation."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    members_service = MembersService()
    try:
        is_reg = await members_service.is_registered(user.id)
    except Exception as e:
        logger.error("Error checking registration for user %s: %s", user.id, e)
        is_reg = False

    if not is_reg:
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        elif update.message:
            await update.message.reply_text(msg)
        return ConversationHandler.END

    member = await members_service.get_member(user.id)
    current_name = member.get("Full Name", user.first_name) if member else user.first_name

    text = (
        "👤 *Ubah Nama Lengkap*\n\n"
        f"Nama Anda saat ini: *{current_name}*\n\n"
        "Silakan ketik nama lengkap baru Anda di bawah ini:\n"
        "_(Ketik /cancel atau klik tombol di bawah untuk membatalkan)_"
    )
    markup = get_edit_name_keyboard()

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=markup, parse_mode="Markdown"
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text=text, reply_markup=markup, parse_mode="Markdown"
            )
    elif update.message:
        await update.message.reply_text(
            text=text, reply_markup=markup, parse_mode="Markdown"
        )

    return WAITING_NEW_NAME


async def handle_new_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the newly submitted name and update Google Sheets and cache."""
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return WAITING_NEW_NAME

    new_name = update.message.text.strip()

    if len(new_name) < 2:
        await update.message.reply_text(
            "⚠️ Nama terlalu pendek. Silakan masukkan nama lengkap yang valid (minimal 2 karakter):",
            reply_markup=get_edit_name_keyboard(),
        )
        return WAITING_NEW_NAME

    if len(new_name) > 100:
        await update.message.reply_text(
            "⚠️ Nama terlalu panjang (maksimal 100 karakter). Silakan masukkan nama yang lebih ringkas:",
            reply_markup=get_edit_name_keyboard(),
        )
        return WAITING_NEW_NAME

    members_service = MembersService()
    try:
        success = await members_service.update_name(
            user_id=user.id,
            new_full_name=new_name,
            username=user.username or "",
        )
    except Exception as e:
        logger.error("Failed to update name for user %s: %s", user.id, e)
        success = False

    if success:
        reply = (
            f"✅ *Nama Berhasil Diperbarui!*\n\n"
            f"Nama lengkap Anda kini telah diubah menjadi: *{new_name}* 🎉\n\n"
            "Nama baru ini otomatis digunakan untuk seluruh catatan amalan yaumiyah dan rekap laporan."
        )
        markup = await get_user_main_menu_keyboard(user.id)
        await update.message.reply_text(
            reply,
            reply_markup=markup,
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    markup = await get_user_main_menu_keyboard(user.id)
    await update.message.reply_text(
        "⚠️ Maaf, terjadi kendala saat menyimpan nama ke Google Sheets. "
        "Silakan coba sesaat lagi dengan mengetik /editnama.",
        reply_markup=markup,
    )
    return ConversationHandler.END


async def cancel_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the name update process."""
    user = update.effective_user
    msg = "❌ Perubahan nama dibatalkan."
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


def get_edit_name_conversation_handler() -> ConversationHandler:
    """ConversationHandler for updating member name."""
    return ConversationHandler(
        entry_points=[
            CommandHandler(["nama", "editnama", "gantinama"], edit_name_command),
            CallbackQueryHandler(edit_name_command, pattern="^btn_edit_name$"),
        ],
        states={
            WAITING_NEW_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_name_input),
                CallbackQueryHandler(cancel_edit_name, pattern="^cancel_edit_name$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_edit_name),
            CommandHandler("start", cancel_edit_name),
            CallbackQueryHandler(cancel_edit_name, pattern="^(cancel_edit_name|btn_main_menu)$"),
        ],
        name="edit_name_conversation",
        persistent=False,
        per_message=False,
        per_chat=True,
        per_user=True,
        allow_reentry=True,
    )
