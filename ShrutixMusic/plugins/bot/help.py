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
    "admin": "<b><u>ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\nᴊᴜsᴛ ᴀᴅᴅ <b>ᴄ</b> ɪɴ ᴛʜᴇ sᴛᴀʀᴛɪɴɢ ᴏғ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴜsᴇ ᴛʜᴇᴍ ғᴏʀ ᴄʜᴀɴɴᴇʟ.\n\n/pause : ᴩᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.\n\n/resume : ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴩᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ.\n\n/skip : sᴋɪᴩ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛ sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ɴᴇxᴛ ᴛʀᴀᴄᴋ ɪɴ ǫᴜᴇᴜᴇ.\n\n/end ᴏʀ /stop : ᴄʟᴇᴀʀs ᴛʜᴇ ǫᴜᴇᴜᴇ ᴀɴᴅ ᴇɴᴅ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.\n\n/player : ɢᴇᴛ ᴀ ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ᴩʟᴀʏᴇʀ ᴩᴀɴᴇʟ.\n\n/queue : sʜᴏᴡs ᴛʜᴇ ǫᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋs ʟɪsᴛ.",
    
    "auth": "<b><u>ᴀᴜᴛʜ ᴜsᴇʀs :</b></u>\n\nᴀᴜᴛʜ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ɪɴ ᴛʜᴇ ʙᴏᴛ ᴡɪᴛʜᴏᴜᴛ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.\n\n/auth [ᴜsᴇʀɴᴀᴍᴇ/ᴜsᴇʀ_ɪᴅ] : ᴀᴅᴅ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜ ʟɪsᴛ ᴏғ ᴛʜᴇ ʙᴏᴛ.\n/unauth [ᴜsᴇʀɴᴀᴍᴇ/ᴜsᴇʀ_ɪᴅ] : ʀᴇᴍᴏᴠᴇ ᴀ ᴀᴜᴛʜ ᴜsᴇʀs ғʀᴏᴍ ᴛʜᴇ ᴀᴜᴛʜ ᴜsᴇʀs ʟɪsᴛ.\n/authusers : sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ᴀᴜᴛʜ ᴜsᴇʀs ᴏғ ᴛʜᴇ ɢʀᴏᴜᴩ.",
    
    "broadcast": "<u><b>ʙʀᴏᴀᴅᴄᴀsᴛ ғᴇᴀᴛᴜʀᴇ</b></u> [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs] :\n\n/broadcast [ᴍᴇssᴀɢᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ] : ʙʀᴏᴀᴅᴄᴀsᴛ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.\n\n<u>ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴍᴏᴅᴇs :</u>\n<b>-pin</b> : ᴩɪɴs ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ ᴍᴇssᴀɢᴇs ɪɴ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs.\n<b>-pinloud</b> : ᴩɪɴs ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ ᴍᴇssᴀɢᴇ ɪɴ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴀɴᴅ sᴇɴᴅ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴛᴏ ᴛʜᴇ ᴍᴇᴍʙᴇʀs.\n<b>-user</b> : ʙʀᴏᴀᴅᴄᴀsᴛs ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ ᴛʜᴇ ᴜsᴇʀs ᴡʜᴏ ʜᴀᴠᴇ sᴛᴀʀᴛᴇᴅ ʏᴏᴜʀ ʙᴏᴛ.\n<b>-assistant</b> : ʙʀᴏᴀᴅᴄᴀsᴛ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛʜᴇ ᴀssɪᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ ᴏғ ᴛʜᴇ ʙᴏᴛ.\n<b>-nobot</b> : ғᴏʀᴄᴇs ᴛʜᴇ ʙᴏᴛ ᴛᴏ ɴᴏᴛ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛʜᴇ ᴍᴇssᴀɢᴇ.",
    
    "blacklist": "<u><b>ᴄʜᴀᴛ ʙʟᴀᴄᴋʟɪsᴛ ғᴇᴀᴛᴜʀᴇ :</b></u> [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs]\n\nʀᴇsᴛʀɪᴄᴛ sʜɪᴛ ᴄʜᴀᴛs ᴛᴏ ᴜsᴇ ᴏᴜʀ ᴘʀᴇᴄɪᴏᴜs ʙᴏᴛ.\n\n/blacklistchat [ᴄʜᴀᴛ ɪᴅ] : ʙʟᴀᴄᴋʟɪsᴛ ᴀ ᴄʜᴀᴛ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ.\n/whitelistchat [ᴄʜᴀᴛ ɪᴅ] : ᴡʜɪᴛᴇʟɪsᴛ ᴛʜᴇ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴄʜᴀᴛ.\n/blacklistedchat : sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴄʜᴀᴛs.",
    
    "gban": "<u><b>ɢʟᴏʙᴀʟ ʙᴀɴ ғᴇᴀᴛᴜʀᴇ</b></u> [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs] :\n\n/gban [ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴜsᴇʀ] : ɢʟᴏʙᴀʟʟʏ ʙᴀɴs ᴛʜᴇ ᴄʜᴜᴛɪʏᴀ ғʀᴏᴍ ᴀʟʟ ᴛʜᴇ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴀɴᴅ ʙʟᴀᴄᴋʟɪsᴛ ʜɪᴍ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ.\n/ungban [ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴜsᴇʀ] : ɢʟᴏʙᴀʟʟʏ ᴜɴʙᴀɴs ᴛʜᴇ ɢʟᴏʙᴀʟʟʏ ʙᴀɴɴᴇᴅ ᴜsᴇʀ.\n/gbannedusers : sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ɢʟᴏʙᴀʟʟʏ ʙᴀɴɴᴇᴅ ᴜsᴇʀs.",
    
    "loop": "<b><u>ʟᴏᴏᴘ sᴛʀᴇᴀᴍ :</b></u>\n\n<b>sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ</b>\n\n/loop [enable/disable] : ᴇɴᴀʙʟᴇs/ᴅɪsᴀʙʟᴇs ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ\n/loop [1, 2, 3, ...] : ᴇɴᴀʙʟᴇs ᴛʜᴇ ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ɢɪᴠᴇɴ ᴠᴀʟᴜᴇ.",
    
    "ping": "<b><u>ᴘɪɴɢ & sᴛᴀᴛs :</b></u>\n\n/start : sᴛᴀʀᴛs ᴛʜᴇ ᴍᴜsɪᴄ ʙᴏᴛ.\n/help : ɢᴇᴛ ʜᴇʟᴩ ᴍᴇɴᴜ ᴡɪᴛʜ ᴇxᴩʟᴀɴᴀᴛɪᴏɴ ᴏғ ᴄᴏᴍᴍᴀɴᴅs.\n\n/ping : sʜᴏᴡs ᴛʜᴇ ᴩɪɴɢ ᴀɴᴅ sʏsᴛᴇᴍ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.\n\n/stats : sʜᴏᴡs ᴛʜᴇ ᴏᴠᴇʀᴀʟʟ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.",
    
    "play": "<u><b>ᴩʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\n<b>v :</b> sᴛᴀɴᴅs ғᴏʀ ᴠɪᴅᴇᴏ ᴩʟᴀʏ.\n<b>force :</b> sᴛᴀɴᴅs ғᴏʀ ғᴏʀᴄᴇ ᴩʟᴀʏ.\n\n/play ᴏʀ /vplay : sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ.\n\n/playforce ᴏʀ /vplayforce : sᴛᴏᴩs ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ.",
    
    "playlist": "<b><u>ᴩʟᴀʏʟɪsᴛ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\n/playlist : sʜᴏᴡs ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴩʟᴀʏʟɪsᴛ.\n/delplaylist : ᴅᴇʟᴇᴛᴇ ᴀɴʏ sᴀᴠᴇᴅ ᴍᴜsɪᴄ ɪɴ ʏᴏᴜʀ ᴩʟᴀʏʟɪsᴛ.",
    
    "shuffle": "<b><u>sʜᴜғғʟᴇ ᴏ̨ᴜᴇᴜᴇ :</b></u>\n\n/shuffle : sʜᴜғғʟᴇ's ᴛʜᴇ ᴏ̨ᴜᴇᴜᴇ.\n/queue : sʜᴏᴡs ᴛʜᴇ sʜᴜғғʟᴇᴅ ᴏ̨ᴜᴇᴜᴇ.",
    
    "seek": "<b><u>sᴇᴇᴋ sᴛʀᴇᴀᴍ :</b></u>\n\n/seek [ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs] : sᴇᴇᴋ ᴛʜᴇ sᴛʀᴇᴀᴍ ᴛᴏ ᴛʜᴇ ɢɪᴠᴇɴ ᴅᴜʀᴀᴛɪᴏɴ.\n/seekback [ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs] : ʙᴀᴄᴋᴡᴀʀᴅ sᴇᴇᴋ ᴛʜᴇ sᴛʀᴇᴀᴍ ᴛᴏ ᴛʜᴇ ᴛʜᴇ ɢɪᴠᴇɴ ᴅᴜʀᴀᴛɪᴏɴ.",
    
    "speed": "<b><u>sᴘᴇᴇᴅ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\nʏᴏᴜ ᴄᴀɴ ᴄᴏɴᴛʀᴏʟ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ᴏғ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ. [ᴀᴅᴍɪɴs ᴏɴʟʏ]\n\n/speed or /playback : ғᴏʀ ᴀᴅᴊᴜsᴛɪɴɢ ᴛʜᴇ ᴀᴜᴅɪᴏ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ɪɴ ɢʀᴏᴜᴘ.\n/cspeed or /cplayback : ғᴏʀ ᴀᴅᴊᴜsᴛɪɴɢ ᴛʜᴇ ᴀᴜᴅɪᴏ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ɪɴ ᴄʜᴀɴɴᴇʟ.",
    
    "telegraph": "<b><u>ᴛᴇʟᴇɢʀᴀᴩʜ :</b></u>\n\n/tgm : ɢᴇᴛ ᴛᴇʟᴇɢʀᴀᴩʜ ʟɪɴᴋ ᴏғ ʀᴇᴩʟɪᴇᴅ ᴍᴇᴅɪᴀ.",
    
    "video": "<b><u>ᴠɪᴅᴇᴏ ᴅᴏᴡɴʟᴏᴀᴅ :</b></u>\n\n/video [ǫᴜᴇʀʏ] : ᴅᴏᴡɴʟᴏᴀᴅ ᴠɪᴅᴇᴏ ғʀᴏᴍ ʏᴏᴜᴛᴜʙᴇ.",
    
    "tools": "<b><u>ᴛᴏᴏʟs :</b></u>\n\n/language : ᴄʜᴀɴɢᴇ ʙᴏᴛ ʟᴀɴɢᴜᴀɢᴇ.\n/settings : sʜᴏᴡs ᴛʜᴇ ɢʀᴏᴜᴩ sᴇᴛᴛɪɴɢs."
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
            "> • **Trigger:** More than 10 kicks/bans in 24 hours\n"
            "• **Action:** Instant Auto-Demotion\n"
            "• **Reset:** Limits reset every 24 hours\n\n"
            "⚠️ **Important Note:**\n"
            "Only admins promoted via this bot can be auto-demoted.\n Use `/promote` and ensure the bot has 'Add Admin' permissions.\n\n"
            "**Keeping your community safe from rogue admins!**"
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






