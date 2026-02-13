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
SUPPORT_LINK = "https://t.me/RoboKaty" 

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

# 🚀 OPT 1: Optimized Regex (Better than \b for special chars)
ABUSE_PATTERN = re.compile(
    r'(?<!\w)(' + '|'.join(map(re.escape, ABUSIVE_WORDS)) + r')(?!\w)',
    re.IGNORECASE
)

# 🚀 OPT 2 & 3: RAM CACHES (To save DB Loads)
ABUSE_CACHE = {}      # Format -> { chat_id: bool }
WHITELIST_CACHE = {}  # Format -> { chat_id: set(user_ids) }

# === CUSTOM ERROR REPLIES ===
REPLIES = {
    "NOT_ADMIN": "❌ <b>Access Denied:</b> Only Admins can use this command.",
    "NOT_SUPER_ADMIN": "⚠️ <b>Access Denied:</b> You need the <b>'Change Group Info'</b> right (Super Admin) to execute this command.",
    "BOT_NO_RIGHTS": "❗️ <b>Permission Error:</b> I don't have the right to <b>Delete Messages</b>. Please promote me properly.",
    "NO_USER_FOUND": "❓ <b>Format Error:</b> Please reply to a user, provide their <code>@username</code>, or <code>user_id</code>.",
    "BOT_ITSELF": "🤖 I cannot whitelist/unwhitelist myself!",
}

# ================= HELPER FUNCTIONS =================

# 🚀 OPT 4: Unified get_member call to save Telegram API limits
async def get_member(client, chat_id, user_id):
    if not user_id:
        return None
    try:
        return await client.get_chat_member(chat_id, user_id)
    except:
        return None

async def get_user_privilege(client, chat_id, user_id):
    if not user_id:
        return "ADMIN" # Anonymous Admins
        
    member = await get_member(client, chat_id, user_id)
    if member:
        if member.status == ChatMemberStatus.OWNER:
            return "CREATOR"
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            if member.privileges and member.privileges.can_change_info:
                return "SUPER_ADMIN"
            return "ADMIN"
    return "MEMBER"

async def check_bot_rights(client, chat_id):
    bot_member = await get_member(client, chat_id, client.me.id)
    if bot_member and bot_member.privileges and bot_member.privileges.can_delete_messages:
        return True
    return False

async def extract_user(client, message: Message):
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

# --- Cache Loaders ---
async def is_abuse_on(chat_id):
    if chat_id not in ABUSE_CACHE:
        ABUSE_CACHE[chat_id] = await is_abuse_enabled(chat_id)
    return ABUSE_CACHE[chat_id]

async def load_whitelist_cache(chat_id):
    if chat_id not in WHITELIST_CACHE:
        users = await get_abuse_whitelisted_users(chat_id)
        WHITELIST_CACHE[chat_id] = set(users) if users else set()
    return WHITELIST_CACHE[chat_id]

async def is_whitelisted(chat_id, user_id):
    cache = await load_whitelist_cache(chat_id)
    return user_id in cache

# ================= MODULE COMMANDS =================

@nand.on_message(filters.command("abusecommands") & filters.group)
async def abuse_help_menu(client, message: Message):
    help_text = (
        "<b>🤬 Abuse Module Commands:</b>\n\n"
        "• <code>/abuse [on/off]</code> — Toggle the slang filter in this chat.\n"
        "• <code>/authabuse [@user/id/reply]</code> — Exempt a user from deletions <b>(Super Admins only)</b>.\n"
        "• <code>/unauthabuse [@user/id/reply]</code> — Remove exemption <b>(Super Admins only)</b>.\n"
        "• <code>/unauthabuse all</code> — Remove all users from the whitelist <b>(Super Admins only)</b>.\n"
        "• <code>/authlistabuse</code> — View all currently exempted users.\n\n"
        "<i>*(Note: 'Super Admin' means you must have 'Change Group Info' rights)*</i>"
    )
    await message.reply_text(help_text, parse_mode=ParseMode.HTML)

