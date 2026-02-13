import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid

from ShrutixMusic import app
from ShrutixMusic.misc import SUDOERS
from ShrutixMusic.utils.database import add_sudo

# ================= SETTINGS STORAGE =================

NSFW_SETTINGS = {}

# ================= HELPER FUNCTIONS =================

async def is_owner_or_sudo(user_id: int):
    if user_id in SUDOERS:
        return True
    return False


async def can_change_info(client, chat_id, user_id):
    member = await client.get_chat_member(chat_id, user_id)
    return member.privileges and member.privileges.can_change_info


async def bot_has_delete_rights(client, chat_id):
    bot = await client.get_chat_member(chat_id, "me")
    return bot.privileges and bot.privileges.can_delete_messages


async def bot_has_ban_rights(client, chat_id):
    bot = await client.get_chat_member(chat_id, "me")
    return bot.privileges and bot.privileges.can_restrict_members


# ================= ADDAMTHY COMMAND =================

@app.on_message(filters.command("addamthy") & filters.private)
async def addamthy_command(client, message):

    if not await is_owner_or_sudo(message.from_user.id):
        return await message.reply_text(
            "❌ Only Owner or Sudo users can use this command."
        )

    if len(message.command) < 2:
        return await message.reply_text("Usage: /addamthy user_id")

    try:
        user_id = int(message.command[1])
        await add_sudo(user_id)
        await message.reply_text(f"✅ Successfully added `{user_id}` as Sudo.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


# ================= MASTER NSFW =================

@app.on_message(filters.command("nsfw") & filters.group)
async def nsfw_toggle(client, message):

    if not await can_change_info(client, message.chat.id, message.from_user.id):
        return await message.reply_text(
            "❌ You need 'Change Group Info' permission to use this."
        )

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfw on/off")

    chat_id = message.chat.id

    NSFW_SETTINGS.setdefault(chat_id, {
        "enabled": False,
        "silent": False,
        "punish": False,
        "warns": {}
    })

    if message.command[1].lower() == "on":
        NSFW_SETTINGS[chat_id]["enabled"] = True
        await message.reply_text("✅ NSFW Protection Enabled.")
    else:
        NSFW_SETTINGS[chat_id]["enabled"] = False
        await message.reply_text("❌ NSFW Protection Disabled.")


# ================= SILENT =================

@app.on_message(filters.command("nsfwsilent") & filters.group)
async def nsfw_silent(client, message):

    if not await can_change_info(client, message.chat.id, message.from_user.id):
        return await message.reply_text(
            "❌ You need 'Change Group Info' permission."
        )

    chat_id = message.chat.id
    settings = NSFW_SETTINGS.get(chat_id)

    if not settings or not settings["enabled"]:
        return await message.reply_text("⚠ Enable /nsfw on first.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwsilent on/off")

    settings["silent"] = message.command[1].lower() == "on"

    await message.reply_text(
        f"✅ Silent Mode {'Enabled' if settings['silent'] else 'Disabled'}."
    )


# ================= PUNISH =================

@app.on_message(filters.command("nsfwpunish") & filters.group)
async def nsfw_punish(client, message):

    if not await can_change_info(client, message.chat.id, message.from_user.id):
        return await message.reply_text(
            "❌ You need 'Change Group Info' permission."
        )

    chat_id = message.chat.id
    settings = NSFW_SETTINGS.get(chat_id)

    if not settings or not settings["enabled"]:
        return await message.reply_text("⚠ Enable /nsfw on first.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nsfwpunish on/off")

    settings["punish"] = message.command[1].lower() == "on"

    await message.reply_text(
        f"⚔ Smart Punish {'Enabled' if settings['punish'] else 'Disabled'}."
    )


# ================= COMMAND LIST =================

@app.on_message(filters.command(["nsfwcommands", "nsfwcommand"]) & filters.group)
async def nsfw_commands(client, message):

    text = """
📛 **NSFW Protection Commands**

/nsfw on/off → Master Switch
/nsfwsilent on/off → Silent Delete Mode
/nsfwpunish on/off → Auto Ban After 3 Warnings
/addamthy user_id → Add Sudo (Owner Only)
"""

    await message.reply_text(text)


# ================= NSFW WATCHER =================

@app.on_message(filters.group & (filters.sticker | filters.photo | filters.video))
async def nsfw_watcher(client, message):

    chat_id = message.chat.id
    settings = NSFW_SETTINGS.get(chat_id)

    if not settings or not settings["enabled"]:
        return

    if not await bot_has_delete_rights(client, chat_id):
        return await message.reply_text(
            "❌ I don't have permission to delete messages."
        )

    user = message.from_user
    if not user:
        return

    member = await client.get_chat_member(chat_id, user.id)
    if member.status in ["administrator", "creator"]:
        return

    try:
        await message.delete()
    except ChatAdminRequired:
        return

    # WARNING SYSTEM
    warns = settings["warns"]
    warns[user.id] = warns.get(user.id, 0) + 1
    count = warns[user.id]

    if not settings["silent"]:
        warn_msg = await client.send_message(
            chat_id,
            f"⚠ {user.mention}\n"
            f"Your message contains NSFW content and was removed.\n"
            f"Warnings: {count}/3"
        )

        await asyncio.sleep(60)
        await warn_msg.delete()

    # BAN IF ENABLED
    if settings["punish"] and count >= 3:

        if not await bot_has_ban_rights(client, chat_id):
            return await client.send_message(
                chat_id,
                "❌ I don't have ban permission."
            )

        try:
            await client.ban_chat_member(chat_id, user.id)
            await client.send_message(
                chat_id,
                f"🚫 {user.mention} has been banned (3/3 warnings)."
            )
        except UserAdminInvalid:
            await client.send_message(
                chat_id,
                "❌ Cannot ban this user."
            )
