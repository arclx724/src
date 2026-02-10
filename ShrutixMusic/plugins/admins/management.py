import time
from pyrogram import filters
from pyrogram.types import ChatPermissions, ChatPrivileges, Message
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter

from ShrutixMusic import nand
from ShrutixMusic.core.mongo import mongodb

# ==========================================================
# CONFIG
# ==========================================================
BAN_LIMIT = 10
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
# PROMOTE / DEMOTE
# ==========================================================

@nand.on_message(filters.group & filters.command(["promote"]))
async def promote_handler(client, message: Message):
    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("Specify a user to promote.")
    
    title = " ".join(message.command[2:]) if len(message.command) > 2 else None

    # Get Bot's Own Permissions
    me = await client.get_chat_member(message.chat.id, client.me.id)
    if not me.privileges or not me.privileges.can_promote_members:
        return await message.reply_text("❌ I don't have permission to promote users.")

    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this command.")
    
    owner_id = await get_owner(client, message.chat.id)
    if user.id == owner_id:
        return await message.reply_text("⚠️ User is already owner.")

    # ERROR FIX: Only give rights that the BOT actually has
    bot_rights = me.privileges
    
    try:
        await client.promote_chat_member(
            message.chat.id,
            user.id,
            privileges=ChatPrivileges(
                can_change_info=bot_rights.can_change_info,
                can_delete_messages=bot_rights.can_delete_messages,
                can_invite_users=bot_rights.can_invite_users,
                can_restrict_members=bot_rights.can_restrict_members,
                can_pin_messages=bot_rights.can_pin_messages,
                can_promote_members=False, # Standard safety
                can_manage_video_chats=bot_rights.can_manage_video_chats,
                can_manage_topics=bot_rights.can_manage_topics,
                can_post_stories=bot_rights.can_post_stories,
                can_edit_stories=bot_rights.can_edit_stories,
                can_delete_stories=bot_rights.can_delete_stories,
                is_anonymous=False
            )
        )
        if title:
            await client.set_administrator_title(message.chat.id, user.id, title)
            
        await message.reply_text(f"✅ {user.mention} promoted successfully!")
    except Exception as e:
        await message.reply_text(f"❌ Failed to promote: {e}")


@nand.on_message(filters.group & filters.command("demote"))
async def demote_user(client: Client, message: Message):
    # Check if executor is admin
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply to a user or use '/demote @username'")

    try:
        target_member = await client.get_chat_member(message.chat.id, user.id)
    except Exception as e:
        if "USER_NOT_PARTICIPANT" in str(e):
            return await message.reply_text("❌ Cannot demote: user is not a member of this chat.")
        return await message.reply_text(f"⚠️ Failed to demote: {e}")

    if target_member.status == ChatMemberStatus.OWNER:
        return await message.reply_text("⚠️ You cannot demote the group owner.")
    if user.id == message.from_user.id:
        return await message.reply_text("❌ You cannot demote yourself.")

    try:
        # HERE IS THE MAGIC FIX: Ban then Unban to fully remove from admin list
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        
        await message.reply_text(f"✅ {user.mention} has been demoted from admin.")

    except Exception as e:
        if "CHAT_ADMIN_REQUIRED" in str(e):
            await message.reply_text("❌ Bot must be admin with 'Ban Users' permission to demote.")
        else:
            await message.reply_text(f"⚠️ Failed to demote: {e}")
    
