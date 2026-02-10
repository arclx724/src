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
    
