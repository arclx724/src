import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ShrutixMusic import nand
from config import BOT_USERNAME
from ShrutixMusic.utils.db import (
    is_abuse_enabled,
    set_abuse_status,
    abuse_whitelist_user,
    abuse_unwhitelist_user,
    is_abuse_whitelisted,
    get_abuse_whitelisted_users
)

# --- Abusive Words List ---
ABUSIVE_WORDS = [
    "aand", "aandu", "ass", "asshole", "b.c", "b.k.l", "b.s.d.k", 
    "bahenchod", "bakchod", "bastard", "bc", "behenchod", "betichod", 
    "bhadua", "bhadwa", "bhenchod", "bhosad", "bhosdk", "bhosdike", 
    "bitch", "bkl", "blowjob", "boobs", "bsdk", "chut", "chutiya", 
    "cock", "cunt", "dick", "fucker", "fucking", "gaand", "gandu", 
    "haramkhor", "jhaatu", "kutta", "lauda", "loda", "lund", "madarchod", 
    "mc", "mkc", "motherfucker", "pussy", "randi", "sex", "slut", "tatte", 
    "tatti", "whore", "xxx"
    # Aap apni poori list yahan add kar sakte hain
]

# Pre-compile Regex for speed
ABUSE_PATTERN = re.compile(r'\b(' + '|'.join(map(re.escape, ABUSIVE_WORDS)) + r')\b', re.IGNORECASE)

# ================= HELPER FUNCTIONS =================

async def is_admin(chat_id, user_id, client):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

# ================= COMMANDS =================

@nand.on_message(filters.command("abuse") & filters.group)
async def toggle_abuse(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply_text("❌ Only admins can use this command.")

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["on", "enable", "yes"]:
            new_status = True
        elif arg in ["off", "disable", "no"]:
            new_status = False
        else:
            return await message.reply_text("Usage: `/abuse on` or `/abuse off`")
    else:
        current = await is_abuse_enabled(message.chat.id)
        new_status = not current
    
    await set_abuse_status(message.chat.id, new_status)
    state = "Enabled ✅" if new_status else "Disabled ❌"
    await message.reply_text(f"🛡 Abuse protection is now {state}")

@nand.on_message(filters.command(["auth", "allow"]) & filters.group)
async def auth_user(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to auth them.")

    target = message.reply_to_message.from_user
    await abuse_whitelist_user(message.chat.id, target.id)
    await message.reply_text(f"✅ {target.mention} is now whitelisted from abuse filter.")

@nand.on_message(filters.command(["unauth", "disallow"]) & filters.group)
async def unauth_user(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to un-auth them.")

    target = message.reply_to_message.from_user
    await abuse_unwhitelist_user(message.chat.id, target.id)
    await message.reply_text(f"🚫 {target.mention} removed from whitelist.")

@nand.on_message(filters.command("authlist") & filters.group)
async def auth_list(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return

    users = await get_abuse_whitelisted_users(message.chat.id)
    if not users:
        return await message.reply_text("📂 Whitelist is empty.")
    
    text = "📋 **Abuse Whitelisted Users:**\n"
    for uid in users:
        try:
            u = await client.get_users(uid)
            text += f"- {u.mention}\n"
        except:
            text += f"- ID: {uid}\n"
    await message.reply_text(text)

# ================= WATCHER LOGIC =================

@nand.on_message(filters.group & ~filters.bot & ~filters.service, group=12)
async def abuse_watcher(client, message: Message):
    text = message.text or message.caption
    if not text:
        return

    # 1. Check if Enabled
    if not await is_abuse_enabled(message.chat.id):
        return

    # 2. Check Whitelist
    if await is_abuse_whitelisted(message.chat.id, message.from_user.id):
        return

    # 3. Local Regex Check
    if ABUSE_PATTERN.search(text):
        try:
            await message.delete()
            
            bot_username = client.me.username if client.me else BOT_USERNAME

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{bot_username}?startgroup=true")
                ]
            ])

            warning_text = (
                f"🚫 {message.from_user.mention}, your message was removed.\n"
                f"⚠️ **Reason:** Profanity/Abuse Detected."
            )

            sent = await message.reply_text(
                warning_text,
                reply_markup=buttons
            )
            
            # 10 Seconds baad warning delete
            await asyncio.sleep(10)
            await sent.delete()
            
        except Exception:
            # Agar bot ke paas delete permission nahi hai
            pass
            
