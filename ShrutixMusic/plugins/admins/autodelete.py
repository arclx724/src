import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.utils.db import (
    set_media_delete_status,
    set_media_delete_delay,
    get_media_delete_config
)

# ==========================================================
# CACHE SYSTEM
# ==========================================================
AUTO_DELETE_CACHE = {}

async def get_cached_config(chat_id: int):
    if chat_id in AUTO_DELETE_CACHE:
        return AUTO_DELETE_CACHE[chat_id]

    config = await get_media_delete_config(chat_id)
    AUTO_DELETE_CACHE[chat_id] = config
    return config


async def update_cache(chat_id: int, status=None, delay=None):
    current_status, current_delay = await get_cached_config(chat_id)

    if status is None:
        status = current_status
    if delay is None:
        delay = current_delay

    AUTO_DELETE_CACHE[chat_id] = (status, delay)


# ==========================================================
# FORMAT TIME
# ==========================================================
def format_time(seconds: int):
    if seconds >= 3600:
        return f"{seconds // 3600} Hour(s)"
    elif seconds >= 60:
        return f"{seconds // 60} Minute(s)"
    return f"{seconds} Second(s)"


# ==========================================================
# /SETDELAY COMMAND
# ==========================================================
@nand.on_message(filters.command(["setdelay"]) & filters.group)
async def set_delay_handler(client, message: Message):

    chat_id = message.chat.id
    user_id = message.from_user.id

    member = await client.get_chat_member(chat_id, user_id)

    # ------------------------------------------------------
    # NON ADMIN
    # ------------------------------------------------------
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await message.reply_text(
            "❌ **Access Denied!**\n"
            "Only group admins can use this command."
        )

    # ------------------------------------------------------
    # ADMIN BUT NO PRIVILEGES
    # ------------------------------------------------------
    if member.status == ChatMemberStatus.ADMINISTRATOR:
        if not member.privileges:
            return await message.reply_text(
                "⚠️ Unable to verify your admin privileges."
            )

        if not member.privileges.can_change_info:
            return await message.reply_text(
                "❌ You need **Change Group Info** permission to modify auto delete settings."
            )

        if not member.privileges.can_delete_messages:
            return await message.reply_text(
                "❌ You need **Delete Messages** permission to use auto delete."
            )

    # ------------------------------------------------------
    # BOT PERMISSION CHECK
    # ------------------------------------------------------
    bot_member = await client.get_chat_member(chat_id, "me")

    if not (bot_member.privileges and bot_member.privileges.can_delete_messages):
        return await message.reply_text(
            "⚠️ I need **Delete Messages** permission to work properly."
        )

    # ------------------------------------------------------
    # SHOW STATUS
    # ------------------------------------------------------
    if len(message.command) == 1:
        status, delay = await get_cached_config(chat_id)
        state = "ON" if status else "OFF"

        return await message.reply_text(
            f"⚙️ **Auto Delete Settings**\n\n"
            f"• Status: **{state}**\n"
            f"• Delay: **{format_time(delay)}**\n\n"
            "Usage:\n"
            "`/setdelay 10 s`\n"
            "`/setdelay 5 m`\n"
            "`/setdelay 1 h`\n"
            "`/setdelay off`"
        )

    arg1 = message.command[1].lower()

    # ------------------------------------------------------
    # TURN OFF
    # ------------------------------------------------------
    if arg1 == "off":
        await set_media_delete_status(chat_id, False)
        await update_cache(chat_id, status=False)

        return await message.reply_text(
            "📴 **Auto Delete Disabled Successfully.**"
        )

    # ------------------------------------------------------
    # INVALID FORMAT CHECK
    # ------------------------------------------------------
    if len(message.command) < 3:
        return await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Example:\n"
            "`/setdelay 10 s`\n"
            "`/setdelay 5 m`\n"
            "`/setdelay 1 h`"
        )

    try:
        value = int(arg1)
        unit = message.command[2].lower()
    except ValueError:
        return await message.reply_text(
            "❌ Delay value must be a number.\nExample: `/setdelay 10 s`"
        )

    if value <= 0:
        return await message.reply_text(
            "❌ Delay must be greater than 0."
        )

    seconds = 0

    if unit.startswith("s"):
        seconds = value
    elif unit.startswith("m"):
        seconds = value * 60
    elif unit.startswith("h"):
        seconds = value * 3600
    else:
        return await message.reply_text(
            "❌ Invalid time unit.\nUse `s` (seconds), `m` (minutes), or `h` (hours)."
        )

    # LIMIT CHECK
    if seconds < 5:
        return await message.reply_text(
            "❌ Minimum allowed delay is 5 seconds."
        )

    if seconds > 86400:
        return await message.reply_text(
            "❌ Maximum allowed delay is 24 hours."
        )

    # SAVE SETTINGS
    await set_media_delete_delay(chat_id, seconds)
    await set_media_delete_status(chat_id, True)
    await update_cache(chat_id, status=True, delay=seconds)

    return await message.reply_text(
        f"✅ **Auto Delete Enabled Successfully!**\n"
        f"⏱ Media will delete after **{format_time(seconds)}**"
    )


# ==========================================================
# BACKGROUND DELETE
# ==========================================================
async def delete_later(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass


# ==========================================================
# MEDIA WATCHER
# ==========================================================
MEDIA_FILTER = (
    filters.photo |
    filters.video |
    filters.document |
    filters.audio |
    filters.voice |
    filters.sticker |
    filters.animation
)

@nand.on_message(MEDIA_FILTER & filters.group, group=10)
async def media_auto_deleter(client, message: Message):

    chat_id = message.chat.id

    is_enabled, delay_time = await get_cached_config(chat_id)

    if not is_enabled:
        return

    bot_member = await client.get_chat_member(chat_id, "me")

    if not (bot_member.privileges and bot_member.privileges.can_delete_messages):
        return

    asyncio.create_task(delete_later(message, delay_time))
