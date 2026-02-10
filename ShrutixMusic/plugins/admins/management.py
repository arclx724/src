import time
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatPermissions
from pyrogram.types import Message, ChatPrivileges
from ShrutixMusic import nand
from ShrutixMusic.core.mongo import db

# ---------------- CONFIG ---------------- #

BAN_LIMIT = 5
KICK_LIMIT = 10
RESET_TIME = 86400  # 24 hours

limits = db.admin_limits

ERROR_TEXT = "I don't know who you're talking about, you're going to need to specify a user...!"


# ---------------- HELPERS ---------------- #

async def is_admin(client, chat_id, user_id):
    member = await client.get_chat_member(chat_id, user_id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def extract_target(client, message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        try:
            return await client.get_users(message.command[1])
        except:
            return None
    return None


async def check_limit(user_id: int, key: str, limit: int):
    now = int(time.time())
    data = await limits.find_one({"user_id": user_id})

    if not data or data["reset_at"] < now:
        await limits.update_one(
            {"user_id": user_id},
            {"$set": {"ban": 0, "kick": 0, "reset_at": now + RESET_TIME}},
            upsert=True
        )
        data = {"ban": 0, "kick": 0}

    if data[key] >= limit:
        return False

    await limits.update_one(
        {"user_id": user_id},
        {"$inc": {key: 1}}
    )
    return True


# ---------------- PROMOTE / DEMOTE ---------------- #

@nand.on_message(filters.command("promote") & filters.group)
async def promote(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    privileges = ChatPrivileges(
        can_change_info=True,
        can_delete_messages=True,
        can_invite_users=True,
        can_restrict_members=True,
        can_pin_messages=True,
        can_promote_members=False
    )

    await client.promote_chat_member(message.chat.id, target.id, privileges)
    await message.reply(f"✅ {target.mention} promoted.")


@nand.on_message(filters.command("demote") & filters.group)
async def demote(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    privileges = ChatPrivileges(
        can_change_info=False,
        can_delete_messages=False,
        can_invite_users=False,
        can_restrict_members=False,
        can_pin_messages=False,
        can_promote_members=False
    )

    await client.promote_chat_member(message.chat.id, target.id, privileges)
    await message.reply(f"✅ {target.mention} demoted.")


# ---------------- ADMIN TITLE ---------------- #

@nand.on_message(filters.command("title") & filters.group)
async def title(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message or len(message.command) < 2:
        return await message.reply("Reply to an admin with `/title text`")

    title = " ".join(message.command[1:])[:16]

    await client.set_administrator_title(
        message.chat.id,
        message.reply_to_message.from_user.id,
        title
    )
    await message.reply("✅ Admin title updated.")


# ---------------- BAN / UNBAN ---------------- #

@nand.on_message(filters.command("ban") & filters.group)
async def ban(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    allowed = await check_limit(message.from_user.id, "ban", BAN_LIMIT)
    if not allowed:
        return await message.reply("❌ Ban limit reached (5 per 24h).")

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    await client.ban_chat_member(message.chat.id, target.id)
    await message.reply(f"🚫 {target.mention} banned.")


@nand.on_message(filters.command("unban") & filters.group)
async def unban(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    await client.unban_chat_member(message.chat.id, target.id)
    await message.reply(f"✅ {target.mention} unbanned.")


# ---------------- KICK ---------------- #

@nand.on_message(filters.command("kick") & filters.group)
async def kick(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    allowed = await check_limit(message.from_user.id, "kick", KICK_LIMIT)
    if not allowed:
        return await message.reply("❌ Kick limit reached (10 per 24h).")

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    await client.ban_chat_member(message.chat.id, target.id)
    await client.unban_chat_member(message.chat.id, target.id)
    await message.reply(f"👢 {target.mention} kicked.")


# ---------------- MUTE / UNMUTE ---------------- #

@nand.on_message(filters.command("mute") & filters.group)
async def mute(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    await client.restrict_chat_member(message.chat.id, target.id, ChatPermissions())
    await message.reply(f"🔇 {target.mention} muted.")


@nand.on_message(filters.command("unmute") & filters.group)
async def unmute(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    await client.restrict_chat_member(
        message.chat.id,
        target.id,
        ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    await message.reply(f"🔊 {target.mention} unmuted.")
