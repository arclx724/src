import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.utils.db import set_antiedit_status, is_antiedit_enabled
from config import SUPPORT_CHAT, BOT_USERNAME

# ======================================================
# 1. SETTINGS COMMAND (/antiedit on/off)
# ======================================================

@nand.on_message(filters.command("antiedit") & filters.group)
async def antiedit_switch(client, message: Message):
    # Admin Permission Check
    try:
        user = await client.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("❌ **Access Denied!** Only Admins can use this command.")
            return
    except:
        return

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg == "on":
            await set_antiedit_status(message.chat.id, True)
            await message.reply_text("✏️ **Anti-Edit System Enabled!**\nEdited messages will be deleted after 60 seconds.")
        elif arg == "off":
            await set_antiedit_status(message.chat.id, False)
            await message.reply_text("😌 **Anti-Edit System Disabled!**")
    else:
        await message.reply_text("Usage: `/antinsfw on` or `/antinsfw off`")

# ======================================================
# 2. WATCHER LOGIC (On Edited Message)
# ======================================================

@nand.on_edited_message(filters.group)
async def anti_edit_watcher(client, message: Message):
    chat_id = message.chat.id
    
    # 1. Check: Feature Enabled hai ya nahi?
    if not await is_antiedit_enabled(chat_id):
        return

    # 2. Check: Admin Exception (Safety ke liye)
    # Agar aap chahte hain ki ADMINS bhi edit na kar payein, toh niche ki 4 lines delete kar dein.
    try:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except:
        pass

    # 3. Send Warning Message
    text = (
        f"⚠️ **Anti-Edit Warning**\n\n"
        f"Hey {message.from_user.mention}, editing messages is strictly prohibited here!\n"
        f"⏳ **Your message will be auto-deleted in 60 seconds.**"
    )
    
    # Bot username config se ya client se le sakte hain
    bot_username = client.me.username if client.me else BOT_USERNAME
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Add Me 🛡️", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("Support", url=SUPPORT_CHAT)]
    ])

    try:
        # Warning Bhejo
        warning_msg = await message.reply_text(text, reply_markup=buttons)

        # 4. Wait for 60 Seconds
        await asyncio.sleep(60)

        # 5. Delete Messages (User's + Bot's Warning)
        await message.delete()      # User ka message delete
        await warning_msg.delete()  # Bot ka warning delete

    except Exception:
        # Agar message pehle hi delete ho gaya ho to crash na ho
        pass
      
