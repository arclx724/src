import re
import html
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
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

# === CONFIGURATION ===
SUPPORT_LINK = "https://t.me/ShrutiBots" 

ABUSIVE_WORDS = [
    "aand", "aandu", "ass", "asshole", "b.c", "b.k.l", "b.s.d.k", 
    "bahenchod", "bakchod", "bastard", "bc", "behenchod", "betichod", 
    "bhadua", "bhadwa", "bhenchod", "bhosad", "bhosdk", "bhosdike", 
    "bitch", "bkl", "blowjob", "boobs", "bsdk", "chut", "chutiya", 
    "cock", "cunt", "dick", "fucker", "fucking", "gaand", "gandu", 
    "haramkhor", "jhaatu", "kutta", "lauda", "loda", "lund", "madarchod", 
    "mc", "mkc", "motherfucker", "pussy", "randi", "sex", "slut", "tatte", 
    "tatti", "whore", "xxx"
]

ABUSE_PATTERN = re.compile(r'\b(' + '|'.join(map(re.escape, ABUSIVE_WORDS)) + r')\b', re.IGNORECASE)

# === CUSTOM ERROR REPLIES ===
REPLIES = {
    "NOT_ADMIN": "❌ **Access Denied:** Only Admins can use this command.",
    "NOT_SUPER_ADMIN": "⚠️ **Access Denied:** You need the **'Change Group Info'** right (Super Admin) to execute this command.",
    "BOT_NO_RIGHTS": "❗️ **Permission Error:** I don't have the right to **Delete Messages**. Please promote me properly.",
    "NO_USER_FOUND": "❓ **Format Error:** Please reply to a user, provide their `@username`, or `user_id`.",
    "BOT_ITSELF": "🤖 I cannot whitelist/unwhitelist myself!",
}

# ================= HELPER FUNCTIONS =================

async def get_user_privilege(client, chat_id, user_id):
    """Returns user's status: 'CREATOR', 'SUPER_ADMIN', 'ADMIN', or 'MEMBER'"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.OWNER:
            return "CREATOR"
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            if member.privileges and member.privileges.can_change_info:
                return "SUPER_ADMIN"
            return "ADMIN"
    except:
        pass
    return "MEMBER"

async def check_bot_rights(client, chat_id):
    """Checks if the bot has permission to delete messages"""
    try:
        bot_member = await client.get_chat_member(chat_id, client.me.id)
        if bot_member.privileges and bot_member.privileges.can_delete_messages:
            return True
    except:
        pass
    return False

async def extract_user(client, message: Message):
    """Extracts user from reply, @username, or user_id"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        arg = message.command[1]
        try:
            user = await client.get_users(arg)
            return user
        except:
            return None
    return None

# ================= MODULE COMMANDS =================

@nand.on_message(filters.command("abusecommands") & filters.group)
async def abuse_help_menu(client, message: Message):
    help_text = (
        "**🤬 Abuse Module Commands:**\n\n"
        "• `/abuse [on/off]` — Toggle the slang filter in this chat.\n"
        "• `/authabuse [@user/id/reply]` — Exempt a user from deletions **(Super Admins only)**.\n"
        "• `/unauthabuse [@user/id/reply]` — Remove exemption **(Super Admins only)**.\n"
        "• `/unauthabuse all` — Remove all users from the whitelist **(Super Admins only)**.\n"
        "• `/authlistabuse` — View all currently exempted users.\n\n"
        "*(Note: 'Super Admin' means you must have 'Change Group Info' rights)*"
    )
    await message.reply_text(help_text)

@nand.on_message(filters.command("abuse") & filters.group)
async def toggle_abuse(client, message: Message):
    privilege = await get_user_privilege(client, message.chat.id, message.from_user.id)
    if privilege in ["MEMBER"]:
        return await message.reply_text(REPLIES["NOT_ADMIN"])

    if not await check_bot_rights(client, message.chat.id):
        return await message.reply_text(REPLIES["BOT_NO_RIGHTS"])

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["on", "enable", "yes"]:
            new_status = True
        elif arg in ["off", "disable", "no"]:
            new_status = False
        else:
            return await message.reply_text("💡 **Usage:** `/abuse on` or `/abuse off`")
    else:
        current = await is_abuse_enabled(message.chat.id)
        new_status = not current
    
    await set_abuse_status(message.chat.id, new_status)
    state = "Enabled ✅" if new_status else "Disabled ❌"
    await message.reply_text(f"🛡 **Slang Filter has been {state}**")


