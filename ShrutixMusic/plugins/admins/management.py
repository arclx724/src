import time
import asyncio
from pyrogram import filters
from pyrogram.types import Message, ChatPermissions, ChatPrivileges
from pyrogram.enums import ChatMemberStatus
from ShrutixMusic import nand
from ShrutixMusic.core.mongo import mongodb

# ==========================================================
# CONFIG
# ==========================================================
BAN_LIMIT = 10
KICK_LIMIT = 10
TIME_WINDOW = 24 * 60 * 60  # 24 hours in seconds

# MongoDB collections
limits_db = mongodb.admin_limits
warns_db = mongodb.warns

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

async def is_power(client, chat_id: int, user_id: int) -> bool:
    """Check if user is admin or owner"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def extract_target_user(client, message: Message):
    """Get target user from reply, username, or id"""
    if message.reply_to_message:
        return message.reply_to_message.from_user

    if len(message.command) < 2:
        return None

    arg = message.command[1]
    try:
        if arg.startswith("@"):
            return await client.get_users(arg)
        if arg.isdigit():
            return await client.get_users(int(arg))
    except Exception:
        return None
    return None

async def get_admin_limit(chat_id, user_id, action):
    """Fetch Mongo-based limit count, auto-reset if TIME_WINDOW passed"""
    doc = await limits_db.find_one({"chat_id": chat_id, "user_id": user_id})
    now = int(time.time())
    if not doc:
        return 0
    last = doc.get("last_update", now)
    if now - last > TIME_WINDOW:
        # Reset after 24h
        await limits_db.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"ban": 0, "kick": 0, "last_update": now}},
            upsert=True
        )
        return 0
    return doc.get(action, 0)

async def add_admin_limit(chat_id, user_id, action):
    """Increment admin action counter"""
    current = await get_admin_limit(chat_id, user_id, action)
    current += 1
    await limits_db.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {action: current, "last_update": int(time.time())}},
        upsert=True
    )
    return current

# ==========================================================
# BAN & KICK
# ==========================================================

@nand.on_message(filters.group & filters.command("ban"))
async def ban_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("❌ Specify a user to ban!")

    count = await add_admin_limit(message.chat.id, message.from_user.id, "ban")
    if count > BAN_LIMIT:
        return await message.reply_text("⛔ Ban limit reached for 24 hours!")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"🚨 {user.mention} has been banned.\nRemaining: `{BAN_LIMIT - count}`")
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: {e}")

@nand.on_message(filters.group & filters.command("kick"))
async def kick_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("❌ Specify a user to kick!")

    count = await add_admin_limit(message.chat.id, message.from_user.id, "kick")
    if count > KICK_LIMIT:
        return await message.reply_text("⛔ Kick limit reached for 24 hours!")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"👢 {user.mention} has been kicked.\nRemaining: `{KICK_LIMIT - count}`")
    except Exception as e:
        await message.reply_text(f"❌ Failed to kick: {e}")

# ==========================================================
# MUTE & UNMUTE
# ==========================================================

@nand.on_message(filters.group & filters.command("mute"))
async def mute_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("❌ Specify a user to mute!")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply_text(f"🔇 {user.mention} has been muted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to mute: {e}")

@nand.on_message(filters.group & filters.command("unmute"))
async def unmute_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("❌ Specify a user to unmute!")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.reply_text(f"🔊 {user.mention} has been unmuted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unmute: {e}")

# ==========================================================
# PROMOTE & DEMOTE
# ==========================================================

@nand.on_message(filters.group & filters.command("promote"))
async def promote_handler(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("❌ Specify a user to promote!")

    privileges = ChatPrivileges(
        can_change_info=True,
        can_delete_messages=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_promote_members=True
    )

    try:
        await client.promote_chat_member(message.chat.id, user.id, privileges)
        await message.reply_text(f"✅ {user.mention} has been promoted to admin.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to promote: {e}")

@nand.on_message(filters.group & filters.command("demote"))
async def demote_handler(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("❌ Specify a user to demote!")

    no_privileges = ChatPrivileges(
        can_change_info=False,
        can_delete_messages=False,
        can_invite_users=False,
        can_pin_messages=False,
        can_promote_members=False
    )

    try:
        await client.promote_chat_member(message.chat.id, user.id, no_privileges)
        await message.reply_text(f"✅ {user.mention} has been demoted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to demote: {e}")

# ==========================================================
# ADMIN TITLE
# ==========================================================

@nand.on_message(filters.group & filters.command("settitle"))
async def set_admin_title(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("❌ Specify a user to set title!")

    if len(message.command) < 3:
        return await message.reply_text("❌ Usage: /settitle @user NewTitle")

    new_title = " ".join(message.command[2:])
    try:
        await client.set_administrator_title(message.chat.id, user.id, new_title)
        await message.reply_text(f"✅ {user.mention} title set to '{new_title}'.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to set title: {e}")
