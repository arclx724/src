from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from ShrutixMusic import nand

ERROR_TEXT = "I don't know who you're talking about, you're going to need to specify a user...!"


async def extract_target(client, message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user

    if len(message.command) > 1:
        try:
            return await client.get_users(message.command[1])
        except:
            return None
    return None


@nand.on_message(filters.command("promote") & filters.group)
async def promote_handler(client, message: Message):

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    issuer = await client.get_chat_member(message.chat.id, message.from_user.id)
    if issuer.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    await client.promote_chat_member(
        chat_id=message.chat.id,
        user_id=target.id,
        can_change_info=True,
        can_delete_messages=True,
        can_invite_users=True,
        can_restrict_members=True,
        can_pin_messages=True,
        can_promote_members=False
    )

    await message.reply(f"✅ {target.mention} promoted successfully.")


@nand.on_message(filters.command("demote") & filters.group)
async def demote_handler(client, message: Message):

    target = await extract_target(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    issuer = await client.get_chat_member(message.chat.id, message.from_user.id)
    if issuer.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    await client.promote_chat_member(
        chat_id=message.chat.id,
        user_id=target.id,
        can_change_info=False,
        can_delete_messages=False,
        can_invite_users=False,
        can_restrict_members=False,
        can_pin_messages=False,
        can_promote_members=False
    )

    await message.reply(f"✅ {target.mention} demoted successfully.")
