import asyncio
from pyrogram import filters
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.misc import SUDOERS

# ==========================================================
#                  STORAGE (Temporary Memory)
# ==========================================================

NSFW_SETTINGS = {}

# ==========================================================
#                  HELPER FUNCTIONS
# ==========================================================

async def is_owner_or_sudo(user_id: int):
    return user_id in SUDOERS


async def has_change_info_permission(chat_id, user_id):
    member = await nand.get_chat_member(chat_id, user_id)
    if member.status == ChatMemberStatus.OWNER:
        return True
    if member.status == ChatMemberStatus.ADMINISTRATOR:
        return member.privileges.can_change_info
    return False


async def bot_can_delete(chat_id):
    bot = await nand.get_chat_member(chat_id, "me")
    return bot.privileges and bot.privileges.can_delete_messages


async def bot_can_ban(chat_id):
    bot = await nand.get_chat_member(chat_id, "me")
    return bot.privileges and bot.privileges.can_restrict_members


def init_chat(chat_id):
    NSFW_SETTINGS.setdefault(chat_id, {
        "enabled": False,
        "silent": False,
        "punish": False,
        "warns": {}
    })


# ==========================================================
#                  /addamthy
# ==========================================================

@nand.on_message(filters.command("addamthy") & filters.private)
async def addamthy_handler(client, message):

    if not await is_owner_or_sudo(message.from_user.id):
        return await message.reply_text(
            "❌ Only Owner or Sudo users can use this command."
        )

    if len(message.command) < 2:
        return await message.reply_text("Usage: /addamthy user_id")

    try:
        user_id = int(message.command[1])
        SUDOERS.add(user_id)
        await message.reply_text(f"✅ {user_id} added as Sudo user.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


# ==========================================================
#                  /nsfw (MASTER)
# ==========================================================

@nand.on_message(filters.command("nsfw") & filters.group)
async def nsfw_master(client, message):

    if not await has_change_info_permission(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "❌ You need 'Change Group Info' permission."
        )

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfw on/off")

    chat_id = message.chat.id
    init_chat(chat_id)

    if message.command[1].lower() == "on":
        NSFW_SETTINGS[chat_id]["enabled"] = True
        await message.reply_text("✅ NSFW Protection Enabled.")
    else:
        NSFW_SETTINGS[chat_id]["enabled"] = False
        await message.reply_text("❌ NSFW Protection Disabled.")


# ==========================================================
#                  /nsfwsilent
# ==========================================================

@nand.on_message(filters.command("nsfwsilent") & filters.group)
async def nsfw_silent(client, message):

    if not await has_change_info_permission(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "❌ You need 'Change Group Info' permission."
        )

    chat_id = message.chat.id
    init_chat(chat_id)

    if not NSFW_SETTINGS[chat_id]["enabled"]:
        return await message.reply_text("⚠ Enable /nsfw on first.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwsilent on/off")

    NSFW_SETTINGS[chat_id]["silent"] = message.command[1].lower() == "on"

    await message.reply_text(
        f"✅ Silent Mode {'Enabled' if NSFW_SETTINGS[chat_id]['silent'] else 'Disabled'}."
    )


# ==========================================================
#                  /nsfwpunish
# ==========================================================

@nand.on_message(filters.command("nsfwpunish") & filters.group)
async def nsfw_punish(client, message):

    if not await has_change_info_permission(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "❌ You need 'Change Group Info' permission."
        )

    chat_id = message.chat.id
    init_chat(chat_id)

    if not NSFW_SETTINGS[chat_id]["enabled"]:
        return await message.reply_text("⚠ Enable /nsfw on first.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwpunish on/off")

    NSFW_SETTINGS[chat_id]["punish"] = message.command[1].lower() == "on"

    await message.reply_text(
        f"⚔ Punish Mode {'Enabled' if NSFW_SETTINGS[chat_id]['punish'] else 'Disabled'}."
    )


# ==========================================================
#                  /nsfwcommands
# ==========================================================

@nand.on_message(filters.command(["nsfwcommands", "nsfwcommand"]) & filters.group)
async def nsfw_help(client, message):

    text = """
📛 <b>NSFW Protection Commands</b>

• /nsfw on/off → Enable or Disable Protection
• /nsfwsilent on/off → Silent Delete Mode
• /nsfwpunish on/off → Auto Ban After 3 Warnings
• /addamthy user_id → Add Sudo (Owner Only)

⚠ Only admins with Change Info rights can use control commands.
"""

    await message.reply_text(text)


# ==========================================================
#                  NSFW WATCHER
# ==========================================================

@nand.on_message(filters.group & (filters.sticker | filters.photo | filters.video))
async def nsfw_watcher(client, message):

    chat_id = message.chat.id
    init_chat(chat_id)

    settings = NSFW_SETTINGS[chat_id]

    if not settings["enabled"]:
        return

    user = message.from_user
    if not user:
        return

    member = await nand.get_chat_member(chat_id, user.id)

    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    if not await bot_can_delete(chat_id):
        return await message.reply_text(
            "❌ I don't have delete permission."
        )

    try:
        await message.delete()
    except ChatAdminRequired:
        return

    # WARN SYSTEM
    warns = settings["warns"]
    warns[user.id] = warns.get(user.id, 0) + 1
    count = warns[user.id]

    if not settings["silent"]:
        warn_msg = await nand.send_message(
            chat_id,
            f"⚠ {user.mention}\n"
            f"Your message contains restricted content and was removed.\n"
            f"Warnings: {count}/3"
        )

        await asyncio.sleep(60)
        await warn_msg.delete()

    # AUTO BAN
    if settings["punish"] and count >= 3:

        if not await bot_can_ban(chat_id):
            return await nand.send_message(
                chat_id,
                "❌ I don't have ban permission."
            )

        try:
            await nand.ban_chat_member(chat_id, user.id)
            await nand.send_message(
                chat_id,
                f"🚫 {user.mention} has been banned (3/3 warnings)."
            )
        except UserAdminInvalid:
            await nand.send_message(
                chat_id,
                "❌ Cannot ban this user."
            )
