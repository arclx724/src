import asyncio
import random
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ShrutixMusic import nand
from config import BOT_USERNAME

# ================= STORAGE =================
ANTI_EDIT_SETTINGS = {}  # chat_id: {"enabled": bool, "whitelist": set(user_ids)}

# ================= HELPER FUNCTIONS =================

def init_chat(chat_id):
    if chat_id not in ANTI_EDIT_SETTINGS:
        ANTI_EDIT_SETTINGS[chat_id] = {"enabled": False, "whitelist": set()}

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

# ================= COMMANDS =================

# --- /antiedit on/off ---
@nand.on_message(filters.command("antiedit") & filters.group)
async def antiedit_toggle(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await has_change_info_permission(chat_id, user_id):
        return await message.reply_text(
            "❌ <b>Access Denied:</b> Only admins with 'Change Group Info' can use this command.",
            parse_mode=ParseMode.HTML
        )

    init_chat(chat_id)
    
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: /antiedit on/off",
            parse_mode=ParseMode.HTML
        )
    
    arg = message.command[1].lower()
    if arg == "on":
        ANTI_EDIT_SETTINGS[chat_id]["enabled"] = True
        await message.reply_text("✏️ <b>Anti-Edit Enabled!</b>\nEdited messages will be deleted after 60 seconds.", parse_mode=ParseMode.HTML)
    elif arg == "off":
        ANTI_EDIT_SETTINGS[chat_id]["enabled"] = False
        await message.reply_text("😌 <b>Anti-Edit Disabled!</b>", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("Usage: /antiedit on/off", parse_mode=ParseMode.HTML)

# --- /authedit ---
@nand.on_message(filters.command("authedit") & filters.group)
async def authedit_user(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await has_change_info_permission(chat_id, user_id):
        return await message.reply_text(
            "❌ <b>Access Denied:</b> Only admins with 'Change Group Info' can use this command.",
            parse_mode=ParseMode.HTML
        )
    
    init_chat(chat_id)
    
    # Extract user
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1])
        except:
            pass
    
    if not target:
        return await message.reply_text("❓ Reply to a user or provide their ID/username.", parse_mode=ParseMode.HTML)
    
    ANTI_EDIT_SETTINGS[chat_id]["whitelist"].add(target.id)
    await message.reply_text(f"✅ {target.mention} is now exempt from Anti-Edit.", parse_mode=ParseMode.HTML)

# --- /unauthedit ---
@nand.on_message(filters.command("unauthedit") & filters.group)
async def unauthedit_user(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await has_change_info_permission(chat_id, user_id):
        return await message.reply_text(
            "❌ <b>Access Denied:</b> Only admins with 'Change Group Info' can use this command.",
            parse_mode=ParseMode.HTML
        )
    
    init_chat(chat_id)
    
    # Remove all
    if len(message.command) == 2 and message.command[1].lower() == "all":
        ANTI_EDIT_SETTINGS[chat_id]["whitelist"].clear()
        return await message.reply_text("🧹 All users removed from Anti-Edit whitelist.", parse_mode=ParseMode.HTML)
    
    # Extract user
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1])
        except:
            pass
    
    if not target:
        return await message.reply_text("❓ Reply to a user or provide their ID/username.", parse_mode=ParseMode.HTML)
    
    ANTI_EDIT_SETTINGS[chat_id]["whitelist"].discard(target.id)
    await message.reply_text(f"🚫 {target.mention} removed from Anti-Edit whitelist.", parse_mode=ParseMode.HTML)

# --- /editcommands ---
@nand.on_message(filters.command(["editcommands", "editcommand"]) & filters.group)
async def edit_commands_list(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not await has_change_info_permission(chat_id, user_id):
        return await message.reply_text(
            "❌ Only admins with 'Change Group Info' can use this command.",
            parse_mode=ParseMode.HTML
        )
    
    text = (
        "<b>✏️ Anti-Edit Commands:</b>\n\n"
        "• /antiedit on/off → Enable or Disable Anti-Edit\n"
        "• /authedit [reply/@user/id] → Exempt a user from Anti-Edit\n"
        "• /unauthedit [reply/@user/id/all] → Remove user(s) from exemption\n"
    )
    await message.reply_text(text, parse_mode=ParseMode.HTML)

# ================= WATCHER =================

WARNING_TEXTS = [
    "⚠️ Hey {mention}, editing messages is not allowed!",
    "⏰ {mention}, your edited message will be deleted in 60 seconds!",
    "❌ {mention}, stop editing messages!",
    "🛡️ {mention}, Anti-Edit is active!"
]

@nand.on_edited_message(filters.group)
async def anti_edit_watcher(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return
    
    init_chat(chat_id)
    
    # Feature enabled?
    if not ANTI_EDIT_SETTINGS[chat_id]["enabled"]:
        return
    
    # Whitelist check
    if user.id in ANTI_EDIT_SETTINGS[chat_id]["whitelist"]:
        return
    
    # Bot delete permission
    if not await bot_can_delete(chat_id):
        return await message.reply_text("❌ I need delete permissions to enforce Anti-Edit!")
    
    # Send warning
    mention = user.mention
    text = random.choice(WARNING_TEXTS).format(mention=mention)
    
    bot_username = client.me.username if client.me else BOT_USERNAME
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{bot_username}?startgroup=true"),
            InlineKeyboardButton("📢 Support", url="https://t.me/RoboKaty")
        ]
    ])
    
    try:
        warn_msg = await message.reply_text(text, reply_markup=buttons)
        await asyncio.sleep(60)
        # Delete both messages
        await message.delete()
        await warn_msg.delete()
    except:
        pass
