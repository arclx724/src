import time
from pyrogram import filters
from pyrogram.types import ChatPermissions, ChatPrivileges, Message
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter

from ShrutixMusic import nand  # Your bot client
from ShrutixMusic.core.mongo import mongodb  # MongoDB instance

# ==========================================================
# CONFIG
# ==========================================================
BAN_LIMIT = 10  # Max combined bans/kicks per 24 hrs per admin
BAN_TIME_WINDOW = 24 * 60 * 60
ADMIN_BAN_TRACKER = {}

# MongoDB Collections
warnsdb = mongodb.warns
abusedb = mongodb.abuse
limitsdb = mongodb.limits

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

async def get_owner(client, chat_id: int) -> int:
    """Get chat owner id (Fixed for Pyrogram V2)"""
    async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        if member.status == ChatMemberStatus.OWNER:
            return member.user.id
    return 0

async def extract_target_user(client, message: Message):
    """Get user from reply, @username or userid"""
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

async def abuse_check(chat_id: int, admin_id: int) -> bool:
    """Check ban/kick limits"""
    now = int(time.time())
    data = await limitsdb.find_one({"chat_id": chat_id, "admin_id": admin_id})
    timestamps = data["timestamps"] if data else []
    timestamps = [t for t in timestamps if now - t < BAN_TIME_WINDOW]

    if len(timestamps) >= BAN_LIMIT:
        return False, BAN_LIMIT - len(timestamps)
    return True, timestamps

async def log_abuse(chat_id: int, admin_id: int):
    """Log ban/kick usage"""
    now = int(time.time())
    await limitsdb.update_one(
        {"chat_id": chat_id, "admin_id": admin_id},
        {"$push": {"timestamps": now}},
        upsert=True
    )

# ==========================================================
# COMMANDS
# ==========================================================

@nand.on_message(filters.group & filters.command(["kick"]))
async def kick_user(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("I don't know who you're talking about, specify a user...!")

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")

    owner_id = await get_owner(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("⚠️ You cannot kick the owner!")

    can_do, _ = await abuse_check(message.chat.id, message.from_user.id)
    if not can_do:
        return await message.reply_text(f"⛔ Ban/Kick limit reached! Max {BAN_LIMIT} in 24 hrs.")

    me = await client.get_chat_member(message.chat.id, client.me.id)
    if not me.privileges.can_restrict_members:
        return await message.reply_text("❌ I don't have permission to kick users.")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await log_abuse(message.chat.id, message.from_user.id)
        await message.reply_text(f"👢 {user.mention} has been kicked.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to kick: {e}")


@nand.on_message(filters.group & filters.command(["ban"]))
async def ban_user(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("I don't know who you're talking about, specify a user...!")

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")

    owner_id = await get_owner(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("⚠️ You cannot ban the owner!")

    can_do, _ = await abuse_check(message.chat.id, message.from_user.id)
    if not can_do:
        return await message.reply_text(f"⛔ Ban/Kick limit reached! Max {BAN_LIMIT} in 24 hrs.")

    me = await client.get_chat_member(message.chat.id, client.me.id)
    if not me.privileges.can_restrict_members:
        return await message.reply_text("❌ I don't have permission to ban users.")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await log_abuse(message.chat.id, message.from_user.id)
        await message.reply_text(f"🚨 {user.mention} has been banned.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: {e}")


@nand.on_message(filters.group & filters.command(["unban"]))
async def unban_user(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("Specify a user to unban.")

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")

    try:
        await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"✅ {user.mention} has been unbanned.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unban: {e}")


@nand.on_message(filters.group & filters.command(["mute"]))
async def mute_user(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("Specify a user to mute.")

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply_text(f"🔇 {user.mention} has been muted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to mute: {e}")


@nand.on_message(filters.group & filters.command(["unmute"]))
async def unmute_user(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("Specify a user to unmute.")

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await message.reply_text(f"🔊 {user.mention} has been unmuted.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unmute: {e}")


# ==========================================================
# PROMOTE / DEMOTE (Updated with Story Permissions)
# ==========================================================

@nand.on_message(filters.group & filters.command(["promote"]))
async def promote_handler(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("Specify a user to promote.")

    title = " ".join(message.command[2:]) if len(message.command) > 2 else None

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")

    owner_id = await get_owner(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("⚠️ User is already owner.")

    try:
        await client.promote_chat_member(
            message.chat.id,
            user.id,
            privileges=ChatPrivileges(
                can_change_info=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_promote_members=False,
                can_manage_video_chats=True,
                is_anonymous=False
            )
        )
        if title:
            await client.set_administrator_title(message.chat.id, user.id, title)
        await message.reply_text(f"✅ {user.mention} promoted successfully!")
    except Exception as e:
        await message.reply_text(f"❌ Failed to promote: {e}")


@nand.on_message(filters.group & filters.command(["demote"]))
async def demote_handler(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("Specify a user to demote.")

    me = await client.get_chat_member(message.chat.id, client.me.id)
    if not me.privileges.can_promote_members:
        return await message.reply_text("❌ I don't have permission to promote/demote users.")

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")

    owner_id = await get_owner(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("⚠️ You cannot demote the owner!")

    try:
        try:
            await client.set_administrator_title(message.chat.id, user.id, "")
        except:
            pass

        # Demote FIX: Added Story Permissions to False
        await client.promote_chat_member(
            message.chat.id,
            user.id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_video_chats=False,
                can_manage_topics=False,
                is_anonymous=False,
                # In naye rights ko False karna zaroori hai
                can_post_stories=False,
                can_edit_stories=False,
                can_delete_stories=False
            )
        )
        await message.reply_text(f"✅ {user.mention} has been demoted to a normal member!")
    except Exception as e:
        await message.reply_text(f"❌ Failed to demote: {e}")
        
