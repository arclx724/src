import time
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BANNED_USERS
from config import OWNER_ID
from ShrutixMusic import nand
from ShrutixMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from ShrutixMusic.utils.decorators.language import LanguageStart
from ShrutixMusic.utils.inline import help_pannel, private_panel, start_panel
from strings import get_string

@nand.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_, True)
            return await message.reply_text(
                _["help_1"].format(config.SUPPORT_CHAT), reply_markup=keyboard
            )
        if name[0:3] == "sud":
            await sudo_menu(client, message, _ if _ else "en")
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched_text = f"""
**🔍 Track Information**

**Title:** {title}
**Duration:** {duration} Mins
**Views:** {views}
**Published:** {published}
**Channel:** {channel}
**Link:** [Watch on YouTube]({link})

__Powered by {nand.mention}__
"""
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="🎥 Watch", url=link),
                        InlineKeyboardButton(text="🔄 Close", callback_data="close"),
                    ],
                ]
            )
            await m.delete()
            await message.reply_photo(
                photo=thumbnail,
                caption=searched_text,
                reply_markup=key,
            )
            return
    
    # Normal Start Message
    out = private_panel(_)
    await message.reply_text(
        _["start_2"].format(message.from_user.mention, nand.mention),
        reply_markup=InlineKeyboardMarkup(out),
    )


@nand.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - nand.start_time)
    await message.reply_text(
        _["start_1"].format(nand.mention, uptime),
        reply_markup=InlineKeyboardMarkup(out),
    )
    await add_served_chat(message.chat.id)
    print(ex)


