import time
from pyrogram import filters
from pyrogram.types import ChatMemberUpdated, ChatPrivileges, Message
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.utils.db import (
    whitelist_user, 
    unwhitelist_user, 
    is_user_whitelisted, 
    get_whitelisted_users
)
from config import OWNER_ID

# ================= CONFIGURATION =================
# 3 Actions in 30 Seconds = Nuke Attempt
LIMIT = 3
TIME_FRAME = 30  
TRAFFIC = {} # RAM Cache: {chat_id: {user_id: [timestamps]}}

# ================= HELPER FUNCTION =================
async def punish_nuker(client, chat_id, user, count):
    """
    Hacker ko Demote karega
    """
    try:
        # Pehle Demote karo (Fastest Action)
        # Saari permissions False kar denge
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
        
        # Fir Alert bhejo
        await client.send_message(
            chat_id,
            f"🚨 **ANTI-NUKE TRIGGERED**\n\n"
            f"👮‍♂️ **Admin:** {user.mention}\n"
            f"🔢 **Action Count:** {count}/{LIMIT}\n"
            f"✅ **Penalty:** Demoted Successfully."
        )
        
    except Exception as e:
        # Agar fail ho jaye (Hierarchy Issue - Bot ka rank user se neeche hai)
        await client.send_message(
            chat_id,
            f"⚠️ **Security Alert:** Detected mass-action by {user.mention}, but I cannot demote them due to Telegram limitations (My rank is lower than theirs)."
        )

# ================= COMMANDS =================

@nand.on_message(filters.command("whitelist") & filters.group)
async def whitelist_handler(client, message: Message):
    # Sirf Owner hi whitelist kar sakta hai security ke liye
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status != ChatMemberStatus.OWNER and message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only Group Owner can whitelist users.")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to whitelist them from Anti-Nuke.")
    
    user = message.reply_to_message.from_user
    await whitelist_user(message.chat.id, user.id)
    await message.reply_text(f"🛡️ {user.mention} is now **Whitelisted** (Anti-Nuke will ignore them).")

@nand.on_message(filters.command("unwhitelist") & filters.group)
async def unwhitelist_handler(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status != ChatMemberStatus.OWNER and message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only Group Owner can use this.")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to remove them from whitelist.")
    
    user = message.reply_to_message.from_user
    await unwhitelist_user(message.chat.id, user.id)
    await message.reply_text(f"⚠️ {user.mention} is removed from Whitelist.")

# ================= MAIN WATCHER =================

@nand.on_chat_member_updated(filters.group, group=5)
async def nuke_watcher(client, update: ChatMemberUpdated):
    chat = update.chat
    
    # 1. Basic Checks
    if not update.from_user:
        return
    actor = update.from_user
    
    # Ignore Bot itself and Global Owner
    if actor.id == client.me.id or actor.id == OWNER_ID:
        return

    # Ignore Whitelisted Admins
    if await is_user_whitelisted(chat.id, actor.id):
        return

    # 2. Define Action Type
    action_detected = False
    
    # Analyze Old vs New Status
    old_status = update.old_chat_member.status if update.old_chat_member else ChatMemberStatus.LEFT
    new_status = update.new_chat_member.status if update.new_chat_member else ChatMemberStatus.LEFT
    
    # A. Kick/Ban Detection
    # Agar user pehle member/admin tha aur ab BANNED/LEFT hai
    if new_status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
        # Target kaun hai?
        target = update.old_chat_member.user if update.old_chat_member else update.new_chat_member.user
        
        # Agar actor ne khud ko leave kiya hai to ignore karo
        if actor.id == target.id:
            return
        
        # Agar actor ne kisi aur ko nikala hai -> Action!
        action_detected = True

    # 3. Traffic Logic
    if action_detected:
        current_time = time.time()
        
        # Initialize Memory
        if chat.id not in TRAFFIC:
            TRAFFIC[chat.id] = {}
        if actor.id not in TRAFFIC[chat.id]:
            TRAFFIC[chat.id][actor.id] = []
        
        # Add timestamp
        TRAFFIC[chat.id][actor.id].append(current_time)
        
        # Clean old actions (jo 30 seconds se purane hain unhe hata do)
        TRAFFIC[chat.id][actor.id] = [t for t in TRAFFIC[chat.id][actor.id] if current_time - t < TIME_FRAME]
        
        # Check Count
        count = len(TRAFFIC[chat.id][actor.id])
        
        if count >= LIMIT:
            await punish_nuker(client, chat.id, actor, count)
            # Reset counter after punishment to avoid spamming alerts
            TRAFFIC[chat.id][actor.id] = []
          