@nand.on_message(filters.command("abuse") & filters.group)
async def toggle_abuse(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    privilege = await get_user_privilege(client, message.chat.id, user_id)
    
    if privilege in ["MEMBER"]:
        return await message.reply_text(REPLIES["NOT_ADMIN"], parse_mode=ParseMode.HTML)

    if not await check_bot_rights(client, message.chat.id):
        return await message.reply_text(REPLIES["BOT_NO_RIGHTS"], parse_mode=ParseMode.HTML)

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["on", "enable", "yes"]:
            new_status = True
        elif arg in ["off", "disable", "no"]:
            new_status = False
        else:
            return await message.reply_text("💡 <b>Usage:</b> <code>/abuse on</code> or <code>/abuse off</code>", parse_mode=ParseMode.HTML)
    else:
        current = await is_abuse_on(message.chat.id)
        new_status = not current
    
    # Update DB AND Cache
    await set_abuse_status(message.chat.id, new_status)
    ABUSE_CACHE[message.chat.id] = new_status
    
    state = "Enabled ✅" if new_status else "Disabled ❌"
    await message.reply_text(f"🛡 <b>Slang Filter has been {state}</b>", parse_mode=ParseMode.HTML)


@nand.on_message(filters.command("authabuse") & filters.group)
async def auth_abuse_user(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    privilege = await get_user_privilege(client, message.chat.id, user_id)
    
    if privilege in ["MEMBER", "ADMIN"]: 
        return await message.reply_text(REPLIES["NOT_SUPER_ADMIN"], parse_mode=ParseMode.HTML)

    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(REPLIES["NO_USER_FOUND"], parse_mode=ParseMode.HTML)
    if user.id == client.me.id:
        return await message.reply_text(REPLIES["BOT_ITSELF"], parse_mode=ParseMode.HTML)

    # Update DB AND Cache
    await abuse_whitelist_user(message.chat.id, user.id)
    cache = await load_whitelist_cache(message.chat.id)
    cache.add(user.id)
    
    await message.reply_text(f"✅ {user.mention} has been <b>exempted</b> from the slang filter.", parse_mode=ParseMode.HTML)


@nand.on_message(filters.command("unauthabuse") & filters.group)
async def unauth_abuse_user(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    privilege = await get_user_privilege(client, message.chat.id, user_id)
    
    if privilege in ["MEMBER", "ADMIN"]: 
        return await message.reply_text(REPLIES["NOT_SUPER_ADMIN"], parse_mode=ParseMode.HTML)

    # Bulk Remove
    if len(message.command) == 2 and message.command[1].lower() == "all":
        users = await get_abuse_whitelisted_users(message.chat.id)
        if not users:
            return await message.reply_text("📂 The whitelist is already empty.", parse_mode=ParseMode.HTML)
        
        # Update DB AND Cache
        for uid in users:
            await abuse_unwhitelist_user(message.chat.id, uid)
        WHITELIST_CACHE[message.chat.id] = set()
        
        return await message.reply_text("🧹 <b>All users have been removed</b> from the exemption list.", parse_mode=ParseMode.HTML)

    # Single Remove
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(REPLIES["NO_USER_FOUND"], parse_mode=ParseMode.HTML)

    # Update DB AND Cache
    await abuse_unwhitelist_user(message.chat.id, user.id)
    cache = await load_whitelist_cache(message.chat.id)
    cache.discard(user.id)
    
    await message.reply_text(f"🚫 {user.mention}'s exemption has been <b>removed</b>.", parse_mode=ParseMode.HTML)


@nand.on_message(filters.command("authlistabuse") & filters.group)
async def auth_abuse_list(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    privilege = await get_user_privilege(client, message.chat.id, user_id)
    
    if privilege in ["MEMBER"]:
        return await message.reply_text(REPLIES["NOT_ADMIN"], parse_mode=ParseMode.HTML)

    # Read from Cache
    users = await load_whitelist_cache(message.chat.id)
    if not users:
        return await message.reply_text("📂 The abuse whitelist is currently empty.", parse_mode=ParseMode.HTML)
    
    text = "📋 <b>Abuse Exempted Users:</b>\n\n"
    for uid in users:
        try:
            u = await client.get_users(uid)
            text += f"• {u.mention} (<code>{uid}</code>)\n"
        except:
            text += f"• ID: <code>{uid}</code>\n"
    await message.reply_text(text, parse_mode=ParseMode.HTML)


# ================= WATCHER LOGIC =================

@nand.on_message(filters.group & ~filters.bot & ~filters.service, group=12)
async def abuse_watcher(client, message: Message):
    text = message.text or message.caption
    if not text:
        return

    # 🚀 OPT 2: Ultra-fast Cache Check
    if not await is_abuse_on(message.chat.id):
        return

    user_id = message.from_user.id if message.from_user else (message.sender_chat.id if message.sender_chat else None)

    # 🚀 OPT 3: Ultra-fast Whitelist Check
    if user_id and await is_whitelisted(message.chat.id, user_id):
        return

    if ABUSE_PATTERN.search(text):
        try:
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

            mention = message.from_user.mention if message.from_user else (f"<b>{message.sender_chat.title}</b>" if message.sender_chat else "User")

            warning_text = (
                f"🚫 Hey {mention}, your message was removed.\n\n"
                f"🔍 <b>Censored:</b>\n"
                f"{censored_text}\n\n"
                f"Please keep the chat respectful."
            )

            sent = await message.reply_text(
                warning_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
            
            await asyncio.sleep(60)
            await sent.delete()
            
        except Exception:
            pass
            
