import asyncio
import os
import re
import time
from logging import getLogger
from time import time as current_time

from pyrogram import Client, enums, filters
from pyrogram.errors import (
    ChatAdminRequired,
    FloodWait,
    PeerIdInvalid,
    UsernameNotOccupied,
)
from pyrogram.types import ChatMember, ChatPermissions, ChatPrivileges, Message, InlineKeyboardMarkup, InlineKeyboardButton

from ShrutixMusic import nand
from ShrutixMusic.core.mongo import mongodb
from config import BANNED_USERS, OWNER_ID

LOGGER = getLogger("ShrutixMusic")

# ==========================================================
# DATABASE LOGIC (ADAPTED FOR SHRUTIX)
# ==========================================================
warnsdb = mongodb.warns

async def get_warn(chat_id, name):
    return await warnsdb.find_one({"chat_id": chat_id, "name": name})

async def add_warn(chat_id, name, warn):
    await warnsdb.update_one(
        {"chat_id": chat_id, "name": name}, {"$set": warn}, upsert=True
    )

async def remove_warns(chat_id, name):
    await warnsdb.delete_many({"chat_id": chat_id, "name": name})

# ==========================================================
# HELPERS & DECORATORS (Locally Defined to avoid Import Errors)
# ==========================================================

SUDO = list(BANNED_USERS) # Using Banned set as placeholder or load sudoers if available
COMMAND_HANDLER = ["/", "!"]

def adminsOnly(permission):
    def sub_decorator(func):
        async def wrapper(client, message):
            if not message.from_user:
                return
            if message.from_user.id == OWNER_ID:
                return await func(client, message)
            try:
                member = await client.get_chat_member(message.chat.id, message.from_user.id)
                if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
                    return await message.reply_text("❌ You are not an admin.")
                
                # Permission Check
                if permission:
                    if getattr(member.privileges, permission, False):
                        return await func(client, message)
                    else:
                        return await message.reply_text(f"❌ You lack the permission: `{permission}`")
                return await func(client, message)
            except Exception as e:
                print(e)
        return wrapper
    return sub_decorator

# Dummy decorator for localization (since Shrutix logic differs)
def use_chat_lang():
    def decorator(func):
        async def wrapper(client, message, *args, **kwargs):
            # Simple strings wrapper
            def strings(key, **kwargs):
                # Basic Fallback Strings
                texts = {
                    "purge_no_reply": "Reply to a message to purge from.",
                    "purge_success": "Deleted {del_total} messages.",
                    "user_not_found": "User not found.",
                    "kick_self_err": "I can't kick myself.",
                    "kick_sudo_err": "I can't kick a sudo user.",
                    "kick_admin_err": "I can't kick an admin.",
                    "kick_msg": "{mention} [`{id}`] was kicked by {kicker}.\nReason: {reasonmsg}",
                    "no_ban_permission": "I don't have permission to restrict members.",
                    "ban_self_err": "I can't ban myself.",
                    "ban_sudo_err": "I can't ban a sudo user.",
                    "ban_admin_err": "I can't ban an admin.",
                    "ban_msg": "{mention} [`{id}`] was banned by {banner}.",
                    "banned_reason": "\nReason: {reas}",
                    "unban_channel_err": "You cannot unban a channel.",
                    "give_unban_user": "Give me a user to unban.",
                    "unban_success": "{umention} has been unbanned.",
                    "delete_no_reply": "Reply to a message to delete it.",
                    "no_delete_perm": "I don't have delete permission.",
                    "promote_self_err": "I can't promote myself.",
                    "no_promote_perm": "I don't have permission to add admins.",
                    "full_promote": "Fully Promoted {umention}!",
                    "normal_promote": "Promoted {umention}!",
                    "demote_self_err": "I can't demote myself.",
                    "demote_sudo_err": "I can't demote a sudo user.",
                    "pin_no_reply": "Reply to a message to pin it.",
                    "unpin_success": "Unpinned [Message]({link}).",
                    "pin_success": "Pinned [Message]({link}).",
                    "pin_no_perm": "I don't have pin permission.",
                    "mute_self_err": "I can't mute myself.",
                    "mute_sudo_err": "I can't mute a sudo user.",
                    "mute_admin_err": "I can't mute an admin.",
                    "mute_msg": "{mention} was muted by {muter}.",
                    "unmute_msg": "{umention} has been unmuted.",
                    "warn_self_err": "I can't warn myself.",
                    "warn_sudo_err": "I can't warn a sudo user.",
                    "warn_admin_err": "I can't warn an admin.",
                    "rm_warn_btn": "Remove Warn",
                    "exceed_warn_msg": "{mention} has exceeded warns and was banned.",
                    "warn_msg": "{mention} has been warned by {warner}.\nReason: {reas}\nWarns: {twarn}/3",
                    "user_no_warn": "{mention} has no warnings.",
                    "unwarn_msg": "Warn removed by {mention}.",
                    "rmmute_msg": "Unmuted by {mention}",
                    "unban_msg": "Unbanned by {mention}",
                    "reply_to_rm_warn": "Reply to a user to remove their warns.",
                    "rmwarn_msg": "Removed warns for {mention}.",
                    "ch_warn_msg": "{mention} has {warns}/3 warnings.",
                    "report_no_reply": "Reply to a message to report it.",
                    "report_self_err": "You can't report yourself.",
                    "reported_is_admin": "That user is an admin.",
                    "report_msg": "Reported {user_mention} to admins.",
                }
                msg = texts.get(key, key)
                return msg.format(**kwargs) if kwargs else msg
            
            return await func(client, message, strings)
        return wrapper
    return decorator