@nand.on_message(filters.command("authabuse") & filters.group)
async def auth_abuse_user(client, message: Message):
    privilege = await get_user_privilege(client, message.chat.id, message.from_user.id)
    if privilege in ["MEMBER", "ADMIN"]: # Standard admins are blocked
        return await message.reply_text(REPLIES["NOT_SUPER_ADMIN"])

    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(REPLIES["NO_USER_FOUND"])
    if user.id == client.me.id:
        return await message.reply_text(REPLIES["BOT_ITSELF"])

    await abuse_whitelist_user(message.chat.id, user.id)
    await message.reply_text(f"✅ {user.mention} has been **exempted** from the slang filter.")


@nand.on_message(filters.command("unauthabuse") & filters.group)
async def unauth_abuse_user(client, message: Message):
    privilege = await get_user_privilege(client, message.chat.id, message.from_user.id)
    if privilege in ["MEMBER", "ADMIN"]: # Standard admins are blocked
        return await message.reply_text(REPLIES["NOT_SUPER_ADMIN"])

    # Check for Bulk Remove ("/unauthabuse all")
    if len(message.command) == 2 and message.command[1].lower() == "all":
        users = await get_abuse_whitelisted_users(message.chat.id)
        if not users:
            return await message.reply_text("📂 The whitelist is already empty.")
        
        # Safe way to clear all users via existing DB logic
        for uid in users:
            await abuse_unwhitelist_user(message.chat.id, uid)
        return await message.reply_text("🧹 **All users have been removed** from the exemption list.")

    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(REPLIES["NO_USER_FOUND"])

    await abuse_unwhitelist_user(message.chat.id, user.id)
    await message.reply_text(f"🚫 {user.mention}'s exemption has been **removed**.")


@nand.on_message(filters.command("authlistabuse") & filters.group)
async def auth_abuse_list(client, message: Message):
    privilege = await get_user_privilege(client, message.chat.id, message.from_user.id)
    if privilege in ["MEMBER"]:
        return await message.reply_text(REPLIES["NOT_ADMIN"])

    users = await get_abuse_whitelisted_users(message.chat.id)
    if not users:
        return await message.reply_text("📂 The abuse whitelist is currently empty.")
    
    text = "📋 **Abuse Exempted Users:**\n\n"
    for uid in users:
        try:
            u = await client.get_users(uid)
            text += f"• {u.mention} (`{uid}`)\n"
        except:
            text += f"• ID: `{uid}`\n"
    await message.reply_text(text)


# ================= WATCHER LOGIC =================

@nand.on_message(filters.group & ~filters.bot & ~filters.service, group=12)
async def abuse_watcher(client, message: Message):
    text = message.text or message.caption
    if not text:
        return

    if not await is_abuse_enabled(message.chat.id):
        return

    # User in whitelist?
    if await is_abuse_whitelisted(message.chat.id, message.from_user.id):
        return

    if ABUSE_PATTERN.search(text):
        try:
            # Check bot rights silently before trying to delete
            if not await check_bot_rights(client, message.chat.id):
                return 

            await message.delete()
            
            safe_text = html.escape(text)
            censored_text = ABUSE_PATTERN.sub(lambda m: f"<spoiler>{m.group(0)}</spoiler>", safe_text)
            
            bot_username = client.me.username if client.me else BOT_USERNAME

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{bot_username}?startgroup=true"),
                    InlineKeyboardButton("📢 Support", url=SUPPORT_LINK)
                ]
            ])

            warning_text = (
                f"🚫 Hey {message.from_user.mention}, your message was removed.\n\n"
                f"🔍 <b>Censored:</b>\n"
                f"{censored_text}\n\n"
                f"Please keep the chat respectful."
            )

            sent = await message.reply_text(
                warning_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
            
            # Exactly 60 seconds baad message auto delete
            await asyncio.sleep(60)
            await sent.delete()
            
        except Exception:
            pass
            
