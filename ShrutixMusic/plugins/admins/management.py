import time
from pyrogram import filters
from pyrogram.types import Message, ChatPrivileges
from pyrogram.enums import ChatMemberStatus
from ShrutixMusic import nand
from ShrutixMusic.core.mongo import mongodb  # MongoDB instance

# ==========================================================
# CONFIG
# ==========================================================
BAN_LIMIT = 10
BAN_TIME_WINDOW = 24 * 60 * 60  # 24 hours
ADMIN_BAN_TRACKER = {}  # {admin_id: [timestamps]}
ADMIN_KICK_TRACKER = {}  # {admin_id: [timestamps]}

warnsdb = mongodb.warns

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
async def is_power(client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def extract_target_user(client, message: Message):
    """User from reply, mention or user_id"""
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

# ==========================================================
# WARN DB FUNCTIONS
# ==========================================================
async def get_warns(chat_id: int, user_id: int) -> int:
    result = await warnsdb.find_one({"chat_id": chat_id, "user_id": user_id})
    return result["warns"] if result else 0

async def add_warn(chat_id: int, user_id: int) -> int:
    warns = await get_warns(chat_id, user_id) + 1
    await warnsdb.update_one({"chat_id": chat_id, "user_id": user_id},
                             {"$set": {"warns": warns}}, upsert=True)
    return warns

async def reset_warns(chat_id: int, user_id: int):
    await warnsdb.delete_one({"chat_id": chat_id, "user_id": user_id})

# ==========================================================
# COMMAND HANDLERS
# ==========================================================
@nand.on_message(filters.group & filters.command("promote"))
async def promote_handler(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    # Optional new title
    title = None
    if len(message.command) > 2:
        title = " ".join(message.command[2:])

    privileges = ChatPrivileges(
        can_change_info=True,
        can_delete_messages=True,
        can_manage_video_chats=True,
        can_restrict_members=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_promote_members=True,
        is_anonymous=False
    )

    try:
        await client.promote_chat_member(message.chat.id, user.id, privileges)
        if title:
            await client.set_administrator_title(message.chat.id, user.id, title)
            await message.reply_text(f"✅ {user.mention} promoted with title: `{title}`")
        else:
            await message.reply_text(f"✅ {user.mention} promoted as admin.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to promote: {e}")

@nand.on_message(filters.group & filters.command("demote"))
async def demote_handler(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    member = await client.get_chat_member(message.chat.id, user.id)
    if member.status == ChatMemberStatus.OWNER:
        return await message.reply_text("⚠️ You cannot demote the owner.")

    try:
        no_privileges = ChatPrivileges(
            can_change_info=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_promote_members=False,
            is_anonymous=False
        )
        await client.promote_chat_member(message.chat.id, user.id, no_privileges)
        await message.reply_text(f"✅ {user.mention} has been demoted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to demote: {e}")

# ==========================================================
# BAN / KICK LIMIT LOGIC (MongoDB)
# ==========================================================
bansdb = mongodb.ban_kick_tracker

async def check_limit(chat_id, admin_id, action_type):
    now = int(time.time())
    record = await bansdb.find_one({"chat_id": chat_id, "admin_id": admin_id})
    if not record:
        record = {"chat_id": chat_id, "admin_id": admin_id, "ban": [], "kick": []}
        await bansdb.insert_one(record)

    timestamps = record[action_type]
    # Filter old timestamps
    timestamps = [t for t in timestamps if now - t < BAN_TIME_WINDOW]
    if len(timestamps) >= BAN_LIMIT:
        return False, BAN_LIMIT - len(timestamps)
    return True, len(timestamps)

async def add_limit_record(chat_id, admin_id, action_type):
    now = int(time.time())
    await bansdb.update_one({"chat_id": chat_id, "admin_id": admin_id},
                            {"$push": {action_type: now}}, upsert=True)

# ==========================================================
# /ban command
# ==========================================================
@nand.on_message(filters.group & filters.command("ban"))
async def ban_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    allowed, _ = await check_limit(message.chat.id, message.from_user.id, "ban")
    if not allowed:
        return await message.reply_text(f"⛔ Ban limit reached! Only {BAN_LIMIT} bans per 24h.")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await add_limit_record(message.chat.id, message.from_user.id, "ban")
        await message.reply_text(f"🚨 {user.mention} has been banned.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: {e}")

# ==========================================================
# /kick command
# ==========================================================
@nand.on_message(filters.group & filters.command("kick"))
async def kick_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    allowed, _ = await check_limit(message.chat.id, message.from_user.id, "kick")
    if not allowed:
        return await message.reply_text(f"⛔ Kick limit reached! Only {BAN_LIMIT} kicks per 24h.")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await add_limit_record(message.chat.id, message.from_user.id, "kick")
        await message.reply_text(f"👢 {user.mention} has been kicked.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to kick: {e}")

# ==========================================================
# /mute / /unmute
# ==========================================================
@nand.on_message(filters.group & filters.command("mute"))
async def mute_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )
    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=None,  # Mute all sending
        )
        await message.reply_text(f"🔇 {user.mention} muted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed: {e}")

@nand.on_message(filters.group & filters.command("unmute"))
async def unmute_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )
    try:
        await client.restrict_chat_member(message.chat.id, user.id, permissions={
            "can_send_messages": True,
            "can_send_media_messages": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True
        })
        await message.reply_text(f"🔊 {user.mention} unmuted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed: {e}")