async def extract_user(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1:
        try:
            user = await nand.get_users(message.command[1])
            return user.id
        except:
            return None
    return None

async def extract_user_and_reason(message: Message, sender_chat=False):
    user_id = await extract_user(message)
    reason = None
    if len(message.command) > 1:
        parts = message.text.split(None, 2)
        if len(parts) > 2:
            reason = parts[2]
        if not user_id and not message.reply_to_message: 
             # If extraction failed but we have args, maybe arg 1 is user
             pass 
    elif message.reply_to_message:
        if len(message.command) > 1:
            reason = message.text.split(None, 1)[1]
    return user_id, reason

async def list_admins(chat_id):
    return [
        member.user.id
        async for member in nand.get_chat_members(
            chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
        )
    ]

async def int_to_alpha(user_id):
    return str(user_id)

def ikb(data: dict):
    keyboard = []
    for key, value in data.items():
        keyboard.append([InlineKeyboardButton(text=key, callback_data=value)])
    return InlineKeyboardMarkup(keyboard)

async def time_converter(message, time_val):
    unit = time_val[-1].lower()
    val = int(time_val[:-1])
    now = time.time()
    if unit == "m":
        return now + val * 60
    elif unit == "h":
        return now + val * 3600
    elif unit == "d":
        return now + val * 86400
    elif unit == "w":
        return now + val * 604800
    else:
        return None

# ==========================================================
# COMMANDS (Ported Logic)
# ==========================================================

# Purge CMD
@nand.on_message(filters.command("purge") & filters.group)
@adminsOnly("can_delete_messages")
@use_chat_lang()
async def purge(_, ctx: Message, strings):
    try:
        repliedmsg = ctx.reply_to_message
        await ctx.delete()

        if not repliedmsg:
            return await ctx.reply_text(strings("purge_no_reply"))

        cmd = ctx.command
        if len(cmd) > 1 and cmd[1].isdigit():
            purge_to = repliedmsg.id + int(cmd[1])
            purge_to = min(purge_to, ctx.id)
        else:
            purge_to = ctx.id

        chat_id = ctx.chat.id
        message_ids = []
        del_total = 0

        for message_id in range(
            repliedmsg.id,
            purge_to,
        ):
            message_ids.append(message_id)

            # Max message deletion limit is 100
            if len(message_ids) == 100:
                await nand.delete_messages(
                    chat_id=chat_id,
                    message_ids=message_ids,
                    revoke=True,
                )
                del_total += len(message_ids)
                message_ids = []

        if len(message_ids) > 0:
            await nand.delete_messages(
                chat_id=chat_id,
                message_ids=message_ids,
                revoke=True,
            )
            del_total += len(message_ids)
        await ctx.reply_text(strings("purge_success").format(del_total=del_total))
    except Exception as err:
        await ctx.reply_text(f"ERROR: {err}")


# Kick members
@nand.on_message(filters.command(["kick", "dkick"]) & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def kickFunc(client: Client, ctx: Message, strings):
    user_id, reason = await extract_user_and_reason(ctx)
    if not user_id:
        return await ctx.reply_text(strings("user_not_found"))
    if user_id == client.me.id:
        return await ctx.reply_text(strings("kick_self_err"))
    if user_id in SUDO or user_id == OWNER_ID:
        return await ctx.reply_text(strings("kick_sudo_err"))
    if user_id in (await list_admins(ctx.chat.id)):
        return await ctx.reply_text(strings("kick_admin_err"))
    try:
        user = await nand.get_users(user_id)
    except PeerIdInvalid:
        return await ctx.reply_text(strings("user_not_found"))
    
    msg = strings("kick_msg").format(
        mention=user.mention,
        id=user.id,
        kicker=ctx.from_user.mention if ctx.from_user else "Anon Admin",
        reasonmsg=reason or "-",
    )
    if ctx.command[0][0] == "d":
        if ctx.reply_to_message:
            await ctx.reply_to_message.delete()
    try:
        await ctx.chat.ban_member(user_id)
        await ctx.reply_text(msg)
        await asyncio.sleep(1)
        await ctx.chat.unban_member(user_id)
    except ChatAdminRequired:
        await ctx.reply_text(strings("no_ban_permission"))
    except Exception as e:
        await ctx.reply_text(str(e))


# Ban/DBan/TBan User
@nand.on_message(filters.command(["ban", "dban", "tban"]) & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def banFunc(client, message, strings):
    try:
        user_id, reason = await extract_user_and_reason(message, sender_chat=True)
    except UsernameNotOccupied:
        return await message.reply_text("Sorry, i didn't know that user.")

    if not user_id:
        return await message.reply_text(strings("user_not_found"))
    if user_id == client.me.id:
        return await message.reply_text(strings("ban_self_err"))
    if user_id in SUDO or user_id == OWNER_ID:
        return await message.reply_text(strings("ban_sudo_err"))
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text(strings("ban_admin_err"))

    try:
        mention = (await nand.get_users(user_id)).mention
    except:
        mention = "User"

    msg = strings("ban_msg").format(
        mention=mention,
        id=user_id,
        banner=message.from_user.mention if message.from_user else "Anon",
    )
    if message.command[0][0] == "d":
        if message.reply_to_message:
            await message.reply_to_message.delete()
    if message.command[0] == "tban":
        if not reason:
             return await message.reply_text("Provide time! Ex: /tban 1d")
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_ban = await time_converter(message, time_value)
        if not temp_ban:
             return await message.reply_text("Invalid time format.")
        msg += f"\nTime: {time_value}"
        if temp_reason:
            msg += strings("banned_reason").format(reas=temp_reason)
        try:
            await message.chat.ban_member(user_id, until_date=temp_ban)
            await message.reply_text(msg)
        except Exception as e:
            await message.reply_text(str(e))
        return

    if reason:
        msg += strings("banned_reason").format(reas=reason)
    keyboard = ikb({"🚨 Unban 🚨": f"unban_{user_id}"})
    try:
        await message.chat.ban_member(user_id)
        await message.reply_text(msg, reply_markup=keyboard)
    except ChatAdminRequired:
        await message.reply("Please give me permission to banned members..!!!")
    except Exception as e:
        await message.reply_text(str(e))


# Unban members
@nand.on_message(filters.command("unban") & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def unban_func(_, message, strings):
    reply = message.reply_to_message

    if reply and reply.sender_chat and reply.sender_chat != message.chat.id:
        return await message.reply_text(strings("unban_channel_err"))

    if len(message.command) == 2:
        try:
            user = await nand.get_users(message.command[1])
            user_id = user.id
        except:
             return await message.reply_text("User not found")
    elif len(message.command) == 1 and reply:
        user_id = message.reply_to_message.from_user.id
    else:
        return await message.reply_text(strings("give_unban_user"))
    try:
        await message.chat.unban_member(user_id)
        umention = (await nand.get_users(user_id)).mention
        await message.reply_text(strings("unban_success").format(umention=umention))
    except Exception as e:
        await message.reply_text(str(e))


# Delete messages
@nand.on_message(filters.command("del") & filters.group)
@adminsOnly("can_delete_messages")
@use_chat_lang()
async def deleteFunc(_, message, strings):
    if not message.reply_to_message:
        return await message.reply_text(strings("delete_no_reply"))
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except:
        await message.reply(strings("no_delete_perm"))


# Promote Members
@nand.on_message(filters.command(["promote", "fullpromote"]) & filters.group)
@adminsOnly("can_promote_members")
@use_chat_lang()
async def promoteFunc(client, message, strings):
    try:
        user_id = await extract_user(message)
        umention = (await client.get_users(user_id)).mention
    except:
        return await message.reply(strings("invalid_id_uname"))
    if not user_id:
        return await message.reply_text(strings("user_not_found"))
    
    me = await client.get_chat_member(message.chat.id, client.me.id)
    bot = me.privileges

    if user_id == client.me.id:
        return await message.reply_text(strings("promote_self_err"))
    if not bot:
        return await message.reply_text("I'm not an admin in this chat.")
    if not bot.can_promote_members:
        return await message.reply_text(strings("no_promote_perm"))
    try:
        if message.command[0][0] == "f":
            await message.chat.promote_member(
                user_id=user_id,
                privileges=ChatPrivileges(
                    can_change_info=bot.can_change_info,
                    can_invite_users=bot.can_invite_users,
                    can_delete_messages=bot.can_delete_messages,
                    can_restrict_members=bot.can_restrict_members,
                    can_pin_messages=bot.can_pin_messages,
                    can_promote_members=bot.can_promote_members,
                    can_manage_chat=bot.can_manage_chat,
                    can_manage_video_chats=bot.can_manage_video_chats,
                ),
            )
            return await message.reply_text(
                strings("full_promote").format(umention=umention)
            )

        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_invite_users=bot.can_invite_users,
                can_delete_messages=bot.can_delete_messages,
                can_restrict_members=bot.can_restrict_members,
                can_pin_messages=bot.can_pin_messages,
                can_promote_members=False,
                can_manage_chat=bot.can_manage_chat,
                can_manage_video_chats=bot.can_manage_video_chats,
            ),
        )
        await message.reply_text(strings("normal_promote").format(umention=umention))
    except Exception as err:
        await message.reply_text(str(err))


# Demote Member
@nand.on_message(filters.command("demote") & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def demote(client, message, strings):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text(strings("user_not_found"))
    if user_id == client.me.id:
        return await message.reply_text(strings("demote_self_err"))
    if user_id in SUDO or user_id == OWNER_ID:
        return await message.reply_text(strings("demote_sudo_err"))
    try:
        # Standard Demote (removes rights)
        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_invite_users=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_chat=False,
                can_manage_video_chats=False,
            ),
        )
        # Also Restrict to update status to member immediately (Fix for zombie admins)
        await message.chat.restrict_member(
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )

        umention = (await nand.get_users(user_id)).mention
        await message.reply_text(f"Demoted! {umention}")
    except ChatAdminRequired:
        await message.reply("Please give permission to demote members..")
    except Exception as e:
        await message.reply_text(str(e))


# Pin Messages
@nand.on_message(filters.command(["pin", "unpin"]) & filters.group)
@adminsOnly("can_pin_messages")
@use_chat_lang()
async def pin(_, message, strings):
    if not message.reply_to_message:
        return await message.reply_text(strings("pin_no_reply"))
    r = message.reply_to_message
    try:
        if message.command[0][0] == "u":
            await r.unpin()
            return await message.reply_text(
                strings("unpin_success").format(link=r.link),
                disable_web_page_preview=True,
            )
        await r.pin(disable_notification=True)
        await message.reply(
            strings("pin_success").format(link=r.link),
            disable_web_page_preview=True,
        )
    except ChatAdminRequired:
        await message.reply(
            strings("pin_no_perm"),
            disable_web_page_preview=True,
        )
    except Exception as e:
        await message.reply_text(str(e))


# Mute members
@nand.on_message(filters.command(["mute", "tmute"]) & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def mute(client, message, strings):
    try:
        user_id, reason = await extract_user_and_reason(message)
    except Exception as err:
        return await message.reply(f"ERROR: {err}")
    if not user_id:
        return await message.reply_text(strings("user_not_found"))
    if user_id == client.me.id:
        return await message.reply_text(strings("mute_self_err"))
    if user_id in SUDO or user_id == OWNER_ID:
        return await message.reply_text(strings("mute_sudo_err"))
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text(strings("mute_admin_err"))
    mention = (await nand.get_users(user_id)).mention
    keyboard = ikb({"🚨 Unmute 🚨": f"unmute_{user_id}"})
    msg = strings("mute_msg").format(
        mention=mention,
        muter=message.from_user.mention if message.from_user else "Anon",
    )
    if message.command[0] == "tmute":
        if not reason:
             return await message.reply_text("Provide time! Ex: /tmute 1h")
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_mute = await time_converter(message, time_value)
        if not temp_mute:
            return await message.reply_text("Invalid Time")

        msg += f"\nTime: {time_value}"
        if temp_reason:
            msg += strings("banned_reason").format(reas=temp_reason)
        try:
            await message.chat.restrict_member(
                user_id,
                permissions=ChatPermissions(all_perms=False),
                until_date=temp_mute,
            )
            await message.reply_text(msg, reply_markup=keyboard)
        except Exception as e:
            await message.reply_text(str(e))
        return

    if reason:
        msg += strings("banned_reason").format(reas=reason)
    try:
        await message.chat.restrict_member(
            user_id, permissions=ChatPermissions(all_perms=False)
        )
        await message.reply_text(msg, reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(str(e))


# Unmute members
@nand.on_message(filters.command("unmute") & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def unmute(_, message, strings):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text(strings("user_not_found"))
    try:
        await message.chat.restrict_member(
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        umention = (await nand.get_users(user_id)).mention
        await message.reply_text(strings("unmute_msg").format(umention=umention))
    except Exception as e:
        await message.reply_text(str(e))


@nand.on_message(filters.command(["warn", "dwarn"]) & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def warn_user(client, message, strings):
    try:
        user_id, reason = await extract_user_and_reason(message)
    except:
        return await message.reply_text("Sorry, i didn't know that user.")
    chat_id = message.chat.id
    if not user_id:
        return await message.reply_text(strings("user_not_found"))
    if user_id == client.me.id:
        return await message.reply_text(strings("warn_self_err"))
    if user_id in SUDO or user_id == OWNER_ID:
        return await message.reply_text(strings("warn_sudo_err"))
    if user_id in (await list_admins(chat_id)):
        return await message.reply_text(strings("warn_admin_err"))
    
    user = await nand.get_users(user_id)
    warns = await get_warn(chat_id, str(user_id))
    
    mention = user.mention
    keyboard = ikb({strings("rm_warn_btn"): f"unwarn_{user_id}"})
    warns = warns["warns"] if warns else 0
    if message.command[0][0] == "d":
        if message.reply_to_message:
            await message.reply_to_message.delete()
    if warns >= 2:
        try:
            await message.chat.ban_member(user_id)
            await message.reply_text(strings("exceed_warn_msg").format(mention=mention))
            await remove_warns(chat_id, str(user_id))
        except ChatAdminRequired:
            await message.reply_text(strings("no_ban_permission"))
    else:
        warn = {"warns": warns + 1}
        msg = strings("warn_msg").format(
            mention=mention,
            warner=message.from_user.mention if message.from_user else "Anon",
            reas=reason or "No Reason Provided.",
            twarn=warns + 1,
        )
        await message.reply_text(msg, reply_markup=keyboard)
        await add_warn(chat_id, str(user_id), warn)


@nand.on_callback_query(filters.regex("unwarn_"))
@use_chat_lang()
async def remove_warning(_, cq, strings):
    from_user = cq.from_user
    chat_id = cq.message.chat.id
    # Simple Perm Check
    member = await nand.get_chat_member(chat_id, from_user.id)
    if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
         return await cq.answer("You are not an admin.", show_alert=True)
    
    user_id = int(cq.data.split("_")[1])
    warns = await get_warn(chat_id, str(user_id))
    if warns:
        warns = warns["warns"]
    if not warns or warns == 0:
        return await cq.answer(
            strings("user_no_warn").format(
                mention=cq.message.reply_to_message.from_user.id
            )
        )
    warn = {"warns": warns - 1}
    await add_warn(chat_id, str(user_id), warn)
    text = cq.message.text.markdown
    text = f"~~{text}~~\n\n"
    text += strings("unwarn_msg").format(mention=from_user.mention)
    await cq.message.edit(text)


@nand.on_callback_query(filters.regex("unmute_"))
@use_chat_lang()
async def unmute_user(_, cq, strings):
    from_user = cq.from_user
    chat_id = cq.message.chat.id
    member = await nand.get_chat_member(chat_id, from_user.id)
    if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
         return await cq.answer("You are not an admin.", show_alert=True)

    user_id = int(cq.data.split("_")[1])
    text = cq.message.text.markdown
    text = f"~~{text}~~\n\n"
    text += strings("rmmute_msg").format(mention=from_user.mention)
    try:
        await cq.message.chat.restrict_member(
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await cq.message.edit(text)
    except Exception as e:
        await cq.answer(str(e))


@nand.on_callback_query(filters.regex("unban_"))
@use_chat_lang()
async def unban_user(_, cq, strings):
    from_user = cq.from_user
    chat_id = cq.message.chat.id
    member = await nand.get_chat_member(chat_id, from_user.id)
    if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
         return await cq.answer("You are not an admin.", show_alert=True)
         
    user_id = int(cq.data.split("_")[1])
    text = cq.message.text.markdown
    text = f"~~{text}~~\n\n"
    text += strings("unban_msg").format(mention=from_user.mention)
    try:
        await cq.message.chat.unban_member(user_id)
        await cq.message.edit(text)
    except Exception as e:
        await cq.answer(str(e))


# Remove Warn
@nand.on_message(filters.command("rmwarn") & filters.group)
@adminsOnly("can_restrict_members")
@use_chat_lang()
async def remove_warnings(_, message, strings):
    if not message.reply_to_message:
        return await message.reply_text(strings("reply_to_rm_warn"))
    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention
    chat_id = message.chat.id
    warns = await get_warn(chat_id, str(user_id))
    if warns:
        warns = warns["warns"]
    if warns == 0 or not warns:
        await message.reply_text(strings("user_no_warn").format(mention=mention))
    else:
        await remove_warns(chat_id, str(user_id))
        await message.reply_text(strings("rmwarn_msg").format(mention=mention))


# Warns
@nand.on_message(filters.command("warns") & filters.group)
@use_chat_lang()
async def check_warns(_, message, strings):
    if not message.from_user:
        return
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text(strings("user_not_found"))
    warns = await get_warn(message.chat.id, str(user_id))
    mention = (await nand.get_users(user_id)).mention
    if warns:
        warns = warns["warns"]
    else:
        return await message.reply_text(strings("user_no_warn").format(mention=mention))
    return await message.reply_text(
        strings("ch_warn_msg").format(mention=mention, warns=warns)
    )


# Report User in Group
@nand.on_message(
    (
        filters.command("report")
        | filters.command(["admins", "admin"], prefixes="@")
    )
    & filters.group
)
@use_chat_lang()
async def report_user(_, ctx: Message, strings):
    if len(ctx.text.split()) <= 1 and not ctx.reply_to_message:
        return await ctx.reply_text(strings("report_no_reply"))
    reply = ctx.reply_to_message if ctx.reply_to_message else ctx
    reply_id = reply.from_user.id if reply.from_user else reply.sender_chat.id
    user_id = ctx.from_user.id if ctx.from_user else ctx.sender_chat.id
    if reply_id == user_id:
        return await ctx.reply_text(strings("report_self_err"))

    list_of_admins = await list_admins(ctx.chat.id)
    if reply_id in list_of_admins:
        return await ctx.reply_text(strings("reported_is_admin"))

    user_mention = (
        reply.from_user.mention if reply.from_user else reply.sender_chat.title
    )
    text = strings("report_msg").format(user_mention=user_mention)
    admin_data = [
        m
        async for m in nand.get_chat_members(
            ctx.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS
        )
    ]
    for admin in admin_data:
        if admin.user.is_bot or admin.user.is_deleted:
            continue
        text += f"<a href='tg://user?id={admin.user.id}'>\u2063</a>"
    await reply.reply_text(text)


@nand.on_message(filters.command("set_chat_title") & filters.group)
@adminsOnly("can_change_info")
async def set_chat_title(_, ctx: Message):
    if len(ctx.command) < 2:
        return await ctx.reply_text(f"**Usage:**\n/{ctx.command[0]} NEW NAME")
    old_title = ctx.chat.title
    new_title = ctx.text.split(None, 1)[1]
    try:
        await ctx.chat.set_title(new_title)
        await ctx.reply_text(
            f"Successfully Changed Group Title From {old_title} To {new_title}"
        )
    except Exception as e:
        await ctx.reply_text(str(e))


@nand.on_message(filters.command("set_user_title") & filters.group)
@adminsOnly("can_change_info")
async def set_user_title(_, ctx: Message):
    if not ctx.reply_to_message:
        return await ctx.reply_text("Reply to user's message to set his admin title")
    if not ctx.reply_to_message.from_user:
        return await ctx.reply_text("I can't change admin title of an unknown entity")
    chat_id = ctx.chat.id
    from_user = ctx.reply_to_message.from_user
    if len(ctx.command) < 2:
        return await ctx.reply_text(
            "**Usage:**\n/set_user_title NEW ADMINISTRATOR TITLE"
        )
    title = ctx.text.split(None, 1)[1]
    try:
        await nand.set_administrator_title(chat_id, from_user.id, title)
        await ctx.reply_text(
            f"Successfully Changed {from_user.mention}'s Admin Title To {title}"
        )
    except Exception as e:
        await ctx.reply_text(str(e))


@nand.on_message(filters.command("set_chat_photo") & filters.group)
@adminsOnly("can_change_info")
async def set_chat_photo(_, ctx: Message):
    reply = ctx.reply_to_message

    if not reply:
        return await ctx.reply_text("Reply to a photo to set it as chat_photo")

    file = reply.document or reply.photo
    if not file:
        return await ctx.reply_text(
            "Reply to a photo or document to set it as chat_photo"
        )

    if file.file_size > 5000000:
        return await ctx.reply("File size too large.")

    photo = await reply.download()
    try:
        await ctx.chat.set_photo(photo=photo)
        await ctx.reply_text("Successfully Changed Group Photo")
    except Exception as err:
        await ctx.reply(f"Failed changed group photo. ERROR: {err}")
    os.remove(photo)


@nand.on_message(filters.group & filters.command("mentionall"))
async def mentionall(app: Client, msg: Message):
    user = await msg.chat.get_member(msg.from_user.id)
    if user.status in (
        enums.ChatMemberStatus.OWNER,
        enums.ChatMemberStatus.ADMINISTRATOR,
    ):
        total = []
        async for member in app.get_chat_members(msg.chat.id):
            if member.user.username:
                total.append(f"@{member.user.username}")
            else:
                total.append(member.user.mention())

        NUM = 4
        for i in range(0, len(total), NUM):
            message = " ".join(total[i : i + NUM])
            await app.send_message(
                msg.chat.id, message
            )
    else:
        await app.send_message(
            msg.chat.id, "Admins only can do that !", reply_to_message_id=msg.id
        )
