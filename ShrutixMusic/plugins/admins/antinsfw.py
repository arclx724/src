import io
import aiohttp
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ChatMemberStatus

from ShrutixMusic import nand
from ShrutixMusic.utils.db import (
    add_nsfw_api, 
    get_nsfw_api, 
    remove_nsfw_api, 
    get_all_nsfw_apis_count,
    set_antinsfw_status, 
    is_antinsfw_enabled
)
from config import OWNER_ID, SUPPORT_CHAT

# SightEngine API URL
API_URL = "https://api.sightengine.com/1.0/check.json"

# ======================================================
# 1. API MANAGEMENT (Owner Only)
# ======================================================

@nand.on_message(filters.command(["addapi", "addamthy"]) & filters.private)
async def add_nsfw_api_cmd(client, message: Message):
    if len(message.command) != 3:
        await message.reply_text("Usage: `/addapi <api_user> <api_secret>`")
        return
    
    # Security Check
    if message.from_user.id != int(OWNER_ID):
        await message.reply_text("❌ **Access Denied!** Only Owner can use this.")
        return

    api_user = message.command[1]
    api_secret = message.command[2]
    
    try:
        await add_nsfw_api(api_user, api_secret)
        if message.command[0] == "addamthy":
            await message.reply_text(f"🎉 **Thanks for contributing!**\nAPI Key Added successfully.")
        else:
            await message.reply_text("✅ **API Added Successfully!**")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@nand.on_message(filters.command("checkapi") & filters.private)
async def check_api_stats(client, message: Message):
    if message.from_user.id != int(OWNER_ID):
        return
    
    count = await get_all_nsfw_apis_count()
    # 1 Key = 2000 requests approx (Free Tier)
    total_scans = count * 2000
    
    await message.reply_text(
        f"📊 **SightEngine Stats**\n\n"
        f"🔑 **Active Keys:** `{count}`\n"
        f"📉 **Est. Capacity:** `~{total_scans} Scans`"
    )

# ======================================================
# 2. GROUP SETTINGS (Admins)
# ======================================================

@nand.on_message(filters.command("antinsfw") & filters.group)
async def antinsfw_switch(client, message: Message):
    # Admin Permission Check
    try:
        user = await client.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("❌ **Access Denied!** Only Admins can use this command.")
            return
    except:
        return

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg == "on":
            await set_antinsfw_status(message.chat.id, True)
            await message.reply_text("🔞 **Anti-NSFW System Enabled!**\nScanning incoming media...")
        elif arg == "off":
            await set_antinsfw_status(message.chat.id, False)
            await message.reply_text("😌 **Anti-NSFW System Disabled!**")
    else:
        await message.reply_text("Usage: `/antinsfw on` or `/antinsfw off`")

# ======================================================
# 3. SCANNER LOGIC
# ======================================================

async def scan_file_in_memory(file_stream):
    """
    Uploads file from RAM to API. Handles key rotation.
    """
    api_data = await get_nsfw_api()
    if not api_data:
        return None 

    try:
        data = aiohttp.FormData()
        data.add_field('models', 'nudity,wad,gore')
        data.add_field('api_user', api_data['api_user'])
        data.add_field('api_secret', api_data['api_secret'])
        
        # Reset pointer
        file_stream.seek(0)
        data.add_field('media', file_stream, filename='image.jpg')

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=data) as resp:
                result = await resp.json()
        
        # API Error Handling (Rate Limits)
        if result['status'] == 'failure':
            error_code = result.get('error', {}).get('code')
            # 21: Rate limit, 23: Monthly limit, 103: Invalid Key
            if error_code in [21, 23, 103]: 
                await remove_nsfw_api(api_data['api_user'])
                return await scan_file_in_memory(file_stream) # Retry with next key
            return None
        
        return result
    except Exception:
        return None

# Helper for Alerts
async def send_alert(message, text, buttons):
    try:
        warn_msg = await message.reply_text(text, reply_markup=buttons)
        await asyncio.sleep(60) # 60 sec baad warning delete
        await warn_msg.delete()
    except:
        pass

@nand.on_message(filters.group & (filters.photo | filters.video | filters.sticker | filters.document | filters.animation), group=35)
async def nsfw_watcher(client, message: Message):
    chat_id = message.chat.id
    
    # Check Database Status
    if not await is_antinsfw_enabled(chat_id):
        return

    # Skip trusted users (optional logic add kar sakte hain)

    media = None
    
    # --- FAST SELECTION LOGIC (Thumbnail Priority) ---
    if message.photo:
        # Original photo ke bajaye chhota thumbnail lo (Speed up 10x)
        if message.photo.thumbs:
            media = message.photo.thumbs[-1]
        else:
            media = message.photo
    elif message.sticker:
        if message.sticker.thumbs:
            media = message.sticker.thumbs[-1]
        elif not message.sticker.is_animated and not message.sticker.is_video:
            media = message.sticker
    elif message.video:
        if message.video.thumbs:
            media = message.video.thumbs[-1]
    elif message.animation: 
        if message.animation.thumbs:
            media = message.animation.thumbs[-1]
    elif message.document and message.document.mime_type and "image" in message.document.mime_type:
        if message.document.thumbs:
            media = message.document.thumbs[-1]
        else:
            media = message.document
    # ------------------------------------------------

    if not media:
        return 

    # Size Check (Skip if > 5MB)
    if hasattr(media, 'file_size') and media.file_size > 5 * 1024 * 1024: 
        return 

    try:
        # 1. Download to RAM (No Disk I/O)
        # in_memory=True bahut fast hai
        file_stream = await client.download_media(media, in_memory=True)
        
        if not file_stream:
            return

        # 2. Scan via API
        result = await scan_file_in_memory(file_stream)
        
        if not result: 
            return 

        # 3. Parse NSFW Score
        nsfw_score = 0
        
        # Nudity
        if 'nudity' in result:
            # Raw aur Partial nudity check
            nsfw_score = max(nsfw_score, result['nudity'].get('raw', 0), result['nudity'].get('partial', 0))
        
        # Weapon / Drugs / Gore
        if 'wad' in result:
            nsfw_score = max(nsfw_score, result['wad'].get('weapon', 0))
        
        if 'gore' in result:
             # Gore structure can vary
             g = result['gore']
             val = g.get('prob', 0) if isinstance(g, dict) else (g if isinstance(g, (float, int)) else 0)
             nsfw_score = max(nsfw_score, val)

        # 4. ACTION (Threshold > 60%)
        if nsfw_score > 0.60:
            percent = int(nsfw_score * 100)
            
            # Step A: Delete First (User experience: Instant removal)
            try: await message.delete()
            except: pass 
            
            # Step B: Prepare Alert
            text = (
                f"⚠️ **NSFW Detected!**\n"
                f"User: {message.from_user.mention}\n"
                f"Certainty: {percent}%\n"
                f"**Action: Deleted** 🗑️"
            )
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url=SUPPORT_CHAT)]
            ])
            
            # Step C: Send Alert Asynchronously (Don't wait for it)
            asyncio.create_task(send_alert(message, text, buttons))

    except Exception:
        # Production mein errors ignore karein
        pass
          
