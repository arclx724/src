from typing import Union
from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, Message

from ShrutixMusic import nand
from ShrutixMusic.utils import help_pannel
from ShrutixMusic.utils.database import get_lang
from ShrutixMusic.utils.decorators.language import LanguageStart, languageCB
from ShrutixMusic.utils.inline.help import (
    help_back_markup, 
    private_help_panel, 
    security_help_panel,
    security_back_markup
)
from config import BANNED_USERS, START_IMG_URL, SUPPORT_CHAT
from strings import get_string, helpers

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
        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)
        
        # Main Menu (2 Buttons wala)
        keyboard = InlineKeyboardMarkup(private_help_panel(_))
        
        await update.edit_message_text(
            _["help_2"], reply_markup=keyboard
        )
    else:
        try:
            await update.delete()
        except:
            pass
        language = await get_lang(update.chat.id)
        _ = get_string(language)
        keyboard = InlineKeyboardMarkup(private_help_panel(_))
        await update.reply_text(
            _["help_2"], reply_markup=keyboard
        )

# --- 1. MUSIC DOMAIN (Old Modules) ---
@nand.on_callback_query(filters.regex("help_domain_music") & ~BANNED_USERS)
@languageCB
async def help_music_domain(client, CallbackQuery, _):
    # Ye purana grid load karega (Admin, Play, Auth etc.)
    # Hum helpers list se Security modules filter kar denge taaki duplicate na ho
    
    _helpers = {}
    security_keywords = ["antinuke", "antibot", "abuse", "antinsfw", "antiedit", "autodelete", "management"]
    
    for module, content in helpers.items():
        if not any(sec in module.lower() for sec in security_keywords):
            _helpers[module] = content

    # Grid Banana
    keyboard = []
    temp = []
    for count, key in enumerate(_helpers):
        if count % 3 == 0 and count > 0:
            keyboard.append(temp)
            temp = []
        temp.append(types.InlineKeyboardButton(text=key.title(), callback_data=f"help_callback {key}"))
    keyboard.append(temp)
    
    keyboard.append([types.InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settings_back_helper")])
    
    await CallbackQuery.edit_message_text(
        "🎸 **Music Management Commands**\n\nChoose a category below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- 2. SECURITY DOMAIN (New Modules) ---
@nand.on_callback_query(filters.regex("help_domain_security") & ~BANNED_USERS)
@languageCB
async def help_security_domain(client, CallbackQuery, _):
    await CallbackQuery.edit_message_text(
        "🛡️ **Group Security Commands**\n\nChoose a category below:",
        reply_markup=InlineKeyboardMarkup(security_help_panel(_))
    )

# --- 3. HANDLE OLD CALLBACKS (Music) ---
@nand.on_callback_query(filters.regex(r"help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = help_back_markup(_)
    
    if cb in helpers:
        await CallbackQuery.edit_message_text(
            helpers[cb], reply_markup=keyboard
        )
    else:
        await CallbackQuery.answer(_["help_7"], show_alert=True)

# --- 4. HANDLE NEW CALLBACKS (Security Texts) ---
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
    
