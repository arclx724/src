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
# CONFIGURATION COMMAND (/setdelay)
# ==========================================================
@nand.on_message(filters.command(["setdelay", "autodelete"]) & filters.group)
async def set_delay_handler(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # --- PERMISSION CHECK ---
    member = await client.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await message.reply_text("❌ Only Admins can use this.")
    
    # Check privileges if admin
    if member.status == ChatMemberStatus.ADMINISTRATOR:
        if not (member.privileges.can_change_info and member.privileges.can_delete_messages):
            return await message.reply_text("❌ You need **Change Info** & **Delete Messages** rights.")

    # --- SHOW STATUS OR HELP ---
    if len(message.command) < 2:
        status, delay = await get_media_delete_config(chat_id)
        state_text = "ON" if status else "OFF"
        return await message.reply_text(
            f"⚙️ **Auto-Delete Settings:**\n"
            f"• Status: **{state_text}**\n"
            f"• Delay: **{delay} seconds**\n\n"
            "⚠️ **Usage:**\n"
            "• `/setdelay on` or `/setdelay off`\n"
            "• `/setdelay 10 s` (Seconds)\n"
            "• `/setdelay 5 m` (Minutes)\n"
            "• `/setdelay 1 h` (Hours)"
        )

    arg1 = message.command[1].lower()

    # A. HANDLE ON/OFF
    if arg1 == "off":
        await set_media_delete_status(chat_id, False)
        return await message.reply_text("📴 **Media Auto-Delete is OFF.**")
    
    if arg1 == "on":
        await set_media_delete_status(chat_id, True)
        _, current_delay = await get_media_delete_config(chat_id)
        return await message.reply_text(f"🔛 **Media Auto-Delete is ON.**\n⏱ Current Delay: `{current_delay} seconds`")

    # B. HANDLE TIME SETTING
    if len(message.command) < 3:
        return await message.reply_text("⚠️ Unit batana zaroori hai. Ex: `/setdelay 30 s`")

    try:
        value = int(arg1)
        unit = message.command[2].lower()
    except ValueError:
        return await message.reply_text("❌ Value number honi chahiye.")

    # Calculate Seconds
    seconds = 0
    if unit.startswith("s"): # seconds
        seconds = value
    elif unit.startswith("m"): # minutes
        seconds = value * 60
    elif unit.startswith("h"): # hours
        seconds = value * 3600
    else:
        return await message.reply_text("❌ Invalid Unit! Use `s`, `m`, or `h`.")

    # Constraints
    if seconds > 86400:
        return await message.reply_text("❌ Maximum delay is **24 Hours**.")
    if seconds < 5:
            return await message.reply_text("❌ Minimum delay is **5 Seconds**.")

    # Save to DB
    await set_media_delete_delay(chat_id, seconds)
    await message.reply_text(f"✅ **Set!** All media will auto-delete after **{seconds} seconds**.")


# ==========================================================
# MEDIA WATCHER & DELETER
# ==========================================================
# Filters: Photo, Video, Document, Audio, Voice, Sticker, Animation
@nand.on_message(filters.media & filters.group, group=10)
async def media_auto_deleter(client, message: Message):
    
    # Check if Enabled
    is_enabled, delay_time = await get_media_delete_config(message.chat.id)
    
    if not is_enabled:
        return

    # Wait for the delay
    await asyncio.sleep(delay_time)

    # Delete
    try:
        await message.delete()
    except Exception:
        # Message might be already deleted or bot lost permission
        pass
      
