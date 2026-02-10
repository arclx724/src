from pyrogram.types import InlineKeyboardButton

import config
from ShrutixMusic import nand


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{nand.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{nand.username}?startgroup=true",
            )
        ],
        [InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_back_helper")],
        [
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
        [
            # FIX: user_id hata kar direct link lagaya hai taaki privacy error na aaye.
            # Agar username 'NoxxOP' nahi hai, toh ise change kar lein.
            InlineKeyboardButton(text=_["S_B_5"], url="https://t.me/SlayWithRose"),
        ],
    ]
    return buttons
