from ShrutixMusic.core.mongo import mongodb  # Apne mongo import ke hisaab se adjust karein

warnsdb = mongodb.warns

async def get_warns(chat_id: int, user_id: int) -> int:
    result = await warnsdb.find_one({"chat_id": chat_id, "user_id": user_id})
    if not result:
        return 0
    return result["warns"]

async def add_warn(chat_id: int, user_id: int) -> int:
    warns = await get_warns(chat_id, user_id)
    warns += 1
    await warnsdb.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"warns": warns}},
        upsert=True,
    )
    return warns

async def reset_warns(chat_id: int, user_id: int):
    await warnsdb.delete_one({"chat_id": chat_id, "user_id": user_id})
  
# ==========================================================
# MEDIA AUTO DELETE DATABASE
# ==========================================================
mediadb = mongodb.mediadelete

async def set_media_delete_status(chat_id: int, status: bool):
    """Enable or Disable Auto Delete"""
    await mediadb.update_one(
        {"chat_id": chat_id},
        {"$set": {"status": status}},
        upsert=True
    )

async def set_media_delete_delay(chat_id: int, delay: int):
    """Set the time delay in seconds"""
    # Jab time set karein, to automatically status ON kar dete hain
    await mediadb.update_one(
        {"chat_id": chat_id},
        {"$set": {"delay": delay, "status": True}}, 
        upsert=True
    )

async def get_media_delete_config(chat_id: int):
    """Returns (status, delay)"""
    data = await mediadb.find_one({"chat_id": chat_id})
    if not data:
        # Default: OFF, 30 Seconds
        return False, 30
    return data.get("status", False), data.get("delay", 30)
    
# ==========================================================
# ANTI-NUKE WHITELIST DATABASE
# ==========================================================
nukedb = mongodb.antinuke

async def whitelist_user(chat_id: int, user_id: int):
    """Add user to whitelist (Ignore checks)"""
    await nukedb.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"whitelist": user_id}},
        upsert=True
    )

async def unwhitelist_user(chat_id: int, user_id: int):
    """Remove user from whitelist"""
    await nukedb.update_one(
        {"chat_id": chat_id},
        {"$pull": {"whitelist": user_id}}
    )

async def is_user_whitelisted(chat_id: int, user_id: int) -> bool:
    """Check if user is trusted"""
    doc = await nukedb.find_one({"chat_id": chat_id})
    if not doc:
        return False
    return user_id in doc.get("whitelist", [])

async def get_whitelisted_users(chat_id: int):
    doc = await nukedb.find_one({"chat_id": chat_id})
    return doc.get("whitelist", []) if doc else []
    
# ==========================================================
# ANTI-NSFW DATABASE
# ==========================================================
nsfwdb = mongodb.nsfw
apidb = mongodb.nsfw_api

# --- Group Settings ---
async def set_antinsfw_status(chat_id: int, status: bool):
    await nsfwdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"status": status}},
        upsert=True
    )

async def is_antinsfw_enabled(chat_id: int) -> bool:
    doc = await nsfwdb.find_one({"chat_id": chat_id})
    return doc.get("status", False) if doc else False

# --- API Key Management (Rotation) ---
async def add_nsfw_api(api_user: str, api_secret: str):
    await apidb.insert_one({
        "api_user": api_user,
        "api_secret": api_secret,
        "usage": 0
    })

async def get_nsfw_api():
    # Get random key or least used key
    doc = await apidb.find_one({}, sort=[("usage", 1)])
    if doc:
        # Increment usage
        await apidb.update_one({"_id": doc["_id"]}, {"$inc": {"usage": 1}})
        return doc
    return None

async def remove_nsfw_api(api_user: str):
    await apidb.delete_one({"api_user": api_user})

async def get_all_nsfw_apis_count():
    return await apidb.count_documents({})
    
# ==========================================================
# ANTI-EDIT DATABASE
# ==========================================================
antieditdb = mongodb.antiedit

async def set_antiedit_status(chat_id: int, status: bool):
    """Enable or Disable Anti-Edit"""
    await antieditdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"status": status}},
        upsert=True
    )

async def is_antiedit_enabled(chat_id: int) -> bool:
    """Check if enabled"""
    doc = await antieditdb.find_one({"chat_id": chat_id})
    return doc.get("status", False) if doc else False

# ==========================================================
# ANTI-BOT DATABASE
# ==========================================================
antibotdb = mongodb.antibot

async def set_antibot_status(chat_id: int, status: bool):
    """Enable or Disable Anti-Bot"""
    await antibotdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"status": status}},
        upsert=True
    )

async def is_antibot_enabled(chat_id: int) -> bool:
    """Check if enabled"""
    doc = await antibotdb.find_one({"chat_id": chat_id})
    return doc.get("status", False) if doc else False
    
