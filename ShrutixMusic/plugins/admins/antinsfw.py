import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from config import OWNER_ID, SUPPORT_CHAT

# ================= SETTINGS CACHE =================

NSFW_SETTINGS = {}
SUDO_USERS = set()

API_URL = "https://api.sightengine.com/1.0/check.json"

# ================= PERMISSION HELPERS =================

async def can_change_info(client, chat_id, user_id):
    member = await client.get_chat_member(chat_id, user_id)

    if member.status == ChatMemberStatus.OWNER:
        return True

    if member.status == ChatMemberStatus.ADMINISTRATOR and member.privileges.can_change_info:
        return True

    return False


async def is_admin(client, chat_id, user_id):
    member = await client.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]


# ================= ADDAMTHY =================

@nand.on_message(filters.command("addamthy") & filters.private)
async def add_amthy(client, message: Message):

    if message.from_user.id != OWNER_ID and message.from_user.id not in SUDO_USERS:
        return await message.reply_text("❌ Owner or Sudo only.")

    if not message.reply_to_message:
        return await message.reply_text("Reply to user.")

    user_id = message.reply_to_message.from_user.id
    SUDO_USERS.add(user_id)

    await message.reply_text("✅ User added as Sudo.")


# ================= NSFW COMMAND LIST =================

@nand.on_message(filters.command(["nsfwcommands", "nsfwcommand"]))
async def nsfw_commands(client, message: Message):

    text = """
<b>📛 NSFW Module Commands</b>

• /addamthy (Owner & Sudo only - Private)
• /nsfwsilent on/off (Change Group Info required)
• /nsfwpunish on/off (Requires Silent ON)

<b>System Logic:</b>

80%+ → Delete + Ban  
60-80 → Delete + Warn  
40-60 → Warn Only  

⚠ Admins → Only Delete
"""

    await message.reply_text(text)


# ================= NSFW SILENT =================

@nand.on_message(filters.command("nsfwsilent") & filters.group)
async def nsfw_silent(client, message: Message):

    if not await can_change_info(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Need Change Group Info permission.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwsilent on/off")

    chat_id = message.chat.id

    NSFW_SETTINGS.setdefault(chat_id, {"enabled": False, "punish": False, "warns": {}})

    if message.command[1].lower() == "on":
        NSFW_SETTINGS[chat_id]["enabled"] = True
        await message.reply_text("✅ NSFW Silent Enabled")

    else:
        NSFW_SETTINGS[chat_id]["enabled"] = False
        NSFW_SETTINGS[chat_id]["punish"] = False
        await message.reply_text("❌ NSFW Silent Disabled")


# ================= NSFW PUNISH =================

@nand.on_message(filters.command("nsfwpunish") & filters.group)
async def nsfw_punish(client, message: Message):

    if not await can_change_info(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Need Change Group Info permission.")

    chat_id = message.chat.id
    settings = NSFW_SETTINGS.get(chat_id)

    if not settings or not settings["enabled"]:
        return await message.reply_text("⚠ Enable Silent first.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwpunish on/off")

    if message.command[1].lower() == "on":
        settings["punish"] = True
        await message.reply_text("✅ Smart Punishment Enabled")

    else:
        settings["punish"] = False
        await message.reply_text("❌ Smart Punishment Disabled")


# ================= API SCAN =================

async def scan_file(file_stream):

    params = {
        "models": "nudity,gore",
        "api_user": "YOUR_API_USER",
        "api_secret": "YOUR_API_SECRET"
    }

    file_stream.seek(0)

    data = aiohttp.FormData()
    for k, v in params.items():
        data.add_field(k, v)

    data.add_field("media", file_stream, filename="img.jpg")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data=data) as resp:
            return await resp.json()


# ================= ALERT AUTO DELETE =================

async def send_alert(message, text):
    try:
        msg = await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Support", url=SUPPORT_CHAT)]]
            )
        )

        await asyncio.sleep(60)
        await msg.delete()

    except:
        pass


# ================= WARN SYSTEM =================

def add_warn(chat_id, user_id):
    warns = NSFW_SETTINGS[chat_id]["warns"]
    warns[user_id] = warns.get(user_id, 0) + 1
    return warns[user_id]


# ================= MAIN WATCHER =================

@nand.on_message(filters.group & (filters.photo | filters.sticker | filters.animation | filters.video))
async def nsfw_watcher(client, message: Message):

    chat_id = message.chat.id

    settings = NSFW_SETTINGS.get(chat_id)

    if not settings or not settings["enabled"]:
        return

    if not message.from_user:
        return

    user_id = message.from_user.id

    # Skip admins punish
    admin = await is_admin(client, chat_id, user_id)

    media = None

    if message.photo:
        media = message.photo.thumbs[-1] if message.photo.thumbs else message.photo

    elif message.sticker:
        if message.sticker.thumbs:
            media = message.sticker.thumbs[-1]

    elif message.video:
        if message.video.thumbs:
            media = message.video.thumbs[-1]

    elif message.animation:
        if message.animation.thumbs:
            media = message.animation.thumbs[-1]

    if not media:
        return

    try:
        file_stream = await client.download_media(media, in_memory=True)

        result = await scan_file(file_stream)

        if not result:
            return

        score = 0

        if "nudity" in result:
            score = max(
                result["nudity"].get("raw", 0),
                result["nudity"].get("partial", 0)
            )

        if "gore" in result:
            score = max(score, result["gore"].get("prob", 0))

        percent = int(score * 100)

        if score < 0.40:
            return

        try:
            await message.delete()
        except:
            pass

        # ================= ACTION LOGIC =================

        if admin:
            asyncio.create_task(
                send_alert(message, f"⚠ NSFW Deleted (Admin Safe)\nScore: {percent}%")
            )
            return

        # ---- WARN ONLY ----
        if 0.40 <= score < 0.60:
            warns = add_warn(chat_id, user_id)

            asyncio.create_task(
                send_alert(message, f"⚠ Warned\nScore: {percent}%\nWarns: {warns}")
            )

        # ---- DELETE + WARN ----
        elif 0.60 <= score < 0.80:
            warns = add_warn(chat_id, user_id)

            asyncio.create_task(
                send_alert(message, f"⚠ Deleted + Warned\nScore: {percent}%\nWarns: {warns}")
            )

        # ---- BAN ----
        elif score >= 0.80 and settings["punish"]:
            try:
                await client.ban_chat_member(chat_id, user_id)
            except:
                pass

            asyncio.create_task(
                send_alert(message, f"🚫 User Banned\nScore: {percent}%")
            )

    except:
        pass
