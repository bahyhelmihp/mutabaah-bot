"""
Handlers for managing user amalan selection and target customization (/amalan, /target, /settings).
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
from app.services.settings import UserSettingsService
from app.services.members import MembersService
from app.services.amalan import (
    AMALAN_DEFINITIONS,
    ALL_AMALAN_KEYS,
    get_amalan_info,
)
from app.keyboards.common import (
    get_main_menu_keyboard,
    get_user_main_menu_keyboard,
    get_amalan_selection_keyboard,
    get_amalan_target_list_keyboard,
    get_target_options_keyboard,
)

logger = logging.getLogger(__name__)

# State for text input when adjusting target
WAITING_CUSTOM_TARGET = 1


async def ensure_registered(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    members_service = MembersService()
    return await members_service.is_registered(user.id)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /settings or /amalan: show amalan checklist."""
    user = update.effective_user
    if not user:
        return

    if update.callback_query:
        await update.callback_query.answer()

    if not await ensure_registered(update):
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    settings_service = UserSettingsService.get_instance()
    active_keys = await settings_service.get_active_amalan(user.id)

    members_service = MembersService()
    member = await members_service.get_member(user.id)
    full_name = member.get("Full Name", user.first_name) if member else user.first_name

    text = (
        "⚙️ *Pengaturan Mutabaah*\n"
        f"👤 *Nama Terdaftar:* {full_name}\n\n"
        "Pilih amalan yang ingin Anda masukkan ke dalam mutabaah yaumiyah Anda.\n"
        "Klik nama amalan untuk mengaktifkan (✅) atau menonaktifkan (❌).\n\n"
        f"_Amalan aktif: {len(active_keys)} dari {len(ALL_AMALAN_KEYS)} amalan._"
    )
    markup = get_amalan_selection_keyboard(active_keys)

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
        await update.message.reply_text(
            text=text, reply_markup=markup, parse_mode="Markdown"
        )


