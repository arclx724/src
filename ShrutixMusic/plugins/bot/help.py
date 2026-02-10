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
from config import BANNED_USERS
from strings import get_string, helpers

# --- HELPER FUNCTION TO FIND DATA ---
def get_help_dict(helpers_obj):
    # Agar helpers ek Module (File) hai
    if isinstance(helpers_obj, py_types.ModuleType):
        # 1. Try finding 'helpers' dict inside the module
        if hasattr(helpers_obj, "helpers") and isinstance(helpers_obj.helpers, dict):
            return helpers_obj.helpers
        # 2. Try finding 'HELPERS' dict inside the module
        elif hasattr(helpers_obj, "HELPERS") and isinstance(helpers_obj.HELPERS, dict):
            return helpers_obj.HELPERS
        # 3. Fallback: Search for ANY dictionary inside the module
        else:
            for name, val in vars(helpers_obj).items():
                if not name.startswith("_") and isinstance(val, dict) and len(val) > 0:
                    return val
            return {} # Kuch nahi mila
    # Agar already Dictionary hai
    elif isinstance(helpers_obj, dict):
        return helpers_obj
    else:
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
            photo=config.START_IMG_URL,
            caption=_["help_2"],
            reply_markup=keyboard
        )

# ======================================================
# 2. MUSIC MANAGEMENT CLICKED (Auto-Fix Logic Here)
# ======================================================
@nand.on_callback_query(filters.regex("help_domain_music") & ~BANNED_USERS)
@languageCB
async def help_music_domain(client, CallbackQuery, _):
    global helpers
    # Use the smart finder function
    help_dict = get_help_dict(helpers)
    
    # Debug: Agar abhi bhi empty hai toh log mein pata chalega
    if not help_dict:
        print("[DEBUG] helpers dictionary is empty! Check strings/__init__.py")

    keyboard = []
    temp = []
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
    global helpers
    help_dict = get_help_dict(helpers)

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
    
