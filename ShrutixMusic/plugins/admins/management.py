import time
from pyrogram import filters
from pyrogram.types import ChatPermissions, ChatPrivileges, Message
from pyrogram.enums import ChatMemberStatus

# Apne bot client ko import karein (nand ya app jo bhi variable name hai)
from ShrutixMusic import nand 
from ShrutixMusic.utils import db  # Jo file Step 1 mein banayi

# ==========================================================
# CONFIG
# ==========================================================
BAN_LIMIT = 10
BAN_TIME_WINDOW = 24 * 60 * 60  # 24 hours
ADMIN_BAN_TRACKER = {}  # {admin_id: [timestamps]}

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

async def is_power(client, chat_id: int, user_id: int) -> bool:
    """Check if user is Admin or Owner"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def extract_target_user(client, message):
    """Extract user from reply or command argument"""
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
# COMMANDS
# ==========================================================

@nand.on_message(filters.group & filters.command("kick"))
async def kick_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/kick @username`")

    # Check bot permissions
    me = await client.get_chat_member(message.chat.id, client.me.id)
    if not me.privileges.can_restrict_members:
        return await message.reply_text("❌ I don't have permission to restrict members.")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"👢 {user.mention} has been kicked.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to kick: {e}")


@nand.on_message(filters.group & filters.command("ban"))
async def ban_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    admin_id = message.from_user.id
    now = int(time.time())

    # Ban Limit Logic
    history = ADMIN_BAN_TRACKER.get(admin_id, [])
    history = [t for t in history if now - t < BAN_TIME_WINDOW]

    if len(history) >= BAN_LIMIT:
        return await message.reply_text(
            "⛔ **Ban limit reached!**\n"
            "You can only ban **10 users in 24 hours**."
        )

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/ban @username`")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        history.append(now)
        ADMIN_BAN_TRACKER[admin_id] = history
        await message.reply_text(f"🚨 {user.mention} has been banned.\n"
                                 f"Remaining bans: `{BAN_LIMIT - len(history)}`")
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: {e}")


@nand.on_message(filters.group & filters.command("unban"))
async def unban_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/unban @username`")

    try:
        await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"✅ {user.mention} has been unbanned.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unban: {e}")


@nand.on_message(filters.group & filters.command("mute"))
async def mute_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/mute @username`")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False),
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
        return await message.reply_text("⚠️ Usage: Reply or use `/unmute @username`")

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


@nand.on_message(filters.group & filters.command("warn"))
async def warn_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/warn @username`")

    warns = await db.add_warn(message.chat.id, user.id)
    if warns >= 3:
        try:
            await client.restrict_chat_member(
                message.chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            await message.reply_text(f"🚫 {user.mention} reached 3 warns and was muted.")
            await db.reset_warns(message.chat.id, user.id)
        except Exception as e:
            await message.reply_text(f"❌ Failed to action: {e}")
    else:
        await message.reply_text(f"⚠️ {user.mention} now has {warns}/3 warnings.")


@nand.on_message(filters.group & filters.command("warns"))
async def check_warns(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/warns @username`")

    warns = await db.get_warns(message.chat.id, user.id)
    await message.reply_text(f"⚠️ {user.mention} has {warns}/3 warnings.")


@nand.on_message(filters.group & filters.command("resetwarns"))
async def reset_warns(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/resetwarns @username`")

    await db.reset_warns(message.chat.id, user.id)
    await message.reply_text(f"✅ {user.mention}'s warns have been reset.")


@nand.on_message(filters.group & filters.command("promote"))
async def promote_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin or owner can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use '/promote @username'")

    privileges = ChatPrivileges(
        can_manage_chat=True,
        can_delete_messages=True,
        can_manage_video_chats=True,
        can_restrict_members=True,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=True,
        is_anonymous=False
    )

    try:
        await client.promote_chat_member(message.chat.id, user.id, privileges)
        await message.reply_text(f"✅ {user.mention} has been promoted to admin.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@nand.on_message(filters.group & filters.command("demote"))
async def demote_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use '/demote @username'")

    try:
        member = await client.get_chat_member(message.chat.id, user.id)
        if member.status == ChatMemberStatus.OWNER:
            return await message.reply_text("⚠️ You cannot demote the owner.")
        if user.id == message.from_user.id:
            return await message.reply_text("❌ You cannot demote yourself.")

        # Permissions false kar dene se demote ho jayega
        no_privileges = ChatPrivileges(
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            is_anonymous=False
        )

        await client.promote_chat_member(message.chat.id, user.id, no_privileges)
        await message.reply_text(f"✅ {user.mention} has been demoted.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
          
