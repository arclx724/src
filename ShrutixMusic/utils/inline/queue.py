from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def queue_markup(_, DUR, CPLAY, videoid, played, dur):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["QU_B_1"], callback_data=f"GetQueued {CPLAY}|{videoid}"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}"
            ),
        ],
    ]
    return buttons

def queue_back_markup(_, CPLAY):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"], callback_data=f"queue_back_timer {CPLAY}"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons
    
