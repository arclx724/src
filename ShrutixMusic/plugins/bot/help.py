from typing import Union
from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified

from ShrutixMusic import nand
from ShrutixMusic.utils.decorators.language import LanguageStart, languageCB
from ShrutixMusic.utils.inline.help import (
    private_help_panel,
    help_back_markup,
    security_help_panel,
    security_back_markup
)
from ShrutixMusic.utils.inline import private_panel
from config import BANNED_USERS, START_IMG_URL

# --- HARDCODED HELP TEXT ---
FALLBACK_HELP_DICT = {
    "admin": "⭐️ **Admin Commands:**\n\n• /pause\n• /resume\n• /skip\n• /stop\n• /queue",
    "auth": "🛡️ **Auth Users:**\n\n• /auth\n• /unauth\n• /authusers",
    "broadcast": "📢 **Broadcast:**\n\n• /broadcast\n• /broadcast_pin",
    "blacklist": "🚫 **Blacklist Chat:**\n\n• /blacklistchat\n• /whitelistchat",
    "gban": "🌍 **Global Ban:**\n\n• /gban\n• /ungban",
    "loop": "🔁 **Loop:**\n\n• /loop",
    "ping": "🏓 **Ping & Stats:**\n\n• /ping\n• /stats",
    "play": "▶️ **Play:**\n\n• /play\n• /vplay\n• /playforce",
    "playlist": "📜 **Playlist:**\n\n• /playlist\n• /delplaylist",
    "shuffle": "🔀 **Shuffle:**\n\n• /shuffle",
    "seek": "⏩ **Seek:**\n\n• /seek\n• /seekback",
    "speed": "⚡ **Speed:**\n\n• /speed",
    "telegraph": "🌐 **Telegraph:**\n\n• /tgm",
    "video": "📹 **Video:**\n\n• /video",
    "tools": "🔧 **Tools:**\n\n• /language\n• /settings"
}

# ======================================================
# 1. MAIN HELP
# ======================================================
@nand.on_message(filters.command("help") & filters.private & ~BANNED_USERS)
@nand.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
@LanguageStart
async def helper_private(client, update: Union[types.Message, types.CallbackQuery], _):
    if isinstance(update, types.CallbackQuery):
        try:
            await update.answer()
            await update.edit_message_text(
                _["help_2"],
                reply_markup=InlineKeyboardMarkup(private_help_panel(_)),
                parse_mode=ParseMode.MARKDOWN
            )
        except MessageNotModified:
            pass
    else:
        try:
            await update.delete()
        except:
            pass
        await update.reply_photo(
            photo=START_IMG_URL,
            caption=_["help_2"],
            reply_markup=InlineKeyboardMarkup(private_help_panel(_))
        )

# ======================================================
# 2. BACK TO HOME
# ======================================================
@nand.on_callback_query(filters.regex("settings_back_home") & ~BANNED_USERS)
@LanguageStart
async def back_to_home_flash(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
        await CallbackQuery.edit_message_caption(
            caption=_["start_2"].format(
                CallbackQuery.from_user.mention, nand.mention
            ),
            reply_markup=InlineKeyboardMarkup(private_panel(_))
        )
    except MessageNotModified:
        pass

# ======================================================
# 3. MUSIC DOMAIN
# ======================================================
@nand.on_callback_query(filters.regex("help_domain_music") & ~BANNED_USERS)
@languageCB
async def help_music_domain(client, CallbackQuery, _):
    keyboard, row = [], []
    for i, key in enumerate(FALLBACK_HELP_DICT):
        if i % 3 == 0 and row:
            keyboard.append(row)
            row = []
        row.append(
            InlineKeyboardButton(
                key.title(), callback_data=f"help_callback {key}"
            )
        )
    keyboard.append(row)
    keyboard.append(
        [InlineKeyboardButton(_["BACK_BUTTON"], callback_data="settings_back_helper")]
    )

    try:
        await CallbackQuery.edit_message_text(
            "🎸 **Music Management Commands**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass

# ======================================================
# 4. SECURITY DOMAIN
# ======================================================
@nand.on_callback_query(filters.regex("help_domain_security") & ~BANNED_USERS)
@languageCB
async def help_security_domain(client, CallbackQuery, _):
    try:
        await CallbackQuery.edit_message_text(
            "🛡️ **Group Management Commands**",
            reply_markup=InlineKeyboardMarkup(security_help_panel(_)),
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass

# ======================================================
# 5. MUSIC HELP CALLBACK
# ======================================================
@nand.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    cb = CallbackQuery.data.split(None, 1)[1]
    try:
        await CallbackQuery.edit_message_text(
            FALLBACK_HELP_DICT.get(cb, "Coming soon"),
            reply_markup=help_back_markup(_),
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass

# ======================================================
# 6. SECURITY SUB MODULES
# ======================================================
@nand.on_callback_query(filters.regex("help_cmd_") & ~BANNED_USERS)
@languageCB
async def security_helper_cb(client, CallbackQuery, _):
    cmd = CallbackQuery.data.split("_")[2]
    text = ""

    if cmd == "antinuke":
        text = (
            "🛡️ **Advanced Anti-Cheater System**\n\n"
            "This system works **automatically** to protect your group from mass-banning and abusive admin actions.\n\n"
            "• **Trigger:** More than 10 kicks/bans in 24 hours\n"
            "• **Action:** Instant Auto-Demotion\n"
            "• **Reset:** Limits reset every 24 hours\n\n"
            "⚠️ **Important Note:**\n"
            "Only admins promoted via this bot can be auto-demoted. Use `/promote` and ensure the bot has 'Add Admin' permissions.\n\n"
            "*Keeping your community safe from rogue admins!*"
        )

    elif cmd == "antibot":
        text = (
            "🤖 **Anti-Bot System**\n\n"
            "**Commands:**\n"
            "• `/nobots on`\n"
            "• `/nobots off`"
        )

    elif cmd == "abuse":
        text = (
            "🤬 **Anti-Abuse (AI)**\n\n"
            "**Commands:**\n"
            "• `/abuse on`\n"
            "• `/abuse off`"
        )

    elif cmd == "antinsfw":
        text = (
            "🔞 **Anti-NSFW**\n\n"
            "**Commands:**\n"
            "• `/antinsfw on`\n"
            "• `/antinsfw off`"
        )

    elif cmd == "antiedit":
        text = (
            "✏️ **Anti-Edit**\n\n"
            "**Commands:**\n"
            "• `/antiedit on`\n"
            "• `/antiedit off`"
        )

    elif cmd == "autodelete":
        text = (
            "🗑️ **Auto Delete**\n\n"
            "**Commands:**\n"
            "• `/setdelay 30 s`"
        )

    elif cmd == "management":
        text = (
            "👮 **Group Management**\n\n"
            "**Commands:**\n"
            "• `/ban` / `/unban`\n"
            "• `/kick`\n"
            "• `/mute` / `/unmute`"
        )

    try:
        await CallbackQuery.edit_message_text(
            text,
            reply_markup=security_back_markup(_),
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass


