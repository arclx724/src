import time
from pyrogram import filters
from pyrogram.types import ChatPrivileges, Message
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.core.mongo import mongodb  # MongoDB client

# ==========================================================
# CONFIG
# ==========================================================
BAN_LIMIT = 10
BAN_TIME_WINDOW = 24 * 60 * 60  # 24 hours
ADMIN_BAN_TRACKER = {}  # Temporary in-memory tracking (MongoDB still primary)

warnsdb = mongodb.warns
abusedb = mongodb.abuse

# ==========================================================
# HELPERS
# ==========================================================

async def is_power(client, chat_id: int, user_id: int) -> bool:
    """Check if user is admin or owner"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def extract_target_user(client, message: Message):
    """Extract user from reply, @username, or user_id"""
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

async def get_owner_id(client, chat_id: int):
    """Auto-detect owner"""
    async for member in client.get_chat_members(chat_id, filter="administrators"):
        if member.status == ChatMemberStatus.OWNER:
            return member.user.id
    return None

# ==========================================================
# WARN FUNCTIONS
# ==========================================================

async def get_warns(chat_id: int, user_id: int) -> int:
    result = await warnsdb.find_one({"chat_id": chat_id, "user_id": user_id})
    return result["warns"] if result else 0

async def add_warn(chat_id: int, user_id: int) -> int:
    warns = await get_warns(chat_id, user_id)
    warns += 1
    await warnsdb.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"warns": warns}},
        upsert=True,
    )
    return warns

async def reset_warns(chat_id: int, user_id: int):
    await warnsdb.delete_one({"chat_id": chat_id, "user_id": user_id})

# ==========================================================
# COMMANDS
# ==========================================================

# -------------------------
# KICK COMMAND
# -------------------------
@nand.on_message(filters.group & filters.command("kick"))
async def kick_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    # Owner immunity
    owner_id = await get_owner_id(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("❌ You cannot kick the owner!")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"👢 {user.mention} has been kicked.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to kick: {e}")

# -------------------------
# BAN COMMAND
# -------------------------
@nand.on_message(filters.group & filters.command("ban"))
async def ban_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    # Owner immunity
    owner_id = await get_owner_id(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("❌ You cannot ban the owner!")

    # Ban limit
    admin_id = message.from_user.id
    now = int(time.time())
    history = ADMIN_BAN_TRACKER.get(admin_id, [])
    history = [t for t in history if now - t < BAN_TIME_WINDOW]

    if len(history) >= BAN_LIMIT:
        return await message.reply_text(
            "⛔ **Ban/Kick limit reached!**\nYou can only ban/kick **10 users in 24 hours**."
        )

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        history.append(now)
        ADMIN_BAN_TRACKER[admin_id] = history
        await message.reply_text(
            f"🚨 {user.mention} has been banned.\nRemaining bans/kicks: `{BAN_LIMIT - len(history)}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: {e}")

# -------------------------
# UNBAN COMMAND
# -------------------------
@nand.on_message(filters.group & filters.command("unban"))
async def unban_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    try:
        await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"✅ {user.mention} has been unbanned.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unban: {e}")

# -------------------------
# MUTE COMMAND
# -------------------------
@nand.on_message(filters.group & filters.command("mute"))
async def mute_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    from pyrogram.types import ChatPermissions

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False),
        )
        await message.reply_text(f"🔇 {user.mention} has been muted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to mute: {e}")

# -------------------------
# UNMUTE COMMAND
# -------------------------
@nand.on_message(filters.group & filters.command("unmute"))
async def unmute_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    from pyrogram.types import ChatPermissions

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.reply_text(f"🔊 {user.mention} has been unmuted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unmute: {e}")

# -------------------------
# PROMOTE COMMAND
# -------------------------
@nand.on_message(filters.group & filters.command("promote"))
async def promote_handler(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    # Owner immunity
    owner_id = await get_owner_id(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("❌ You cannot promote the owner!")

    # Extract custom title if provided
    if len(message.command) > 2:
        new_title = " ".join(message.command[2:])
    else:
        new_title = None

    privileges = ChatPrivileges(
        can_change_info=True,
        can_delete_messages=True,
        can_manage_video_chats=True,
        can_restrict_members=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_promote_members=False,
        is_anonymous=False
    )

    try:
        await client.promote_chat_member(message.chat.id, user.id, privileges)
        if new_title:
            await client.set_administrator_title(message.chat.id, user.id, new_title)
            await message.reply_text(f"✅ {user.mention} promoted with title: {new_title}")
        else:
            await message.reply_text(f"✅ {user.mention} promoted to admin.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# -------------------------
# DEMOTE COMMAND
# -------------------------
@nand.on_message(filters.group & filters.command("demote"))
async def demote_handler(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )

    # Owner immunity
    owner_id = await get_owner_id(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("❌ You cannot demote the owner!")

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

    try:
        await client.promote_chat_member(message.chat.id, user.id, no_privileges)
        await message.reply_text(f"✅ {user.mention} has been demoted.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# -------------------------
# CHECK WARNS
# -------------------------
@nand.on_message(filters.group & filters.command("warns"))
async def check_warns(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )
    warns = await get_warns(message.chat.id, user.id)
    await message.reply_text(f"⚠️ {user.mention} has {warns}/3 warnings.")

# -------------------------
# RESET WARNS
# -------------------------
@nand.on_message(filters.group & filters.command("resetwarns"))
async def reset_warns_cmd(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user...!"
        )
    await reset_warns(message.chat.id, user.id)
    await message.reply_text(f"✅ {user.mention}'s warnings have been reset.")
