from typing import Union
from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import types as py_types

from ShrutixMusic import nand
from ShrutixMusic.utils.database import get_lang
from ShrutixMusic.utils.decorators.language import LanguageStart, languageCB
from ShrutixMusic.utils.inline.help import (
    private_help_panel,
    help_back_markup,
    security_help_panel,
    security_back_markup
)
from config import BANNED_USERS, START_IMG_URL
from strings import get_string

# --- SMART IMPORT LOGIC ---
# Ye logic khud dhoondhega ki commands kahan chupe hain
try:
    from strings import HELPERS as helpers
except ImportError:
    try:
        from strings import helpers
    except ImportError:
        helpers = {}

def get_valid_helpers():
    global helpers
    # Agar helpers dictionary hai, to wahi return karo
    if isinstance(helpers, dict):
        return helpers
    # Agar helpers module (file) hai, to uske andar dhoondho
    elif isinstance(helpers, py_types.ModuleType):
        if hasattr(helpers, "HELPERS") and isinstance(helpers.HELPERS, dict):
            return helpers.HELPERS
        elif hasattr(helpers, "helpers") and isinstance(helpers.helpers, dict):
            return helpers.helpers
    return {}

# ======================================================
# 1. MAIN HELP COMMAND (Shows 2 Buttons)
# ======================================================
@nand.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@nand.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
@LanguageStart
async def helper_private(client, update: Union[types.Message, types.CallbackQuery], _):
    is_callback = isinstance(update, types.CallbackQuery)
    if is_callback:
        try:
            await update.answer()
        except:
            pass
        keyboard = InlineKeyboardMarkup(private_help_panel(_))
        await update.edit_message_text(
            _["help_2"], reply_markup=keyboard
        )
    else:
        try:
            await update.delete()
        except:
            pass
        keyboard = InlineKeyboardMarkup(private_help_panel(_))
        await update.reply_photo(
            photo=START_IMG_URL,
            caption=_["help_2"],
            reply_markup=keyboard
        )

# ======================================================
# 2. MUSIC MANAGEMENT CLICKED (Fixed)
# ======================================================
@nand.on_callback_query(filters.regex("help_domain_music") & ~BANNED_USERS)
@languageCB
async def help_music_domain(client, CallbackQuery, _):
    # Sahi dictionary fetch karo
    help_dict = get_valid_helpers()
    
    keyboard = []
    temp = []
    # Ab loop sahi dictionary par chalega
    for count, key in enumerate(help_dict):
        if count % 3 == 0 and count > 0:
            keyboard.append(temp)
            temp = []
        temp.append(InlineKeyboardButton(text=key.title(), callback_data=f"help_callback {key}"))
    keyboard.append(temp)
    
    keyboard.append([InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settings_back_helper")])
    
    await CallbackQuery.edit_message_text(
        "🎸 **Music Management Commands**\n\nChoose a category below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ======================================================
# 3. GROUP MANAGEMENT CLICKED
# ======================================================
@nand.on_callback_query(filters.regex("help_domain_security") & ~BANNED_USERS)
@languageCB
async def help_security_domain(client, CallbackQuery, _):
    await CallbackQuery.edit_message_text(
        "🛡️ **Group Management Commands**\n\nChoose a category below:",
        reply_markup=InlineKeyboardMarkup(security_help_panel(_))
    )

# ======================================================
# 4. HANDLE MUSIC SUB-MODULES
# ======================================================
@nand.on_callback_query(filters.regex(r"help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    help_dict = get_valid_helpers()

    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = help_back_markup(_)
    
    if cb in help_dict:
        await CallbackQuery.edit_message_text(
            help_dict[cb], reply_markup=keyboard
        )
    else:
        await CallbackQuery.answer(_["help_7"], show_alert=True)

# ======================================================
# 5. HANDLE SECURITY SUB-MODULES
# ======================================================
@nand.on_callback_query(filters.regex(r"help_cmd_") & ~BANNED_USERS)
@languageCB
async def security_helper_cb(client, CallbackQuery, _):
    cmd = CallbackQuery.data.split("_")[2]
    keyboard = security_back_markup(_)
    text = ""

    if cmd == "antinuke":
        text = (
            "☢️ **Anti-Nuke System**\n\n"
            "Protects the group from unauthorized bans/kicks/demotions.\n\n"
            "• **Trigger:** 3 Actions in 30 Seconds.\n"
            "• **Action:** Instant Demotion.\n\n"
            "**Commands:**\n"
            "• `/whitelist [Reply]` - Add trusted admin.\n"
            "• `/unwhitelist [Reply]` - Remove trusted admin."
        )
    elif cmd == "antibot":
        text = (
            "🤖 **Anti-Bot System**\n\n"
            "Prevents unauthorized bots from entering the group.\n\n"
            "**Commands:**\n"
            "• `/nobots on` - Enable Protection.\n"
            "• `/nobots off` - Disable Protection.\n\n"
            "*Only Admins with 'Add New Admins' permission can add bots.*"
        )
    elif cmd == "abuse":
        text = (
            "🤬 **Anti-Abuse (AI)**\n\n"
            "Deletes messages containing abuse or hate speech using AI & Regex.\n\n"
            "**Commands:**\n"
            "• `/abuse on` - Enable Filter.\n"
            "• `/abuse off` - Disable Filter.\n"
            "• `/auth [Reply]` - Allow user to abuse.\n"
            "• `/unauth [Reply]` - Remove allowance."
        )
    elif cmd == "antinsfw":
        text = (
            "🔞 **Anti-NSFW**\n\n"
            "Deletes adult content (Nudity/Gore) automatically.\n\n"
            "**Commands:**\n"
            "• `/antinsfw on` - Enable Scanner.\n"
            "• `/antinsfw off` - Disable Scanner.\n"
            "• `/addapi` - (Owner Only) Add SightEngine Key."
        )
    elif cmd == "antiedit":
        text = (
            "✏️ **Anti-Edit**\n\n"
            "Deletes edited messages to prevent deception.\n\n"
            "**Commands:**\n"
            "• `/antiedit on` - Enable.\n"
            "• `/antiedit off` - Disable.\n\n"
            "*Admins are bypassed.*"
        )
    elif cmd == "autodelete":
        text = (
            "🗑️ **Media Auto-Delete**\n\n"
            "Automatically deletes photos/videos after X time.\n\n"
            "**Commands:**\n"
            "• `/setdelay [Time] [Unit]`\n"
            "Example: `/setdelay 30 s` (Seconds)"
        )
    elif cmd == "management":
        text = (
            "👮‍♂️ **Group Management**\n\n"
            "Basic admin tools.\n\n"
            "**Commands:**\n"
            "• `/ban`, `/unban` - Ban/Unban user.\n"
            "• `/kick` - Kick user.\n"
            "• `/mute`, `/unmute` - Mute/Unmute.\n"
            "• `/warn` - Warn user (Max 3).\n"
            "• `/promote`, `/demote` - Change Admin rights."
        )

    await CallbackQuery.edit_message_text(text, reply_markup=keyboard)
    
