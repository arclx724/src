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
    "admin": "⭐️ **Admin Commands:**\n\n• /pause - Pause the playing music.\n• /resume - Resume the paused music.\n• /skip - Skip the current track.\n• /stop - Stop the music and clear queue.\n• /queue - Check the current queue.",
    "auth": "🛡️ **Auth Users:**\n\nAuthorized users can use admin commands without admin rights.\n\n• /auth [Username] - Add user to auth list.\n• /unauth [Username] - Remove user.\n• /authusers - List auth users.",
    "broadcast": "**📢 Broadcast:**\n\n• /broadcast [Message] - Send message to all chats.\n• /broadcast_pin - Pin the broadcasted message.",
    "blacklist": "**🚫 Blacklist Chat:**\n\n• /blacklistchat [Chat ID] - Block bot usage in a chat.\n• /whitelistchat [Chat ID] - Unblock chat.",
    "gban": "**🌍 Global Ban:**\n\n• /gban [User] - Ban user from all bot chats.\n• /ungban [User] - Unban user.",
    "loop": "**🔁 Loop Stream:**\n\n• /loop [enable/disable] - Toggle loop.\n• /loop [1-10] - Loop specific times.",
    "ping": "**🏓 Ping & Stats:**\n\n• /ping - Check bot latency and uptime.\n• /stats - Check system statistics.",
    "play": "**▶️ Play Commands:**\n\n• /play [Song] - Play audio.\n• /vplay [Song] - Play video.\n• /playforce - Force play immediately.\n• /slider - Play slider query.",
    "playlist": "**📜 Playlist:**\n\n• /playlist - Check your saved playlist.\n• /delplaylist - Delete playlist.\n• /play - Play your playlist.",
    "shuffle": "**🔀 Shuffle:**\n\n• /shuffle - Shuffle the queue.",
    "seek": "**⏩ Seek:**\n\n• /seek [Seconds] - Forward stream.\n• /seekback [Seconds] - Rewind stream.",
    "speed": "**⚡ Speed:**\n\n• /speed [0.5/1.5/2.0] - Change playback speed.",
    "telegraph": "**🌐 Telegraph:**\n\n• /tgm - Upload replied media to Telegraph link.",
    "video": "**📹 Video Download:**\n\n• /video [Song] - Download video from YouTube.",
    "tools": "**🔧 Tools:**\n\n• /language - Change bot language.\n• /settings - Open bot settings."
}

# ======================================================
# 1. MAIN HELP COMMAND
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
        try:
            await update.edit_message_text(
                _["help_2"],
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        except MessageNotModified:
            pass
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
# 2. BACK TO START MENU
# ======================================================
@nand.on_callback_query(filters.regex("settings_back_home") & ~BANNED_USERS)
@LanguageStart
async def back_to_home_flash(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass

    out = private_panel(_)
    text = _["start_2"].format(CallbackQuery.from_user.mention, nand.mention)

    try:
        await CallbackQuery.edit_message_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(out)
        )
    except MessageNotModified:
        pass

# ======================================================
# 3. MUSIC MANAGEMENT BUTTONS
# ======================================================
@nand.on_callback_query(filters.regex("help_domain_music") & ~BANNED_USERS)
@languageCB
async def help_music_domain(client, CallbackQuery, _):
    command_list = list(FALLBACK_HELP_DICT.keys())
    keyboard, temp = [], []

    for count, key in enumerate(command_list):
        if count % 3 == 0 and count > 0:
            keyboard.append(temp)
            temp = []
        temp.append(
            InlineKeyboardButton(
                text=key.title(),
                callback_data=f"help_callback {key}"
            )
        )
    keyboard.append(temp)
    keyboard.append(
        [InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settings_back_helper")]
    )

    try:
        await CallbackQuery.edit_message_text(
            "🎸 **Music Management Commands**\n\nChoose a category below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass

# ======================================================
# 4. GROUP MANAGEMENT
# ======================================================
@nand.on_callback_query(filters.regex("help_domain_security") & ~BANNED_USERS)
@languageCB
async def help_security_domain(client, CallbackQuery, _):
    try:
        await CallbackQuery.edit_message_text(
            "🛡️ **Group Management Commands**\n\nChoose a category below:",
            reply_markup=InlineKeyboardMarkup(security_help_panel(_)),
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass

# ======================================================
# 5. SHOW COMMAND TEXT
# ======================================================
@nand.on_callback_query(filters.regex(r"help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    cb = CallbackQuery.data.split(None, 1)[1].lower()
    keyboard = help_back_markup(_)

    try:
        await CallbackQuery.edit_message_text(
            FALLBACK_HELP_DICT.get(cb, f"**{cb.title()} Commands**\n\nComing soon!"),
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass

# ======================================================
# 6. SECURITY SUB-MODULES
# ======================================================
@nand.on_callback_query(filters.regex(r"help_cmd_") & ~BANNED_USERS)
@languageCB
async def security_helper_cb(client, CallbackQuery, _):
    cmd = CallbackQuery.data.split("_")[2]
    keyboard = security_back_markup(_)
    text = ""

    if cmd == "antinuke":
        text = (
            "🛡️ **Anti-Cheater System**\n\n"
            "Protects the group from cheaters and malicious admin actions.\n\n"
            "• **Trigger:** 3 Suspicious Actions in 30 Seconds.\n"
            "• **Action:** Instant Demotion.\n\n"
            "**Commands:**\n"
            "• `/whitelist [Reply]` - Add trusted admin.\n"
            "• `/unwhitelist [Reply]` - Remove trusted admin."
        )

    try:
        await CallbackQuery.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass
