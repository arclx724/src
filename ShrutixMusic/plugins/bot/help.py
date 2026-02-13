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
    "admin": "**ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs :**\n\nᴊᴜsᴛ ᴀᴅᴅ **ᴄ** ɪɴ ᴛʜᴇ sᴛᴀʀᴛɪɴɢ ᴏғ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴜsᴇ ᴛʜᴇᴍ ғᴏʀ ᴄʜᴀɴɴᴇʟ.\n\n/pause : ᴩᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.\n\n/resume : ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴩᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ.\n\n/skip : sᴋɪᴩ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛ sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ɴᴇxᴛ ᴛʀᴀᴄᴋ ɪɴ ǫᴜᴇᴜᴇ.\n\n/end ᴏʀ /stop : ᴄʟᴇᴀʀs ᴛʜᴇ ǫᴜᴇᴜᴇ ᴀɴᴅ ᴇɴᴅ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.\n\n/player : ɢᴇᴛ ᴀ ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ᴩʟᴀʏᴇʀ ᴩᴀɴᴇʟ.\n\n/queue : sʜᴏᴡs ᴛʜᴇ ǫᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋs ʟɪsᴛ.",
    
    "auth": "**ᴀᴜᴛʜ ᴜsᴇʀs :**\n\nᴀᴜᴛʜ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ɪɴ ᴛʜᴇ ʙᴏᴛ ᴡɪᴛʜᴏᴜᴛ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.\n\n/auth [ᴜsᴇʀɴᴀᴍᴇ/ᴜsᴇʀ_ɪᴅ] : ᴀᴅᴅ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜ ʟɪsᴛ ᴏғ ᴛʜᴇ ʙᴏᴛ.\n/unauth [ᴜsᴇʀɴᴀᴍᴇ/ᴜsᴇʀ_ɪᴅ] : ʀᴇᴍᴏᴠᴇ ᴀ ᴀᴜᴛʜ ᴜsᴇʀs ғʀᴏᴍ ᴛʜᴇ ᴀᴜᴛʜ ᴜsᴇʀs ʟɪsᴛ.\n/authusers : sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ᴀᴜᴛʜ ᴜsᴇʀs ᴏғ ᴛʜᴇ ɢʀᴏᴜᴩ.",
    
    "broadcast": "**ʙʀᴏᴀᴅᴄᴀsᴛ ғᴇᴀᴛᴜʀᴇ** [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs] :\n\n/broadcast [ᴍᴇssᴀɢᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ] : ʙʀᴏᴀᴅᴄᴀsᴛ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.\n\n**ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴍᴏᴅᴇs :**\n**-pin** : ᴩɪɴs ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ ᴍᴇssᴀɢᴇs ɪɴ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs.\n**-pinloud** : ᴩɪɴs ʏᴏᴜʀ ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ ᴍᴇssᴀɢᴇ ɪɴ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴀɴᴅ sᴇɴᴅ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴛᴏ ᴛʜᴇ ᴍᴇᴍʙᴇʀs.\n**-user** : ʙʀᴏᴀᴅᴄᴀsᴛs ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ ᴛʜᴇ ᴜsᴇʀs ᴡʜᴏ ʜᴀᴠᴇ sᴛᴀʀᴛᴇᴅ ʏᴏᴜʀ ʙᴏᴛ.\n**-assistant** : ʙʀᴏᴀᴅᴄᴀsᴛ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛʜᴇ ᴀssɪᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ ᴏғ ᴛʜᴇ ʙᴏᴛ.\n**-nobot** : ғᴏʀᴄᴇs ᴛʜᴇ ʙᴏᴛ ᴛᴏ ɴᴏᴛ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛʜᴇ ᴍᴇssᴀɢᴇ.",
    
    "blacklist": "**ᴄʜᴀᴛ ʙʟᴀᴄᴋʟɪsᴛ ғᴇᴀᴛᴜʀᴇ :** [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs]\n\nʀᴇsᴛʀɪᴄᴛ sʜɪᴛ ᴄʜᴀᴛs ᴛᴏ ᴜsᴇ ᴏᴜʀ ᴘʀᴇᴄɪᴏᴜs ʙᴏᴛ.\n\n/blacklistchat [ᴄʜᴀᴛ ɪᴅ] : ʙʟᴀᴄᴋʟɪsᴛ ᴀ ᴄʜᴀᴛ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ.\n/whitelistchat [ᴄʜᴀᴛ ɪᴅ] : ᴡʜɪᴛᴇʟɪsᴛ ᴛʜᴇ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴄʜᴀᴛ.\n/blacklistedchat : sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴄʜᴀᴛs.",
    
    "gban": "**ɢʟᴏʙᴀʟ ʙᴀɴ ғᴇᴀᴛᴜʀᴇ** [ᴏɴʟʏ ғᴏʀ sᴜᴅᴏᴇʀs] :\n\n/gban [ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴜsᴇʀ] : ɢʟᴏʙᴀʟʟʏ ʙᴀɴs ᴛʜᴇ ᴄʜᴜᴛɪʏᴀ ғʀᴏᴍ ᴀʟʟ ᴛʜᴇ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs ᴀɴᴅ ʙʟᴀᴄᴋʟɪsᴛ ʜɪᴍ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ.\n/ungban [ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴜsᴇʀ] : ɢʟᴏʙᴀʟʟʏ ᴜɴʙᴀɴs ᴛʜᴇ ɢʟᴏʙᴀʟʟʏ ʙᴀɴɴᴇᴅ ᴜsᴇʀ.\n/gbannedusers : sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ɢʟᴏʙᴀʟʟʏ ʙᴀɴɴᴇᴅ ᴜsᴇʀs.",
    
    "loop": "**ʟᴏᴏᴘ sᴛʀᴇᴀᴍ :**\n\n**sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ**\n\n/loop [enable/disable] : ᴇɴᴀʙʟᴇs/ᴅɪsᴀʙʟᴇs ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ\n/loop [1, 2, 3, ...] : ᴇɴᴀʙʟᴇs ᴛʜᴇ ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ɢɪᴠᴇɴ ᴠᴀʟᴜᴇ.",
    
    "ping": "**ᴘɪɴɢ & sᴛᴀᴛs :**\n\n/start : sᴛᴀʀᴛs ᴛʜᴇ ᴍᴜsɪᴄ ʙᴏᴛ.\n/help : ɢᴇᴛ ʜᴇʟᴩ ᴍᴇɴᴜ ᴡɪᴛʜ ᴇxᴩʟᴀɴᴀᴛɪᴏɴ ᴏғ ᴄᴏᴍᴍᴀɴᴅs.\n\n/ping : sʜᴏᴡs ᴛʜᴇ ᴩɪɴɢ ᴀɴᴅ sʏsᴛᴇᴍ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.\n\n/stats : sʜᴏᴡs ᴛʜᴇ ᴏᴠᴇʀᴀʟʟ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.",
    
    "play": "**ᴩʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs :**\n\n**v :** sᴛᴀɴᴅs ғᴏʀ ᴠɪᴅᴇᴏ ᴩʟᴀʏ.\n**force :** sᴛᴀɴᴅs ғᴏʀ ғᴏʀᴄᴇ ᴩʟᴀʏ.\n\n/play ᴏʀ /vplay : sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ.\n\n/playforce ᴏʀ /vplayforce : sᴛᴏᴩs ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ.",
    
    "playlist": "**ᴩʟᴀʏʟɪsᴛ ᴄᴏᴍᴍᴀɴᴅs :**\n\n/playlist : sʜᴏᴡs ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴩʟᴀʏʟɪsᴛ.\n/delplaylist : ᴅᴇʟᴇᴛᴇ ᴀɴʏ sᴀᴠᴇᴅ ᴍᴜsɪᴄ ɪɴ ʏᴏᴜʀ ᴩʟᴀʏʟɪsᴛ.",
    
    "shuffle": "**sʜᴜғғʟᴇ ᴏ̨ᴜᴇᴜᴇ :**\n\n/shuffle : sʜᴜғғʟᴇ's ᴛʜᴇ ᴏ̨ᴜᴇᴜᴇ.\n/queue : sʜᴏᴡs ᴛʜᴇ sʜᴜғғʟᴇᴅ ᴏ̨ᴜᴇᴜᴇ.",
    
    "seek": "**sᴇᴇᴋ sᴛʀᴇᴀᴍ :**\n\n/seek [ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs] : sᴇᴇᴋ ᴛʜᴇ sᴛʀᴇᴀᴍ ᴛᴏ ᴛʜᴇ ɢɪᴠᴇɴ ᴅᴜʀᴀᴛɪᴏɴ.\n/seekback [ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs] : ʙᴀᴄᴋᴡᴀʀᴅ sᴇᴇᴋ ᴛʜᴇ sᴛʀᴇᴀᴍ ᴛᴏ ᴛʜᴇ ᴛʜᴇ ɢɪᴠᴇɴ ᴅᴜʀᴀᴛɪᴏɴ.",
    
    "speed": "**sᴘᴇᴇᴅ ᴄᴏᴍᴍᴀɴᴅs :**\n\nʏᴏᴜ ᴄᴀɴ ᴄᴏɴᴛʀᴏʟ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ᴏғ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ. [ᴀᴅᴍɪɴs ᴏɴʟʏ]\n\n/speed or /playback : ғᴏʀ ᴀᴅᴊᴜsᴛɪɴɢ ᴛʜᴇ ᴀᴜᴅɪᴏ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ɪɴ ɢʀᴏᴜᴘ.\n/cspeed or /cplayback : ғᴏʀ ᴀᴅᴊᴜsᴛɪɴɢ ᴛʜᴇ ᴀᴜᴅɪᴏ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ɪɴ ᴄʜᴀɴɴᴇʟ.",
    
    "telegraph": "**ᴛᴇʟᴇɢʀᴀᴩʜ :**\n\n/tgm : ɢᴇᴛ ᴛᴇʟᴇɢʀᴀᴩʜ ʟɪɴᴋ ᴏғ ʀᴇᴩʟɪᴇᴅ ᴍᴇᴅɪᴀ.",
    
    "video": "**ᴠɪᴅᴇᴏ ᴅᴏᴡɴʟᴏᴀᴅ :**\n\n/video [ǫᴜᴇʀʏ] : ᴅᴏᴡɴʟᴏᴀᴅ ᴠɪᴅᴇᴏ ғʀᴏᴍ ʏᴏᴜᴛᴜʙᴇ.",
    
    "tools": "**ᴛᴏᴏʟs :**\n\n/language : ᴄʜᴀɴɢᴇ ʙᴏᴛ ʟᴀɴɢᴜᴀɢᴇ.\n/settings : sʜᴏᴡs ᴛʜᴇ ɢʀᴏᴜᴩ sᴇᴛᴛɪɴɢs."
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
            "**🔞 ᴀɴᴛɪ-ɴsғᴡ ᴄᴏᴍᴍᴀɴᴅs :**\n\nᴋᴇᴇᴘ ʏᴏᴜʀ ɢʀᴏᴜᴘ sᴀғᴇ ғʀᴏᴍ 18+ ᴀɴᴅ ɪɴᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ᴄᴏɴᴛᴇɴᴛ.\n\n/antinsfw [on ᴏʀ enable] : ᴛᴜʀɴ ᴏɴ ᴀɴᴛɪ-ɴsғᴡ sʏsᴛᴇᴍ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.\n/antinsfw [off ᴏʀ disable] : ᴛᴜʀɴ ᴏғғ ᴀɴᴛɪ-ɴsғᴡ sʏsᴛᴇᴍ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.\n\n**ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs:**\nᴡʜᴇɴ ᴇɴᴀʙʟᴇᴅ, ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇᴛᴇᴄᴛ ᴀɴᴅ ᴅᴇʟᴇᴛᴇ ɴsғᴡ/18+ ɪᴍᴀɢᴇs ᴀɴᴅ ᴠɪᴅᴇᴏs, ᴀɴᴅ ᴘᴜɴɪsʜ ᴛʜᴇ sᴇɴᴅᴇʀ."
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
            "**🔞 ᴀɴᴛɪ-ɴsғᴡ ᴄᴏᴍᴍᴀɴᴅs :**\n\nᴋᴇᴇᴘ ʏᴏᴜʀ ɢʀᴏᴜᴘ sᴀғᴇ ғʀᴏᴍ 18+ ᴀɴᴅ ɪɴᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ᴄᴏɴᴛᴇɴᴛ.\n\n/antinsfw [on ᴏʀ enable] : ᴛᴜʀɴ ᴏɴ ᴀɴᴛɪ-ɴsғᴡ sʏsᴛᴇᴍ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.\n/antinsfw [off ᴏʀ disable] : ᴛᴜʀɴ ᴏғғ ᴀɴᴛɪ-ɴsғᴡ sʏsᴛᴇᴍ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.\n\n**ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs:**\nᴡʜᴇɴ ᴇɴᴀʙʟᴇᴅ, ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇᴛᴇᴄᴛ ᴀɴᴅ ᴅᴇʟᴇᴛᴇ ɴsғᴡ/18+ ɪᴍᴀɢᴇs ᴀɴᴅ ᴠɪᴅᴇᴏs, ᴀɴᴅ ᴘᴜɴɪsʜ ᴛʜᴇ sᴇɴᴅᴇʀ."
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
            "**🛠 ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ᴄᴏᴍᴍᴀɴᴅs :**\n\n**ʙᴀɴ/ᴋɪᴄᴋ :**\n/kick ᴏʀ /dkick : ᴋɪᴄᴋ ᴀ ᴜsᴇʀ.\n/ban ᴏʀ /dban : ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ ʙᴀɴ ᴀ ᴜsᴇʀ.\n/tban [ᴛɪᴍᴇ] : ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʙᴀɴ (ᴇ.ɢ. 1d, 1h).\n/unban : ᴜɴʙᴀɴ ᴀ ᴜsᴇʀ.\n\n**ᴍᴜᴛᴇ & ᴡᴀʀɴ :**\n/mute ᴏʀ /tmute [ᴛɪᴍᴇ] : ᴍᴜᴛᴇ ᴀ ᴜsᴇʀ.\n/unmute : ᴜɴᴍᴜᴛᴇ ᴀ ᴜsᴇʀ.\n/warn ᴏʀ /dwarn : ᴡᴀʀɴ ᴀ ᴜsᴇʀ (3 ᴡᴀʀɴs = ʙᴀɴ).\n/rmwarn : ʀᴇᴍᴏᴠᴇ ᴀ ᴡᴀʀɴɪɴɢ.\n/warns : ᴄʜᴇᴄᴋ ᴡᴀʀɴɪɴɢs.\n\n**ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟs :**\n/promote [ᴛɪᴛʟᴇ] : ᴘʀᴏᴍᴏᴛᴇ ᴜsᴇʀ ᴛᴏ ᴀᴅᴍɪɴ.\n/fullpromote : ɢɪᴠᴇ ғᴜʟʟ ᴀᴅᴍɪɴ ʀɪɢʜᴛs.\n/demote : ᴅᴇᴍᴏᴛᴇ ᴀɴ ᴀᴅᴍɪɴ.\n/set_user_title [ᴛɪᴛʟᴇ] : sᴇᴛ ᴄᴜsᴛᴏᴍ ᴀᴅᴍɪɴ ʙᴀᴅɢᴇ.\n\n**ɢʀᴏᴜᴘ ᴜᴛɪʟɪᴛɪᴇs :**\n/purge [ɴ] : ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs ɪɴ ʙᴜʟᴋ.\n/del : ᴅᴇʟᴇᴛᴇ ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ.\n/pin ᴏʀ /unpin : ᴘɪɴ/ᴜɴᴘɪɴ ᴀ ᴍᴇssᴀɢᴇ.\n/set_chat_title [ɴᴀᴍᴇ] : ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɴᴀᴍᴇ.\n/set_chat_photo : ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɪᴄᴏɴ.\n/report ᴏʀ @admins : ʀᴇᴘᴏʀᴛ ᴛᴏ ᴀᴅᴍɪɴs.\n/mentionall : ᴛᴀɢ ᴀʟʟ ᴍᴇᴍʙᴇʀs ɪɴ ɢʀᴏᴜᴘ."
        )

    try:
        await CallbackQuery.edit_message_text(
            text,
            reply_markup=security_back_markup(_),
            parse_mode=ParseMode.MARKDOWN
        )
    except MessageNotModified:
        pass










