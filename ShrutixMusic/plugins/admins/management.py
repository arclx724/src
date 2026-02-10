import time
from pyrogram import filters
from pyrogram.types import ChatPermissions, ChatPrivileges, Message
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.utils import db

# ==========================================================
# CONFIG
# ==========================================================
ABUSE_LIMIT = 10
ABUSE_TIME_WINDOW = 24 * 60 * 60  # 24 hours

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

async def is_power(client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ]
    except:
        return False


async def is_owner(client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status == ChatMemberStatus.OWNER
    except:
        return False


async def extract_target_user(client, message):
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
    except:
        return None
    return None


async def auto_demote(client, chat_id, user_id):
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
    await client.promote_chat_member(chat_id, user_id, no_privileges)


# ==========================================================
# MONGO HELPERS (UNCHANGED)
# ==========================================================

async def get_abuse_history(chat_id: int, admin_id: int):
    data = await db.admin_abuse.find_one(
        {"chat_id": chat_id, "admin_id": admin_id}
    )
    return data["timestamps"] if data else []


async def save_abuse_history(chat_id: int, admin_id: int, timestamps: list):
    await db.admin_abuse.update_one(
        {"chat_id": chat_id, "admin_id": admin_id},
        {"$set": {"timestamps": timestamps}},
        upsert=True
    )

# ==========================================================
# COMMANDS
# ==========================================================

@nand.on_message(filters.group & filters.command("kick"))
async def kick_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    admin_id = message.from_user.id
    chat_id = message.chat.id
    now = int(time.time())

    owner = await is_owner(client, chat_id, admin_id)

    if not owner:
        history = await get_abuse_history(chat_id, admin_id)
        history = [t for t in history if now - t < ABUSE_TIME_WINDOW]

        if len(history) >= ABUSE_LIMIT:
            await auto_demote(client, chat_id, admin_id)
            return await message.reply_text(
                "🚨 **Abuse detected!**\n"
                "Ban/Kick limit exceeded.\n"
                "🔻 You have been auto-demoted."
            )
    else:
        history = None  # owner immunity

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/kick @username`")

    me = await client.get_chat_member(chat_id, client.me.id)
    if not me.privileges.can_restrict_members:
        return await message.reply_text("❌ I don't have permission to restrict members.")

    try:
        await client.ban_chat_member(chat_id, user.id)
        await client.unban_chat_member(chat_id, user.id)

        if not owner:
            history.append(now)
            await save_abuse_history(chat_id, admin_id, history)

        await message.reply_text(
            f"👢 {user.mention} has been kicked."
        )
    except Exception as e:
        await message.reply_text(f"❌ Failed to kick: {e}")


@nand.on_message(filters.group & filters.command("ban"))
async def ban_user(client, message: Message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    admin_id = message.from_user.id
    chat_id = message.chat.id
    now = int(time.time())

    owner = await is_owner(client, chat_id, admin_id)

    if not owner:
        history = await get_abuse_history(chat_id, admin_id)
        history = [t for t in history if now - t < ABUSE_TIME_WINDOW]

        if len(history) >= ABUSE_LIMIT:
            await auto_demote(client, chat_id, admin_id)
            return await message.reply_text(
                "🚨 **Abuse detected!**\n"
                "Ban/Kick limit exceeded.\n"
                "🔻 You have been auto-demoted."
            )
    else:
        history = None  # owner immunity

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply or use `/ban @username`")

    try:
        await client.ban_chat_member(chat_id, user.id)

        if not owner:
            history.append(now)
            await save_abuse_history(chat_id, admin_id, history)

        await message.reply_text(
            f"🚨 {user.mention} has been banned."
        )
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: {e}")
