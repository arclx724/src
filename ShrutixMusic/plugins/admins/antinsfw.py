import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions

# ================= CONFIG =================

OWNER_ID = 123456789  # <-- CHANGE THIS

SUDO_USERS = set()

NSFW_SETTINGS = {}  
USER_WARNINGS = {}
USER_LAST_SCAN = {}

COOLDOWN = 10
SCAN_LIMIT = asyncio.Semaphore(3)

# ================= UTIL =================

async def delete_later(msg, delay):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

async def fake_nsfw_scan():
    # Yaha apna real API lagao
    return 0.75

# ================= OWNER COMMAND =================

@Client.on_message(filters.command("addamthy") & filters.private)
async def add_amthy(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only owner can use this command.")

    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to add as sudo.")

    user_id = message.reply_to_message.from_user.id
    SUDO_USERS.add(user_id)

    await message.reply_text("✅ User added as Sudo.")

# ================= SETTINGS =================

@Client.on_message(filters.command("nsfwsilent") & filters.group)
async def nsfw_silent(client, message):
    if message.from_user.id not in SUDO_USERS and message.from_user.id != OWNER_ID:
        return

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwsilent on/off")

    chat_id = message.chat.id
    NSFW_SETTINGS.setdefault(chat_id, {"silent": False, "punish": True})

    if message.command[1].lower() == "on":
        NSFW_SETTINGS[chat_id]["silent"] = True
        await message.reply_text("✅ Silent Mode Enabled.")
    else:
        NSFW_SETTINGS[chat_id]["silent"] = False
        await message.reply_text("❌ Silent Mode Disabled.")

@Client.on_message(filters.command("nsfwpunish") & filters.group)
async def nsfw_punish(client, message):
    if message.from_user.id not in SUDO_USERS and message.from_user.id != OWNER_ID:
        return

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwpunish on/off")

    chat_id = message.chat.id
    NSFW_SETTINGS.setdefault(chat_id, {"silent": False, "punish": True})

    if message.command[1].lower() == "on":
        NSFW_SETTINGS[chat_id]["punish"] = True
        await message.reply_text("✅ Smart Punishment Enabled.")
    else:
        NSFW_SETTINGS[chat_id]["punish"] = False
        await message.reply_text("❌ Smart Punishment Disabled.")

@Client.on_message(filters.command("nsfwcommands"))
async def nsfw_commands(client, message):
    text = """
<b>📛 NSFW Module Commands</b>

• /addamthy (Owner only)
• /nsfwsilent on/off
• /nsfwpunish on/off

Smart Punishment:

Score > 80% → Delete + Ban
Score 60–80% → Delete + Warn
Score 40–60% → Warn Only

⚠ Admins: Only Delete (No punish)
"""
    await message.reply_text(text)

# ================= NSFW HANDLER =================

@Client.on_message(filters.group & (filters.photo | filters.sticker))
async def nsfw_handler(client, message):

    chat_id = message.chat.id
    user_id = message.from_user.id

    settings = NSFW_SETTINGS.get(chat_id, {"silent": False, "punish": True})

    # Cooldown
    now = time.time()
    if now - USER_LAST_SCAN.get(user_id, 0) < COOLDOWN:
        return
    USER_LAST_SCAN[user_id] = now

    async with SCAN_LIMIT:
        score = await fake_nsfw_scan()

    if score < 0.40:
        return

    member = await client.get_chat_member(chat_id, user_id)
    is_admin = member.status in ["administrator", "creator"]

    try:
        await message.delete()
    except:
        pass

    warn_msg = None

    if not settings["silent"]:
        warn_msg = await message.reply_text(
            f"⚠ NSFW Detected ({int(score*100)}%)"
        )

    if warn_msg:
        asyncio.create_task(delete_later(warn_msg, 60))

    if is_admin:
        return

    if not settings["punish"]:
        return

    if score >= 0.80:
        try:
            await client.kick_chat_member(chat_id, user_id)
        except:
            pass

    elif score >= 0.60:
        USER_WARNINGS[user_id] = USER_WARNINGS.get(user_id, 0) + 1

    elif score >= 0.40:
        USER_WARNINGS[user_id] = USER_WARNINGS.get(user_id, 0) + 1
