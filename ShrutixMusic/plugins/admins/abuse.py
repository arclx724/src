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

# ================= CONFIG =================

SUPPORT_LINK = "https://t.me/ShrutiBots"

ABUSIVE_WORDS = [
    "aand", "aandu", "ass", "asshole", "b.c", "b.k.l", "b.s.d.k",
    "bahenchod", "bakchod", "bastard", "bc", "behenchod", "betichod",
    "bhadua", "bhadwa", "bhenchod", "bhosad", "bhosdk", "bhosdike",
    "bitch", "bkl", "blowjob", "boobs", "bsdk", "chut", "chutiya",
    "cock", "cunt", "dick", "fucker", "fucking", "gaand", "gandu",
    "haramkhor", "jhaatu", "kutta", "lauda", "loda", "lund", "madarchod",
    "mc", "mkc", "motherfucker", "pussy", "randi", "sex", "slut",
    "tatte", "tatti", "whore", "xxx"
]

ABUSE_PATTERN = re.compile(
    r'(?<!\w)(' + '|'.join(map(re.escape, ABUSIVE_WORDS)) + r')(?!\w)',
    re.IGNORECASE
)

# ================= RAM CACHE =================

ABUSE_CACHE = {}          # chat_id: True/False
WHITELIST_CACHE = {}      # chat_id: set(user_ids)
WARNING_COOLDOWN = {}     # (chat_id, user_id): timestamp

# ================= ERROR REPLIES =================

REPLIES = {
    "NOT_ADMIN": "❌ **Access Denied:** Only Admins can use this command.",
    "NOT_SUPER_ADMIN": "⚠️ **Access Denied:** You need 'Change Group Info' right.",
    "BOT_NO_RIGHTS": "❗ I don't have Delete Message permission.",
    "NO_USER_FOUND": "❓ Reply or give @username/user_id.",
    "BOT_ITSELF": "🤖 I cannot whitelist myself!"
}

# ================= HELPER =================

async def get_user_privilege(client, chat_id, user_id):
    if not user_id:
        return "ADMIN"

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
    try:
        bot = await client.get_chat_member(chat_id, client.me.id)
        return bot.privileges and bot.privileges.can_delete_messages
    except:
        return False


async def extract_user(client, message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        try:
            return await client.get_users(message.command[1])
        except:
            return None
    return None


# ================= COMMANDS =================

@nand.on_message(filters.command("abuse") & filters.group)
async def toggle_abuse(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    privilege = await get_user_privilege(client, message.chat.id, user_id)

    if privilege == "MEMBER":
        return await message.reply_text(REPLIES["NOT_ADMIN"])

    if not await check_bot_rights(client, message.chat.id):
        return await message.reply_text(REPLIES["BOT_NO_RIGHTS"])

    current = ABUSE_CACHE.get(message.chat.id)

    if current is None:
        current = await is_abuse_enabled(message.chat.id)

    new_status = not current
    await set_abuse_status(message.chat.id, new_status)

    ABUSE_CACHE[message.chat.id] = new_status

    state = "Enabled ✅" if new_status else "Disabled ❌"
    await message.reply_text(f"🛡 Slang Filter {state}")


@nand.on_message(filters.command("authabuse") & filters.group)
async def auth_abuse_user(client, message: Message):
    privilege = await get_user_privilege(
        client,
        message.chat.id,
        message.from_user.id if message.from_user else None
    )

    if privilege not in ["CREATOR", "SUPER_ADMIN"]:
        return await message.reply_text(REPLIES["NOT_SUPER_ADMIN"])

    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(REPLIES["NO_USER_FOUND"])

    if user.id == client.me.id:
        return await message.reply_text(REPLIES["BOT_ITSELF"])

    await abuse_whitelist_user(message.chat.id, user.id)

    WHITELIST_CACHE.setdefault(message.chat.id, set()).add(user.id)

    await message.reply_text(f"✅ {user.mention} exempted from filter.")


@nand.on_message(filters.command("unauthabuse") & filters.group)
async def unauth_abuse_user(client, message: Message):
    privilege = await get_user_privilege(
        client,
        message.chat.id,
        message.from_user.id if message.from_user else None
    )

    if privilege not in ["CREATOR", "SUPER_ADMIN"]:
        return await message.reply_text(REPLIES["NOT_SUPER_ADMIN"])

    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(REPLIES["NO_USER_FOUND"])

    await abuse_unwhitelist_user(message.chat.id, user.id)

    if message.chat.id in WHITELIST_CACHE:
        WHITELIST_CACHE[message.chat.id].discard(user.id)

    await message.reply_text(f"🚫 {user.mention} removed from exemption.")


# ================= WATCHER =================

@nand.on_message(filters.group & ~filters.bot & ~filters.service, group=12)
async def abuse_watcher(client, message: Message):

    text = message.text or message.caption
    if not text:
        return

    chat_id = message.chat.id

    # === Abuse Status Cache ===
    enabled = ABUSE_CACHE.get(chat_id)

    if enabled is None:
        enabled = await is_abuse_enabled(chat_id)
        ABUSE_CACHE[chat_id] = enabled

    if not enabled:
        return

    # === Get User ID ===
    if message.from_user:
        user_id = message.from_user.id
    elif message.sender_chat:
        user_id = message.sender_chat.id
    else:
        return

    # === Whitelist Cache ===
    if chat_id not in WHITELIST_CACHE:
        users = await get_abuse_whitelisted_users(chat_id)
        WHITELIST_CACHE[chat_id] = set(users)

    if user_id in WHITELIST_CACHE[chat_id]:
        return

    # === Regex Check ===
    if not ABUSE_PATTERN.search(text):
        return

    # === Cooldown (30 sec) ===
    key = (chat_id, user_id)
    now = asyncio.get_event_loop().time()

    if key in WARNING_COOLDOWN and now - WARNING_COOLDOWN[key] < 30:
        return

    WARNING_COOLDOWN[key] = now

    if not await check_bot_rights(client, chat_id):
        return

    try:
        await message.delete()

        safe_text = html.escape(text)
        censored = ABUSE_PATTERN.sub(
            lambda m: f"<spoiler>{m.group(0)}</spoiler>",
            safe_text
        )

        mention = (
            message.from_user.mention
            if message.from_user
            else f"<b>{html.escape(message.sender_chat.title)}</b>"
        )

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ Add Me",
                    url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
                ),
                InlineKeyboardButton("📢 Support", url=SUPPORT_LINK)
            ]
        ])

        warn_msg = await message.reply_text(
            f"🚫 Hey {mention}, message removed.\n\n"
            f"🔍 <b>Censored:</b>\n{censored}\n\n"
            f"Keep chat respectful.",
            parse_mode=ParseMode.HTML,
            reply_markup=buttons
        )

        await asyncio.sleep(60)
        await warn_msg.delete()

    except:
        pass
