import asyncio
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.utils.db import set_antiedit_status, is_antiedit_enabled
from config import SUPPORT_CHAT, BOT_USERNAME

# ======================================================
# CONFIG
# ======================================================

DELETE_DELAY = 60  # seconds before deleting edited message + bot warning
ADMIN_CACHE = {}   # Cache for admin users per chat

# ======================================================
# RANDOM WARNING MESSAGES
# ======================================================

ANTI_EDIT_REPLIES = [
    "⚠️ {user}, editing messages is not allowed here!\n⏳ Your message will be deleted in 60 seconds.",
    "🚫 Nice try {user}!\nEditing messages won't work in this group.\n⏳ Deleting soon...",
    "🛑 {user}, stealth editing detected!\nAnti-Edit is enabled here.\n⏳ Auto delete in 60 seconds.",
    "❌ {user}, message editing is disabled here.\n⏳ Please wait while I remove it.",
    "👀 {user}, trying to edit huh?\nNot allowed here!\n⏳ Deleting in 60 seconds."
]

# ======================================================
# ADMIN CHECK (CACHED)
# ======================================================

async def is_admin(client, chat_id, user_id):
    if chat_id not in ADMIN_CACHE:
        try:
            admins = await client.get_chat_members(chat_id, filter="administrators")
            ADMIN_CACHE[chat_id] = {admin.user.id for admin in admins}
        except:
            return False
    return user_id in ADMIN_CACHE[chat_id]

# ======================================================
# COMMAND: /antiedit on/off
# ======================================================

@nand.on_message(filters.command("antiedit") & filters.group)
async def antiedit_switch(client, message: Message):
    try:
        if not await is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ Only admins can use this command.")
    except:
        return await message.reply_text("❌ Could not verify admin status.")

    if len(message.command) < 2:
        return await message.reply_text(
            "⚙️ Usage:\n"
            "/antiedit on - Enable Anti-Edit\n"
            "/antiedit off - Disable Anti-Edit"
        )

    arg = message.command[1].lower()

    if arg == "on":
        await set_antiedit_status(message.chat.id, True)
        await message.reply_text("✅ Anti-Edit Enabled!")
    elif arg == "off":
        await set_antiedit_status(message.chat.id, False)
        await message.reply_text("❌ Anti-Edit Disabled!")
    else:
        await message.reply_text("❌ Invalid option. Use `on` or `off`.")

# ======================================================
# BACKGROUND DELETE FUNCTION
# ======================================================

async def delete_later(user_msg, warning_msg):
    await asyncio.sleep(DELETE_DELAY)
    try:
        await user_msg.delete()
    except:
        pass
    try:
        await warning_msg.delete()
    except:
        pass

# ======================================================
# WATCHER: ON EDITED MESSAGE
# ======================================================

@nand.on_edited_message(filters.group)
async def anti_edit_watcher(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Feature enabled?
    if not await is_antiedit_enabled(chat_id):
        return

    # Ignore admins
    try:
        if await is_admin(client, chat_id, user_id):
            return
    except:
        pass

    # Pick a random warning
    reply_text = random.choice(ANTI_EDIT_REPLIES).format(
        user=message.from_user.mention
    )

    bot_username = client.me.username if client.me else BOT_USERNAME

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("Support", url=SUPPORT_CHAT)]
    ])

    try:
        # Send warning message
        warning = await message.reply_text(reply_text, reply_markup=buttons)

        # Non-blocking delete after DELETE_DELAY
        asyncio.create_task(delete_later(message, warning))
    except:
        pass
