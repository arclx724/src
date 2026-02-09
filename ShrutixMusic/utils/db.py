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
  
