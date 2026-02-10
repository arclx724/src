from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message

ERROR_TEXT = "I don't know who you're talking about, you're going to need to specify a user...!"


async def extract_target_and_title(client: Client, message: Message):
    target = None
    title = None

    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if len(message.command) > 1:
            title = " ".join(message.command[1:])

    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1])
        except Exception:
            return None, None

        if len(message.command) > 2:
            title = " ".join(message.command[2:])

    return target, title


@Client.on_message(filters.command("promote") & filters.group)
async def promote_handler(client: Client, message: Message):

    if not message.from_user:
        return

    # ✅ FIRST: extract target
    target, title = await extract_target_and_title(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    # ✅ THEN: permission check
    issuer = await client.get_chat_member(message.chat.id, message.from_user.id)
    if issuer.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    target_member = await client.get_chat_member(message.chat.id, target.id)

    # AUTO-DETECT OWNER IMMUNITY
    if target_member.status == ChatMemberStatus.OWNER:
        return await message.reply("👑 Group owner ko promote ya demote nahi kiya ja sakta.")

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_video_chats=True
        )

        if title:
            try:
                await client.set_administrator_title(
                    chat_id=message.chat.id,
                    user_id=target.id,
                    title=title[:16]
                )
            except Exception:
                pass

        await message.reply(f"✅ {target.mention} promoted successfully.")

    except Exception as e:
        await message.reply(f"❌ Error:\n`{e}`")


@Client.on_message(filters.command("demote") & filters.group)
async def demote_handler(client: Client, message: Message):

    if not message.from_user:
        return

    # ✅ FIRST: extract target
    target, _ = await extract_target_and_title(client, message)
    if not target:
        return await message.reply(ERROR_TEXT)

    # ✅ THEN: permission check
    issuer = await client.get_chat_member(message.chat.id, message.from_user.id)
    if issuer.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    target_member = await client.get_chat_member(message.chat.id, target.id)

    # AUTO-DETECT OWNER IMMUNITY
    if target_member.status == ChatMemberStatus.OWNER:
        return await message.reply("👑 Group owner ko promote ya demote nahi kiya ja sakta.")

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_video_chats=False
        )

        await message.reply(f"✅ {target.mention} demoted successfully.")

    except Exception as e:
        await message.reply(f"❌ Error:\n`{e}`")
