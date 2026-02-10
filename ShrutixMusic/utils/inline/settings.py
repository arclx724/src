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
    
