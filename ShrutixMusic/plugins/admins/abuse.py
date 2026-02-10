import re
import aiohttp
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ShrutixMusic import nand
from config import OPENROUTER_API_KEY, BOT_USERNAME
from ShrutixMusic.utils.db import (
    is_abuse_enabled,
    set_abuse_status,
    abuse_whitelist_user,
    abuse_unwhitelist_user,
    is_abuse_whitelisted,
    get_abuse_whitelisted_users
)

# --- Abusive Words List (Shortened for display, but logic remains same) ---
ABUSIVE_WORDS = [
    "aand", "aandu", "ass", "asshole", "b.c", "b.k.l", "b.s.d.k", 
    "bahenchod", "bakchod", "bastard", "bc", "behenchod", "betichod", 
    "bhadua", "bhadwa", "bhenchod", "bhosad", "bhosdk", "bhosdike", 
    "bitch", "bkl", "blowjob", "boobs", "bsdk", "chut", "chutiya", 
    "cock", "cunt", "dick", "fucker", "fucking", "gaand", "gandu", 
    "haramkhor", "jhaatu", "kutta", "lauda", "loda", "lund", "madarchod", 
    "mc", "mkc", "motherfucker", "pussy", "randi", "sex", "slut", "tatte", 
    "tatti", "whore", "xxx"
    # Aap apni poori list yahan wapas paste kar sakte hain
]

API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Pre-compile Regex for speed
ABUSE_PATTERN = re.compile(r'\b(' + '|'.join(map(re.escape, ABUSIVE_WORDS)) + r')\b', re.IGNORECASE)

# ================= HELPER FUNCTIONS =================

async def is_admin(chat_id, user_id, client):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def check_toxicity_ai(text: str) -> bool:
    """Checks text using Free AI Model"""
    if not text or not OPENROUTER_API_KEY:
        return False
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram.org", 
    }
    
    payload = {
        # Using a free, fast model
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "system", 
                "content": "You are a content filter. Reply ONLY with 'YES' if the message contains hate speech, severe abuse, or extreme profanity. Reply 'NO' if safe or mild."
            },
            {"role": "user", "content": text}
        ],
        "temperature": 0.1,
        "max_tokens": 5
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'choices' in data:
                        answer = data['choices'][0]['message']['content'].strip().upper()
                        return "YES" in answer
    except Exception:
        pass
    return False

# ================= COMMANDS =================

@nand.on_message(filters.command("abuse") & filters.group)
async def toggle_abuse(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id, client):
        return await message.reply_text("❌ Only admins can use this.")

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
    # Text ya Caption check karein
    text = message.text or message.caption
    if not text:
        return

    # 1. Check if Enabled
    if not await is_abuse_enabled(message.chat.id):
        return

    # 2. Check Whitelist (Admins can also be filtered if not whitelisted)
    if await is_abuse_whitelisted(message.chat.id, message.from_user.id):
        return

    detected = False
    censored_text = text

    # --- A. Local Regex Check (Fast) ---
    if ABUSE_PATTERN.search(text):
        detected = True
        # Gali ko hide karne ke liye replace logic
        censored_text = ABUSE_PATTERN.sub(lambda m: f"||{m.group(0)}||", text)

    # --- B. AI Check (Slower, but Smart) ---
    # Sirf tab check kare jab Local detect na kare aur text thoda lamba ho
    if not detected and OPENROUTER_API_KEY and len(text.split()) > 2:
        if await check_toxicity_ai(text):
            detected = True
            censored_text = f"||{text}||" # AI detected, hide full text

    # --- ACTION ---
    if detected:
        try:
            await message.delete()
            
            # Bot username fetch for link
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
            
            # 10 Seconds baad warning delete (Clean chat)
            await asyncio.sleep(10)
            await sent.delete()
            
        except Exception:
            # Agar bot ke paas delete permission nahi hai
            pass