async def target_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /target: show targets for active amalan."""
    user = update.effective_user
    if not user:
        return

    if update.callback_query:
        await update.callback_query.answer()

    if not await ensure_registered(update):
        msg = "⚠️ Anda belum terdaftar. Silakan ketik /start untuk mendaftar terlebih dahulu."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    settings_service = UserSettingsService.get_instance()
    active_keys = await settings_service.get_active_amalan(user.id)
    targets = await settings_service.get_user_targets(user.id)

    text = (
        "🎯 *Pengaturan Target Harian & Bulanan*\n\n"
        "Setiap orang dapat menentukan target amalan sesuai komitmen pribadi.\n"
        "Pilih amalan di bawah untuk mengubah targetnya:"
    )
    markup = get_amalan_target_list_keyboard(targets, active_keys)

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
        await update.message.reply_text(
            text=text, reply_markup=markup, parse_mode="Markdown"
        )


async def handle_settings_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle interactive button clicks for amalan checklist and settings."""
    query = update.callback_query
    if not query:
        return

    data = query.data
    user = update.effective_user
    if not user:
        return

    settings_service = UserSettingsService.get_instance()

    if data == "btn_settings" or data == "btn_settings_amalan":
        await query.answer()
        return await settings_command(update, context)

    if data == "btn_settings_target":
        await query.answer()
        return await target_command(update, context)

    if data.startswith("toggle_amalan_"):
        key = data.replace("toggle_amalan_", "")
        await query.answer()
        active_keys = await settings_service.toggle_amalan(user.id, key)

        members_service = MembersService()
        member = await members_service.get_member(user.id)
        full_name = member.get("Full Name", user.first_name) if member else user.first_name

        text = (
            "⚙️ *Pengaturan Mutabaah*\n"
            f"👤 *Nama Terdaftar:* {full_name}\n\n"
            "Pilih amalan yang ingin Anda masukkan ke dalam mutabaah yaumiyah Anda.\n"
            "Klik nama amalan untuk mengaktifkan (✅) atau menonaktifkan (❌).\n\n"
            f"_Amalan aktif: {len(active_keys)} dari {len(ALL_AMALAN_KEYS)} amalan._"
        )
        markup = get_amalan_selection_keyboard(active_keys)
        try:
            await query.edit_message_text(
                text=text, reply_markup=markup, parse_mode="Markdown"
            )
        except Exception:
            pass
        return


    if data == "amalan_select_all":
        await query.answer("Memilih semua amalan.")
        targets = await settings_service.get_user_targets(user.id)
        await settings_service.save_user_settings(user.id, list(ALL_AMALAN_KEYS), targets)
        return await settings_command(update, context)

    if data == "amalan_reset_default":
        await query.answer("Mereset ke pengaturan default.")
        await settings_service.reset_to_default(user.id)
        return await settings_command(update, context)

    if data == "btn_settings_save":
        await query.answer("Pilihan tersimpan!")
        active_keys = await settings_service.get_active_amalan(user.id)
        text = (
            f"✅ *Pengaturan Berhasil Disimpan!*\n\n"
            f"Anda memilih *{len(active_keys)} amalan* untuk dimutabaah.\n"
            "Data mutabaah dan perhitungan progres akan disesuaikan dengan pilihan Anda."
        )
        markup = await get_user_main_menu_keyboard(user.id)
        await query.edit_message_text(
            text=text, reply_markup=markup, parse_mode="Markdown"
        )
        return

    if data == "btn_main_menu":
        await query.answer()
        text = (
            f"Assalamu’alaikum *{user.first_name}* 👋\n"
            "Silakan pilih menu di bawah ini:"
        )
        markup = await get_user_main_menu_keyboard(user.id)
        await query.edit_message_text(
            text=text, reply_markup=markup, parse_mode="Markdown"
        )
        return

    if data.startswith("edit_target_"):
        key = data.replace("edit_target_", "")
        await query.answer()
        defn = get_amalan_info(key)
        targets = await settings_service.get_user_targets(user.id)
        curr_target = targets.get(key, defn.get("default_target", 0))

        context.user_data["editing_target_amalan"] = key
        text = (
            f"🎯 *Ubah Target: {defn.get('icon', '')} {defn.get('name', key)}*\n\n"
            f"Target saat ini: *{curr_target} {defn.get('unit', '')}*\n"
            f"Target bawaan: *{defn.get('default_target', 0)} {defn.get('unit', '')}*\n\n"
            "Pilih angka cepat di bawah, atau ketik langsung angka target baru:"
        )
        markup = get_target_options_keyboard(key, curr_target)
        await query.edit_message_text(
            text=text, reply_markup=markup, parse_mode="Markdown"
        )
        return

    if data.startswith("set_target_"):
        parts = data.split("_")
        # format: set_target_{amalan_key}_{val}
        # note: amalan_key can contain underscores like shaum_sunnah, sholat_wajib
        val_str = parts[-1]
        amalan_key = "_".join(parts[2:-1])
        if val_str.isdigit():
            new_target = int(val_str)
            await settings_service.set_target(user.id, amalan_key, new_target)
            await query.answer(f"Target diubah ke {new_target}!")
            return await target_command(update, context)


async def handle_custom_target_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual text input for target if user types an arbitrary number."""
    key = context.user_data.get("editing_target_amalan")
    if not key or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text.isdigit() and int(text) > 0:
        new_val = int(text)
        user = update.effective_user
        settings_service = UserSettingsService.get_instance()
        await settings_service.set_target(user.id, key, new_val)
        context.user_data.pop("editing_target_amalan", None)

        defn = get_amalan_info(key)
        await update.message.reply_text(
            f"✅ Target untuk *{defn.get('name', key)}* berhasil diubah menjadi *{new_val} {defn.get('unit', '')}*!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "⚠️ Masukkan angka positif yang valid (misal: 100)."
        )
