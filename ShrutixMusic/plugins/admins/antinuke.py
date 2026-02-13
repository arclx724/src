import time
from pyrogram import filters
from pyrogram.types import ChatMemberUpdated, ChatPrivileges, Message
from pyrogram.enums import ChatMemberStatus, ParseMode

from ShrutixMusic import nand
from ShrutixMusic.utils.db import (
    whitelist_user,
    unwhitelist_user,
    is_user_whitelisted,
    get_whitelisted_users
)
from config import OWNER_ID

# ================= CONFIG =================

LIMIT = 3
TIME_FRAME = 30

TRAFFIC = {}              # {chat_id: {user_id: [timestamps]}}
WHITELIST_CACHE = {}      # {chat_id: set(user_ids)}
PUNISHED_USERS = set()    # Prevent repeated punishment spam


# ================= HELPER =================

async def load_whitelist(chat_id):
    if chat_id not in WHITELIST_CACHE:
        users = await get_whitelisted_users(chat_id)
        WHITELIST_CACHE[chat_id] = set(users)


async def punish_nuker(client, chat_id, user, count):

    if user.id in PUNISHED_USERS:
        return

    try:
        # Hierarchy Check
        bot_member = await client.get_chat_member(chat_id, client.me.id)
        actor_member = await client.get_chat_member(chat_id, user.id)

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            return

        if actor_member.status != ChatMemberStatus.ADMINISTRATOR:
            return

        # Demote (Remove all privileges)
        await client.promote_chat_member(
            chat_id,
            user.id,
            privileges=ChatPrivileges(
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
        )

        # Restrict Sending (extra safety)
        await client.restrict_chat_member(
            chat_id,
            user.id,
            permissions=ChatPrivileges(
                can_send_messages=False
            )
        )

        await client.send_message(
            chat_id,
            f"<b>🚨 ANTI-NUKE TRIGGERED</b>\n\n"
            f"<b>Admin:</b> {user.mention}\n"
            f"<b>Actions:</b> {count}/{LIMIT}\n"
            f"<b>Penalty:</b> Demoted & Restricted.",
            parse_mode=ParseMode.HTML
        )

        PUNISHED_USERS.add(user.id)

    except Exception:
        await client.send_message(
            chat_id,
            f"⚠️ <b>Security Alert:</b> Detected mass-action by {user.mention}, "
            f"but I cannot demote them (Hierarchy issue).",
            parse_mode=ParseMode.HTML
        )


# ================= WHITELIST COMMANDS =================

@nand.on_message(filters.command("whitelist") & filters.group)
async def whitelist_handler(client, message: Message):

    member = await client.get_chat_member(message.chat.id, message.from_user.id)

    if member.status != ChatMemberStatus.OWNER and message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only Group Owner can whitelist users.")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to whitelist.")

    user = message.reply_to_message.from_user

    await whitelist_user(message.chat.id, user.id)
    await load_whitelist(message.chat.id)
    WHITELIST_CACHE[message.chat.id].add(user.id)

    await message.reply_text(f"🛡️ {user.mention} is now Whitelisted.")


@nand.on_message(filters.command("unwhitelist") & filters.group)
async def unwhitelist_handler(client, message: Message):

    member = await client.get_chat_member(message.chat.id, message.from_user.id)

    if member.status != ChatMemberStatus.OWNER and message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only Group Owner can use this.")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user.")

    user = message.reply_to_message.from_user

    await unwhitelist_user(message.chat.id, user.id)
    await load_whitelist(message.chat.id)
    WHITELIST_CACHE[message.chat.id].discard(user.id)

    await message.reply_text(f"⚠️ {user.mention} removed from whitelist.")


# ================= MAIN WATCHER =================

@nand.on_chat_member_updated(filters.group, group=5)
async def nuke_watcher(client, update: ChatMemberUpdated):

    chat = update.chat

    if not update.from_user:
        return

    actor = update.from_user

    # Ignore bot & global owner
    if actor.id == client.me.id or actor.id == OWNER_ID:
        return

    # Load whitelist cache
    await load_whitelist(chat.id)

    if actor.id in WHITELIST_CACHE.get(chat.id, set()):
        return

    # ===== REAL BAN DETECTION =====

    if not update.old_chat_member or not update.new_chat_member:
        return

    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status

    # Detect only REAL bans (not voluntary leave)
    if not (
        old_status != ChatMemberStatus.BANNED and
        new_status == ChatMemberStatus.BANNED
    ):
        return

    target = update.new_chat_member.user

    # Ignore self leave
    if actor.id == target.id:
        return

    # ===== TRAFFIC LOGIC =====

    current_time = time.time()

    TRAFFIC.setdefault(chat.id, {})
    TRAFFIC[chat.id].setdefault(actor.id, [])

    TRAFFIC[chat.id][actor.id].append(current_time)

    # Remove old timestamps
    TRAFFIC[chat.id][actor.id] = [
        t for t in TRAFFIC[chat.id][actor.id]
        if current_time - t < TIME_FRAME
    ]

    count = len(TRAFFIC[chat.id][actor.id])

    if count >= LIMIT:
        await punish_nuker(client, chat.id, actor, count)
        TRAFFIC[chat.id][actor.id] = []

    # Memory cleanup (prevent RAM leak)
    if len(TRAFFIC) > 1000:
        TRAFFIC.clear()
