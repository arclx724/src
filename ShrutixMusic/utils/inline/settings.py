import config
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def setting_markup(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="Audio Quality", callback_data="AQ"
            ),
            InlineKeyboardButton(
                text="Auth Users", callback_data="AU"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Clean Mode", callback_data="CM"
            ),
            InlineKeyboardButton(
                text="Play Mode", callback_data="PM"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Vote Mode", callback_data="VM"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons

def audio_quality_markup(_, current):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["ST_B_1"], callback_data="AQ|High"
            ),
            InlineKeyboardButton(
                text=_["ST_B_2"], callback_data="AQ|Medium"
            ),
            InlineKeyboardButton(
                text=_["ST_B_3"], callback_data="AQ|Low"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"], callback_data="settings_helper"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons

def aq_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="Low",
                callback_data=f"AQ|Low|{chat_id}",
            ),
            InlineKeyboardButton(
                text="Medium",
                callback_data=f"AQ|Medium|{chat_id}",
            ),
            InlineKeyboardButton(
                text="High",
                callback_data=f"AQ|High|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ],
    ]
    return buttons

def cleanmode_settings_markup(_, status):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["ST_B_4"], callback_data="CM|True"
            ),
            InlineKeyboardButton(
                text=_["ST_B_5"], callback_data="CM|False"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"], callback_data="settings_helper"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons

def auth_users_markup(_, status):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["ST_B_6"], callback_data="AU|True"
            ),
            InlineKeyboardButton(
                text=_["ST_B_7"], callback_data="AU|False"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"], callback_data="settings_helper"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons

def playmode_users_markup(_, status):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["ST_B_8"], callback_data="PM|Everyone"
            ),
            InlineKeyboardButton(
                text=_["ST_B_9"], callback_data="PM|Admin"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"], callback_data="settings_helper"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons

def vote_mode_markup(_, status):
    buttons = [
        [
            InlineKeyboardButton(
                text="Enable", callback_data="VOTE|True"
            ),
            InlineKeyboardButton(
                text="Disable", callback_data="VOTE|False"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"], callback_data="settings_helper"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons

# --- NEW ADDITION: SUPP MARKUP (Ping ke liye) ---
def supp_markup(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="Support",
                url=config.SUPPORT_CHAT,
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ],
    ]
    return buttons
    
